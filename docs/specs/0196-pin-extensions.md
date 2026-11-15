# Pin extensions from the extension list and unpin from the toolbar (#196)

> **Issue:** [#196](https://github.com/lukasborges/kondor/issues/196) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Make pinning an extension to the toolbar work as it does in Chrome:

- **Pin from the list:** every row of the Extensions panel (level 1) gets a pin toggle.
- **Unpin from the toolbar:** a pinned extension button gets a context menu with
  **Unpin from Toolbar**.

Today (#183) the only pin control is the **Pin to Toolbar / Unpin from Toolbar** button on level 2,
after opening one extension, and a pinned button cannot unpin itself.

## Context

- **Panel:** `qml/extensions/panel/` (#183), which already has **10 files**, the folder limit. Add
  no new file there: the changes go into existing files.
  - `ExtensionRow.qml` (63 lines): one level-1 row (icon, name, `go-next` arrow), an `ItemDelegate`.
  - `ExtensionList.qml`: the level-1 `ListView` of `ExtensionRow`s.
  - `ExtensionActions.qml` / `ExtensionActionsFooter.qml`: level 2. The footer holds the level-2
    pin `Button` (`objectName: "pinButton"`) and **Settings…**.
  - `ExtensionsToolButtons.qml`: the `Repeater` of `PinnedExtensionButton.qml` (18 lines) before the
    Extensions button. Its model is `ExtensionManager.pinnedActionExtensions(isPrivate)`, which
    depends on `ExtensionManager.revision` and `Settings.pinnedExtensions`.
- **Pins:** `ExtensionManager.isPinned(id)` and `setPinned(id, pinned)` already exist
  (`src/kondor/extensions/extensionmanager.py`, `extensions/state/extensionpins.py`). No Python
  change is needed.
- **Context-menu keys:** `qml/bookmarks/bar/BookmarksBarItem.qml` (#229) already opens a context menu
  with the Menu key (`Keys.onMenuPressed`) and Shift+F10 (`isContextMenuKey`). Use the same pattern.
- **Tests:** `tests/extensions/panel/test_extensionspanel.py` (157 lines) and
  `test_pinnedtoolbar.py` (189 lines), both close to the 200-line limit.

## Design / behavior

### 1. Pin toggle on every level-1 row (`ExtensionRow.qml`)

- **Control:** a flat, icon-only `ToolButton`, `objectName: "rowPinButton"`, placed between the
  name and the `go-next` arrow:
  - `icon.name: "window-pin"` in both states;
  - `checkable: true`, and `checked` is `true` when the extension is pinned, so a pinned row shows
    the toggle's checked background (see the prototype);
  - always visible, not only on hover.
- **Stays in sync:** `checked` must follow `Settings.pinnedExtensions` at all times, also after a
  click (a click on a checkable button breaks a plain binding). For example, re-bind it in
  `onToggled`, or drive it with a `Binding`. Pinning or unpinning anywhere else (the toolbar context
  menu of item 2) updates the toggle while the panel is open.
- **Action:** a click calls `ExtensionManager.setPinned(id, !pinned)`:
  - the panel stays open, on level 1;
  - the pinned button appears in or disappears from the toolbar at once;
  - the row keeps its place, and focus stays on the toggle.
- **Words:**
  - `ToolTip.text`: **"Pin to Toolbar"** when not pinned, **"Unpin from Toolbar"** when pinned,
    with `ToolTip.delay: 600`;
  - `Accessible.name`: **"Pin %1 to Toolbar"** / **"Unpin %1 from Toolbar"** (%1 = extension name),
    so the ten toggles have distinct names (#158), with a `//:` translator note.
- **The rest of the row** is unchanged: a click elsewhere on the row, Enter/Return or Right (Left in
  right-to-left) opens level 2. The dimming of #183 applies to the icon and the name only; the pin
  toggle keeps its normal look on a row that is off on this site.
- **Keyboard:**
  - Up and Down still move between rows (row focus);
  - Tab from a focused row moves to its pin toggle, Shift+Tab back to the row;
  - Space on the toggle pins or unpins; Up/Down on the toggle move to the previous/next row.
- **Private tabs:** the toggle is not shown (`visible: !tab.isPrivate`), because a pin is written to
  disk (same rule as #183). The row looks as in #183.

### 2. Context menu on a pinned toolbar button (`PinnedExtensionButton.qml`)

- **Menu:** a `Menu` with one item, **"Unpin from Toolbar"**, icon `window-unpin`. It calls
  `ExtensionManager.setPinned(id, false)`; the button disappears from the toolbar.
- **Opening it:**
  - right-click on the button (a `TapHandler` with `acceptedButtons: Qt.RightButton`, as in
    `BookmarksBarItem.qml`): the menu opens at the pointer;
  - Menu key or Shift+F10 on the focused button: the menu opens under the button
    (`popup(button, 0, button.height)`).
- **Left-click** keeps opening the panel at the extension's level 2 (#183).
- **Focus after unpinning:** the button is destroyed, so give focus to the Extensions button when
  the unpin came from the keyboard, so a keyboard user is not left without focus.
- **Private windows:** the pinned buttons open no context menu (`TapHandler` and key handlers
  disabled when the current tab is private), since unpinning writes to disk.
- **File size:** `PinnedExtensionButton.qml` is 18 lines; with the menu it stays under 200. If
  `ExtensionsToolButtons.qml` needs to pass the private flag or the Extensions button for focus, add
  `required property`s.

### 3. Level 2 loses its pin button (`ExtensionActionsFooter.qml`)

- Remove the **Pin to Toolbar / Unpin from Toolbar** `Button` from the level-2 footer, with the
  `isPinned` / `isPrivate` plumbing that only fed it (`ExtensionActions.qml`). The footer keeps
  **Settings…**, aligned to the trailing edge as today.
- Reason: pinning now has one place on level 1 and one undo on the toolbar; a third control for the
  same state on level 2 is duplication (see "Decisions").

### 4. Strings, README, decisions

- **New strings:** "Pin %1 to Toolbar", "Unpin %1 from Toolbar" (with `//:` notes).
- **Reused strings:** "Pin to Toolbar", "Unpin from Toolbar" (now tooltips and the menu item).
- **Translations:** run `update_translations` and translate the new strings in every `i18n/*.ts`;
  no `unfinished` messages.
- **`README.md`:** the **Extensions** bullet says extensions can be pinned from the list and
  unpinned from the toolbar (at most about ten words for the change).

### 5. Tests (pytest, through `scripts/run-pytests.sh`)

Put the new tests in `tests/extensions/panel/`, in a new file `test_pinning.py` (the two existing
test files are close to 200 lines). Move `test_pin_button_toggles_pin` out of
`test_extensionspanel.py` and replace it; update `test_private_tab_has_no_site_switch_and_no_pin`
to the row toggle.

- `test_row_pin_toggles_pin`: clicking `rowPinButton` pins, the panel stays open on level 1, a
  second click unpins.
- `test_row_pin_is_checked_when_pinned`: `checked` follows a `setPinned` made outside the panel,
  also after the toggle has been clicked once.
- `test_row_pin_names_the_extension`: accessible name "Pin Sample Extension to Toolbar", then
  "Unpin Sample Extension from Toolbar".
- `test_private_tab_has_no_row_pin` (in the private-tab test).
- `test_level_two_has_no_pin_button`.
- `test_pinned_button_menu_unpins` (right-click opens the menu; its item unpins and the button goes
  away).
- `test_pinned_button_menu_opens_with_keys` (Menu key and Shift+F10).
- `test_private_window_pinned_button_has_no_menu`.

## Acceptance criteria

- [ ] Level 1 matches `prototypes/196-extensions-pin-list.qml`: a `window-pin` toggle on every row,
      checked for pinned extensions, between the name and the arrow.
- [ ] Clicking the toggle (or Space on it) pins / unpins at once, the toolbar updates, and the panel
      stays open on level 1. Clicking the rest of the row still opens level 2.
- [ ] The toggle's checked state always matches `Settings.pinnedExtensions`, also after clicks and
      after unpinning from the toolbar.
- [ ] Tooltips "Pin to Toolbar" / "Unpin from Toolbar"; accessible names "Pin %1 to Toolbar" /
      "Unpin %1 from Toolbar".
- [ ] Right-click, the Menu key and Shift+F10 on a pinned toolbar button open a menu with
      **Unpin from Toolbar** (`window-unpin`), matching `prototypes/196b-pinned-button-menu.qml`;
      it removes the button. Keyboard focus goes to the Extensions button afterwards.
- [ ] Level 2 has no pin button any more (`prototypes/183b-extensions-panel-actions.qml`).
- [ ] Private tabs and windows: no row toggle and no context menu on pinned buttons; nothing is
      written to disk.
- [ ] No new file in `qml/extensions/panel/` (folder limit); `scripts/check-code-quality.py
      --changed origin/main` is clean.
- [ ] The tests of "Design → Tests" exist and pass, with all Python checks of AGENTS.md
      (`ruff`, `mypy --strict`, `scripts/build.py`, `scripts/run-pytests.sh`,
      `scripts/check-qml-api.py`); the smoke test prints no QML errors.
- [ ] Translations complete; `README.md` Extensions bullet updated.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Install at least three action extensions from `lukasborges/kondor-extensions`
   (`python3 tools/pack.py extensions/<id>`, then **Install from File…**).
2. Open the Extensions panel. Every row has a pin; none is checked.
3. Click the pin of one extension: its button appears before the Extensions button, the pin is
   checked, the panel stays open. Click the pin again: the button goes away.
4. Pin two extensions. Right-click one pinned button and choose **Unpin from Toolbar**: it goes away.
   Open the panel: its pin is no longer checked.
5. Keyboard only: open the panel, Down to a row, Tab to its pin, Space. Close with Esc. Tab to the
   pinned button and press Shift+F10, then Enter: the button goes away and focus is on the
   Extensions button.
6. Open an extension (level 2): there is no Pin / Unpin button, only **Settings…**.
7. Open a private window: no pins on the rows; right-clicking a pinned button opens no menu.

## Out of scope

- Reordering pins by dragging.
- More items in the pinned button's context menu (Settings…, Remove, Manage Extensions…).
- A context menu on the level-1 rows or on the Extensions button.
- Any Python or Settings change: the pin API of #183 is reused as is.

## Dependencies

- #183 Extensions panel (the panel, `setPinned`, `Settings.pinnedExtensions`), closed.
- #229 (the context-menu key pattern in `BookmarksBarItem.qml`).

## Prototype

- Level 1 with pin toggles, two extensions pinned:
  [`prototypes/196-extensions-pin-list.qml`](../../prototypes/196-extensions-pin-list.qml),
  [screenshot](../../prototypes/screenshots/196-extensions-pin-list.png).
- Context menu of a pinned button:
  [`prototypes/196b-pinned-button-menu.qml`](../../prototypes/196b-pinned-button-menu.qml),
  [screenshot](../../prototypes/screenshots/196b-pinned-button-menu.png).
- Level 2 without the pin button:
  [`prototypes/183b-extensions-panel-actions.qml`](../../prototypes/183b-extensions-panel-actions.qml),
  [screenshot](../../prototypes/screenshots/183b-extensions-panel-actions.png).
- Shared mock: `prototypes/common/ExtensionsPanelMock.qml` (`showPins`).

## Decisions

| Question | Decision |
| --- | --- |
| A pin button on every level-1 row, rejected in #183? | Reversed by the maintainer: pinning works as in Chrome. The #183 row in the kde-ux `decisions.md` is updated. |
| Two icons (`window-pin` / `window-unpin`) for the row toggle, or one checkable toggle? | One `window-pin` checkable toggle: the checked background shows "pinned" without words, the state is in the tooltip and accessible name. `window-unpin` on nine rows would read as "these are pinned". |
| Show the row pin only on hover? | No: hover-only controls fail on touch and keyboard (kde-ux non-negotiable). Always visible. |
| Keep Pin / Unpin on level 2? | Removed. Level 1 and the toolbar menu cover pinning and unpinning; a third control for the same state is duplication. |
| Same accessible name on every row toggle ("Pin to Toolbar")? | No: "Pin %1 to Toolbar" so the ten toggles are distinct (#158). The tooltip stays short because the row already names the extension. |
| More items in the pinned button's menu? | Out of scope; only **Unpin from Toolbar**, as the issue asks. |
| Pin toggle or context menu in private windows? | Neither: a pin is written to disk (#183 rule). |
