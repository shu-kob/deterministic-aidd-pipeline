import re
import json

def segment_sentences(text: str) -> list[str]:
    """
    SaT (Segment Any Text) - Robust sentence boundary detector.
    Splits text on English periods (followed by space) and Japanese '。',
    while preventing splitting on abbreviations (e.g., U.S., Prof., e.g.).
    """
    if not text:
        return []

    # Standardize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Common abbreviations that should not trigger sentence boundaries
    abbrevs = [
        "U.S.", "Prof.", "Dr.", "e.g.", "i.e.", "vs.", "al.", "etc.",
        "Jan.", "Feb.", "Mar.", "Apr.", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."
    ]
    
    # Protect abbreviations by temporarily replacing their periods
    protected_text = text
    for i, abbrev in enumerate(abbrevs):
        # Escape for regex and replace the period with a special placeholder
        escaped = re.escape(abbrev)
        placeholder = f"__ABBREV_{i}__"
        protected_text = re.sub(r'\b' + escaped, placeholder, protected_text)

    # Split on Japanese full-width periods and English periods followed by space/newline
    # Also split on double newlines
    raw_sentences = []
    current_chunk = []
    
    # Simple character scanning or split by regex
    # Split by: '。' or '\n+' or '. ' or '.\n'
    split_pattern = re.compile(r'(。|\n+|(?:(?<=\.)|(?<=\?)|(?<=!))\s+(?=[A-Z\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]))')
    parts = split_pattern.split(protected_text)
    
    current_sentence = ""
    for part in parts:
        if not part:
            continue
        if part == "。" or "\n" in part or (part.isspace() and len(part) > 1):
            if current_sentence.strip():
                if part == "。":
                    current_sentence += "。"
                raw_sentences.append(current_sentence.strip())
                current_sentence = ""
        else:
            # If it's a split punctuation marker that is a space, we just finalize
            if part.isspace():
                if current_sentence.strip():
                    raw_sentences.append(current_sentence.strip())
                    current_sentence = ""
            else:
                current_sentence += part
                
    if current_sentence.strip():
        raw_sentences.append(current_sentence.strip())

    # Restore the protected abbreviations
    final_sentences = []
    for sentence in raw_sentences:
        restored = sentence
        for i, abbrev in enumerate(abbrevs):
            placeholder = f"__ABBREV_{i}__"
            restored = restored.replace(placeholder, abbrev)
        # Clean up inner whitespace/newlines
        restored = re.sub(r'\s+', ' ', restored).strip()
        if restored:
            final_sentences.append(restored)

    return final_sentences


def parse_logic_string(expr: str) -> dict:
    """
    Parses a First-Order Logic (FOL) string expression into a FOLAST node dict.
    Example inputs:
      - "forall x (User(x) -> CanLogin(x))"
      - "exists y (Database(y) and IsSecure(y))"
      - "not (Active(x))"
      - "Performance(x, y) & Efficient(y)"
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Cannot parse empty expression")

    # Helper: remove matching outer parentheses if they wrap the entire expression
    def strip_outer_parens(s: str) -> str:
        s = s.strip()
        if s.startswith('(') and s.endswith(')'):
            # Verify they actually match each other
            depth = 0
            for idx, char in enumerate(s):
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        if idx == len(s) - 1:
                            return strip_outer_parens(s[1:-1])
                        else:
                            break
        return s

    expr = strip_outer_parens(expr)

    # 1. Parse Quantifiers
    # Matches: forall <var> ( <body> ) or exists <var> ( <body> )
    # Let's also support short hands: \forall, \exists
    quant_match = re.match(r'^(forall|exists|\\forall|\\exists)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(.+)$', expr, re.IGNORECASE)
    if quant_match:
        q_type_str, var_name, scope_str = quant_match.groups()
        q_type_str = q_type_str.lower()
        operator = "ForAll" if "forall" in q_type_str else "ThereExists"
        
        # Clean scope_str
        scope_str = strip_outer_parens(scope_str)
        
        return {
            "node_type": "Quantified",
            "operator": operator,
            "variable": var_name,
            "scope": parse_logic_string(scope_str)
        }

    # 2. Parse Negation
    # Matches: not ( <body> ) or ~ ( <body> )
    neg_match = re.match(r'^(not|~|\\neg)\s+(.+)$', expr, re.IGNORECASE)
    if neg_match:
        _, scope_str = neg_match.groups()
        scope_str = strip_outer_parens(scope_str)
        return {
            "node_type": "Negation",
            "operator": "Not",
            "scope": parse_logic_string(scope_str)
        }

    # 3. Parse Binary Logical Operators
    # Precedence (lowest to highest, meaning we split on lowest first):
    # IfAndOnlyIf (<->, iff, <=>)
    # If (->, implies, =>)
    # Or (|, or, \lor)
    # And (&, and, \land)
    binary_ops = [
        (["<->", "iff", "<=>", "⇔"], "IfAndOnlyIf"),
        (["->", "implies", "=>", "⇒"], "If"),
        (["|", "or", "∨", "\\lor"], "Or"),
        (["&", "and", "^", "∧", "\\land"], "And")
    ]

    for op_aliases, op_enum in binary_ops:
        # We need to find the operator at parenthesis depth 0
        depth = 0
        found_idx = -1
        matched_alias = None
        
        # Scan through the string
        i = 0
        while i < len(expr):
            char = expr[i]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif depth == 0:
                # Check if any operator alias matches starting at index i
                for alias in op_aliases:
                    # Match word boundary if alias is alphabetic
                    is_word = alias[0].isalpha()
                    if expr[i:i+len(alias)] == alias:
                        if is_word:
                            # Check boundaries to avoid matching sub-words (e.g. 'and' inside 'brand')
                            before_ok = (i == 0 or not expr[i-1].isalnum())
                            after_ok = (i + len(alias) == len(expr) or not expr[i+len(alias)].isalnum())
                            if not (before_ok and after_ok):
                                continue
                        found_idx = i
                        matched_alias = alias
                        break
            if found_idx != -1:
                break
            i += 1

        if found_idx != -1:
            left_part = expr[:found_idx].strip()
            right_part = expr[found_idx + len(matched_alias):].strip()
            return {
                "node_type": "Logical",
                "operator": op_enum,
                "left_operand": parse_logic_string(left_part),
                "right_operand": parse_logic_string(right_part)
            }

    # 4. Parse Atomic Predicate
    # Format: PredicateName(arg1, arg2, ...) or PredicateName
    atomic_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)(?:\((.*)\))?$', expr)
    if atomic_match:
        pred_name, args_str = atomic_match.groups()
        arguments = []
        if args_str:
            # Simple comma split (assuming arguments do not contain parentheses themselves)
            raw_args = [a.strip() for a in args_str.split(',') if a.strip()]
            for arg in raw_args:
                # Deduce argument type: Single letters or starting with x,y,z or lower case is Variable, others Constant
                # Standard convention
                is_var = arg.islower() and (len(arg) == 1 or arg[0] in ['x', 'y', 'z', 'u', 'v', 'w'])
                arg_type = "Variable" if is_var else "Constant"
                arguments.append({
                    "type": arg_type,
                    "name": arg
                })
        return {
            "node_type": "Atomic",
            "operator": "None",
            "predicate_name": pred_name,
            "arguments": arguments
        }

    raise ValueError(f"Unable to parse expression as FOL: {expr}")


def parse_requirements_to_folast(spec_text: str) -> list[dict]:
    """
    Extracts requirements sentences, attempts to parse them to FOLAST,
    and returns a list of FOLAST nodes.
    """
    sentences = segment_sentences(spec_text)
    ast_nodes = []
    for sentence in sentences:
        # Search for logic strings inside brackets or starting with logical words
        # E.g. [forall x: ...] or lines that contain logic operators
        # We can extract any substring that looks like logical expressions or try to parse sentences
        # Let's check if the sentence looks like a logic expression
        is_logical = (
            "forall" in sentence.lower() or 
            "exists" in sentence.lower() or 
            "->" in sentence or 
            "&" in sentence or 
            "|" in sentence or
            "not(" in sentence.lower() or
            re.search(r'[a-zA-Z0-9_]+\([a-zA-Z0-9_,\s]+\)', sentence)
        )
        if is_logical:
            # If the sentence contains Japanese explanation followed by logic, extract the logic
            # e.g., "要件A: forall x (User(x) -> CanLogin(x))"
            logic_part = sentence
            match = re.search(r'([a-zA-Z_\\~].*)$', sentence)
            if match:
                potential_logic = match.group(1).strip()
                # Remove trailing Japanese periods or explanation marks if any
                potential_logic = re.sub(r'[。、]$', '', potential_logic).strip()
                try:
                    ast_node = parse_logic_string(potential_logic)
                    ast_nodes.append(ast_node)
                except Exception:
                    # If parsing failed, skip or log
                    pass
    return ast_nodes


def save_folast_to_file(nodes: list[dict], filepath: str):
    """
    Saves a list of FOLAST nodes as a compliant FOLAST JSON file.
    If multiple nodes are parsed, wraps them or saves the first primary logical node.
    """
    # According to FOLAST_Schema.json, the root is a single object representing a node
    # If we have multiple, we can wrap them under an 'And' logical node
    if not nodes:
        root_node = {
            "node_type": "Atomic",
            "operator": "None",
            "predicate_name": "True",
            "arguments": []
        }
    elif len(nodes) == 1:
        root_node = nodes[0]
    else:
        # Combine recursively into a nested And tree
        root_node = nodes[0]
        for next_node in nodes[1:]:
            root_node = {
                "node_type": "Logical",
                "operator": "And",
                "left_operand": root_node,
                "right_operand": next_node
            }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(root_node, f, indent=2, ensure_ascii=False)
    return root_node
