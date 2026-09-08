import os
import sys
import subprocess

# Root of the project (folder this file lives in)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(ROOT_DIR, "Core")
DATA_DIR = os.path.join(ROOT_DIR, "Data")

# Pipeline steps in order: Parser -> VLM -> Chroma Store -> Query Generation -> Job Search
PIPELINE_STEPS = [
    ("Parser", os.path.join(CORE_DIR, "parser.py")),
    ("VLM", os.path.join(CORE_DIR, "vlm.py")),
    ("Chroma Store", os.path.join(DATA_DIR, "chroma_store.py")),
    ("Query Generation", os.path.join(CORE_DIR, "query-generation.py")),
    ("Job Search", os.path.join(CORE_DIR, "job-search.py")),
]


def run_step(step_name: str, script_path: str):
    if not os.path.exists(script_path):
        print(f"\n[SKIPPED] {step_name}: file not found at {script_path}")
        return

    print(f"\n=== Running: {step_name} ({os.path.basename(script_path)}) ===")
    result = subprocess.run([sys.executable, script_path], cwd=os.path.dirname(script_path))

    if result.returncode != 0:
        print(f"\n[STOPPED] {step_name} exited with an error (code {result.returncode}).")
        sys.exit(result.returncode)

    print(f"=== Finished: {step_name} ===")


def main():
    print("############################################")
    print("#  JobScout-AI -- Full Pipeline Run        #")
    print("############################################")

    for step_name, script_path in PIPELINE_STEPS:
        run_step(step_name, script_path)

    print("\nAll steps completed. Pipeline finished successfully.")


if __name__ == "__main__":
    main()