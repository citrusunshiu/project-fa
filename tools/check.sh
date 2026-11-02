#!/bin/sh
# Runs every check CI runs. Needs uv (https://docs.astral.sh/uv/).
set -eu
cd "$(dirname "$0")/.."
status=0
uv run --quiet tools/check_catalog.py || status=1
uv run --quiet tools/check_links.py || status=1
uv run --quiet tools/check_public_text.py "$@" || status=1
exit $status
