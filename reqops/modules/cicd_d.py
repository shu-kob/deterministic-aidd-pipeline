import os
import stat
import re

class ReqOpsCICDGate:
    """
    Module D: GitOps CI/CD Integration & Risk Assessment.
    Manages pre-commit hook installations, Traceability Link Recovery, and project risk ratings.
    """
    def __init__(self):
        pass

    def perform_traceability_link_recovery(self, spec_text: str, ast_structure: dict) -> list[dict]:
        """
        Traceability Link Recovery (TLR):
        Analyzes and maps requirements in spec.md to actual classes/functions in the AST.
        """
        links = []
        if "structure" not in ast_structure:
            return links

        # Extract potential keywords/classes/functions from spec text
        # E.g. find any mentioned names like ParserSelector, LogicalSentenceParser, etc.
        all_funcs = []
        for cls in ast_structure["structure"].get("classes", []):
            all_funcs.append(("class", cls["name"]))
            for method in cls.get("methods", []):
                all_funcs.append(("method", f"{cls['name']}.{method['name']}"))
        for func in ast_structure["structure"].get("functions", []):
            all_funcs.append(("function", func["name"]))

        # For each class/function/method in AST, check if it's referenced in the spec
        for element_type, name in all_funcs:
            # Simple keyword match
            # If name is mentioned in spec (case insensitive or exact)
            base_name = name.split(".")[-1]
            pattern = re.compile(rf'\b{re.escape(base_name)}\b', re.IGNORECASE)
            matches = list(pattern.finditer(spec_text))
            
            if matches:
                # Resolve match contexts
                links.append({
                    "element_type": element_type,
                    "name": name,
                    "occurrences_in_spec": len(matches),
                    "confidence": "HIGH" if len(matches) > 1 else "MEDIUM"
                })
        return links

    def predict_project_risk_cdt(self, composite_score: float, violations_count: int, z3_status: str) -> dict:
        """
        Credal Decision Tree (CDT) Risk Assessment:
        Estimates the probability of project failure/risk based on verification outputs.
        """
        # Lightweight deterministic CDT decision rule:
        if z3_status == "FAIL":
            risk_level = "HIGH"
            failure_probability = 0.98
            reason = "Mathematical logic contradiction in Z3 validation"
        elif composite_score < 0.60:
            risk_level = "HIGH"
            failure_probability = 0.85
            reason = "Composite reward score below safety critical threshold"
        elif violations_count > 5:
            risk_level = "MEDIUM"
            failure_probability = 0.55
            reason = "High volume of static performance anti-pattern violations"
        elif composite_score < 0.80:
            risk_level = "MEDIUM"
            failure_probability = 0.35
            reason = "Moderate performance or LLM-critique ratings"
        else:
            risk_level = "LOW"
            failure_probability = 0.05
            reason = "Excellent logical alignment and AST efficiency ratings"

        return {
            "risk_level": risk_level,
            "failure_probability": failure_probability,
            "reason": reason
        }

    def install_git_pre_commit_hook(self, workspace_path: str) -> bool:
        """
        Installs a Git pre-commit hook to automatically run the ReqOps verification
        and prevent commits if requirements or quality metrics are violated.
        """
        hooks_dir = os.path.join(workspace_path, ".git", "hooks")
        if not os.path.exists(hooks_dir):
            return False

        hook_path = os.path.join(hooks_dir, "pre-commit")
        
        # Hook script content that calls our CLI
        hook_script = """#!/bin/bash
# ReqOps Quality Gate Hook

echo "==========================================="
echo "🛡️  Running ReqOps Quality Gate Verification..."
echo "==========================================="

# Run verification check
python3 -m reqops.cli check

RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo ""
  echo "❌ [ReqOps Error] Quality gate verification failed! Commit blocked."
  echo "Please resolve the performance violations or logic inconsistencies."
  echo "==========================================="
  exit 1
fi

echo "✅ [ReqOps Success] Quality gate passed! Proceeding with commit..."
echo "==========================================="
exit 0
"""
        
        try:
            with open(hook_path, "w", encoding="utf-8") as f:
                f.write(hook_script)
                
            # Make the pre-commit hook executable (chmod +x)
            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
            return True
        except Exception:
            return False
