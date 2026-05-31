import ast
import json

class ASTStructureExtractor(ast.NodeVisitor):
    """
    An AST Node Visitor that extracts structural features from Python source code
    and creates a serializable JSON-friendly dictionary representation of its control structures.
    """
    def __init__(self):
        self.structure = {
            "classes": [],
            "functions": [],
            "loops": [],
            "imports": [],
            "global_variables": []
        }
        self.current_class = None
        self.current_function = None
        self.nesting_level = 0

    def visit_Import(self, node):
        for alias in node.names:
            self.structure["imports"].append({
                "type": "import",
                "name": alias.name,
                "asname": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.structure["imports"].append({
                "type": "import_from",
                "module": node.module,
                "name": alias.name,
                "asname": alias.asname,
                "line": node.lineno
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_info = {
            "name": node.name,
            "bases": [ast.unparse(base) for base in node.bases],
            "methods": [],
            "line": node.lineno
        }
        self.structure["classes"].append(class_info)
        
        # Track current class context
        prev_class = self.current_class
        self.current_class = class_info
        
        self.generic_visit(node)
        
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        # Calculate function body length (number of lines/statements)
        func_body_len = len(node.body)
        func_info = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "body_length": func_body_len,
            "line": node.lineno,
            "parent_class": self.current_class["name"] if self.current_class else None
        }
        
        if self.current_class:
            self.current_class["methods"].append(func_info)
        else:
            self.structure["functions"].append(func_info)
            
        prev_function = self.current_function
        self.current_function = func_info
        
        self.generic_visit(node)
        
        self.current_function = prev_function

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_For(self, node):
        loop_info = {
            "type": "For",
            "target": ast.unparse(node.target),
            "iter": ast.unparse(node.iter),
            "line": node.lineno,
            "nesting_level": self.nesting_level,
            "parent_function": self.current_function["name"] if self.current_function else None
        }
        self.structure["loops"].append(loop_info)
        
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_While(self, node):
        loop_info = {
            "type": "While",
            "test": ast.unparse(node.test),
            "line": node.lineno,
            "nesting_level": self.nesting_level,
            "parent_function": self.current_function["name"] if self.current_function else None
        }
        self.structure["loops"].append(loop_info)
        
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1


def parse_code_to_ast_structure(source_code: str) -> dict:
    """
    Parses Python source code and extracts its structural components.
    If syntax error is encountered, returns a structure with error details.
    """
    try:
        root = ast.parse(source_code)
        extractor = ASTStructureExtractor()
        extractor.visit(root)
        return {
            "status": "success",
            "structure": extractor.structure
        }
    except SyntaxError as e:
        return {
            "status": "syntax_error",
            "error": {
                "message": e.msg,
                "line": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        }


def save_ast_structure_to_file(structure: dict, filepath: str):
    """
    Saves Code AST structure dict as a Code_AST_Structure.json file.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
