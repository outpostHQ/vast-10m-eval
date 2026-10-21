"""Writes the q2 answer key: every call site of the six functions, as rustc resolves them.

Usage: python3 -I key/make_q2_key.py CHOCK_CHECKOUT > key/q2-callers.tsv

It exports the tested commit into a temporary directory, puts `#[deprecated]` in front of the
`fn` of each of the six functions, on the same line (so no line number moves), and runs
`cargo check --all-targets --all-features`. Each `use of deprecated` warning is one site.
rustc cannot report three sites here, so they are added by hand and marked in the `how` column:
- the deprecation lint is silent inside the deprecated function itself, which hides the two
  recursive calls of the two `copied` functions;
- code under `#[cfg(not(target_os = "linux"))]` is not compiled on Linux, which hides one call
  of `run_paced`.
`use` lines name a function but do not call it or use it as a value, so they are left out.
Needs git, tar, network access for cargo, and the Rust toolchain that the commit pins (rustup
installs it).
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

COMMIT = "e18fff5a34bbe2d2e1f40bd21d20f89133ff643c"
# (number, file, line, text before the change, text after the change)
MARKED = [
    (1, "src/gates/proofs/patch.rs", 78, "pub(crate) fn normalized(", "gates::proofs::patch::normalized"),
    (2, "src/gates/proofs/patch.rs", 93, "pub(crate) fn copied(", "gates::proofs::patch::copied"),
    (3, "src/oracle.rs", 274, "fn copied(", "oracle::copied"),
    (4, "src/exec/mod.rs", 353, "pub fn run_paced(", "exec::run_paced"),
    (5, "src/run/report.rs", 121, "    pub fn sort_by_place(", "run::report::Finding::sort_by_place"),
    (6, "src/project/mod.rs", 42, "pub fn relative(", "project::relative"),
]
BY_HAND = [
    (2, "src/gates/proofs/patch.rs:104", "by hand: recursive call"),
    (3, "src/oracle.rs:281", "by hand: recursive call"),
    (4, "src/gates/mutation/mutest.rs:146", 'by hand: under cfg(not(target_os = "linux"))'),
]
IMPORTS = {"src/gates/proofs/verus.rs:6", "src/oracle/side.rs:6"}


def main():
    chock = pathlib.Path(sys.argv[1]).resolve()
    work = pathlib.Path(tempfile.mkdtemp(prefix="q2-key-"))
    try:
        archive = subprocess.run(["git", "-C", str(chock), "archive", COMMIT], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(work)], input=archive.stdout, check=True)
        names = {}
        for number, path, line, before, name in MARKED:
            file = work / path
            lines = file.read_text().split("\n")
            if not lines[line - 1].startswith(before):
                sys.exit(f"{path}:{line} does not start with {before!r}")
            indent = len(before) - len(before.lstrip())
            lines[line - 1] = lines[line - 1][:indent] + "#[deprecated] " + lines[line - 1][indent:]
            file.write_text("\n".join(lines))
            names[name] = number
        env = dict(os.environ)
        env.setdefault("CARGO_TARGET_DIR", str(work / "target"))
        check = subprocess.run(["cargo", "check", "--all-targets", "--all-features", "--message-format=short"],
                               cwd=work, env=env, capture_output=True, text=True)
        if check.returncode != 0:
            sys.exit(check.stderr[-2000:])
        rows = {(number, site): how for number, site, how in BY_HAND}
        for m in re.finditer(r"^(\S+?):(\d+):\d+: warning: use of deprecated [a-z ]+ `([^`]+)`", check.stderr, re.M):
            site = f"{m[1]}:{m[2]}"
            if site not in IMPORTS:
                rows.setdefault((names[m[3]], site), "rustc")
        print("function\tsite\thow")
        for (number, site), how in sorted(rows.items(), key=lambda r: (r[0][0], r[0][1].split(":")[0],
                                                                       int(r[0][1].split(":")[1]))):
            print(f"{number}\t{site}\t{how}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


main()
