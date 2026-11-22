# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Run a gh command that posts text to GitHub only after the public-text check passes.

Usage: post_checked.py <file> [<file> ...] -- gh <command> [<arg> ...]

Every file before `--` is checked with check_public_text.py, and so is any title in the command
(--title, -t, --subject). The check also scans every file in the checkout, so a finding anywhere
blocks every post until it's fixed. The command runs only when the check passes; otherwise nothing
runs and the exit code is 1, or 2 for a usage error.

It accepts only the gh commands agents post with, each with the flags listed in SPEC below, written
as separate words (`-t Title` or `--title=Title`, not `-tTitle` or `-dt`). Text comes only through a
title or a checked file (--body-file, or --input for gh api). Any other flag, and so any inline body,
comment or field, is refused. It guards against mistakes, not against an agent set on getting around
it: CI's check of pull request text and the cold read of memory changes still stand behind it.
"""
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
USAGE = "usage: post_checked.py <file> [<file> ...] -- gh <command> [<arg> ...]"

SWITCH, VALUE, TITLE, FILE = "switch", "value", "title", "file"
COMMON = {"-R": VALUE, "--repo": VALUE}
SPEC = {
    ("issue", "create"): {"-t": TITLE, "--title": TITLE, "-F": FILE, "--body-file": FILE, "-l": VALUE, "--label": VALUE,
                          "-m": VALUE, "--milestone": VALUE, "-a": VALUE, "--assignee": VALUE, "-p": VALUE, "--project": VALUE},
    ("issue", "comment"): {"-F": FILE, "--body-file": FILE},
    ("issue", "edit"): {"-t": TITLE, "--title": TITLE, "-F": FILE, "--body-file": FILE, "--add-label": VALUE,
                        "--remove-label": VALUE, "-m": VALUE, "--milestone": VALUE},
    ("issue", "close"): {"-r": VALUE, "--reason": VALUE},
    ("pr", "create"): {"-t": TITLE, "--title": TITLE, "-F": FILE, "--body-file": FILE, "-B": VALUE, "--base": VALUE,
                       "-H": VALUE, "--head": VALUE, "-d": SWITCH, "--draft": SWITCH, "-l": VALUE, "--label": VALUE,
                       "-m": VALUE, "--milestone": VALUE, "-a": VALUE, "--assignee": VALUE, "-r": VALUE, "--reviewer": VALUE},
    ("pr", "comment"): {"-F": FILE, "--body-file": FILE},
    ("pr", "edit"): {"-t": TITLE, "--title": TITLE, "-F": FILE, "--body-file": FILE, "--add-label": VALUE,
                     "--remove-label": VALUE, "-B": VALUE, "--base": VALUE, "-m": VALUE, "--milestone": VALUE},
    ("pr", "review"): {"-a": SWITCH, "--approve": SWITCH, "-r": SWITCH, "--request-changes": SWITCH,
                       "-c": SWITCH, "--comment": SWITCH, "-F": FILE, "--body-file": FILE},
    ("pr", "close"): {"-d": SWITCH, "--delete-branch": SWITCH},
    ("pr", "merge"): {"-s": SWITCH, "--squash": SWITCH, "-t": TITLE, "--subject": TITLE, "-F": FILE, "--body-file": FILE,
                      "--auto": SWITCH, "-d": SWITCH, "--delete-branch": SWITCH, "--match-head-commit": VALUE},
    ("api",): {"-X": VALUE, "--method": VALUE, "--input": FILE, "-H": VALUE, "--header": VALUE, "-q": VALUE,
               "--jq": VALUE, "--silent": SWITCH, "--paginate": SWITCH},
}


class Refused(Exception):
    pass


def inspect(command: list[str], checked: set[pathlib.Path]) -> list[str]:
    """Return the titles to check, or raise Refused for a command, flag or text that can't be checked."""
    if command[0] != "gh":
        raise Refused("only gh commands are supported, called as gh")
    key = ("api",) if command[1:2] == ["api"] else tuple(command[1:3])
    if key not in SPEC:
        raise Refused(f"gh {' '.join(command[1:3])} isn't a supported command")
    spec = {**COMMON, **SPEC[key]}
    titles = []
    i = 1 + len(key)
    while i < len(command):
        arg = command[i]
        if not arg.startswith("-"):
            i += 1  # a positional argument, such as a number or an endpoint
            continue
        name, has_value, attached = arg.partition("=") if arg.startswith("--") else (arg, "", "")
        kind = spec.get(name)
        if kind is None:
            raise Refused(f"{arg} isn't a flag allowed for gh {' '.join(key)}; flags go as separate words")
        if kind == SWITCH:
            if has_value:
                raise Refused(f"{name} takes no value")
            i += 1
            continue
        if has_value:
            given, i = attached, i + 1
        elif i + 1 < len(command):
            given, i = command[i + 1], i + 2
        else:
            raise Refused(f"{arg} has no value")
        if kind == TITLE:
            titles.append(given)
        elif kind == FILE and (given == "-" or pathlib.Path(given).resolve() not in checked):
            raise Refused(f"{name} {given} isn't one of the checked files")
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
