import z3
from reqops.utils.ast_inspector import analyze_ast_performance
from reqops.utils.z3_compiler import compile_folast_to_z3

class ReqOpsCritiqueEngine:
    """
    Module C: Critique Engine.
    Executes composite reward optimizations and runs the Z3 math solver
    to verify deterministic logical requirements against generated code AST structures.
    """
    def __init__(self, alpha=0.5, beta=0.4, gamma=0.1):
        # Parameters for composite reward
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def calculate_composite_reward(self, source_code: str, r_llm=0.8, perplexity=1.5) -> dict:
        """
        Calculates composite reward scoring:
        r = alpha * r_AST + beta * r_LLM - gamma * PP
        """
        # Step 1: Analyze static AST pattern rewards (r_AST)
        ast_result = analyze_ast_performance(source_code)
        r_ast = ast_result["score"]
        
        # Step 2: Compute composite score
        # Cap Perplexity penalty: we normalize perplexity (e.g. log-likelihood penalty)
        # PP penalty is proportional to gamma * perplexity, but we make sure the final reward is normalized
        composite_score = (self.alpha * r_ast) + (self.beta * r_llm) - (self.gamma * perplexity)
        
        # Clamp reward to [0, 1]
        clamped_score = max(0.0, min(1.0, composite_score))
        
        return {
            "composite_score": clamped_score,
            "r_ast": r_ast,
            "r_llm": r_llm,
            "perplexity": perplexity,
            "ast_violations": ast_result["violations"]
        }

    def verify_logical_consistency(self, folast_dict: dict, code_ast_conditions: list = None) -> dict:
        """
        Compiles the logical requirement from FOLAST, adds any code AST constraints
        (such as invariants extracted from Code_AST_Structure.json),
        and runs the Z3 Theorem Prover to verify mathematical consistency.
        """
        solver = z3.Solver()
        
        # Step 1: Compile requirement FOLAST to Z3 expression
        try:
            req_expr, symbol_table = compile_folast_to_z3(folast_dict)
            solver.add(req_expr)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to compile FOLAST to Z3: {str(e)}"
            }

        # Step 2: Add any additional Code conditions/assertions if present
        # If code ast defines specific facts (e.g. IsSecure(db), etc.), we translate them to assertions
        if code_ast_conditions:
            for cond in code_ast_conditions:
                # E.g. simple custom z3 assertions can be injected for verification
                solver.add(cond)

        # Step 3: Run Z3 Prover Check
        check_result = solver.check()
        
        if check_result == z3.sat:
            # Consistent! Provide model/sample assignments
            model = solver.model()
            # Serialize model assignments for debugging
            model_info = {}
            for decl in model.decls():
                model_info[decl.name()] = str(model[decl])
                
            return {
                "status": "PASS",
                "message": "Requirements model is mathematically consistent & satisfied.",
                "verification": "SAT",
                "counterexamples": None,
                "model_assignments": model_info
            }
        elif check_result == z3.unsat:
            # Inconsistent or contradicts! Provide proof or core
            try:
                proof = solver.proof()
                proof_str = str(proof)
            except Exception:
                proof_str = "Mathematical contradiction found."
                
            return {
                "status": "FAIL",
                "message": "Mathematical contradiction or requirement violation detected.",
                "verification": "UNSAT",
                "proof_trace": proof_str,
                "counterexamples": "Requirements and code conditions are mutually exclusive."
            }
        else:
            return {
                "status": "UNKNOWN",
                "message": "Z3 solver could not determine consistency (Resource limit or undecidable FOL domain).",
                "verification": "UNKNOWN",
                "counterexamples": None
            }
