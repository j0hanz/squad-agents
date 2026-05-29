#!/usr/bin/env python3
"""
visualize_policy.py
Visualizes the permission graph for agent teams based on a policy.yaml file.
"""

import os
import sys

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)


def print_tree(data, prefix=""):
    if isinstance(data, dict):
        keys = list(data.keys())
        for i, key in enumerate(keys):
            is_last = i == (len(keys) - 1)
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{key}")

            extension = "    " if is_last else "│   "
            print_tree(data[key], prefix + extension)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            is_last = i == (len(data) - 1)
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{item}")
    else:
        print(f"{prefix}└── {data}")


def main(policy_file):
    if not os.path.exists(policy_file):
        print(f"Error: Policy file '{policy_file}' not found.")
        sys.exit(1)

    try:
        with open(policy_file, "r") as f:
            policy_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)

    print(f"--- Permission Policy Graph ({policy_file}) ---\n")

    default_policy = policy_data.get("default_policy", "unknown")
    print(f"Default Policy: {default_policy}")

    policies = policy_data.get("policies", {})
    if not policies:
        print("\nNo specific agent policies defined.")
        sys.exit(0)

    print("\nAgent Roles:")
    for role, rules in policies.items():
        print(f"\n[{role}]")
        print_tree(rules)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        policy_file = sys.argv[1]
    else:
        policy_file = "policy.yaml"
        print("No policy file specified, trying default 'policy.yaml'...\n")

    main(policy_file)
