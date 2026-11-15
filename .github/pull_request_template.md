Closes #<!-- issue number -->

Spec: `docs/specs/<NNNN>-<slug>.md`

## What changed

<!-- Short summary of the implementation, grouped by file/area. -->

## Differences from spec / prototype

<!-- Anything that deviates, and why. "None" if nothing. -->

## How it was tested

- [ ] `ruff check` and `mypy --strict kondor` pass
- [ ] `python3 scripts/build.py` and `scripts/run-pytests.sh` pass
- [ ] Offscreen smoke test (`QT_QPA_PLATFORM=offscreen timeout 15 env PYTHONPATH=src python3 -m kondor`, isolated `XDG_*` dirs) shows no QML errors
- [ ] Spec "Manual test" done (describe results below)

## Checklist

- [ ] Every "Acceptance criteria" item is met; nothing from "Out of scope" was built
- [ ] Matches the prototype (screenshot attached if it has UI)
- [ ] Nothing from private tabs touches disk
- [ ] English strings in `qsTr()`, KDE HIG wording, Breeze icon names, `Kirigami.Theme` colors
- [ ] README updated (features, shortcuts) when user-visible behavior changed
- [ ] New dependencies added to README, `build.yml`, `release.yml`, `prepare-appdir.sh` / `pyside-modules.txt` and the Flatpak manifest
- [ ] Branch rebased on current `main`; Conventional Commits; no attribution trailers
