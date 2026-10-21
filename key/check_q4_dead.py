"""Checks the q4 answer "NONE": lists the dead items that rustc finds when it must also judge
the public API of the library.

Usage: python3 -I key/check_q4_dead.py CHOCK_CHECKOUT

rustc's dead_code lint does not judge a `pub` item of a library, because a user of the crate
could call it. q4 counts such an item as used only if something in the repository uses it. So
this script exports the tested commit into a temporary directory, makes every `pub` in the
library `pub(crate)`, and adds src/main.rs and tests/*.rs to the library as modules, so that
their uses still count. Then it checks the library with its unit tests and prints every warning.
A planted function and struct, with no use, make sure that the lint is on.

Limits: rustc does not report an unused trait implementation, and it does not compile code that
cfg turns off on the host system.
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
JOINED = """
extern crate self as chock;
#[allow(dead_code)]
#[path = "main.rs"]
mod as_main;
#[cfg(test)]
#[path = "../tests/cli.rs"]
mod as_test_cli;
#[cfg(test)]
#[path = "../tests/contracts.rs"]
mod as_test_contracts;
"""
PLANTED = "\npub(crate) fn planted_unused() {}\npub(crate) struct PlantedUnused;\n"


def main():
    chock = pathlib.Path(sys.argv[1]).resolve()
    work = pathlib.Path(tempfile.mkdtemp(prefix="q4-check-"))
    try:
        archive = subprocess.run(["git", "-C", str(chock), "archive", COMMIT], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(work)], input=archive.stdout, check=True)
        changed = 0
        for file in (work / "src").rglob("*.rs"):
            if file == work / "src/main.rs":
                continue
            text, count = re.subn(r"(^|[^A-Za-z0-9_])pub ([a-z(&A-Z_])", r"\1pub(crate) \2", file.read_text(),
                                  flags=re.M)
            file.write_text(text)
            changed += count
        with open(work / "src/lib.rs", "a") as lib:
            lib.write(JOINED + PLANTED)
        env = dict(os.environ, CARGO_BIN_EXE_chock="/nonexistent")
        env.setdefault("CARGO_TARGET_DIR", str(work / "target"))
        check = subprocess.run(["cargo", "check", "--lib", "--profile", "test", "--all-features",
                                "--message-format=short"], cwd=work, env=env, capture_output=True, text=True)
        warnings = [line for line in check.stderr.splitlines() if ": warning: " in line]
        print(f"pub made pub(crate): {changed}; cargo check exit {check.returncode}; warnings {len(warnings)}")
        print("\n".join(warnings))
        if check.returncode != 0:
            print(check.stderr[-2000:])
    finally:
        shutil.rmtree(work, ignore_errors=True)


main()
