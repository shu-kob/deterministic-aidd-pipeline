# ReqOps Quality Gate Pipeline

ReqOps is a continuous requirements and mathematical logic verification tool. It is designed to bridge the gap between high-level requirements specifications (written in First-Order Logic) and low-level code implementation, ensuring mathematical consistency and structural execution efficiency.

By parsing first-order logic (FOL) specifications and comparing them against Abstract Syntax Tree (AST) patterns extracted from code, ReqOps acts as a rigorous quality gate for Git repositories and CI/CD pipelines.

---

## 🚀 Key Features

- **Module A: SaT & Recursive FOL Parser**
  - Uses Segment Any Text (SaT) pre-processing to cleanly split natural language requirements on logical sentence boundaries without being fooled by standard abbreviations.
  - Recursively compiles quantified formulas (e.g. `forall`, `exists`) and logical connectors (`and`, `or`, `->`, `not`) into a standardized JSON logic schema.

- **Module B: Static AST Structure Extractor**
  - Inspects Python source code and extracts classes, methods, functions, and loop levels into a serializable AST JSON representation.

- **Module C: Composite Reward & Z3 Solver Engine**
  - **12 Static Performance Anti-Patterns Check**: Automatically audits code for inefficient structures (e.g., nested loops, redundant list searches, recursion, string concatenation inside loops) and assigns precise penalties.
  - **Z3 Logical Theorem Prover**: Generates live Z3 mathematical assertions from the compiled FOL logic schema and verifies if the code's declared logical statements are consistent or if there are logical contradictions.
  - **Composite Reward Evaluation**: Optimizes code selections using the mathematical formula:
    $$r = \alpha \cdot r_{AST} + \beta \cdot r_{LLM} - \gamma \cdot PP$$

- **Module D: GitOps Integration & Risk Assessment**
  - **Traceability Link Recovery (TLR)**: Maps requirements from your specifications directly to matching classes and methods in implementation code.
  - **Credal Decision Tree (CDT)**: Predicts non-delivery and failure risk ratings (LOW, MEDIUM, HIGH) probabilistically based on Z3 logical consistency and composite scores.
  - **Executable Pre-commit Hook**: Automatically registers a Git pre-commit hook that guards your repository and prevents faulty commits.

---

## 📦 Directory Structure

```
├── reqops/
│   ├── cli.py               # Main CLI entrypoint
│   ├── config.py            # Global hyperparameter settings
│   ├── modules/
│   │   ├── parser_a.py      # FOL Preprocessing and Top-Down logical compiler
│   │   ├── parser_b.py      # Code AST parser
│   │   ├── solver_c.py      # Composite reward engine and Z3 solver
│   │   └── cicd_d.py        # TLR, CDT Risk Assessment, and Git hook manager
│   └── utils/
│       ├── ast_inspector.py # AST NodeVisitor for 12 performance rules
│       └── z3_compiler.py   # Z3 Symbol collection and assertion builder
├── tests/                   # Extensive test suites
└── requirements.txt         # Project dependencies
```

---

## 💻 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install the Git Pre-commit Hook
Install the automated quality gate hook in your active workspace:
```bash
python3 -m reqops.cli install-hook
```
Once installed, any `git commit` command will trigger an automated check of all modified files and prevent the commit if the logic contains errors or performance score falls below target thresholds.

---

## 🛠️ CLI Reference

### E2E Automated Checking (Supports Private Repositories)
The `check` command runs all modules end-to-end. To verify any local or **Private GitHub Repository**, use the `--dir` option to specify the path to the cloned repository. This executes checks locally without requiring SSH keys or API tokens:
```bash
python3 -m reqops.cli check --dir /path/to/local/cloned-repo
```

### Parse Specifications
Compile first-order logic specification markdown documents to logic JSON:
```bash
python3 -m reqops.cli parse-spec --spec-file .spec/spec.md --output .spec/FOLAST_Schema.json
```

### Parse Code Structure
Extract class and method contexts from target Python source files:
```bash
python3 -m reqops.cli parse-code --code-file main.py --output .spec/Code_AST_Structure.json
```

### Run Logic and Performance Verification
Verify a source file against compiled requirements logic and output a premium formatting report:
```bash
python3 -m reqops.cli verify --folast .spec/FOLAST_Schema.json --code-file main.py
```

---

## 📊 Sample Verification Report

When a file fails to satisfy the requirements or exceeds complexity limits, ReqOps will print a detailed audit report:

```
==================================================
🛡️  REQOPS QUALITY GATE REPORT  🛡️
==================================================
📊 Composite Reward Score: 0.5826  (Min Target: 0.70)
   • Static AST Reward (r_AST)  : 0.8252
   • Simulated LLM Score (r_LLM): 0.8000
   • Perplexity Penalty (PP)    : 1.5000
--------------------------------------------------
🧮 Z3 Logic Solver Status: PASS
   • Message: Requirements model is mathematically consistent & satisfied.
--------------------------------------------------
📉 Project Failure Risk Rating (CDT): HIGH
   • Failure Probability: 85.0%
   • Assessment Reason : Composite reward score below safety critical threshold
--------------------------------------------------
⚠️  Static AST Performance Violations Detected (2):
   [1] Nested Loops (Penalty: -10)
       Line numbers: 10
   [2] Redundant Function Calls inside Loops (Penalty: -8)
       Line numbers: 11
--------------------------------------------------
==================================================

❌ ReqOps Quality Gate: REJECTED
```
