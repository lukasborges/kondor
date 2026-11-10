#!/usr/bin/env bash
# Finish the signed Flatpak repository and assemble the site served on GitHub Pages.
# Used by the release workflow and by the Flatpak pull-request check (docs/specs/0098-*.md).
#
# Usage: scripts/flatpak-site.sh <gpg key id> <repo dir> <site dir>
# GNUPGHOME must point to the keyring that holds the key.
set -euo pipefail

key_id="$1"
repo="$2"
site="$3"
app_id="io.github.lukasborges.Kondor"
repo_url="https://lukasborges.github.io/kondor/repo/"
max_bytes=$((900 * 1024 * 1024))
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

gpg_home="${GNUPGHOME:?GNUPGHOME must be set}"

# Prune to depth 2, add static deltas, refresh summary and the AppStream branch.
flatpak build-update-repo --gpg-sign="$key_id" --gpg-homedir="$gpg_home" \
    --generate-static-deltas --prune --prune-depth=2 --title="Kondor Browser" "$repo"

gpg --export "$key_id" > kondor-public.gpg
gpg_key_b64="$(base64 -w0 < kondor-public.gpg)"

# Bundle that also receives updates from the repository.
flatpak build-bundle --repo-url="$repo_url" --gpg-keys=kondor-public.gpg \
    --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo \
    "$repo" Kondor.flatpak "$app_id" stable

rm -rf "$site"
mkdir -p "$site"
cp -a "$repo" "$site/repo"
for f in kondor.flatpakrepo "$app_id.flatpakref"; do
    sed "s|@GPGKEY@|$gpg_key_b64|" "$here/packaging/flatpak/$f" > "$site/$f"
done
cat > "$site/index.html" <<'HTML'
<!DOCTYPE html>
<meta charset="utf-8">
<title>Kondor Browser</title>
<meta http-equiv="refresh" content="0; url=https://github.com/lukasborges/kondor#download">
<link rel="canonical" href="https://github.com/lukasborges/kondor#download">
<p><a href="https://github.com/lukasborges/kondor#download">Kondor Browser</a></p>
HTML

size="$(du -sb "$site" | cut -f1)"
echo "Site size: $size bytes"
echo "Largest file:"
find "$site" -type f -printf '%s %p\n' | sort -rn | head -n 1
if [ "$size" -gt "$max_bytes" ]; then
    echo "::error::The site is $size bytes, above the 900 MB limit for GitHub Pages"
    exit 1
fi
