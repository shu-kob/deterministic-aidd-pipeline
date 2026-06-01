import ast

class PerformancePatternInspector(ast.NodeVisitor):
    """
    An AST visitor that statically scans code for 12 performance anti-patterns,
    collects line numbers and metadata, and calculates AST rewards.
    """
    def __init__(self):
        # 12 Anti-patterns metadata
        self.rules = {
            1: {"name": "Nested Loops", "penalty": 10},
            2: {"name": "Redundant Function Calls inside Loops", "penalty": 8},
            3: {"name": "Redundant Function Calls for Memoization", "penalty": 6},
            4: {"name": "Inefficient Use of Data Structures", "penalty": 6},
            5: {"name": "Excessive Function Calls in Loops", "penalty": 7},
            6: {"name": "Unnecessary Recursion", "penalty": 12},
            7: {"name": "Deeply Nested Conditions", "penalty": 4},
            8: {"name": "Inefficient String Concatenation", "penalty": 6},
            9: {"name": "Inefficient File/Database Operations", "penalty": 10},
            10: {"name": "Large Functions", "penalty": 8},
            11: {"name": "Inefficient Loop Terminology", "penalty": 6},
            12: {"name": "Potential Syntax Errors", "penalty": 20}
        }
        
        # Results container: ID -> list of line numbers
        self.violations = {rule_id: [] for rule_id in self.rules}
        
        # Traversal contexts
        self.loop_stack = []        # Keeps track of loop nodes we are currently inside
        self.function_stack = []    # Keeps track of function definition nodes
        self.if_nesting_depth = 0   # Track nested if conditions

    def visit_For(self, node):
        self.check_loop_nesting(node)
        self.check_inefficient_loop_range(node)
        
        self.loop_stack.append(node)
        self.generic_visit(node)
        self.loop_stack.pop()

    def visit_While(self, node):
        self.check_loop_nesting(node)
        
        self.loop_stack.append(node)
        self.generic_visit(node)
        self.loop_stack.pop()

    def visit_FunctionDef(self, node):
        # Check Rule 10: Large Functions (body length > 20 statements)
        if len(node.body) > 20:
            self.violations[10].append(node.lineno)

        self.function_stack.append(node)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_If(self, node):
        # Check Rule 7: Deeply Nested Conditions (> 3 deep)
        self.if_nesting_depth += 1
        if self.if_nesting_depth > 3:
            self.violations[7].append(node.lineno)
            
        self.generic_visit(node)
        self.if_nesting_depth -= 1

    def visit_Call(self, node):
        # Analyze function calls inside loop
        if self.loop_stack:
            # Rule 2: Redundant / high-cost function calls in loop bodies
            # For simplicity, we detect any call inside loop bodies
            self.violations[2].append(node.lineno)
            
            # Rule 5: Excessive/Specific repeated calls inside loop
            # Let's count them or check for common repeated calls
            # We flag any method/attr call inside loop as a potential excessive call
            if isinstance(node.func, ast.Attribute):
                self.violations[5].append(node.lineno)

            # Rule 9: File/Database operations inside loops (e.g. open(), execute(), query())
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in ["open", "execute", "query", "connect"]:
                    self.violations[9].append(node.lineno)
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ["execute", "query", "commit"]:
                    self.violations[9].append(node.lineno)

        # Rule 6: Unnecessary Recursion
        # Check if call is calling the current enclosing function
        if self.function_stack:
            current_func = self.function_stack[-1]
            if isinstance(node.func, ast.Name) and node.func.id == current_func.name:
                self.violations[6].append(node.lineno)

        self.generic_visit(node)

    def visit_BinOp(self, node):
        # Rule 8: Inefficient String Concatenation (+ or += inside loops)
        if self.loop_stack and isinstance(node.op, ast.Add):
            # We check if left or right operands look like strings
            # In a static analysis, we flag addition operations inside loops as potential str concat
            self.violations[8].append(node.lineno)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        # String concat via += inside loops
        if self.loop_stack and isinstance(node.op, ast.Add):
            self.violations[8].append(node.lineno)
        self.generic_visit(node)

    def visit_Compare(self, node):
        # Rule 4: Inefficient Use of Data Structures (List 'in' membership testing)
        # Check if the operator is 'In' or 'NotIn'
        for op in node.ops:
            if isinstance(op, (ast.In, ast.NotIn)):
                # If the comparator is a list literal e.g. x in [1, 2, 3], it's inefficient compared to sets
                for comp in node.comparators:
                    if isinstance(comp, ast.List):
                        self.violations[4].append(node.lineno)
                        break
        self.generic_visit(node)

    # Specific Helpers for Checks

    def check_loop_nesting(self, node):
        # Rule 1: Nested Loops
        if self.loop_stack:
            self.violations[1].append(node.lineno)

    def check_inefficient_loop_range(self, node):
        # Rule 11: Inefficient Loop Terminology (e.g., range(len(...)))
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range" and node.iter.args:
                arg = node.iter.args[0]
                if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
                    if arg.func.id == "len":
                        self.violations[11].append(node.lineno)


def analyze_ast_performance(source_code: str) -> dict:
    """
    Statically analyzes source code AST, detects anti-patterns,
    and returns detail of violations and normalized AST reward score (r_AST).
    """
    inspector = PerformancePatternInspector()
    
    try:
        root = ast.parse(source_code)
        inspector.visit(root)
    except SyntaxError:
        # Rule 12: Potential Syntax Error
        inspector.violations[12].append(1)

    # Compute reward:
    # r_AST = 1 - (sum of penalties for present patterns) / (sum of all possible penalties)
    total_possible_penalty = sum(rule["penalty"] for rule in inspector.rules.values())
    total_actual_penalty = 0
    
    active_violations = {}
    for rule_id, rule in inspector.rules.items():
        lines = sorted(list(set(inspector.violations[rule_id])))
        if lines:
            active_violations[rule_id] = {
                "name": rule["name"],
                "penalty": rule["penalty"],
                "lines": lines
            }
            total_actual_penalty += rule["penalty"]

    # Cap reward between 0.0 and 1.0
    r_ast = 1.0 - (total_actual_penalty / total_possible_penalty)
    r_ast = max(0.0, min(1.0, r_ast))

    return {
        "score": r_ast,
        "violations": active_violations,
        "total_penalty": total_actual_penalty,
        "max_penalty": total_possible_penalty
    }
