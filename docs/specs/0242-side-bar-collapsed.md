# Side Bar tab style: collapse to icons only (#242)

> **Issue:** [#242](https://github.com/lukasborges/kondor/issues/242) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Let the Side Bar tab style (#212) shrink to a narrow strip of tab icons, so it costs almost no page
width, and expand back to the full list with one click. The maintainer asked for it after using the
side bar: `gridUnit * 14` is a lot of width to give up on every page.

## Context

- **When:** after the switch to Python (#174), so the setting is added only to the Python
  `Settings` (`kondor/core/settings/`). If the C++ app still exists when this issue starts, the twin
  rule of #162 applies instead.
- **Side bar:** `qml/browser/sidebar/` (#212): `TabSideBar.qml` (the column: pinned tabs, separator,
  list), `SideBarPinnedTabs.qml` / `SideBarPinnedButton.qml` (icon buttons, title as tooltip),
  `SideBarTabList.qml` (the `ListView`, its `New Tab` footer, scrolling), `SideBarTabRow.qml` (one
  row: icon or spinner, title, close button), `SideBarRowDrag.qml` (reorder by drag).
  `qml/app/BrowserWindow.qml` gives the side bar its width.
- **Settings:** one `Q_PROPERTY` per option, written at once (`settingsoptions.py`,
  `settingsdefaults.py`), the same way `tabStyle` was added in #211.

## Design / behavior

### 1. The setting

- `Settings.sideBarCollapsed`: a bool, default `false`, key `UI/SideBarCollapsed` in `Kondor.conf`.
- It is not in the Settings dialog: it is changed only by the button of item 2, like the bookmarks
  bar switch. It is not part of `SettingsDraft`, so the dialog's Defaults does not touch it.
- It is global: every open window collapses or expands together, without a restart and without
  reloading a page. Collapsing in a private window writes the setting too; it is a look preference,
  not browsing data.

### 2. The toggle button

- At the bottom of the side bar, under a `Kirigami.Separator`, an icon-only `ToolButton`:
  `sidebar-collapse-left` / text **Collapse Side Bar** when expanded, `sidebar-expand-left` /
  **Expand Side Bar** when collapsed. In right-to-left layouts the `-right` icons.
  `ToolTip.text` and `Accessible.name` are the text, `ToolTip.delay: 600`.
- It is in the tab order of the side bar; Space or Enter toggles.
- Expanded: aligned to the start edge (`prototypes/212-vertical-tabs.qml`). Collapsed: centered
  (`prototypes/242-side-bar-collapsed.qml`).

### 3. Collapsed side bar (`prototypes/242-side-bar-collapsed.qml`)

- Width `gridUnit * 2 + smallSpacing * 4`, the same `Window` color set and separator.
- **Pinned tabs:** the same icon buttons; the row wraps into one column.
- **Other tabs:** each row shows only the icon (favicon, spinner, private or crashed icon),
  centered. The current tab keeps the full-width highlight of the row. No title and no close
  button: middle click, Ctrl+W and the context menu close a tab.
- **Title:** the row's `ToolTip.text` is the tab title (`ToolTip.delay: 600`), and
  `Accessible.name` stays the title, so screen readers read the same as when expanded.
- **New Tab:** the footer row shows only `tab-new`, centered, with "New Tab" as tooltip and
  accessible name.
- The scroll bar is hidden (`ScrollBar.AlwaysOff`); the mouse wheel and the "current tab stays in
  view" rule of #212 still scroll the list.
- Click, middle click, right click, double-click on empty space, drag to reorder, and the keyboard
  (Up, Down, Enter, Delete) work exactly as when expanded.

### 4. Code layout

- One `collapsed` property flows from `TabSideBar` to the list, the rows, the pinned buttons and
  the footer; no second side bar. New files, if any, stay in `qml/browser/sidebar/` within the
  AGENTS.md limits.

## Acceptance criteria

- [ ] `Settings.sideBarCollapsed` exists (default `false`), persists across restarts, and has a
      pytest test.
- [ ] The toggle button of item 2 collapses and expands the side bar in every open window at once.
- [ ] Collapsed matches `prototypes/242-side-bar-collapsed.qml`; expanded matches
      `prototypes/212-vertical-tabs.qml` with the collapse button at the bottom.
- [ ] Collapsed rows show the title as a tooltip and keep it as the accessible name.
- [ ] Every tab interaction of #212 works collapsed, keyboard included.
- [ ] Right-to-left: the side bar is on the right and uses the `-right` icons.
- [ ] Breeze and Breeze Dark; no hex colors.
- [ ] New strings in `qsTr()`; `i18n/*.ts` updated.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Choose Settings → General → Appearance → Side Bar. Open 20 tabs, pin two.
2. Click Collapse Side Bar: only icons remain; hover one: its title shows as a tooltip; the current
   tab is highlighted.
3. Middle click a tab, drag one to another position, use Up/Down/Enter in the list.
4. Open a second window: it is collapsed too. Restart Kondor: still collapsed.
5. Click Expand Side Bar: the full list is back.
6. Run with `-reverse`: the side bar is on the right with the mirrored icons.

## Out of scope

- Expanding on hover, or a resizable side bar width.
- A keyboard shortcut or a menu entry for collapsing.
- Collapsing in the horizontal styles.

## Dependencies

- #212 Vertical tabs (the side bar).
- #174 (the Python switch), so the setting is added once.

## Prototype

- Collapsed: [`prototypes/242-side-bar-collapsed.qml`](../../prototypes/242-side-bar-collapsed.qml),
  [screenshot](../../prototypes/screenshots/242-side-bar-collapsed.png).
- Expanded, with the collapse button: [`prototypes/212-vertical-tabs.qml`](../../prototypes/212-vertical-tabs.qml),
  [screenshot](../../prototypes/screenshots/212-vertical-tabs.png).
- Shared mock: `prototypes/common/TabStyleFrame.qml` (`sideBarCollapsed`).

## Decisions

| Question | Decision |
| --- | --- |
| Where is the toggle? | At the bottom of the side bar, like the sidebar toggles of KDE apps: visible, one click, in the place it changes. Not only a shortcut or a menu entry, which nobody would find. |
| Expand on hover? | No: the side bar would jump over the page whenever the mouse passes by. Tooltips give the title. |
| How does the user find a tab without titles? | The favicon, the tooltip on hover, and the accessible name. Expanding is one click away. |
| Part of the Settings dialog? | No: it is a view state changed in place, like the bookmarks bar switch; a dialog entry would duplicate the button. |
