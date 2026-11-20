"""
Reproduce the entire analysis from raw data downloads.

Usage:
    python run_all.py

All random seeds are fixed inside each script.
"""

import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

scripts = [
    ("Stage 1a: Download data", "src/download_data.py"),
    ("Stage 1b: Prepare data", "src/prepare_data.py"),
    ("Stage 2a: Estimate quantile regressions", "src/estimate.py"),
    ("Stage 2b: Paper's exact specification", "src/paper_spec.py"),
    ("Stage 3: Out-of-sample evaluation", "src/out_of_sample.py"),
]

for desc, script in scripts:
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"  Running: {script}")
    print(f"{'='*60}\n")
    result = subprocess.run([sys.executable, script], capture_output=False)
    if result.returncode != 0:
        print(f"\nFAILED: {script} returned exit code {result.returncode}")
        sys.exit(1)

print(f"\n{'='*60}")
print("  All stages completed successfully.")
print(f"{'='*60}")
print("\nOutputs:")
print("  results/coefficients.csv     — quantile regression coefficients (extended grid)")
print("  results/paper_spec.csv       — paper's exact specification (Table 2 & A2)")
print("  results/out_of_sample.csv    — out-of-sample tick losses")
print("  results/assessment.txt       — qualitative assessment")
print("  figures/                     — all figures")
