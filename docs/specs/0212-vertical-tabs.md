# Vertical tabs in a side bar (#212)

> **Issue:** [#212](https://github.com/lukasborges/kondor/issues/212) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Add a fourth tab style, **Side Bar**, to the picker from #211: the tabs become a vertical list on
the side of the page, like the sidebars of System Settings and Dolphin. With many tabs the titles
stay readable, where horizontal tabs shrink to 120 px.

## Context

- **#211** adds `Settings.tabStyle` (`"floating"`, `"below"`, `"classic"`), the
  Settings → General → Appearance picker, and the `tabStyle` property of `TabStrip`. This issue adds
  the value `"vertical"`.
- **Window layout:** `qml/app/BrowserWindow.qml` has `header: ColumnLayout { TabStrip;
  NavigationToolBar; BookmarksBar }`, and `PageArea` fills the window content.
  `fullScreenControl.pageFullScreen` hides the header.
- **Tab behavior to keep:** `TabModel` (`count`, `currentIndex`, `pinnedCount`, `move…`),
  `TabContextMenu.qml` (New Tab, Reload, Duplicate Tab, Move Tab to New Window, Close Tab…),
  the drag logic of `TabDragHandler.qml` (it reorders within the pinned or unpinned section), and
  `TabButtonDelegate.qml` (icon or `BusyIndicator`, private icon, crashed icon, title).

## Design / behavior

### 1. The setting

- `Settings.tabStyle` also accepts `"vertical"`. The picker gets a fourth entry, **Side Bar**, as the
  third of four (Floating, Below Address Bar, Side Bar, Classic), matching
  `prototypes/212b-settings-tab-style.qml`.

### 2. Layout

- In the Side Bar style the horizontal `TabStrip` is hidden. The header keeps the navigation
  toolbar and the bookmarks bar.
- A side bar sits at the start edge of the content area (left; right in right-to-left languages),
  `gridUnit * 14` wide, in the `Window` color set, with a `Kirigami.Separator` between it and the
  page. It hides with the header in page full screen.
- **Private window:** the `view-private` icon moves to the start of the navigation toolbar, since
  the tab strip that held it is hidden.

### 3. Content of the side bar

- **Pinned tabs:** at the top, a wrapping row of icon-only `ToolButton`s, `checked` for the
  current tab, with the tab title as `ToolTip.text` (`ToolTip.delay: 600`) and `Accessible.name`.
  A `Kirigami.Separator` under the row. The row and the separator are hidden when no tab is pinned.
- **Other tabs:** a `ListView` of `ItemDelegate` rows, `highlighted` for the current tab: favicon or
  `BusyIndicator` (16 px), the title elided at the end, and the close button
  (`window-close-symbolic`) on the current and the hovered row only, with its space kept.
- **New Tab:** the last row of the list (`tab-new`, "New Tab"), as the list's footer.
- The list scrolls vertically with a `ScrollBar` and keeps the current tab visible when it changes.

### 4. Interaction

- Click activates a tab; middle click closes it; right click opens `TabContextMenu`; double-click on
  empty space below the rows opens a new tab.
- Dragging a row up or down reorders the unpinned tabs, with the same section rules as today.
- Keyboard: when the list has focus, Up and Down move the focus, Enter activates, and Delete closes
  the focused tab. Ctrl+Tab, Ctrl+W and the other tab shortcuts work as in the other styles.
- The mouse wheel scrolls the list. It never switches tabs.

## Acceptance criteria

- [ ] The picker offers **Side Bar**, and choosing it applies to every open window at once.
- [ ] The side bar matches `prototypes/212-vertical-tabs.qml`: pinned icons on top, the list,
      New Tab at the end, the current tab highlighted.
- [ ] With 30 tabs the list scrolls, and the current tab is scrolled into view when it changes.
- [ ] Click, middle click, the context menu, double-click on empty space, and drag to reorder
      work in the side bar.
- [ ] Keyboard only: Up, Down, Enter and Delete in the list; the tab shortcuts work.
- [ ] Private window: the private icon shows at the start of the toolbar, and the tabs show the
      private icon as in the other styles.
- [ ] Page full screen hides the side bar.
- [ ] Right-to-left layout puts the side bar on the right.
- [ ] Switching back to another style restores the horizontal strip without a restart.
- [ ] New strings are in `qsTr()`; `i18n/*.ts` are updated.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Settings → General → Appearance → **Side Bar** → OK. The tabs move into a side bar in every
   open window.
2. Pin a tab: it appears as an icon at the top. Open 30 tabs and switch with Ctrl+Tab: the list
   scrolls to follow.
3. Drag a tab to another position, middle-click a tab, right-click → Duplicate Tab.
4. Click in the list and use Up, Down, Enter and Delete.
5. Play a video in full screen: the side bar hides, and comes back after Esc.
6. Start Kondor with `-reverse` (a Qt option): the side bar is on the right.
7. Choose Floating again: the horizontal tabs come back.

## Out of scope

- Resizing or collapsing the side bar to icons only.
- Reordering pinned tabs by dragging inside the side bar.
- Tab groups or tree-style tabs.
- Moving the side bar to the other edge.

## Dependencies

- #211 (setting, picker, `TabStrip.tabStyle`).

## Prototype

- Side bar with 16 tabs, one pinned:
  [`prototypes/212-vertical-tabs.qml`](../../prototypes/212-vertical-tabs.qml),
  [screenshot](../../prototypes/screenshots/212-vertical-tabs.png).
- Picker with the fourth style:
  [`prototypes/212b-settings-tab-style.qml`](../../prototypes/212b-settings-tab-style.qml),
  [screenshot](../../prototypes/screenshots/212b-settings-tab-style.png).
- Shared mocks: `prototypes/common/TabStyleFrame.qml`, `TabStylePicker.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| Side bar as the default? | No: an option. It takes `gridUnit * 14` from the page width, which costs more than it gives with few tabs. The maintainer chose Floating as the default (#211). |
| Pinned tabs as list rows? | No: icons in a wrapping row on top, as pinned tabs are icon-only in the horizontal styles. Rows would repeat the same look for a different kind of tab. |
| New Tab as a toolbar button above the list? | No: the last row of the list, where the next tab appears. |
| Full-width blue highlight for the current tab? | Yes: it is the Breeze selection of System Settings and Dolphin sidebars. |
