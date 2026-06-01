import argparse
import sys
import os
import json

from reqops.config import (
    ALPHA, BETA, GAMMA,
    FOLAST_SCHEMA_PATH, CODE_AST_STRUCTURE_PATH,
    MINIMUM_COMPOSITE_REWARD
)
from reqops.modules.parser_a import parse_requirements_to_folast, save_folast_to_file
from reqops.modules.parser_b import parse_code_to_ast_structure, save_ast_structure_to_file
from reqops.modules.solver_c import ReqOpsCritiqueEngine
from reqops.modules.cicd_d import ReqOpsCICDGate

def ensure_spec_dir_exists(base_dir="."):
    """Creates .spec directory relative to the specified base_dir."""
    os.makedirs(os.path.join(base_dir, ".spec"), exist_ok=True)

def parse_spec_command(args):
    target_dir = getattr(args, "dir", ".")
    ensure_spec_dir_exists(target_dir)
    spec_path = args.spec_file
    if not os.path.isabs(spec_path):
        spec_path = os.path.join(target_dir, spec_path)
    if not os.path.exists(spec_path):
        print(f"❌ Error: Specification file not found at '{spec_path}'")
        sys.exit(1)
        
    print(f"📖 Parsing specifications from: {spec_path}...")
    with open(spec_path, "r", encoding="utf-8") as f:
        spec_text = f.read()
        
    nodes = parse_requirements_to_folast(spec_text)
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(target_dir, output_path)
    save_folast_to_file(nodes, output_path)
    print(f"✅ Success: Compiled logical FOLAST tree saved to '{output_path}'")


def parse_code_command(args):
    target_dir = getattr(args, "dir", ".")
    ensure_spec_dir_exists(target_dir)
    code_path = args.code_file
    if not os.path.isabs(code_path):
        code_path = os.path.join(target_dir, code_path)
    if not os.path.exists(code_path):
        print(f"❌ Error: Target code file not found at '{code_path}'")
        sys.exit(1)
        
    print(f"🐍 Extracting AST structure from: {code_path}...")
    with open(code_path, "r", encoding="utf-8") as f:
        source_code = f.read()
        
    structure = parse_code_to_ast_structure(source_code)
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(target_dir, output_path)
    save_ast_structure_to_file(structure, output_path)
    print(f"✅ Success: Code AST structure saved to '{output_path}'")


def verify_command(args):
    target_dir = getattr(args, "dir", ".")
    ensure_spec_dir_exists(target_dir)
    
    folast_path = args.folast
    if not os.path.isabs(folast_path):
        folast_path = os.path.join(target_dir, folast_path)
        
    if not os.path.exists(folast_path):
        print(f"❌ Error: Compiled requirements FOLAST file not found at '{folast_path}'. Run 'parse-spec' first.")
        sys.exit(1)
        
    code_file_path = args.code_file
    if not os.path.isabs(code_file_path):
        code_file_path = os.path.join(target_dir, code_file_path)
        
    if not os.path.exists(code_file_path):
        print(f"❌ Error: Target code file not found at '{code_file_path}'")
        sys.exit(1)

    print(f"🔍 Starting quality gate verification...")
    with open(folast_path, "r", encoding="utf-8") as f:
        folast_dict = json.load(f)
        
    with open(code_file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Step 1: Execute Module C Composite Reward Scorer & Z3 Prover
    engine = ReqOpsCritiqueEngine(alpha=ALPHA, beta=BETA, gamma=GAMMA)
    
    reward_info = engine.calculate_composite_reward(source_code, r_llm=args.r_llm, perplexity=args.perplexity)
    z3_info = engine.verify_logical_consistency(folast_dict)

    # Step 2: Extract AST structure for Module D TLR Mapping
    ast_structure = parse_code_to_ast_structure(source_code)
    
    # Step 3: Run Module D CI/CD Gate
    gate = ReqOpsCICDGate()
    
    # Traceability links (resolved dynamically using target_dir)
    spec_text = ""
    spec_path = os.path.join(target_dir, ".spec", "spec.md")
    if os.path.exists(spec_path):
        with open(spec_path, "r", encoding="utf-8") as sf:
            spec_text = sf.read()
    links = gate.perform_traceability_link_recovery(spec_text, ast_structure)
    
    # CDT Risk estimation
    violations_count = len(reward_info["ast_violations"])
    risk_info = gate.predict_project_risk_cdt(reward_info["composite_score"], violations_count, z3_info["status"])

    # Step 4: Display Premium Formatted Summary Report
    print("\n" + "="*50)
    print("🛡️  REQOPS QUALITY GATE REPORT  🛡️")
    print("="*50)
    print(f"📊 Composite Reward Score: {reward_info['composite_score']:.4f}  (Min Target: {MINIMUM_COMPOSITE_REWARD:.2f})")
    print(f"   • Static AST Reward (r_AST)  : {reward_info['r_ast']:.4f}")
    print(f"   • Simulated LLM Score (r_LLM): {reward_info['r_llm']:.4f}")
    print(f"   • Perplexity Penalty (PP)    : {reward_info['perplexity']:.4f}")
    print("-"*50)
    
    print(f"🧮 Z3 Logic Solver Status: {z3_info['status']}")
    print(f"   • Message: {z3_info['message']}")
    if z3_info['model_assignments']:
        print("   • Z3 Model Variables:")
        for k, v in z3_info['model_assignments'].items():
            print(f"     - {k}: {v}")
    print("-"*50)

    print(f"📉 Project Failure Risk Rating (CDT): {risk_info['risk_level']}")
    print(f"   • Failure Probability: {risk_info['failure_probability']*100:.1f}%")
    print(f"   • Assessment Reason : {risk_info['reason']}")
    print("-"*50)

    if reward_info["ast_violations"]:
        print(f"⚠️  Static AST Performance Violations Detected ({violations_count}):")
        for rule_id, viol in reward_info["ast_violations"].items():
            print(f"   [{rule_id}] {viol['name']} (Penalty: -{viol['penalty']})")
            print(f"       Line numbers: {', '.join(map(str, viol['lines']))}")
    else:
        print("🎉 No static performance violations found! Code AST is highly optimal.")
    print("-"*50)

    if links:
        print(f"🔗 Traceability Links Found ({len(links)}):")
        for link in links[:5]:
            print(f"   - {link['element_type'].capitalize()}: {link['name']} (Confidence: {link['confidence']})")
        if len(links) > 5:
            print(f"   - ...and {len(links)-5} more links.")
    print("="*50 + "\n")

    # Exit with code based on Gate requirements
    if z3_info["status"] == "FAIL" or reward_info["composite_score"] < MINIMUM_COMPOSITE_REWARD:
        print("❌ ReqOps Quality Gate: REJECTED")
        sys.exit(1)
    else:
        print("✅ ReqOps Quality Gate: APPROVED")
        sys.exit(0)


def install_hook_command(args):
    gate = ReqOpsCICDGate()
    success = gate.install_git_pre_commit_hook(args.workspace)
    if success:
        print("✅ Success: Installed ReqOps quality gate git pre-commit hook successfully.")
    else:
        print("❌ Error: Failed to install git pre-commit hook. Make sure you are in a Git repository.")
        sys.exit(1)


def check_command(args):
    """
    End-to-end check command called by pre-commit or CI pipeline.
    Finds <dir>/.spec/spec.md, runs Modules A & B & C & D and blocks if they fail.
    """
    target_dir = args.dir
    spec_file = os.path.join(target_dir, ".spec", "spec.md")
    if not os.path.exists(spec_file):
        print(f"⚠️ Warning: Specification file not found at '{spec_file}', bypassing checks.")
        sys.exit(0)

    # Automatically identify target python files to verify under the target directory
    py_files = []
    for root, dirs, files in os.walk(target_dir):
        # Ignore common non-project and build directories
        # Split root to match exactly so we don't partially match folder names
        parts = root.split(os.sep)
        if any(d in parts for d in [".git", "reqops", "tests", "venv", ".venv", "env", "build", "dist", "__pycache__"]):
            continue
        for f in files:
            if f.endswith(".py") and f != "setup.py":
                py_files.append(os.path.join(root, f))

    if not py_files:
        print(f"ℹ️ Info: No Python source code files found to verify in '{target_dir}'. Quality gate passed.")
        sys.exit(0)

    # Run spec parse
    ensure_spec_dir_exists(target_dir)
    with open(spec_file, "r", encoding="utf-8") as f:
        spec_text = f.read()
    nodes = parse_requirements_to_folast(spec_text)
    
    folast_output_path = os.path.join(target_dir, ".spec", "FOLAST_Schema.json")
    save_folast_to_file(nodes, folast_output_path)

    overall_passed = True
    for py_file in py_files:
        print(f"\n⚡ Verifying python file: {py_file}")
        try:
            # Setup Namespace mock with target directory context
            args_mock = argparse.Namespace(
                folast=folast_output_path,
                code_file=py_file,
                r_llm=0.85,
                perplexity=1.2,
                dir=target_dir
            )
            verify_command(args_mock)
        except SystemExit as e:
            if e.code != 0:
                overall_passed = False

    if not overall_passed:
        sys.exit(1)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="ReqOps Quality Gate Pipeline - Continuous Requirements & Logic Verification Tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # parse-spec
    parser_a = subparsers.add_parser("parse-spec", help="Parse specification document requirements to FOLAST schema JSON")
    parser_a.add_argument("--spec-file", default=".spec/spec.md", help="Path to the Markdown specification document")
    parser_a.add_argument("--output", default=FOLAST_SCHEMA_PATH, help="Output path for FOLAST JSON schema")
    parser_a.add_argument("--dir", default=".", help="Base directory context of the project")

    # parse-code
    parser_b = subparsers.add_parser("parse-code", help="Parse Python source code to AST Structure JSON")
    parser_b.add_argument("--code-file", required=True, help="Path to Python source code file to extract")
    parser_b.add_argument("--output", default=CODE_AST_STRUCTURE_PATH, help="Output path for AST Structure JSON")
    parser_b.add_argument("--dir", default=".", help="Base directory context of the project")

    # verify
    parser_c = subparsers.add_parser("verify", help="Run composite reward scoring and Z3 logical verification")
    parser_c.add_argument("--code-file", required=True, help="Path to Python source code file to verify")
    parser_c.add_argument("--folast", default=FOLAST_SCHEMA_PATH, help="Path to the compiled FOLAST JSON schema")
    parser_c.add_argument("--r-llm", type=float, default=0.8, help="Simulated or calculated LLM critique rating")
    parser_c.add_argument("--perplexity", type=float, default=1.5, help="Simulated or calculated LLM perplexity likelihood")
    parser_c.add_argument("--dir", default=".", help="Base directory context of the project")

    # install-hook
    parser_d = subparsers.add_parser("install-hook", help="Install local Git pre-commit verification hook")
    parser_d.add_argument("--workspace", default=".", help="Absolute path to target Git workspace repository")

    # check (E2E pre-commit gate)
    parser_check = subparsers.add_parser("check", help="Automated end-to-end quality gate check of modified files")
    parser_check.add_argument("--dir", default=".", help="Path to the target project directory to verify")

    args = parser.parse_args()

    if args.command == "parse-spec":
        parse_spec_command(args)
    elif args.command == "parse-code":
        parse_code_command(args)
    elif args.command == "verify":
        verify_command(args)
    elif args.command == "install-hook":
        install_hook_command(args)
    elif args.command == "check":
        check_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
