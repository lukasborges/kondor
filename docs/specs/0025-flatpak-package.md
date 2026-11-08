# Flatpak package (#25)

> **Issue:** [#25](https://github.com/lukasborges/kondor/issues/25) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish Kondor as a Flatpak (bundle attached to releases now, Flathub later).

## Context

Only an AppImage built in `.github/workflows/release.yml`. App id is effectively `kondor` (`packaging/kondor.desktop`, icon `kondor`), there is no AppStream metainfo.

## Design / behavior

1. **App id**: `io.github.lukasborges.Kondor`. Add `packaging/io.github.lukasborges.Kondor.metainfo.xml` (AppStream: id, name, summary, description, `<launchable type="desktop-id">io.github.lukasborges.Kondor.desktop</launchable>`, screenshots pointing to `assets/screenshot.png` raw GitHub URL, `<releases>` with 0.1.x entries, `<content_rating type="oars-1.1"/>`, project license GPL-3.0-or-later, metadata license CC0-1.0). Install it to `share/metainfo/` from CMake. Validate with `appstreamcli validate`.
2. **Manifest** `packaging/flatpak/io.github.lukasborges.Kondor.yml`:
   - `runtime: org.kde.Platform`, `sdk: org.kde.Sdk`, `base: io.qt.qtwebengine.BaseApp` — pick the newest matching branches available on Flathub (check with `flatpak remote-ls flathub --all | grep -E 'org.kde.Platform|io.qt.qtwebengine.BaseApp'`; BaseApp branch must equal the KDE runtime version).
   - `command: kondor`, `rename-desktop-file: kondor.desktop`, `rename-icon: kondor`.
   - `finish-args`: `--share=ipc`, `--share=network`, `--socket=wayland`, `--socket=fallback-x11`, `--socket=pulseaudio`, `--device=dri`, `--filesystem=xdg-download`, `--talk-name=org.freedesktop.Notifications`, `--talk-name=org.freedesktop.FileManager1`, `--talk-name=org.kde.kwalletd6` (if #21 is merged), `--env=QTWEBENGINE_DISABLE_SANDBOX=1` only if required (prefer the BaseApp's zypak setup).
   - module `kondor`: `buildsystem: cmake-ninja`, `config-opts: [-DCMAKE_BUILD_TYPE=Release]`, `sources: [{type: dir, path: ../..}]`.
   - Kirigami and qqc2-desktop-style come with `org.kde.Platform` (verify; otherwise add modules).
3. **CI**: new job in `release.yml` (or `flatpak.yml` on tags) using the container `ghcr.io/flathub-infra/flatpak-github-actions:kde-<version>` and the action `flatpak/flatpak-github-actions/flatpak-builder@v6` with `bundle: Kondor.flatpak`, then upload the bundle to the GitHub release (`gh release upload "$GITHUB_REF_NAME" Kondor.flatpak --clobber`).
4. **README**: install instructions (`flatpak install --user Kondor.flatpak`), note that Flathub submission is a later step.

## Acceptance criteria

- [ ] `flatpak-builder --user --install build-dir packaging/flatpak/io.github.lukasborges.Kondor.yml` builds and installs locally; `flatpak run io.github.lukasborges.Kondor` opens with Breeze style and icons.
- [ ] Downloads, notifications and audio work inside the sandbox.
- [ ] Tag builds attach `Kondor.flatpak` to the release.
- [ ] `appstreamcli validate` and `desktop-file-validate` pass.

## Manual test

Build locally, install the bundle on a clean user, browse, download a file, play a video with sound.

## Out of scope

Flathub submission PR, ARM builds.

## Dependencies

#10 (desktop file `%U` / MIME types) recommended first.

## Prototype

No UI for this issue, so there is no prototype.

## Decisions

_None yet._ Answers to developer questions (`question` label) are recorded here as `| Question | Decision |` rows.
