"""Global configuration for vision evaluation."""

import os
import matplotlib
matplotlib.use("Agg")  # headless rendering, must be before any pyplot import

# Model
MODEL_ID = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

# API
API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Paths
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "figures")
GENERATED_DIR = os.path.join(os.path.dirname(__file__), "generate", "images")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
