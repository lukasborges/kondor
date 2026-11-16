#!/usr/bin/env bash
# Release the current origin/main as the next version: bump it, commit, push, tag, push the tag.
# The tag starts the Release workflow (AppImage, Flatpak, GitHub release, Flatpak repository).
#
#   scripts/release.sh --next <patch|minor>   # print the next version, change nothing
#   scripts/release.sh <patch|minor>          # release it
#
# Run it from a worktree whose HEAD is origin/main, after writing the user-facing notes in
# docs/releases/v<next>.md (see docs/releases/README.md); the notes go into the release commit.
# The maintainer decided that every merged fix or feature is released: a fix is a patch, a
# feature a minor version.
set -euo pipefail

current_version() { sed -n 's/^version = "\(.*\)"$/\1/p' pyproject.toml; }

next_version() {
  local major minor patch
  IFS=. read -r major minor patch <<< "$(current_version)"
  case "$1" in
    patch) echo "$major.$minor.$((patch + 1))" ;;
    minor) echo "$major.$((minor + 1)).0" ;;
    *) echo "usage: scripts/release.sh [--next] <patch|minor>" >&2; return 1 ;;
  esac
}

require_main() {
  git fetch -q origin main
  [[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] && return
  echo "HEAD is not origin/main: refresh the worktree first" >&2; return 1
}

require_notes() {
  [[ -s "docs/releases/v$1.md" ]] && return
  echo "write the release notes in docs/releases/v$1.md first" >&2; return 1
}

bump_version() {
  local old new="$1" today
  old="$(current_version)" today="$(date +%F)"
  sed -i "s/^version = \"$old\"$/version = \"$new\"/" pyproject.toml
  sed -i "s/^PROJECT_VERSION = \"$old\"$/PROJECT_VERSION = \"$new\"/" src/kondor/app/startup/stagedbuild.py
  sed -i "s/\"Kondor $old\"/\"Kondor $new\"/" tests/app/test_appmain.py
  sed -i "s|^\(\s*\)<releases>$|&\n\1  <release version=\"$new\" date=\"$today\"/>|" \
    packaging/io.github.lukasborges.Kondor.metainfo.xml
}

publish() {
  git add -A pyproject.toml src/kondor/app/startup/stagedbuild.py tests/app/test_appmain.py \
    packaging/io.github.lukasborges.Kondor.metainfo.xml "docs/releases/v$1.md"
  git commit -q -m "chore: release v$1"
  git push -q origin HEAD:main
  git tag -a "v$1" -m "Kondor Browser $1"
  git push -q origin "v$1"
  echo "released v$1"
}

release() {
  local version
  version="$(next_version "$1")"
  require_main
  require_notes "$version"
  bump_version "$version"
  publish "$version"
}

cd "$(git rev-parse --show-toplevel)"
if [[ "${1:-}" == --next ]]; then next_version "${2:-}"; else release "${1:-}"; fi
