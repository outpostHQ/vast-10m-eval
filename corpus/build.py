"""Builds the input text of the main test: 203 files of chock at commit e18fff5, numbered.

Usage: python3 -I corpus/build.py CHOCK_CHECKOUT corpus/repo.txt

It reads each file with `git show COMMIT:path`, so the working tree, its branch and the line
ending settings of the checkout do not change the result. The text must match SHA256 below; if it
does not, the script stops and writes nothing.
"""
import hashlib
import pathlib
import subprocess
import sys

COMMIT = "e18fff5a34bbe2d2e1f40bd21d20f89133ff643c"
SHA256 = "3098139443c7e8ca64b74b070a0e2ba3d9e6283a1421122a6451aadc87657ff6"
# The text as it was sent. CLAUDE.md, the one tracked file not in files.txt, was left out.
INTRO = (
    "Below is the whole repository of chock, a Rust command-line tool (version 0.13.0). Every "
    "tracked file is here. Each file starts with a line `=== FILE: <path> ===`, and each line of a "
    "file starts with its line number and `|`. The question comes after the last file.\n"
)


def main():
    chock, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    paths = (pathlib.Path(__file__).parent / "files.txt").read_text().split()
    parts = [INTRO]
    for path in paths:
        blob = subprocess.run(["git", "-C", str(chock), "show", f"{COMMIT}:{path}"], capture_output=True,
                              check=True).stdout.decode()
        numbered = "\n".join(f"{n:5}| {line}" for n, line in enumerate(blob.splitlines(), 1))
        parts.append(f"\n=== FILE: {path} ===\n{numbered}\n")
    parts.append("\n=== END OF THE REPOSITORY ===\n")
    text = "".join(parts)
    digest = hashlib.sha256(text.encode()).hexdigest()
    print(f"{len(paths)} files, {len(text)} characters, sha256 {digest}")
    if digest != SHA256:
        sys.exit(f"the text differs from the one that was sent; {out} is not written")
    out.write_text(text)


main()
