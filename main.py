import os
import sys
import subprocess

# Root of the project (folder this file lives in)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(ROOT_DIR, "Core")
DATA_DIR = os.path.join(ROOT_DIR, "Data")

# Cache files that should be wiped so every run starts completely from scratch
QUERY_CACHE = os.path.join(ROOT_DIR, "query_cache.json")
JOB_RESULTS_CACHE = os.path.join(ROOT_DIR, "job_results_cache.json")

# Pipeline steps in order. check_db.py is intentionally excluded --
# it's treated as a standalone debug/inspection tool, not part of the run.
PIPELINE_STEPS = [
    ("Query Generation", os.path.join(CORE_DIR, "query-generation.py")),
    ("Job Search", os.path.join(CORE_DIR, "job-search.py")),
    ("Parser", os.path.join(CORE_DIR, "parser.py")),
    ("Chroma Store", os.path.join(DATA_DIR, "chroma_store.py")),
]


def reset_cache_files():
    """Delete stale cache files so this run doesn't reuse old data."""
    for path in (QUERY_CACHE, JOB_RESULTS_CACHE):
        if os.path.exists(path):
            os.remove(path)
            print(f"[reset] Removed old cache: {os.path.basename(path)}")
        else:
            print(f"[reset] No existing cache to remove: {os.path.basename(path)}")


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
    print("#  JobScout-AI -- Full Pipeline Run          #")
    print("############################################")

    reset_cache_files()

    for step_name, script_path in PIPELINE_STEPS:
        run_step(step_name, script_path)

    print("\nAll steps completed. Pipeline finished from scratch.")


if __name__ == "__main__":
    main()