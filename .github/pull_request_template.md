Closes #<!-- issue number -->

Spec: `docs/specs/<NNNN>-<slug>.md`

## What changed

<!-- Short summary of the implementation, grouped by file/area. -->

## Differences from spec / prototype

<!-- Anything that deviates, and why. "None" if nothing. -->

## How it was tested

- [ ] Clean build, no new warnings in changed files
- [ ] `QT_QPA_PLATFORM=offscreen timeout 15 ./build/kondor` shows no QML errors
- [ ] Spec "Manual test" done (describe results below)
- [ ] `ctest --test-dir build` passes (once tests exist)

## Checklist

- [ ] Every "Acceptance criteria" item is met; nothing from "Out of scope" was built
- [ ] Matches the prototype (screenshot attached if it has UI)
- [ ] Nothing from private tabs touches disk
- [ ] English strings in `qsTr()`, KDE HIG wording, Breeze icon names, `Kirigami.Theme` colors
- [ ] README updated (features, shortcuts) when user-visible behavior changed
- [ ] New dependencies added to CMake, README and both workflows
- [ ] Branch rebased on current `main`; Conventional Commits; no attribution trailers
