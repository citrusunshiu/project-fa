#!/bin/sh
# Runs every check CI runs. Needs uv (https://docs.astral.sh/uv/).
set -eu
cd "$(dirname "$0")/.."
status=0
uv run --quiet tools/check_catalog.py || status=1
uv run --quiet tools/check_links.py || status=1
uv run --quiet tools/check_public_text.py "$@" || status=1
uv run --quiet tools/test_post_checked.py 2>/dev/null || { echo "error: tools/test_post_checked.py failed; run it for details" >&2; status=1; }
exit $status
