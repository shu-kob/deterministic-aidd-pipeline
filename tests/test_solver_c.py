import pytest
from reqops.utils.ast_inspector import analyze_ast_performance
from reqops.modules.solver_c import ReqOpsCritiqueEngine

def test_ast_performance_nested_loops():
    # Loop stack and nested loop detection
    code = """
def process():
    for i in range(10):
        for j in range(5):
            print(i, j)
"""
    result = analyze_ast_performance(code)
    # Violation 1 is Nested Loops
    assert 1 in result["violations"]
    assert result["score"] < 1.0


def test_ast_performance_inefficient_ds_and_loops():
    code = """
def check_items(items):
    # Rule 4: List membership check
    is_present = 5 in [1, 2, 3, 4, 5]
    
    # Rule 11: range(len(...))
    for i in range(len(items)):
        print(items[i])
"""
    result = analyze_ast_performance(code)
    assert 4 in result["violations"]   # Inefficient Use of DS
    assert 11 in result["violations"]  # Inefficient Loop Terminology (range(len))


def test_critique_engine_reward():
    code = """
def good_code():
    pass
"""
    engine = ReqOpsCritiqueEngine(alpha=0.5, beta=0.4, gamma=0.1)
    # Perfect AST code, simulated r_llm=0.9, perplexity=1.0
    reward = engine.calculate_composite_reward(code, r_llm=0.9, perplexity=1.0)
    assert reward["r_ast"] == 1.0
    # composite = 0.5*1.0 + 0.4*0.9 - 0.1*1.0 = 0.5 + 0.36 - 0.1 = 0.76
    assert abs(reward["composite_score"] - 0.76) < 1e-5


def test_z3_consistency_sat():
    # 'forall x (User(x) -> CanLogin(x))'
    folast = {
        "node_type": "Quantified",
        "operator": "ForAll",
        "variable": "x",
        "scope": {
            "node_type": "Logical",
            "operator": "If",
            "left_operand": {
                "node_type": "Atomic",
                "operator": "None",
                "predicate_name": "User",
                "arguments": [{"type": "Variable", "name": "x"}]
            },
            "right_operand": {
                "node_type": "Atomic",
                "operator": "None",
                "predicate_name": "CanLogin",
                "arguments": [{"type": "Variable", "name": "x"}]
            }
        }
    }
    
    engine = ReqOpsCritiqueEngine()
    result = engine.verify_logical_consistency(folast)
    assert result["status"] == "PASS"
    assert result["verification"] == "SAT"
