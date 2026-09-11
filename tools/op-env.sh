#!/usr/bin/env bash
# Print `export VAR=value` lines for every secret reference in op.env, resolved
# through the 1Password CLI. Nothing is written to disk.
#
#   eval "$(tools/op-env.sh)"          # export into the current shell
#   tools/op-env.sh --check            # report which items resolve, print no values
#
# Prefer `op run --env-file=op.env -- <cmd>` (what the Makefile does) when you only
# need the keys for a single command.
set -euo pipefail

here=$(cd "$(dirname "$0")/.." && pwd)
envfile="$here/op.env"

command -v op >/dev/null || { echo "1Password CLI 'op' not found: brew install 1password-cli" >&2; exit 1; }
op whoami >/dev/null 2>&1 || op signin >/dev/null

check=0
[ "${1:-}" = "--check" ] && check=1

status=0
while IFS='=' read -r name ref; do
  case "$name" in ''|\#*) continue ;; esac
  if value=$(op read "$ref" 2>/dev/null); then
    if [ $check -eq 1 ]; then echo "ok       $name  ($ref)"; else printf 'export %s=%q\n' "$name" "$value"; fi
  else
    echo "missing  $name  ($ref)" >&2
    status=1
  fi
done < "$envfile"
exit $status
