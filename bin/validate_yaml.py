import sys
import json
import yaml

def main():
    try:
        content = sys.stdin.read()
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            print("Frontmatter must be a key-value mapping", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(data))
        sys.exit(0)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
