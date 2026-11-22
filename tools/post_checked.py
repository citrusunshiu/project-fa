# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run a command that posts text to GitHub only after the public-text check passes.

Usage: post_checked.py <file> [<file> ...] -- <command> [<arg> ...]

Every file before `--` is checked with check_public_text.py, and so is the value of any --title or -t
in the command. The command runs only when the check passes; otherwise nothing runs and the exit code
is 1. Post from the same files you pass here, such as `gh issue create --title ... --body-file <file>`.
"""
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
USAGE = "usage: post_checked.py <file> [<file> ...] -- <command> [<arg> ...]"


def titles(command: list[str]) -> list[str]:
    out = []
    for i, arg in enumerate(command):
        if arg in ("--title", "-t") and i + 1 < len(command):
            out.append(command[i + 1])
        elif arg.startswith("--title="):
            out.append(arg.split("=", 1)[1])
    return out


def main(argv: list[str]) -> int:
    if "--" not in argv:
        print(USAGE, file=sys.stderr)
        return 2
    split = argv.index("--")
    files, command = argv[:split], argv[split + 1:]
    if not files or not command:
        print(USAGE, file=sys.stderr)
        return 2
    for name in files:
        if not pathlib.Path(name).is_file():
            print(f"post_checked: {name} is not a file, so nothing was posted", file=sys.stderr)
            return 1
    with tempfile.TemporaryDirectory() as tmp:
        texts = list(files)
        found = titles(command)
        if found:
            title = pathlib.Path(tmp) / "title.txt"
            title.write_text("\n".join(found) + "\n")
            texts.append(str(title))
        check = [sys.executable, str(HERE / "check_public_text.py")]
        for name in texts:
            check += ["--text", name]
        if subprocess.run(check).returncode != 0:
            print("post_checked: the public-text check failed, so nothing was posted", file=sys.stderr)
            return 1
    os.execvp(command[0], command)
    return 1  # not reached


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
