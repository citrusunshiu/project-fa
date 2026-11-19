# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Keep the issue tracker's labels and milestones in line with the repository.

The fixed labels come from .github/labels.yml. Each slice design doc named in the catalog gets a
slice:<name> label, and each roadmap phase in the charter gets a milestone described by its exit
criteria. Prints the changes; --apply makes them, and --prune also deletes labels that aren't
listed. Milestones are never deleted. Needs an authenticated gh.

Usage: sync_tracker.py [--repo OWNER/REPO] [--apply] [--prune]
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PHASE = re.compile(r"^\| \*\*(\d+)\. (.+?)\*\* \| [^|]+ \| (.+?) \|$")
LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def gh(*args: str) -> str:
    done = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True)
    if done.returncode:
        sys.exit(f"sync_tracker: gh {' '.join(args[:3])} failed: {done.stderr.strip()}")
    return done.stdout


def wanted_labels() -> dict[str, tuple[str, str]]:
    spec = yaml.safe_load((ROOT / ".github" / "labels.yml").read_text())
    labels = {l["name"]: (l["color"].lower(), l["description"]) for l in spec["labels"]}
    slices: dict[str, list[str]] = {}
    for c in yaml.safe_load((ROOT / "catalog" / "components.yaml").read_text())["components"]:
        slices.setdefault(pathlib.Path(c["design"]).stem, []).append(c["id"])
    for name, ids in sorted(slices.items()):
        description = ", ".join(ids)
        if len(description) > 100:  # GitHub's limit
            description = description[:97] + "..."
        labels[f"slice:{name}"] = (spec["slice_color"].lower(), description)
    return labels


def wanted_milestones() -> dict[str, str]:
    milestones = {}
    for line in (ROOT / "docs" / "charter.md").read_text().splitlines():
        if m := PHASE.match(line):
            milestones[f"Phase {m[1]}: {m[2]}"] = "Done when: " + LINK.sub(r"\1", m[3])
    if not milestones:
        sys.exit("sync_tracker: no roadmap phases found in docs/charter.md")
    return milestones


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="OWNER/REPO; defaults to this checkout's GitHub repository")
    ap.add_argument("--apply", action="store_true", help="make the changes instead of printing them")
    ap.add_argument("--prune", action="store_true", help="also delete labels that aren't listed")
    a = ap.parse_args()
    repo = a.repo or gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner").strip()

    have = {l["name"]: (l["color"].lower(), l["description"] or "")
            for l in json.loads(gh("label", "list", "-R", repo, "--limit", "500", "--json", "name,color,description"))}
    changes = []
    for name, (color, description) in wanted_labels().items():
        if name not in have:
            changes.append((f"create label {name}", ["label", "create", name, "-R", repo, "--color", color, "--description", description]))
        elif have[name] != (color, description):
            changes.append((f"update label {name}", ["label", "edit", name, "-R", repo, "--color", color, "--description", description]))
    for name in sorted(set(have) - set(wanted_labels())):
        if a.prune:
            changes.append((f"delete label {name}", ["label", "delete", name, "-R", repo, "--yes"]))
        else:
            print(f"unlisted label {name} (kept; --prune deletes it)")

    existing = {m["title"]: m for m in json.loads(gh("api", f"repos/{repo}/milestones?state=all&per_page=100"))}
    for title, description in wanted_milestones().items():
        if title not in existing:
            changes.append((f"create milestone {title}", ["api", f"repos/{repo}/milestones", "-f", f"title={title}", "-f", f"description={description}"]))
        elif (existing[title]["description"] or "") != description:
            number = existing[title]["number"]
            changes.append((f"update milestone {title}", ["api", "-X", "PATCH", f"repos/{repo}/milestones/{number}", "-f", f"description={description}"]))

    for summary, args in changes:
        print(summary)
        if a.apply:
            gh(*args)
    verdict = "applied" if a.apply else "dry run, nothing changed (--apply makes them)"
    print(f"tracker {repo}: {len(changes)} changes; {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
