"""Writes the q3 answer key: every key of `.chock/config.json`, from the serde structs in
src/project/config.rs at the tested commit.

Usage: python3 -I key/make_q3_key.py CHOCK_CHECKOUT > key/q3-keys.tsv

It reads each file with `git show COMMIT:path`, so the branch of the checkout does not matter.
Columns: key, kind, field line, schema, doc lines.
- kind `object` is a field of `Config`, or of a struct that a `Config` field holds as one JSON
  object (written as a dotted path).
- kind `list-item` is a field of a struct that a `Config` field holds in a JSON array, such as
  `commands[].name`. The examples in the question name only object keys, so score.py counts
  these as neither right nor wrong.
- schema is `yes` when schema/config-v1.json defines the key at that place.
- doc lines is a rough count: the lines in README.md and docs/**/*.md where the last part of the
  key's name stands between two backticks. It is not used for the score.
"""
import json
import re
import subprocess
import sys

COMMIT = "e18fff5a34bbe2d2e1f40bd21d20f89133ff643c"
CHOCK = sys.argv[1]
CONFIG = "src/project/config.rs"


def git(*args):
    return subprocess.run(["git", "-C", CHOCK, *args], capture_output=True, text=True, check=True).stdout


def show(path):
    return git("show", f"{COMMIT}:{path}")


lines = show(CONFIG).splitlines()
if any(re.search(r"serde\([^)]*\b(flatten|alias)\b", line) for line in lines):
    sys.exit("config.rs uses serde flatten or alias; this script does not handle them")

structs, current, attrs = {}, None, []
for number, line in enumerate(lines, 1):
    start = re.match(r"pub struct (\w+) \{", line)
    if start:
        current, attrs = start[1], []
        structs[current] = []
        continue
    if current is None:
        continue
    if line == "}":
        current = None
        continue
    attrs.append(line)
    field = re.match(r"    pub (\w+): (.+),$", line)
    if field:
        serde = " ".join(a.strip() for a in attrs if not a.strip().startswith("///"))
        renamed = re.search(r'rename = "([^"]+)"', serde)
        structs[current].append((renamed[1] if renamed else field[1], field[2], number))
        attrs = []

schema = json.loads(show("schema/config-v1.json"))
docs = ["README.md"] + sorted(p for p in git("ls-tree", "-r", "--name-only", COMMIT, "docs").split() if p.endswith(".md"))
doc_lines = [line for path in docs for line in show(path).splitlines()]


def in_schema(path):
    node = schema
    for part in path:
        node = node.get("items", node) if part == "[]" else node.get("properties", {}).get(part)
        if node is None:
            return False
    return True


def documented(name):
    pattern = re.compile(r"`[^`]*(?<![\w$])" + re.escape(name) + r"(?![\w])[^`]*`")
    return sum(1 for line in doc_lines if pattern.search(line))


rows = []
for name, kind, number in structs["Config"]:
    rows.append((name, "object", number, in_schema([name]), documented(name)))
    inner = re.fullmatch(r"(?:Option<)?(Vec<)?(\w+)>?>?", kind.replace(" ", ""))
    if not inner or inner[2] not in structs:
        continue
    listed = bool(inner[1])
    for sub, sub_kind, sub_number in structs[inner[2]]:
        dotted = f"{name}[].{sub}" if listed else f"{name}.{sub}"
        place = [name, "[]", sub] if listed else [name, sub]
        rows.append((dotted, "list-item" if listed else "object", sub_number, in_schema(place), documented(sub)))
        deeper = re.fullmatch(r"Vec<(\w+)>", sub_kind.replace(" ", ""))
        if deeper and deeper[1] in structs:
            for leaf, _, leaf_number in structs[deeper[1]]:
                rows.append((f"{dotted}[].{leaf}", "list-item", leaf_number,
                             in_schema(place + ["[]", leaf]), documented(leaf)))

print("key\tkind\tfield\tschema\tdoc_lines")
for key, kind, number, defined, count in rows:
    print(f"{key}\t{kind}\t{CONFIG}:{number}\t{'yes' if defined else 'no'}\t{count}")
