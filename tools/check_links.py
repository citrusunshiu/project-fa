# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check that every relative link in tracked Markdown files points at a file and heading that exist.

External links aren't fetched. Anchors are compared with GitHub's heading slugs.
"""
import pathlib
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^(```|~~~)")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
INLINE_CODE = re.compile(r"`[^`]*`")


def slugs(path: pathlib.Path) -> set[str]:
    """GitHub's heading anchors for a Markdown file, with -1, -2 suffixes for repeats."""
    seen: dict[str, int] = {}
    out = set()
    for line in strip_code(path.read_text()):
        m = HEADING.match(line)
        if not m:
            continue
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", m.group(1))
        slug = re.sub(r"[^\w\- ]", "", text.lower().replace("`", "")).replace(" ", "-")
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        out.add(slug if n == 0 else f"{slug}-{n}")
    return out


def strip_code(text: str) -> list[str]:
    """The file's lines with fenced blocks blanked out and inline code removed."""
    lines, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line.strip()):
            fenced = not fenced
            lines.append("")
            continue
        lines.append("" if fenced else INLINE_CODE.sub("", line))
    return lines


def main() -> int:
    files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "*.md"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    errors, cache = [], {}
    for name in files:
        src = ROOT / name
        for lineno, line in enumerate(strip_code(src.read_text()), 1):
            for target in LINK.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                    continue  # http:, https:, mailto: and other schemes
                file_part, _, anchor = target.partition("#")
                dest = (src.parent / unquote(file_part)).resolve() if file_part else src
                if not dest.exists():
                    errors.append(f"{name}:{lineno}: {target}: no such file")
                    continue
                if anchor and dest.suffix == ".md":
                    if dest not in cache:
                        cache[dest] = slugs(dest)
                    if anchor not in cache[dest]:
                        errors.append(f"{name}:{lineno}: {target}: no heading #{anchor}")
    for e in errors:
        print(f"error: {e}")
    print(f"links: {len(files)} Markdown files; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
