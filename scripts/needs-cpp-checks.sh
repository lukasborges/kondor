#!/usr/bin/env bash
# Tells whether a change can affect the C++ app, so it needs the C++ checks (CMake build, ctest,
# smoke test, translations). Used by agents (AGENTS.md → "Which checks a change needs") and CI.
#
#   scripts/needs-cpp-checks.sh <base>   # exit 0 and list the paths that need them, or exit 1
set -euo pipefail

readonly NON_CPP_PATHS='^(kondor|pytests|docs|prototypes|scripts|packaging/python-proof)/|^\.github/workflows/python-proof\.yml$|^(pyproject\.toml|opencode\.json|\.gitignore|LICENSE)$|\.md$'

main() {
  local base="${1:?usage: $0 <base>}"
  local paths
  paths="$(cpp_paths "$base")"
  if [[ -z "$paths" ]]; then
    echo "No change affects the C++ app: skip the C++ checks."
    return 1
  fi
  echo "These changes need the C++ checks:"
  echo "$paths"
}

cpp_paths() {
  git diff --name-only "$1...HEAD" | grep -vE "$NON_CPP_PATHS" || true
}

main "$@"
