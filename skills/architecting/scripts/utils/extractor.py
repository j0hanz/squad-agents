import re
from typing import List, Optional, TypedDict


class ImportMatch(TypedDict):
    specifier: str
    index: int


# Python regexes
PY_IMPORT_REGEX = re.compile(r"^import\s+([\w.]+)", re.MULTILINE)
PY_FROM_REGEX = re.compile(r"^from\s+(\.{0,2}[\w.]*)\s+import", re.MULTILINE)

# Go regexes
GO_BLOCK_REGEX = re.compile(r"import\s*\(([\s\S]*?)\)")
GO_INNER_STR_REGEX = re.compile(r'(?:[\w.]+\s+)?"([^"]+)"')
GO_SINGLE_REGEX = re.compile(r'import\s+(?:[\w.]+\s+)?"([^"]+)"')

# JS/TS regexes
JS_IMPORT_REGEX = re.compile(
    r'import(?:[\s.*{},_a-zA-Z0-9]+from\s+)?[\'"](.*?)[\'"]', re.DOTALL
)
JS_REQUIRE_REGEX = re.compile(r'require\([\'"](.*?)[\'"]\)')


def extract_python_imports_with_positions(content: str) -> List[ImportMatch]:
    results: List[ImportMatch] = []
    for match in PY_IMPORT_REGEX.finditer(content):
        results.append({"specifier": match.group(1), "index": match.start()})

    for match in PY_FROM_REGEX.finditer(content):
        results.append({"specifier": match.group(1) or ".", "index": match.start()})

    return results


def extract_go_imports_with_positions(content: str) -> List[ImportMatch]:
    results: List[ImportMatch] = []
    # Block form: import ( ... )
    for m in GO_BLOCK_REGEX.finditer(content):
        inner = m.group(1)
        inner_start = m.start() + m.group(0).find(inner)
        for s in GO_INNER_STR_REGEX.finditer(inner):
            results.append({"specifier": s.group(1), "index": inner_start + s.start()})

    # Single form: import "pkg"
    for m in GO_SINGLE_REGEX.finditer(content):
        results.append({"specifier": m.group(1), "index": m.start()})

    return results


def extract_js_imports_with_positions(content: str) -> List[ImportMatch]:
    results: List[ImportMatch] = []
    for match in JS_IMPORT_REGEX.finditer(content):
        results.append({"specifier": match.group(1), "index": match.start()})

    for match in JS_REQUIRE_REGEX.finditer(content):
        results.append({"specifier": match.group(1), "index": match.start()})

    return results


def detect_lang(file_path: str) -> str:
    if file_path.endswith(".py"):
        return "py"
    if file_path.endswith(".go"):
        return "go"
    return "js"


def extract_imports_with_positions(
    content: str, lang: Optional[str] = None
) -> List[ImportMatch]:
    if lang == "py":
        return extract_python_imports_with_positions(content)
    if lang == "go":
        return extract_go_imports_with_positions(content)
    return extract_js_imports_with_positions(content)


def extract_imports(content: str, lang: Optional[str] = None) -> List[str]:
    return [m["specifier"] for m in extract_imports_with_positions(content, lang)]
