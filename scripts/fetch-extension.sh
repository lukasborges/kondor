#!/usr/bin/env bash
# Download a Chrome Web Store extension and unpack it for `kondor --load-extension`.
#
# Usage: scripts/fetch-extension.sh <extension-id> <out-dir> [--prodversion <x.y.z>]
set -euo pipefail

usage() {
    echo "Usage: $0 <extension-id> <out-dir> [--prodversion <x.y.z>]" >&2
    exit 2
}

[ $# -ge 2 ] || usage
id=$1
out=$2
shift 2
prodversion=
while [ $# -gt 0 ]; do
    case $1 in
        --prodversion) [ $# -ge 2 ] || usage; prodversion=$2; shift 2 ;;
        *) usage ;;
    esac
done

[[ $id =~ ^[a-p]{32}$ ]] || { echo "error: '$id' is not a valid extension id (32 letters a-p)" >&2; exit 1; }

for tool in curl unzip od; do
    command -v "$tool" >/dev/null || { echo "error: '$tool' is required" >&2; exit 1; }
done

if [ -z "$prodversion" ]; then
    lib=$(ldconfig -p 2>/dev/null | awk '/libQt6WebEngineCore\.so\.6 /{print $NF; exit}')
    [ -n "$lib" ] || lib=$(find /usr/lib64 /usr/lib /usr/lib/x86_64-linux-gnu -name 'libQt6WebEngineCore.so.6' 2>/dev/null | head -n1)
    if [ -n "$lib" ]; then
        prodversion=$(strings "$lib" | grep -o 'Chrome/[0-9][0-9.]*' | head -n1 | cut -d/ -f2 || true)
    fi
    [ -n "$prodversion" ] || { echo "error: cannot detect the Chromium version; pass --prodversion" >&2; exit 1; }
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

url="https://clients2.google.com/service/update2/crx?response=redirect&prodversion=${prodversion}&acceptformat=crx2,crx3&x=id%3D${id}%26uc"
curl -fsSL --connect-timeout 15 --max-time 120 "$url" -o "$work/ext.crx" || { echo "error: download failed for $id" >&2; exit 1; }

# CRX3: "Cr24", uint32 version (3), uint32 header length, header, then a ZIP.
magic=$(head -c 4 "$work/ext.crx")
[ "$magic" = "Cr24" ] || { echo "error: the response is not a CRX file (extension not found or not available?)" >&2; exit 1; }
u32() { od -An -tu4 -j"$1" -N4 --endian=little "$work/ext.crx" | tr -d ' '; }
version=$(u32 4)
case $version in
    3) offset=$((12 + $(u32 8))) ;;
    2) offset=$((16 + $(u32 8) + $(u32 12))) ;;  # CRX2: key length, signature length
    *) echo "error: unsupported CRX version $version" >&2; exit 1 ;;
esac
tail -c +$((offset + 1)) "$work/ext.crx" > "$work/ext.zip"

mkdir -p "$out"
# unzip exits 1 for warnings only (CRX payloads are fine otherwise).
rc=0
unzip -oq "$work/ext.zip" -d "$out" || rc=$?
[ "$rc" -le 1 ] || { echo "error: cannot unzip the extension (unzip exit $rc)" >&2; exit 1; }
[ -f "$out/manifest.json" ] || { echo "error: no manifest.json in the package" >&2; exit 1; }
echo "Extension $id unpacked into $out (Chromium $prodversion)"
