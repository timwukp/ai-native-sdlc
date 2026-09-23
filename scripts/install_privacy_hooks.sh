#!/bin/sh
set -eu

case "$(uname -s 2>/dev/null || echo unknown)" in
  MINGW*|MSYS*|CYGWIN*)
    echo "privacy hook installer: POSIX-only; use the required CI check on Windows" >&2
    exit 1
    ;;
esac

command -v git >/dev/null 2>&1 || {
  echo "privacy hook installer: git is required" >&2
  exit 1
}
command -v python3 >/dev/null 2>&1 || {
  echo "privacy hook installer: python3 is required" >&2
  exit 1
}

root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "privacy hook installer: run inside the target repository" >&2
  exit 1
}
cd "$root"

[ -f scripts/privacy_scan.py ] || {
  echo "privacy hook installer: checked-in scanner is missing" >&2
  exit 1
}
[ -x .githooks/pre-push ] || {
  echo "privacy hook installer: .githooks/pre-push is not executable" >&2
  exit 1
}

current=$(git config --local --get core.hooksPath 2>/dev/null || true)
if [ -n "$current" ] && [ "$current" != ".githooks" ]; then
  echo "privacy hook installer: refusing to replace existing core.hooksPath" >&2
  exit 1
fi

legacy=$(git rev-parse --git-path hooks/pre-push)
if [ -z "$current" ] && [ -f "$legacy" ]; then
  echo "privacy hook installer: refusing to displace an existing pre-push hook" >&2
  exit 1
fi

python3 scripts/privacy_scan.py --repo .
git config --local core.hooksPath .githooks
installed=$(git config --local --get core.hooksPath)
[ "$installed" = ".githooks" ] || {
  echo "privacy hook installer: activation read-back failed" >&2
  exit 1
}
echo "privacy pre-push hook active for this repository (.githooks)"
