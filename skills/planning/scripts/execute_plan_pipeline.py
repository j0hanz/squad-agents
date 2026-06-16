import sys
import json
import os
import subprocess


def main():
    if "--input" not in sys.argv:
        print("Usage: python execute_plan_pipeline.py --input <plan.json>")
        sys.exit(1)

    input_file = sys.argv[sys.argv.index("--input") + 1]

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        sys.exit(1)

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        sys.exit(1)

    name = data.get("name")
    if not name:
        print("Error: 'name' field missing in JSON.")
        sys.exit(1)

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    os.path.dirname(os.path.abspath(input_file))

    # 1. Scaffold
    print(f"[*] Scaffolding {name}...")
    subprocess.run(
        [
            "python",
            os.path.join(scripts_dir, "scaffold.py"),
            name,
            "--depth",
            "contract",
        ],
        check=False,
    )

    # Normally the LLM writes to the file here.
    # For the pipeline, we assume the LLM wrote to the files, OR the LLM wrote the JSON and we'd construct it.
    # To keep it safe and compatible, we'll just run the validations. If they fail, the LLM will fix the files.

    print("[*] Validating Spec...")
    res_spec = subprocess.run(
        ["python", os.path.join(scripts_dir, "validate.py"), name, "--spec"]
    )
    if res_spec.returncode != 0:
        print("\n[!] Spec validation failed. Please fix the spec file and re-run.")
        sys.exit(res_spec.returncode)

    print("[*] Syncing...")
    subprocess.run(
        ["python", os.path.join(scripts_dir, "sync.py"), f"plan/{name}.specs.md"],
        check=False,
    )

    print("[*] Validating Plan...")
    res_plan = subprocess.run(
        ["python", os.path.join(scripts_dir, "validate.py"), name, "--plan"]
    )
    if res_plan.returncode != 0:
        print("\n[!] Plan validation failed. Please fix the plan file and re-run.")
        sys.exit(res_plan.returncode)

    print("[*] Cross-Validating...")
    res_cross = subprocess.run(
        ["python", os.path.join(scripts_dir, "validate.py"), name, "--cross"]
    )
    if res_cross.returncode != 0:
        print("\n[!] Cross validation failed.")
        sys.exit(res_cross.returncode)

    print("\n[+] Pipeline completed successfully. All validations passed.")


if __name__ == "__main__":
    main()
