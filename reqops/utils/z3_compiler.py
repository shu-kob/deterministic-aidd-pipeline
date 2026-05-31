import z3
import json

class FOLZ3Compiler:
    """
    A 2-pass compiler that compiles FOLAST schema trees into executable Z3 formulas.
    """
    def __init__(self):
        # Env table: holds Z3 variables, functions, and constant declarations
        self.symbol_table = {}
        # Define a general entity sort for first-order logic domains
        self.entity_sort = z3.DeclareSort('Entity')
        self.boolean_sort = z3.BoolSort()
        # Dictionary of compiled variables (Z3 Const) to prevent duplicates
        self.variables = {}
        # Dictionary of compiled predicates (Z3 Function)
        self.predicates = {}

    def compile(self, folast_dict: dict):
        """
        Main compile entrypoint.
        Runs 1st pass to collect declarations, then 2nd pass to generate expressions.
        """
        # Pass 1: Declaration Collection
        self._collect_declarations(folast_dict)
        
        # Pass 2: Expression Generation
        z3_expr = self._generate_expression(folast_dict)
        return z3_expr, self.symbol_table

    def _collect_declarations(self, node: dict):
        """
        Pass 1: Collects all constants, variables, and predicate signatures,
        and registers them in Z3 environments.
        """
        if not node:
            return

        node_type = node.get("node_type")
        operator = node.get("operator")

        if node_type == "Quantified":
            var_name = node.get("variable")
            if var_name and var_name not in self.variables:
                self.variables[var_name] = z3.Const(var_name, self.entity_sort)
            self._collect_declarations(node.get("scope"))

        elif node_type == "Negation":
            self._collect_declarations(node.get("scope"))

        elif node_type == "Logical":
            self._collect_declarations(node.get("left_operand"))
            self._collect_declarations(node.get("right_operand"))

        elif node_type == "Atomic":
            pred_name = node.get("predicate_name")
            args = node.get("arguments", [])
            
            # Register argument names as variables or constants
            for arg in args:
                arg_name = arg.get("name")
                arg_type = arg.get("type")
                if arg_name not in self.variables:
                    self.variables[arg_name] = z3.Const(arg_name, self.entity_sort)

            # Define predicate function signature based on arity
            if pred_name and pred_name not in self.predicates:
                arity = len(args)
                if arity == 0:
                    # Arity 0 is a simple boolean variable
                    self.predicates[pred_name] = z3.Bool(pred_name)
                else:
                    # Arity N is a Z3 Function mapping Entity sorts to Bool
                    sig = [self.entity_sort] * arity + [self.boolean_sort]
                    self.predicates[pred_name] = z3.Function(pred_name, *sig)

    def _generate_expression(self, node: dict):
        """
        Pass 2: Recursively compiles logical structures to Z3 terms.
        """
        if not node:
            return None

        node_type = node.get("node_type")
        operator = node.get("operator")

        if node_type == "Quantified":
            var_name = node.get("variable")
            z3_var = self.variables[var_name]
            scope_expr = self._generate_expression(node.get("scope"))
            
            if operator == "ForAll":
                return z3.ForAll([z3_var], scope_expr)
            elif operator == "ThereExists":
                return z3.Exists([z3_var], scope_expr)

        elif node_type == "Negation":
            scope_expr = self._generate_expression(node.get("scope"))
            return z3.Not(scope_expr)

        elif node_type == "Logical":
            left_expr = self._generate_expression(node.get("left_operand"))
            right_expr = self._generate_expression(node.get("right_operand"))
            
            if operator == "And":
                return z3.And(left_expr, right_expr)
            elif operator == "Or":
                return z3.Or(left_expr, right_expr)
            elif operator == "If":
                return z3.Implies(left_expr, right_expr)
            elif operator == "OnlyIf":
                return z3.Implies(right_expr, left_expr)
            elif operator == "IfAndOnlyIf":
                return left_expr == right_expr

        elif node_type == "Atomic":
            pred_name = node.get("predicate_name")
            args = node.get("arguments", [])
            
            if not pred_name:
                return z3.BoolVal(True)
                
            pred_func = self.predicates[pred_name]
            
            if len(args) == 0:
                # Return the bare boolean constant
                return pred_func
            else:
                # Call the Z3 Function with the compiled Z3 constant arguments
                z3_args = [self.variables[arg.get("name")] for arg in args]
                return pred_func(*z3_args)

        # Fallback
        return z3.BoolVal(True)


def compile_folast_to_z3(folast_data: dict):
    """
    Utility function to compile a FOLAST dictionary to Z3 expression and symbol declarations.
    """
    compiler = FOLZ3Compiler()
    return compiler.compile(folast_data)
