#!/usr/bin/env bash
# Maintainer tool: build an AppImage of origin/main and install it on this machine after every
# merged PR, so the installed Kondor Browser always matches main.
#
#   scripts/local-appimage.sh --if-merged   # build + install only if a PR was merged since the last install (timer)
#   scripts/local-appimage.sh --now         # build + install origin/main right away
#   scripts/local-appimage.sh --install     # create the control worktree + systemd user timer (every 2 min)
#   scripts/local-appimage.sh --uninstall   # remove the timer and service (keeps the installed AppImage)
#
# What it does (same packaging as .github/workflows/release.yml):
#   1. builds origin/main (Release) in a cached build dir and packages it with linuxdeploy;
#   2. smoke-tests the AppImage offscreen on a throwaway profile (no QML errors allowed);
#   3. installs it to ~/AppImages/kondor.appimage (previous one kept as kondor.appimage.prev),
#      plus the desktop entry (Exec pointing at the AppImage) and the icons in ~/.local/share;
#   4. sends a desktop notification. A failed build or smoke test installs nothing.
#
# Environment (all optional):
#   KONDOR_REPO             main checkout (default: the repository this script belongs to)
#   KONDOR_APPIMAGE_CONTROL worktree kept at origin/main (default: ~/.local/share/kondor-appimage/control)
#   KONDOR_APPIMAGE_STATE   log, lock and last installed commit (default: ~/.local/state/kondor-appimage)
#   KONDOR_APPIMAGE_CACHE   build dir, AppDir and linuxdeploy tools (default: ~/.cache/kondor-appimage)
#   KONDOR_APPIMAGE_DEST    installed AppImage (default: ~/AppImages/kondor.appimage)

main() {
  set -uo pipefail

  local script_dir repo
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo="${KONDOR_REPO:-$(dirname "$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir)")}"
  local control="${KONDOR_APPIMAGE_CONTROL:-$HOME/.local/share/kondor-appimage/control}"
  local state="${KONDOR_APPIMAGE_STATE:-$HOME/.local/state/kondor-appimage}"
  local cache="${KONDOR_APPIMAGE_CACHE:-$HOME/.cache/kondor-appimage}"
  local dest="${KONDOR_APPIMAGE_DEST:-$HOME/AppImages/kondor.appimage}"
  local gh_repo="lukasborges/kondor"
  mkdir -p "$state" "$cache"

  log() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$state/appimage.log" >&2; }
  notify() { command -v notify-send >/dev/null && notify-send -a "Kondor AppImage" -i kondor "$1" "$2" || true; }

  ensure_control() {
    git -C "$repo" fetch -q origin || { log "git fetch failed"; return 1; }
    if [[ ! -e "$control/.git" ]]; then
      mkdir -p "$(dirname "$control")"
      git -C "$repo" worktree add -q --detach "$control" origin/main || return 1
    fi
    git -C "$control" checkout -q --force --detach origin/main
  }

  # Merged PRs (number<TAB>title) whose merge commit is on origin/main but not in the installed build.
  merged_since() {
    local installed="$1" num oid title
    gh pr list --repo "$gh_repo" --state merged --limit 30 \
      --json number,title,mergeCommit -q '.[] | "\(.number)\t\(.mergeCommit.oid)\t\(.title)"' 2>/dev/null |
      while IFS=$'\t' read -r num oid title; do
        git -C "$control" merge-base --is-ancestor "$oid" HEAD 2>/dev/null || continue
        [[ -n "$installed" ]] && git -C "$control" merge-base --is-ancestor "$oid" "$installed" 2>/dev/null && continue
        printf '%s\t%s\n' "$num" "$title"
      done
  }

  check_deps() {
    local missing=() p
    for p in file qt6-qttools-devel qt6-qtwebengine-devel kf6-kirigami kf6-qqc2-desktop-style \
             plasma-integration plasma-breeze-qt6 qt6-qtsvg fuse-libs; do
      rpm -q "$p" >/dev/null 2>&1 || missing+=("$p")
    done
    if (( ${#missing[@]} )); then
      if [[ ! -e "$state/deps-notified" ]]; then
        log "missing packages: ${missing[*]} (sudo dnf install ${missing[*]})"
        notify "Kondor AppImage not built" "Missing packages: sudo dnf install ${missing[*]}"
        touch "$state/deps-notified"
      fi
      return 1
    fi
    rm -f "$state/deps-notified"
  }

  tools() {
    local t="$cache/tools"
    mkdir -p "$t"
    [[ -x "$t/linuxdeploy" ]] || { curl -fsSL -o "$t/linuxdeploy" \
      https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage &&
      chmod +x "$t/linuxdeploy"; } || return 1
    [[ -x "$t/linuxdeploy-plugin-qt" ]] || { curl -fsSL -o "$t/linuxdeploy-plugin-qt" \
      https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage &&
      chmod +x "$t/linuxdeploy-plugin-qt"; } || return 1
  }

  # Mirrors the "Prepare AppDir" and "Create AppImage" steps of release.yml.
  package() {
    local appdir="$cache/AppDir" out="$cache/out" p
    rm -rf "$appdir" "$out"
    mkdir -p "$out"
    DESTDIR="$appdir" cmake --install "$cache/build" >/dev/null || return 1
    cp "$control/packaging/kondor.desktop" "$control/packaging/kondor.png" "$appdir/"
    mkdir -p "$appdir/usr/libexec" "$appdir/usr/share/qt6" "$appdir/usr/qml/org/kde" \
             "$appdir/usr/plugins/platforms" "$appdir/usr/plugins/sqldrivers"
    cp /usr/lib64/qt6/libexec/QtWebEngineProcess "$appdir/usr/libexec/" 2>/dev/null || true
    cp -r /usr/share/qt6/resources /usr/share/qt6/translations "$appdir/usr/share/qt6/" 2>/dev/null || true
    cp -r /usr/lib64/qt6/qml/org/kde/desktop /usr/lib64/qt6/qml/org/kde/qqc2desktopstyle "$appdir/usr/qml/org/kde/"
    cp /usr/lib64/qt6/plugins/platforms/libqwayland.so "$appdir/usr/plugins/platforms/" 2>/dev/null || true
    cp -r /usr/lib64/qt6/plugins/wayland-* "$appdir/usr/plugins/" 2>/dev/null || true
    cp /usr/lib64/qt6/plugins/sqldrivers/libqsqlite.so "$appdir/usr/plugins/sqldrivers/"
    for p in platformthemes/KDEPlasmaPlatformTheme6.so styles/breeze6.so \
             kf6/kirigami/platform/org.kde.desktop.so iconengines/libqsvgicon.so; do
      mkdir -p "$appdir/usr/plugins/$(dirname "$p")"
      cp "/usr/lib64/qt6/plugins/$p" "$appdir/usr/plugins/$p" || return 1
    done
    (cd "$out" && PATH="$cache/tools:/usr/lib64/qt6/bin:$PATH" QML_SOURCES_PATHS="$control/qml" \
      APPIMAGE_EXTRACT_AND_RUN=1 NO_STRIP=1 LDAI_OUTPUT=Kondor-x86_64.AppImage OUTPUT=Kondor-x86_64.AppImage \
      "$cache/tools/linuxdeploy" --appdir "$appdir" --plugin qt \
        --exclude-library "libp11-kit.so*" \
        --deploy-deps-only "$appdir/usr/plugins/platformthemes" \
        --deploy-deps-only "$appdir/usr/plugins/styles" \
        --deploy-deps-only "$appdir/usr/plugins/kf6" \
        --deploy-deps-only "$appdir/usr/plugins/iconengines" \
        --deploy-deps-only "$appdir/usr/plugins/sqldrivers" &&
      # The Qt plugin deploys libp11-kit again despite --exclude-library: drop it, then package.
      # NSS loads the system p11-kit-proxy.so (a symlink to libp11-kit); a second, bundled copy
      # crashes in its destructor when the app quits.
      rm -f "$appdir"/usr/lib/libp11-kit.so* &&
      "$cache/tools/linuxdeploy" --appdir "$appdir" --exclude-library "libp11-kit.so*" \
        --output appimage) || return 1
    [[ ! -e "$appdir/usr/lib/libp11-kit.so.0" ]] || return 1
    [[ -s "$out/Kondor-x86_64.AppImage" ]]
  }

  # Runs the extracted AppImage offscreen on a throwaway profile. The AppImage has no offscreen
  # platform plugin, so the system one is copied into the extracted tree (never into the image).
  smoke() {
    local dir rc out
    dir="$(mktemp -d "$cache/smoke.XXXXXX")"
    (cd "$dir" && "$cache/out/Kondor-x86_64.AppImage" --appimage-extract >/dev/null) || { rm -rf "$dir"; return 1; }
    cp /usr/lib64/qt6/plugins/platforms/libqoffscreen.so "$dir/squashfs-root/usr/plugins/platforms/"
    out="$(XDG_CONFIG_HOME="$dir/config" XDG_DATA_HOME="$dir/data" XDG_CACHE_HOME="$dir/cache" \
      QT_QPA_PLATFORM=offscreen timeout 15 "$dir/squashfs-root/AppRun" about:blank 2>&1)"
    rc=$?
    rm -rf "$dir"
    printf '%s\n' "$out" > "$state/smoke.log"
    if [[ $rc -ne 124 && $rc -ne 0 ]]; then log "smoke test: exit code $rc"; return 1; fi
    if grep -Eq 'ReferenceError|TypeError|Cannot assign|is not a type|is not installed|qrc:.*error' <<<"$out"; then
      log "smoke test: QML errors (see $state/smoke.log)"; return 1
    fi
  }

  install_files() {
    local d="$HOME/.local/share" new="$dest.new"
    mkdir -p "$(dirname "$dest")" "$d/applications" "$d/icons/hicolor/scalable/apps" "$d/icons/hicolor/256x256/apps"
    cp "$cache/out/Kondor-x86_64.AppImage" "$new" && chmod +x "$new" || return 1
    [[ -e "$dest" ]] && cp -p "$dest" "$dest.prev"
    mv -f "$new" "$dest"   # new inode: a running copy keeps working
    sed -e "s|^Exec=kondor|Exec=$dest|" -e "/^Type=Application\$/a TryExec=$dest" \
      "$control/packaging/kondor.desktop" > "$d/applications/kondor.desktop"
    local icons_changed=0
    cmp -s "$control/packaging/kondor.svg" "$d/icons/hicolor/scalable/apps/kondor.svg" || icons_changed=1
    cp "$control/packaging/kondor.svg" "$d/icons/hicolor/scalable/apps/kondor.svg"
    cp "$control/packaging/kondor.png" "$d/icons/hicolor/256x256/apps/kondor.png"
    (( icons_changed )) && rm -f "$HOME/.cache/icon-cache.kcache"
    command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1 || true
  }

  # A failed commit is not retried by the timer (only --now or a newer merge builds again).
  fail() {
    log "$1: $2"
    notify "Kondor AppImage not installed" "$1: $2"
    git -C "$control" rev-parse HEAD > "$state/failed"
  }

  build_and_install() {
    local reason="$1" head build_log
    head="$(git -C "$control" rev-parse --short HEAD)"
    check_deps || return 1
    build_log="$state/build-$head.log"
    log "building $head ($reason); log: $build_log"
    {
      cmake -S "$control" -B "$cache/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr &&
        cmake --build "$cache/build" --parallel "$(nproc)" &&
        tools && package
    } >"$build_log" 2>&1 || { fail "$head" "build failed: see $build_log"; return 1; }
    smoke || { fail "$head" "smoke test failed: see $state/smoke.log"; return 1; }
    install_files || { log "install of $head failed"; return 1; }
    git -C "$control" rev-parse HEAD > "$state/installed"
    log "installed $head at $dest"
    notify "Kondor Browser updated" "$reason"
  }

  run() {
    local mode="$1" installed merged reason
    exec 9>"$state/lock"
    flock -n 9 || { log "another build is running"; return 0; }
    ensure_control || return 1
    installed="$(cat "$state/installed" 2>/dev/null || true)"
    if [[ "$mode" == if-merged ]]; then
      [[ "$installed" == "$(git -C "$control" rev-parse HEAD)" ]] && return 0
      [[ "$(cat "$state/failed" 2>/dev/null)" == "$(git -C "$control" rev-parse HEAD)" ]] && return 0
      merged="$(merged_since "$installed")"
      [[ -n "$merged" ]] || return 0
      reason="$(printf '%s\n' "$merged" | sed 's/^\([0-9]*\)\t/#\1 /' | paste -sd ';' | sed 's/;/; /g')"
    else
      reason="manual build of origin/main"
    fi
    build_and_install "$reason"
  }

  install_timer() {
    ensure_control || exit 1
    local unit_dir="$HOME/.config/systemd/user"
    mkdir -p "$unit_dir"
    cat > "$unit_dir/kondor-appimage.service" <<EOF
[Unit]
Description=Build and install the Kondor Browser AppImage after merged PRs
After=network-online.target

[Service]
Type=oneshot
Nice=10
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=KONDOR_REPO=$repo
Environment=KONDOR_APPIMAGE_CONTROL=$control
Environment=KONDOR_APPIMAGE_STATE=$state
Environment=KONDOR_APPIMAGE_CACHE=$cache
Environment=KONDOR_APPIMAGE_DEST=$dest
ExecStartPre=/usr/bin/git -C $repo fetch -q origin
ExecStartPre=/usr/bin/git -C $control checkout -q --force --detach origin/main
ExecStart=/bin/bash $control/scripts/local-appimage.sh --if-merged
EOF
    cat > "$unit_dir/kondor-appimage.timer" <<EOF
[Unit]
Description=Check for merged Kondor PRs every 2 minutes

[Timer]
OnActiveSec=30s
OnBootSec=2min
OnUnitInactiveSec=2min

[Install]
WantedBy=timers.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now kondor-appimage.timer
    log "installed kondor-appimage.timer (journalctl --user -u kondor-appimage -f)"
  }

  case "${1:-}" in
    --if-merged) run if-merged ;;
    --now)       run now ;;
    --install)   install_timer ;;
    --uninstall) systemctl --user disable --now kondor-appimage.timer
                 rm -f "$HOME/.config/systemd/user/kondor-appimage."{service,timer}
                 systemctl --user daemon-reload; log "timer removed" ;;
    *) sed -n '2,23p' "${BASH_SOURCE[0]}"; exit 2 ;;
  esac
}

main "$@"
