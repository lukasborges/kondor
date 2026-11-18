# Responsive design mode: preview a page at phone and tablet sizes (#430)

> **Issue:** [#430](https://github.com/lukasborges/kondor/issues/430) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

DevTools' device mode does not work like Chrome's in Kondor: Qt WebEngine runs DevTools in a
separate view, so Chromium falls back to a screencast inside the DevTools panel, without the
device toolbar (maintainer's report). Kondor gets its own responsive mode, like Firefox's, that
lays the page out at a device's size, with or without DevTools open.

## Context

- Page view: `qml/browser/view/PageView.qml` / `WebViewTab.qml`; page area `qml/app/PageArea.qml`.
- Per-host user agent kept in memory for the session: `ProfileIdentity.set_for_session(host,
  agent)` (`src/kondor/site/identity/profileidentity.py`, #376), which sets the header and the
  `navigator` values.
- Main menu "More Tools": `qml/app/menu/MainMenu.qml`, actions in `qml/app/BrowserActions.qml`;
  shortcuts in `qml/app/BrowserShortcuts.qml` (Ctrl+Shift+M is free; Mute Tab is Ctrl+M).

## Design / behavior (`prototypes/430-responsive-mode.qml`)

### 1. Turning it on and off

- **Ctrl+Shift+M**, the checkable **Responsive Design Mode** in More Tools (`smartphone`), toggle
  the mode **for the current tab**. It is per tab and not remembered across restarts. Private
  tabs can use it.

### 2. Toolbar

- A `ToolBar` under the navigation toolbar (above InlineBars), only for the tab in the mode:
  - device `ComboBox` (`Accessible.name` "Device"): **Responsive**, iPhone 15 (393 × 852),
    Pixel 8 (412 × 915), Galaxy S24 (360 × 780), iPad Air (820 × 1180), iPad Pro 12.9″
    (1024 × 1366);
  - width and height `SpinBox`es (200–4000, editable), "×" between them; editing them switches
    the device to Responsive;
  - **Rotate** (`object-rotate-right`) swaps width and height;
  - **Zoom to Fit** (`zoom-fit-best`, checkable, on by default): scales the view down to fit the
    page area when the size is larger, never up;
  - right-aligned **Close Responsive Mode** (`window-close`, tooltip with the shortcut).
- The last device / size used is remembered (setting `responsiveDevice`, `responsiveSize`) for
  the next time the mode is turned on.

### 3. Stage

- The page area gets a neutral background (`Kirigami.Theme` text color at 8 % over the
  background). The `WebEngineView` is laid out at exactly the chosen size in CSS pixels at zoom
  100 % (the tab's own zoom is kept but applied inside), centered horizontally, a large spacing
  from the top; when Zoom to Fit is on and it does not fit, the view item is scaled down with
  `scale` (rendering and input stay correct), and the percentage shows under it.
- Handles on the right edge, bottom edge and bottom-right corner resize it by dragging (switching
  to Responsive); the size boxes follow.
- Scroll bars of the page area appear when the view is larger and Zoom to Fit is off.

### 4. Mobile identity

- Choosing a phone or tablet sets that device's mobile user agent (iOS Safari for iPhone and iPad,
  Android Chrome for Pixel and Galaxy, matching Qt's Chromium version) for the tab's host with
  `set_for_session`, and reloads; Responsive keeps the tab's normal agent. Turning the mode off,
  or navigating to another host, restores the previous agent of that host and reloads once.
  Nothing is written to disk.
- Touch events and the device pixel ratio are **not** emulated (no Qt API without CDP): the PR
  checks Qt WebEngine 6.11 and uses a direct API if one exists.

## Acceptance criteria

- [ ] Ctrl+Shift+M and the menu item toggle the mode in the current tab only; switching tabs
      shows each tab's own state.
- [ ] iPhone 15: the page lays out at 393 × 852 (`window.innerWidth === 393`), with the iOS
      Safari agent (`navigator.userAgent` and the request header); closing restores the agent.
- [ ] Rotate, size boxes, handles and Zoom to Fit work; iPad Pro 12.9″ fits a 1100 × 700 window
      scaled down, and clicks land on the right element when scaled.
- [ ] Works with DevTools docked and in private tabs; nothing written to disk for private tabs.
- [ ] Matches `430-responsive-mode.png`, Breeze and Breeze Dark; strings in `qsTr()`,
      translations complete; README shortcut table and the "Developer tools" bullet updated.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`.

1. Open kde.org, Ctrl+Shift+M, choose iPhone 15: mobile layout; rotate; drag the corner.
2. Choose iPad Pro: scaled to fit; click a link: the right one opens.
3. Ctrl+Shift+M again: normal layout and agent back.

## Out of scope

- Touch and DPR emulation through CDP, network throttling, screenshots of the device (#410
  covers page capture), custom device lists.

## Dependencies

- None (uses #376's session identity).

## Prototype

- [`prototypes/430-responsive-mode.qml`](../../prototypes/430-responsive-mode.qml) →
  [screenshot](../../prototypes/screenshots/430-responsive-mode.png)

## Decisions

| Question | Decision |
| --- | --- |
| Fix DevTools' own device mode or build Kondor's? | Kondor's own: DevTools runs in a separate view in Qt, where Chromium only offers a screencast; a native mode works the same with DevTools closed. Maintainer approved the prototype. |
| Per tab or per window? | Per tab, like Firefox: each tab can preview a different size. |
| Mobile user agent for the whole host? | Yes, while the mode is on: #376's session identity is per host, and other tabs of that host in the same profile see it too until the mode is turned off. Accepted as a developer tool. |
