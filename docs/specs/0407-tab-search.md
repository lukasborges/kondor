# Tab search: find and switch to any open tab (#407)

> **Issue:** [#407](https://github.com/lukasborges/kondor/issues/407) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

With many tabs in several windows, finding one by scanning the tab strip is slow. A search popup
lists every open tab, filters as the user types and switches to the chosen one, raising its window.

## Context

- Windows and their tabs: `src/kondor/app/windows/` (`WindowManager`, `windowtabs.py`:
  `index_in_window`, `show_tab_in`), one `TabModel` per window.
- Tab strip: `qml/browser/tabstrip/` (all horizontal styles); side bar: `qml/browser/sidebar/`.
- Toolbar popups: `qml/common/ToolbarPopup.qml`. Shortcuts: `qml/app/BrowserShortcuts.qml`.

## Design / behavior (`prototypes/407-tab-search.qml`)

### 1. Opening

- **Ctrl+Shift+A** (free today) and a **Search Tabs** button (`go-down-search`, tooltip "Search
  Tabs", `Accessible.name` the same) open the popup in the current window.
- Horizontal tab styles: the button is the last item of the tab row, after the empty space, right
  aligned. Vertical style: the button sits in the side bar's bottom row next to the collapse
  toggle (also when collapsed). The popup opens under / next to the button; with Ctrl+Shift+A it
  opens at the same place.
- The search field has the focus; Esc closes the popup and returns the focus where it was.

### 2. The list

- Sections in window order: **This Window** first, then **Window 2**, **Window 3**… (the other
  normal windows, numbered in the order `WindowManager` keeps them), as
  `Kirigami.ListSectionHeader`.
- A **private window** lists only its own tabs (one section, no header). A normal window never
  lists the tabs of private windows.
- Each row: favicon (`SiteIcon`), title, and the address without the scheme (`kde.org/…`,
  `ElideMiddle`) in the small disabled-color font. The current tab of this window has a
  `checkmark` at the end. Pinned and sleeping tabs are listed like the others (sleeping tabs
  dimmed as in the strip).
- Filter: case-insensitive substring of the title or the address, every word of the query must
  match (`kde doc` finds "Kirigami documentation" on develop.kde.org); matches are bold. Empty
  query: every tab. No match: a `Kirigami.PlaceholderMessage` "No matching tabs".
- Keyboard: Up/Down move the selection (it starts on the first row that is not this window's
  current tab), Enter switches, Esc closes. Mouse: click switches.
- The selected (or hovered) row shows a close button (`window-close-symbolic`, tooltip "Close
  Tab"); closing keeps the popup open and the list updates. Ctrl+W in the field does the same
  for the selected row.
- Long lists scroll; the popup is `gridUnit * 24` wide and at most 70 % of the window height.

### 3. Switching

- A tab of this window becomes current; a tab of another window becomes current there and that
  window is raised and activated (`show_tab_in`), un-minimized if needed. The popup closes.

## Acceptance criteria

- [ ] Ctrl+Shift+A and the button open the popup in every tab style (floating, below, classic,
      vertical expanded and collapsed); the field has focus.
- [ ] Two normal windows and a private one: a normal window lists its own and the other normal
      window's tabs, never the private ones; the private window lists only its own.
- [ ] Filtering by title, by address and by two words works; matches are bold; no match shows the
      placeholder.
- [ ] Enter / click switches tabs and raises the other window; the close button and Ctrl+W close
      the selected tab and the list updates.
- [ ] Matches `407-tab-search.png`, Breeze and Breeze Dark.
- [ ] Strings in `qsTr()`, translations complete; README shortcut table and the "Tidy tabs"
      bullet updated.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`.

1. Two windows with five tabs each, a private window with two. Ctrl+Shift+A in window 1, type a
   word from a tab of window 2, Enter: window 2 comes to the front on that tab.
2. In the private window: only its tabs are listed.
3. Vertical tabs, collapsed side bar: the button is there and the popup opens next to it.

## Out of scope

- Searching history or bookmarks (the address bar does that), recently closed tabs, tab groups
  (#408) in the list, sorting by last use.

## Dependencies

- None.

## Prototype

- [`prototypes/407-tab-search.qml`](../../prototypes/407-tab-search.qml) →
  [screenshot](../../prototypes/screenshots/407-tab-search.png) (`withTabSearch` in
  `prototypes/common/TabStyleFrame.qml`)

## Decisions

| Question | Decision |
| --- | --- |
| Shortcut? | Ctrl+Shift+A, as Chrome and Firefox: users already know it, and it is free in Kondor. |
| Show private tabs from normal windows? | No, and private windows see only themselves: listing them would mix the two worlds that private browsing keeps apart. |
| Close tabs from the list? | Yes, on the selected or hovered row only: cleaning up many tabs is a common reason to search them, and a close button on every row would be clutter. |
| Approved | Prototype approved by the maintainer. |
