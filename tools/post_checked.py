# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run a command that posts text to GitHub only after the public-text check passes.

Usage: post_checked.py <file> [<file> ...] -- <command> [<arg> ...]

Every file before `--` is checked with check_public_text.py, and so is any title in the command
(--title, -t). The command runs only when the check passes; otherwise nothing runs and the exit code
is 1. It fails closed on text it can't check: an inline body (--body, -b), a body file that isn't one
of the checked files (--body-file, -F), and `gh api` fields (-f, -F, --field, --raw-field), which
must come from a checked file through --input instead.
"""
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
USAGE = "usage: post_checked.py <file> [<file> ...] -- <command> [<arg> ...]"


class Refused(Exception):
    pass


def value(command: list[str], i: int, arg: str, short: str, long: str) -> str | None:
    """The value of `arg` when it is the option short/long in any form gh accepts, else None."""
    if arg in (short, long):
        if i + 1 >= len(command):
            raise Refused(f"{arg} has no value")
        return command[i + 1]
    if arg.startswith(long + "="):
        return arg[len(long) + 1:]
    if short and arg.startswith(short) and len(arg) > len(short) and not arg.startswith("--"):
        return arg[len(short):].removeprefix("=")
    return None


def inspect(command: list[str], checked: set[pathlib.Path]) -> list[str]:
    """Return the titles to check, or raise Refused for text that can't be checked."""
    is_api = len(command) > 1 and pathlib.Path(command[0]).name == "gh" and command[1] == "api"
    titles = []
    for i, arg in enumerate(command):
        if is_api:
            for short, long in (("-f", "--raw-field"), ("-F", "--field")):
                if value(command, i, arg, short, long) is not None:
                    raise Refused("gh api fields can carry text; pass a checked file with --input")
            path = value(command, i, arg, "", "--input")
            if path is not None and pathlib.Path(path).resolve() not in checked:
                raise Refused(f"--input {path} isn't one of the checked files")
            continue
        title = value(command, i, arg, "-t", "--title")
        if title is not None:
            titles.append(title)
        if value(command, i, arg, "-b", "--body") is not None:
            raise Refused("an inline body can't be checked; write it to a file and use --body-file")
        path = value(command, i, arg, "-F", "--body-file")
        if path is not None and pathlib.Path(path).resolve() not in checked:
            raise Refused(f"--body-file {path} isn't one of the checked files")
    return titles


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
    try:
        titles = inspect(command, {pathlib.Path(f).resolve() for f in files})
    except Refused as why:
        print(f"post_checked: {why}, so nothing was posted", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        texts = list(files)
        if titles:
            title = pathlib.Path(tmp) / "title.txt"
            title.write_text("\n".join(titles) + "\n")
            texts.append(str(title))
        check = [sys.executable, str(HERE / "check_public_text.py")]
        for name in texts:
            check += ["--text", name]
        if subprocess.run(check).returncode != 0:
            print("post_checked: the public-text check failed, so nothing was posted", file=sys.stderr)
            return 1
    try:
        os.execvp(command[0], command)
    except OSError as error:
        print(f"post_checked: couldn't run {command[0]}: {error.strerror}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
