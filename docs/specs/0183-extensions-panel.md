# Extensions panel that scales to many extensions (#183)

> **Issue:** [#183](https://github.com/lukasborges/kondor/issues/183) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Replace the toolbar **Extensions** `Menu` with a two-level **panel** that stays small with many
extensions:

- **Level 1:** one row per extension.
- **Level 2:** the actions of one extension. The panel stays open after an action, so it can be
  repeated.
- **Pins:** an extension can be pinned to the toolbar as its own button.

Today's menu lists every item of every extension in one flat list: a header, its actions and
"Run on <host>". With 10 extensions that is 40+ rows, and the menu closes after every click. This
issue replaces #179.

## Context

- **Menu today:** `qml/extensions/ExtensionsMenu.qml`, opened by the `extensionsButton` `ToolButton`
  in `qml/app/NavigationToolBar.qml` (lines 132–151). Its logic stays valid and moves into the panel:
  - **Rows:** `ExtensionManager.actionExtensions(isPrivate)` returns one map per extension:
    `id`, `name`, `iconSource`, `siteToggle` (already `false` in private tabs) and `items`
    (`id`, `title`, `checkable`, `icon`).
  - **Actions:** `tab.extensionItems.trigger(extensionId, itemId, checkable)` runs an action, and
    `tab.extensionItems.isChecked(extensionId, itemId)` reads a checkable one.
  - **This site:** `ExtensionManager.siteEnabled(id, url)` / `setSiteEnabled(id, url, enabled)`,
    then `tab.siteReload.recordToggle(id, name, enabled)` shows the **Reload** `SiteReloadBar`
    (#180). Nothing reloads automatically.
  - **Run on <host>:** the row is shown only when `ExtensionManager.originOf(tab.url) !== ""`.
- **Settings of one extension:** `qml/extensions/ExtensionSettingsDialog.qml`, opened with
  `openFor(id)`. It works on its own: the settings page and `tests/extensions` use it standalone.
- **Settings page:** `BrowserWindow.openSettingsPage("extensions")` (from #176).
- **Removing an extension:** `ExtensionManager::remove(id)` emits `extensionRemoved(id)`.
- **Popup model:** `qml/passwords/bar/SavedPasswordsPopup.qml` (#176) is the newest address-bar popup:
  its header, keyboard handling, Esc → `tab.focusPage()`, and closing on tab change.
- **Folder limits:**
  - `qml/extensions/` and `src/extensions/` already hold 10 files each.
  - New QML goes into a new sub-feature folder, `qml/extensions/panel/`. `ExtensionsMenu.qml` is
    deleted.
  - New C++ goes into an existing sub-folder (`src/extensions/state/`) or into existing files.

## Design / behavior

### 1. Pins (Settings + ExtensionManager)

- **Settings:** add `Q_PROPERTY(QStringList pinnedExtensions READ … WRITE … NOTIFY …)`, default
  empty: a list of extension ids in pin order (Shared building block **Settings**).
- **ExtensionManager**, new members:

  | Member | Behavior |
  | --- | --- |
  | `Q_INVOKABLE bool isPinned(const QString &id) const` | `id` is in `Settings::pinnedExtensions`. |
  | `Q_INVOKABLE void setPinned(const QString &id, bool pinned)` | Appends `id` to the list or removes it. Does nothing if the list would not change. |
  | `Q_INVOKABLE QVariantList pinnedActionExtensions(bool isPrivate) const` | The entries of `actionExtensions(isPrivate)` whose id is pinned, **in pin order**. Disabled extensions, and extensions not allowed in private windows, are left out because `actionExtensions` already leaves them out. |

- **Uninstall:** `remove(id)` also calls `setPinned(id, false)`.
- **Disable:** disabling an extension keeps its pin, so the button comes back when it is enabled
  again.
- **QML bindings** that list pins depend on both `ExtensionManager.revision` and
  `Settings.pinnedExtensions`.
- **Sorting:** `actionExtensions` returns the entries sorted by their localized name
  (`QString::localeAwareCompare`), so level 1 is sorted by name.
- **File and folder limits:** keep the folder and file limits (see Context). For example, put the pin
  logic in a small class in `src/extensions/state/` that `ExtensionManager` forwards to, rather than
  growing `extensionconfiguration.cpp` (193 lines) past 200.

### 2. The panel (`qml/extensions/panel/ExtensionsPanel.qml`)

- **Type:** a `Popup` under the Extensions button. Its right edge is aligned with the button
  (`x: button.width - width`, `y: button.height`).
- **Popup settings:** `width: 380`, `padding: Kirigami.Units.largeSpacing`, `modal: false`,
  `focus: true`, and it closes on press outside. The Extensions button has `checked: panel.opened`.
- **API:**
  - `required property var tab`;
  - `open()` shows level 1;
  - `openAt(extensionId)` shows level 2 of that extension;
  - `signal manageRequested()`;
  - `signal settingsRequested(string extensionId)`.
- **Two levels:** the panel shows **one level at a time** in the same popup. It is not a submenu,
  and there is no animation requirement.
- **Rebuild** the level-1 data on every open, and whenever `ExtensionManager.revision` or
  `Settings.pinnedExtensions` changes while the panel is open:
  - if the extension shown on level 2 no longer exists, go back to level 1;
  - if no action extension is left, close the panel.
- **Close** the panel when the current tab changes.
- **Esc** closes the panel and calls `tab.focusPage()`, as in #176.

#### Level 1: the list

- **Header:**
  - `Kirigami.Heading { level: 4 }` "Extensions";
  - under it, a `Label` with the tab's host in `Kirigami.Theme.disabledTextColor`, hidden when the
    host is empty.
- **Separators:** a `Kirigami.Separator` comes next. A list in a `ScrollView`/`ListView` follows,
  then a separator, then the footer.
- **List height:** the list's height is `Math.min(contentHeight, Kirigami.Units.gridUnit * 18)`. It
  scrolls above that.
- **Rows** (`ExtensionRow.qml`, an `ItemDelegate`), one per action extension, sorted by name:
  - **Content:**
    - the extension icon (`Kirigami.Icon`, `source: iconSource`, `smallMedium`);
    - the name, elided, filling the width;
    - a `go-next` arrow at `iconSizes.small`.
  - **Off on this site:** the extension is *off on this site* when it has `siteToggle` and
    `!ExtensionManager.siteEnabled(id, tab.url)`. Then:
    - `enabled: false` is set on the icon and the name **only**, which dims them;
    - the row itself stays enabled, hoverable, focusable and clickable;
    - the arrow keeps its normal look.
  - **Tooltip:** "Off on this site" (`ToolTip.delay: 600`) when the extension is off. Otherwise
    there is no tooltip.
  - **`Accessible.name`:** the name, or "%1, off on %2" (extension, host) when it is off.
  - **Opening level 2:** clicking the row, Enter/Return or Right opens its level 2.
- **Footer:** a flat `Button` **"Manage Extensions…"** with icon `configure`. It closes the panel and
  emits `manageRequested()`.
- **Keyboard:** opening on level 1 focuses the first row. Up and Down move between rows, and the
  focused row is scrolled into view.

#### Level 2: one extension

- **Header** (`RowLayout`):
  - a `ToolButton` `go-previous`, icon-only, with `ToolTip.text` and `Accessible.name`
    **"Back to Extensions"** (`ToolTip.delay: 600`);
  - the extension icon at `smallMedium`;
  - a `Kirigami.Heading { level: 4 }` with the name, elided.

  A separator follows the header.
- **Actions,** one per item, in manifest order:
  - **Plain items:** an `ItemDelegate` row (`ExtensionActionRow.qml`) with a `smallMedium` icon slot
    showing `item.icon`. The slot keeps its width when the item has no icon, so titles line up.
    The row also has the title. Click or Enter calls `tab.extensionItems.trigger(id, itemId, false)`.
  - **Checkable items:** a `CheckBox` with the title. It is bound to
    `tab.extensionItems.isChecked(…)`, which is refreshed on `tab.extensionItems.changed()`.
    Toggling it calls `trigger(id, itemId, true)`.
  - **The panel stays open** after any action.
- **This site:** only when the extension has `siteToggle` and the tab's origin is not empty:
  - a separator;
  - then a row with a `Label` "Run on %1" (host) and a `Switch`.
  - The `Switch` has `Accessible.name` "Run %1 on %2" (extension, host). It is checked when
    `siteEnabled(id, tab.url)`.
  - **Toggling it** calls `setSiteEnabled` and then `tab.siteReload.recordToggle`, as the menu does
    today. Going back to level 1 shows the new dimmed or normal state.
- **Footer,** after a separator, in a `RowLayout`:
  - **Pin button** (left), a flat non-checkable `Button`:
    - **"Pin to Toolbar"** with `window-pin` when the extension is not pinned;
    - **"Unpin from Toolbar"** with `window-unpin` when it is pinned;
    - it calls `ExtensionManager.setPinned(id, !pinned)`, and the panel stays open.
    - **Hidden in private tabs:** pins are written to disk, and private tabs offer nothing that
      writes.
  - **"Settings…"** with `configure` (right): it closes the panel and emits
    `settingsRequested(id)`.
- **Going back:** the Back button, Left or Backspace returns to level 1, with focus on that
  extension's row.
- **Keyboard:** opening level 2 focuses the first action, or the Back button when there is none.
  Up and Down move between action rows, and Tab moves through every control.
- **Right-to-left:**
  - `go-next` and `go-previous` follow `LayoutMirroring`, as the arrows in other Kondor popups do:
    use `Qt.application.layoutDirection` to swap them;
  - the keys swap too: Left opens level 2, and Right goes back.

### 3. Toolbar: pinned buttons (`qml/extensions/panel/ExtensionsToolButtons.qml`)

- **Moving out of `NavigationToolBar.qml`:** the Extensions button, the panel and an
  `ExtensionSettingsDialog` (`parent: Overlay.overlay`) move into one new component.
  `NavigationToolBar` uses that component where the button is today, and gives it `tabs` and
  `browserWindow`.
- **Pinned buttons:** before the Extensions button, a `Repeater` over
  `ExtensionManager.pinnedActionExtensions(tabs.currentTab.isPrivate)`. Each is an icon-only
  `ToolButton` (`PinnedExtensionButton.qml`):
  - its icon is the extension's `iconSource`;
  - `ToolTip.text` and `Accessible.name` are the extension name, with `ToolTip.delay: 600`;
  - clicking it calls `panel.openAt(id)`. The panel is still anchored to the Extensions button.
- **Visibility:** the Extensions button keeps its current visibility rule. Pinned buttons follow
  `pinnedActionExtensions(isPrivate)`, so private windows show only the extensions allowed there.
  Showing them writes nothing.
- **Signals:**
  - `manageRequested` → `browserWindow.openSettingsPage("extensions")`;
  - `settingsRequested(id)` → `settingsDialog.openFor(id)`.

### 4. Strings and README

- **Strings:** every string is in `qsTr()`. `%1`/`%2` strings use `.arg()`, with a `//:`
  translator note.
- **New strings:** "Off on this site", "%1, off on %2", "Back to Extensions", "Pin to Toolbar",
  "Unpin from Toolbar" and "Settings…".
- **Reused strings:** "Extensions", "Manage Extensions…", "Run on %1" and "Run %1 on %2".
- **Translations:** run `update_translations` and translate the new strings in every `i18n/*.ts`,
  and drop the obsolete ones.
- **`README.md`:** the **Extensions** bullet mentions pinning an extension to the toolbar.

### 5. Tests

- **C++** (in `tests/extensions/state/` or `tst_extensions.cpp`, wherever the folder limits allow):
  - `pinnedExtensionsKeepPinOrder`;
  - `setPinnedIgnoresDuplicates`;
  - `removeUnpinsExtension`;
  - `pinnedHidesExtensionsNotAllowedInPrivate`;
  - `actionExtensionsAreSortedByName`.
- **Settings:** `pinnedExtensionsDefaultsToEmpty` and a round trip, in `tests/core/tst_settings.cpp`.
- **QML** (`tests/extensions/tst_extensionsui.cpp`): replace the `ExtensionsMenu` tests and keep
  their coverage:
  - `listShowsOneRowPerExtension`;
  - `rowIsDimmedWhenOffOnSite` (icon and label disabled, row enabled, accessible name "…, off on …");
  - `rowOpensActions`;
  - `backReturnsToListAndFocusesRow`;
  - `actionKeepsPanelOpen`;
  - `checkableActionShowsState`;
  - `runOnSiteSwitchShowsReloadBar` (replacing the menu + reload-bar tests);
  - `privateTabHasNoSiteSwitchAndNoPin`;
  - `openAtShowsActions`;
  - `pinButtonTogglesPin`.

## Acceptance criteria

- [ ] The Extensions button opens the panel, not a `Menu`. Level 1 and level 2 match
      `prototypes/183-extensions-panel.qml` and `prototypes/183b-extensions-panel-actions.qml`. The
      shortcut text on level 2 comes with #182, not here.
- [ ] Level 1:
  - [ ] one row per action extension, sorted by name;
  - [ ] a row is dimmed (icon and name only) when the extension is off on this site, and stays
        clickable;
  - [ ] the tooltip and the accessible name give the state;
  - [ ] the list scrolls above `gridUnit * 18`.
- [ ] Level 2:
  - [ ] it shows the items, with checkable ones as `CheckBox`es;
  - [ ] actions keep the panel open;
  - [ ] the **Run on <host>** switch saves at once and shows the Reload bar;
  - [ ] Back, Left and Backspace return to level 1.
- [ ] **Pin to Toolbar** / **Unpin from Toolbar** adds or removes a toolbar button before the
      Extensions button. Clicking that button opens the panel at the extension's level 2.
- [ ] Pins persist in `Settings.pinnedExtensions`. Uninstalling an extension removes its pin.
- [ ] **Settings…** opens that extension's settings dialog. **Manage Extensions…** opens Settings →
      Extensions.
- [ ] Keyboard and accessibility:
  - [ ] the first row is focused on open, and Up/Down, Enter/Right, Left/Backspace and Esc work
        (Esc gives focus back to the page);
  - [ ] the focus is always visible;
  - [ ] every icon-only control has a tooltip and an `Accessible.name`;
  - [ ] in right-to-left layouts the arrows and keys mirror.
- [ ] Private tabs:
  - [ ] no Run on switch and no Pin button;
  - [ ] pinned buttons appear only for extensions allowed in private windows;
  - [ ] nothing is written to disk.
- [ ] `ExtensionsMenu.qml` is gone, and no file still refers to it.
- [ ] The tests in "Design → Tests" exist and pass, `ctest` passes, and the smoke test prints no QML
      errors.
- [ ] Translations are complete. `scripts/check-code-quality.py --changed origin/main` is clean, and
      the folder limits hold.
- [ ] The `README.md` Extensions bullet is updated.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Install at least three action extensions from `lukasborges/kondor-extensions`, packed with
   `python3 tools/pack.py extensions/<id>` and added with **Install from File…**. Include Video
   Speed Controller and one with `siteToggle`.
2. Open `https://www.youtube.com/` and click the Extensions button. The panel shows "Extensions",
   the host, and one row per extension sorted by name.
3. Open an extension with `siteToggle` and turn **Run on www.youtube.com** off. The Reload bar
   appears and the page does not reload by itself. Click Back: the row is dimmed and its tooltip
   says "Off on this site". Open it again and turn the switch back on.
4. Open Video Speed Controller and click **Faster** three times. The panel stays open, and the video
   speed changes each time.
5. Click **Pin to Toolbar**. A button with its icon appears before the Extensions button, and the
   label changes to **Unpin from Toolbar**. Close the panel and click the pinned button: the panel
   opens directly on Video Speed Controller.
6. Keyboard only: open the panel, use Down and Right to open an extension, Left to go back, and
   Esc to close.
7. Click **Settings…**: that extension's settings dialog opens. **Manage Extensions…** opens Settings
   → Extensions.
8. Restart Kondor with the same temporary profile: the pin is still there. Remove the extension in
   Settings: its toolbar button disappears.
9. Open a private window: no Run on switch and no Pin button. A pinned extension shows only if it is
   allowed in private windows.

## Out of scope

- **#182:** item icons that are validated against the theme, and the shortcut text column, come
  from the `keysSetting` field. Show `item.icon` as it arrives today.
- Showing an extension's live state, such as the current speed. That needs a new extension API.
- Reordering pins by dragging.
- A stepper row (− 1.25× +) for extension actions.
- Any change to the extension settings dialog or to the Settings → Extensions page.

## Dependencies

- #107 Kondor extensions (`ExtensionManager`, action items).
- #180 (`tab.siteReload`, `SiteReloadBar`).
- #176 (`openSettingsPage`, popup pattern).
- #156 (sub-feature folders).
- #182 builds on this panel.

## Prototype

- Level 1, ten extensions, one off on this site:
  [`prototypes/183-extensions-panel.qml`](../../prototypes/183-extensions-panel.qml), rendered in
  [`prototypes/screenshots/183-extensions-panel.png`](../../prototypes/screenshots/183-extensions-panel.png).
- Level 2, Video Speed Controller pinned:
  [`prototypes/183b-extensions-panel-actions.qml`](../../prototypes/183b-extensions-panel-actions.qml),
  rendered in
  [`prototypes/screenshots/183b-extensions-panel-actions.png`](../../prototypes/screenshots/183b-extensions-panel-actions.png).
- Shared mock: `prototypes/common/ExtensionsPanelMock.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| Keep the flat menu, with section headers (#179)? | Rejected. 10 extensions made 40+ rows taller than the screen, and the menu closed after each action. Two levels in one popup instead. |
| A pin button on every level-1 row? | Rejected: ten identical icons for a rare action. Pin / Unpin is a labeled button on level 2. |
| A status icon or a "Running on this site" subtitle on rows? | Rejected. The icon alone was ambiguous, and the subtitle doubled the row height. |
| A `Switch` on every level-1 row? | Rejected: ten switches made the list noisy. The switch is on level 2. |
| An "Off on this site" label on rows? | Rejected as noisy (maintainer). The icon and name are dimmed, the row stays enabled, and the state is in the tooltip and `Accessible.name`. |
| Level 2 as a submenu? | No. The popup replaces its content (drill-down with Back), because submenus close on every action and hide behind hover. |
| Pin / Unpin in private windows? | Hidden. A pin is written to disk, and private tabs offer nothing that writes. Pins made in normal windows still show there when the extension is allowed in private windows. |
| Where does a pinned button open the panel? | At the extension's level 2, anchored to the Extensions button, so the panel is always in one place. |
| Shortcut text on level 2, as in the prototype? | Comes with #182 (`keysSetting`). The spec wins over the prototype here. |
| Kept pins of disabled extensions? | Yes: disabling hides the button, and enabling brings it back. Only uninstalling removes the pin. |
| Right-to-left | Arrows and Left/Right keys mirror, so "forward" always points into level 2 (kde-ux review of the prototype; the screenshots are left-to-right only). |
