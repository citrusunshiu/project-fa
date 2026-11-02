# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Check catalog/components.yaml against the docs and the code (ADR-0002).

Errors fail the check. While the repository is in Phase 0, planned components whose design
doc doesn't exist yet are listed as pending instead: writing them is what Phase 0 is for.
"""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "components.yaml"
STATUSES = {"planned", "proposed", "optional"}
FIDELITIES = ["F0", "F1", "F2", "F3"]
KINDS = {"service", "platform", "client"}
REQUIRED = ("id", "name", "line", "kind", "status", "fidelity", "design")


def main() -> int:
    cat = yaml.safe_load(CATALOG.read_text())
    errors, pending = [], []
    languages = set(cat["languages"])
    lines = set(cat["lines"])
    infra = {i["id"] for i in cat["infrastructure"]}
    comps = cat["components"]
    ids = [c.get("id") for c in comps]
    known = set(ids) | infra

    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"duplicate id: {dup}")

    for c in comps:
        cid = c.get("id", "?")
        for field in REQUIRED:
            if field not in c:
                errors.append(f"{cid}: missing {field}")
        if c.get("line") not in lines:
            errors.append(f"{cid}: unknown line {c.get('line')!r}")
        if c.get("kind") not in KINDS:
            errors.append(f"{cid}: unknown kind {c.get('kind')!r}")
        if c.get("status") not in STATUSES:
            errors.append(f"{cid}: unknown status {c.get('status')!r}")
        fid = c.get("fidelity")
        if fid not in FIDELITIES:
            errors.append(f"{cid}: unknown fidelity {fid!r}")
            continue
        lang = c.get("language")
        if lang is not None and lang not in languages:
            errors.append(f"{cid}: language {lang!r} is not on the closed list (ADR-0004)")
        for ref in c.get("depends_on", []) + c.get("stores", []) + c.get("brokers", []):
            if ref not in known:
                errors.append(f"{cid}: refers to unknown id {ref!r}")

        design = c.get("design")
        if design and not (ROOT / design).is_file():
            if c.get("status") != "planned":
                pass  # proposed and optional components need a design doc once accepted
            elif cat.get("phase", 0) == 0:
                pending.append((design, cid))
            else:
                errors.append(f"{cid}: design doc {design} does not exist")

        level = FIDELITIES.index(fid)
        if level >= 2 and c.get("kind") != "client":
            path = c.get("path")
            if not path or not (ROOT / path).is_dir():
                errors.append(f"{cid}: at {fid} but has no code directory (set path)")
            if lang and not (ROOT / "templates" / lang).is_dir():
                errors.append(f"{cid}: language {lang} has no service template in templates/{lang}/")
        if level >= 3:
            for field in ("slo", "runbook", "experiment"):
                ref = c.get(field)
                if not ref or not (ROOT / ref).is_file():
                    errors.append(f"{cid}: at F3 but {field} is missing")

    paths = {c.get("path") for c in comps}
    services = ROOT / "services"
    if services.is_dir():
        for d in sorted(p for p in services.iterdir() if p.is_dir()):
            if f"services/{d.name}" not in paths:
                errors.append(f"services/{d.name} has no catalog entry")

    for e in errors:
        print(f"error: {e}")
    if pending:
        print(f"Phase 0: {len({d for d, _ in pending})} design docs still to write")
        for design in sorted({d for d, _ in pending}):
            owners = ", ".join(cid for d, cid in pending if d == design)
            print(f"  {design}  ({owners})")
    by_status = {s: sum(c.get("status") == s for c in comps) for s in sorted(STATUSES)}
    print(f"catalog: {len(comps)} components ({', '.join(f'{n} {s}' for s, n in by_status.items())}), "
          f"{len(infra)} off-the-shelf; {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
