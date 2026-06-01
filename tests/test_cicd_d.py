import pytest
from reqops.modules.cicd_d import ReqOpsCICDGate

def test_tlr_traceability_link_recovery():
    spec_text = "The system must use ParserSelector to parse statements, and then apply LogicalSentenceParser recursively."
    ast_structure = {
        "structure": {
            "classes": [
                {"name": "ParserSelector", "bases": [], "methods": [], "line": 5},
                {"name": "LogicalSentenceParser", "bases": [], "methods": [], "line": 12}
            ],
            "functions": [],
            "loops": [],
            "imports": []
        }
    }
    
    gate = ReqOpsCICDGate()
    links = gate.perform_traceability_link_recovery(spec_text, ast_structure)
    assert len(links) == 2
    names = [link["name"] for link in links]
    assert "ParserSelector" in names
    assert "LogicalSentenceParser" in names


def test_predict_project_risk_cdt_low():
    gate = ReqOpsCICDGate()
    # High score, no violations, Z3 PASS
    risk = gate.predict_project_risk_cdt(composite_score=0.92, violations_count=0, z3_status="PASS")
    assert risk["risk_level"] == "LOW"
    assert risk["failure_probability"] == 0.05


def test_predict_project_risk_cdt_high_unsat():
    gate = ReqOpsCICDGate()
    # Contradiction in Z3
    risk = gate.predict_project_risk_cdt(composite_score=0.80, violations_count=0, z3_status="FAIL")
    assert risk["risk_level"] == "HIGH"
    assert risk["failure_probability"] == 0.98


def test_predict_project_risk_cdt_medium():
    gate = ReqOpsCICDGate()
    # Low composite score
    risk = gate.predict_project_risk_cdt(composite_score=0.55, violations_count=0, z3_status="PASS")
    assert risk["risk_level"] == "HIGH"
