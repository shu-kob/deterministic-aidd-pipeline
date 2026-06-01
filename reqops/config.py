import os

# Default Hyperparameters for Composite Scorer
ALPHA = 0.5   # Weight for static AST performance pattern reward
BETA = 0.4    # Weight for LLM critique evaluation
GAMMA = 0.1   # Weight for perplexity likelihood penalty

# Schema Output Paths
FOLAST_SCHEMA_PATH = ".spec/FOLAST_Schema.json"
CODE_AST_STRUCTURE_PATH = ".spec/Code_AST_Structure.json"

# Thresholds for CI/CD Gates
MINIMUM_COMPOSITE_REWARD = 0.70
CDT_HIGH_RISK_THRESHOLD = 0.50
CDT_MEDIUM_RISK_THRESHOLD = 0.75
