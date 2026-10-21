"""Scores the answers of one run.

Usage: python3 -I score.py RUN_DIR
RUN_DIR holds any of q1-docs.answer.txt ... q5-bloat.answer.txt; results/run3 is the main run.
It can also hold probe.answer.txt (results/run1), whose repetition is counted.
corpus/repo.txt must exist (corpus/build.py makes it), because the scorer reads the cited lines.

q2 and q3 are scored by rule against key/q2-callers.tsv and key/q3-keys.tsv. q1, q4 and q5 have no
complete key. For them the scorer prints each item with the lines it cites, and for q1 the verdict
from key/q1-reviewed.tsv when we reviewed the item by hand.
"""
import csv
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUN = pathlib.Path(sys.argv[1])
NAMES = {1: "normalized", 2: "copied", 3: "copied", 4: "run_paced", 5: "sort_by_place", 6: "relative"}
NEAR = 2  # a site this many lines from a key site, in the same file, counts as near, not as invented


def corpus():
    files, path = {}, None
    for line in (HERE / "corpus" / "repo.txt").read_text().splitlines():
        head = re.fullmatch(r"=== FILE: (.+) ===", line)
        if head:
            path = head[1]
            files[path] = []
            continue
        body = re.fullmatch(r" *\d+\| (.*)", line)
        if path and body:
            files[path].append(body[1])
    return files


FILES = corpus()


def table(name):
    with open(HERE / "key" / name, newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def answer(question):
    path = RUN / f"{question}.answer.txt"
    return path.read_text() if path.exists() else None


def cited(path, line):
    lines = FILES.get(path)
    if lines is None:
        return "(no such file)"
    if not 1 <= line <= len(lines):
        return f"(the file has {len(lines)} lines)"
    return lines[line - 1].strip()


def site(text):
    m = re.fullmatch(r"`?([^:`\s]+):(\d+)(?:-\d+)?`?", text.strip())
    return (m[1], int(m[2])) if m else None


def q1(text):
    reviewed = {(r["doc"], r["code"]): r for r in table("q1-reviewed.tsv")}
    items = [line for line in text.splitlines() if line.startswith("DOC ")]
    print(f"q1: {len(items)} items" + (", answer NONE" if text.strip() == "NONE" else ""))
    for line in items:
        m = re.match(r"DOC (\S+) \| CODE (\S+) \| (.*)", line)
        if not m:
            print("  not in the asked form:", line[:120])
            continue
        review = reviewed.get((m[1], m[2]))
        print(f"  {m[1]} | {m[2]} | {m[3][:100]}")
        for place in (m[1], m[2]):
            where = site(place)
            print(f"    {place}: {cited(*where) if where else '(not path:line)'}"[:160])
        print(f"    verdict: {review['verdict']}: {review['evidence']}" if review else "    verdict: not reviewed")


def q2(text):
    key = {}
    for r in table("q2-callers.tsv"):
        path, line = r["site"].rsplit(":", 1)
        key.setdefault(int(r["function"]), set()).add((path, int(line)))
    said, malformed = {}, 0
    for line in text.splitlines():
        m = re.fullmatch(r"\s*(\d+)\s*\|\s*([^:|\s]+):(\d+)\s*\|.*", line)
        if m and int(m[1]) in NAMES:
            said.setdefault(int(m[1]), set()).add((m[2], int(m[3])))
        elif line.strip() not in ("", "END"):
            malformed += 1
    listed = sum(len(s) for s in said.values())
    print(f"q2: {len(text.splitlines())} lines, {listed} unique sites, other lines {malformed}, "
          f"ends with END: {text.rstrip().endswith('END')}")
    print("  fn  key  listed  exact  near  invented  missed  | of the listed: no such file, past the end, "
          "file without the name, line without the name")
    totals = [0] * 6
    for number, truth in sorted(key.items()):
        got = said.get(number, set())
        exact = got & truth
        near = {g for g in got - truth if any(g[0] == t[0] and abs(g[1] - t[1]) <= NEAR for t in truth)}
        invented = got - truth - near
        missed = len(truth) - len(exact) - len(near)
        name = NAMES[number]
        absent = {g for g in got if g[0] not in FILES}
        past = {g for g in got - absent if g[1] > len(FILES[g[0]])}
        no_name_file = {g for g in got - absent if not any(name in line for line in FILES[g[0]])}
        no_name_line = {g for g in got - absent - past if name not in FILES[g[0]][g[1] - 1]}
        row = [len(truth), len(got), len(exact), len(near), len(invented), missed]
        totals = [a + b for a, b in zip(totals, row)]
        print(f"  {number:2}  {row[0]:3}  {row[1]:6}  {row[2]:5}  {row[3]:4}  {row[4]:8}  {row[5]:6}  | "
              f"{len(absent)}, {len(past)}, {len(no_name_file)}, {len(no_name_line)}")
        for path in sorted({g[0] for g in absent}):
            print(f"      no such file: {path}")
    print(f"  all {totals[0]:3}  {totals[1]:6}  {totals[2]:5}  {totals[3]:4}  {totals[4]:8}  {totals[5]:6}")


def q3(text):
    key = {r["key"]: r for r in table("q3-keys.tsv")}
    asked = {k for k, r in key.items() if r["kind"] == "object"}
    rows = [[c.strip() for c in line.split("|")] for line in text.splitlines() if line.count("|") >= 3]
    said = {r[0].strip("`") for r in rows}
    found = said & asked
    print(f"q3: {len(rows)} rows; key {len(asked)} keys (and {len(key) - len(asked)} list-item fields, "
          f"neither right nor wrong); found {len(found)}; not keys {len(said - set(key))}")
    if not rows:
        print("  answer:", text.strip()[:300])
        return
    right_line = sum(1 for r in rows if r[0].strip("`") in key and r[1].strip("`") == key[r[0].strip("`")]["field"])
    right_schema = sum(1 for r in rows if r[0].strip("`") in key
                       and r[3].lower().startswith(key[r[0].strip("`")]["schema"]))
    print(f"  field line right {right_line}; schema answer right {right_schema}")
    print("  missed:", ", ".join(sorted(asked - said)) or "none")
    print("  not keys:", ", ".join(sorted(said - set(key))) or "none")


def q4(text):
    items = [line for line in text.splitlines() if line.count("|") >= 2]
    print(f"q4: {len(items)} items" + (", answer NONE" if text.strip() == "NONE" else ""))
    print("  key/check_q4_dead.py finds no dead item at the tested commit (rustc on Linux; see the README).")
    for line in items:
        parts = [c.strip() for c in line.split("|")]
        where = site(parts[0])
        print(f"  {line[:120]}\n    cited line: {cited(*where) if where else '(not path:line)'}"[:200])


def q5(text):
    items = [line for line in text.splitlines() if line.count("|") >= 4]
    print(f"q5: {len(items)} items" + (", answer NONE" if text.strip() == "NONE" else "")
          + "; no key: only a build can measure the bytes")
    for line in items:
        parts = [c.strip() for c in line.split("|")]
        m = re.fullmatch(r"([^:\s]+):(\d+)(?:-(\d+))?", parts[0])
        name = re.search(r"`(\w+)`", parts[1])
        print(f"  {parts[0]} | {parts[1][:80]} | saves {parts[3]} | {parts[4]}")
        if not (m and name) or m[1] not in FILES:
            continue
        first, last = int(m[2]), int(m[3] or m[2])
        lines = FILES[m[1]]
        inside = any(name[1] in line for line in lines[first - 1:last])
        defined = [n for n, line in enumerate(lines, 1) if re.search(rf"\bfn {name[1]}\b", line)]
        users = sum(1 for path, body in FILES.items() if path != m[1] and any(name[1] in line for line in body))
        print(f"    `{name[1]}` in the cited lines: {'yes' if inside else 'no'}; defined at line "
              f"{', '.join(map(str, defined)) or '?'}; other files that name it: {users}")


def repetition(text):
    items = re.findall(r'"((?:[^"\\]|\\.)*)"', text)
    best, run, previous = 0, 0, None
    for item in items:
        run = run + 1 if item == previous else 1
        previous = item
        best = max(best, run)
    cut = text.count('"') % 2 == 1
    print(f"run 1 probe: {len(text)} characters; the longest run of one string repeated: {best}; "
          f"ends inside a string: {cut}")


for question, check in (("q1-docs", q1), ("q2-callers", q2), ("q3-keys", q3), ("q4-dead", q4), ("q5-bloat", q5),
                        ("probe", repetition)):
    found = answer(question)
    if found is not None:
        check(found)
        print()
