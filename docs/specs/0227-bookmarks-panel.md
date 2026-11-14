# Bookmarks panel: search, recent bookmarks and folders from one toolbar button (#227)

> **Issue:** [#227](https://github.com/lukasborges/kondor/issues/227) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Reach every bookmark from one toolbar button, without the bookmarks bar taking a row of the
window: a **Bookmarks panel** with search, the recently added bookmarks, and the folders, which
open in place. The bookmarks bar stays as it is and becomes optional: the panel has its switch.

Today the only ways to a bookmark are the bookmarks bar (a flat row: items that do not fit are cut,
no search), the main menu's Bookmarks submenu, address-bar suggestions, and the Bookmarks window.

## Context

- **When:** `qml/` and `src/` are frozen during the Python port (#162), so this starts after #174.
  `BookmarkManager` is the Python class by then, with the same QML API.
- **`BookmarkManager` (QML singleton):** `search(text, limit)`, `folderContents(folderId)`,
  `childCount(folderId)`, `toolbarFolderId()`, `otherFolderId()`, `bookmark(id)`, the `revision`
  property and the `bookmarksChanged` signal. Bookmark rows have an increasing `id`, and no date.
- **Bookmarks bar:** `qml/bookmarks/bar/BookmarksBar.qml`, shown when `Settings.showBookmarksBar`
  (Ctrl+Shift+B toggles it). `BookmarkMenu.qml` is the folder menu; `SiteIcon` draws favicons.
- **Address bar star:** `qml/bookmarks/bar/BookmarkButton.qml`, in `AddressBarButtons.qml`, uses
  `bookmarks` / `bookmarks-bookmarked`. In the current Breeze these are the same ribbon as
  `bookmarks-organize` and `bookmark-toolbar`.
- **Panel pattern:** the Extensions panel (#183, `qml/extensions/panel/ExtensionsPanel.qml`): a
  `Popup` under its toolbar button, two levels, Back with Left/Backspace, Esc closes and focuses
  the page, it closes when the tab changes.
- **Bookmarks window:** `BrowserWindow.openBookmarks()` (Ctrl+Shift+O).
- **Opening:** `BrowserWindow.openUrl(url, background)`; Ctrl+click and middle click open in a
  background tab elsewhere in the app.

## Design / behavior

### 1. The button

- A `ToolButton` in the navigation toolbar, before the main menu button: icon `bookmarks`,
  `ToolTip.text` and `Accessible.name` "Bookmarks", `ToolTip.delay: 600`, `checked` while the panel
  is open. **Ctrl+B** toggles the panel (add it to the README shortcut table).
- **The address bar star becomes a star:** `non-starred-symbolic` (not bookmarked) and
  `starred-symbolic` (bookmarked), so the ribbon means only "bookmarks". Nothing else in
  `BookmarkButton.qml` changes.

### 2. Level 1: overview (`prototypes/227-bookmarks-panel.qml`)

- Width `gridUnit * 18`; the list part scrolls above `gridUnit * 24`.
- **Search field** on top, with the first focus: placeholder "Search bookmarks", `edit-find`
  icon.
- **Recently Added:** a `Kirigami.ListSectionHeader`, then the 5 bookmarks with the highest `id`
  (most recently added), each a row with the favicon (`SiteIcon`) and the title (the URL when the
  title is empty), elided at the end; the tooltip shows the URL.
- **Folders:** a section header, then **Bookmarks Toolbar** (`bookmark-toolbar`) and **Other
  Bookmarks** (`folder`), each with its number of items (`childCount`, dimmed) and a
  `go-next-symbolic` arrow.
- **Footer**, under a separator: the `Switch` **Show Bookmarks Bar** bound to
  `Settings.showBookmarksBar`, and at the end an icon button `configure` ("Manage Bookmarks",
  tooltip and accessible name) that opens the Bookmarks window and closes the panel.

### 3. Level 2: a folder (`prototypes/227b-bookmarks-panel-folder.qml`)

- Header: a Back button (`go-previous-symbolic`, "Back") and the folder name as a level-4 heading.
- The folder's contents in their order: subfolders (open in place, one level deeper; Back goes up
  one level) and bookmarks.
- Footer: **Open All in Tabs** (`tab-new`) opens every bookmark of this folder (not of its
  subfolders) in new background tabs and closes the panel. Disabled when the folder has no
  bookmarks.
- An empty folder shows the line "Empty folder" in the list.

### 4. Search (`prototypes/227c-bookmarks-panel-search.qml`)

- Typing replaces both sections with the results of `BookmarkManager.search(text, 50)`, from any
  folder, updated as the user types. The first result is highlighted, so Enter opens it.
- No results: the line "No bookmarks match". Clearing the field shows the overview again.

### 5. Empty state (`prototypes/227d-bookmarks-panel-empty.qml`)

- With no bookmarks at all: a `Kirigami.PlaceholderMessage` with icon `bookmarks`, text "No
  Bookmarks" and explanation "Bookmarked pages show up here.", no search field, and the footer.

### 6. Opening and keyboard

- **Click or Enter** on a bookmark opens it in the current tab and closes the panel. **Ctrl+click,
  Ctrl+Enter or middle click** opens it in a background tab and keeps the panel open.
- **Keyboard:** Down moves from the search field into the list; Up/Down move in the list; Enter
  opens; Right or Enter on a folder opens it; Left or Backspace goes back (in the search field,
  Backspace edits the text); Esc closes the panel and focuses the page.
- The panel closes when the current tab changes, as the Extensions panel does.
- It refreshes on `bookmarksChanged`, so a bookmark added with the star shows up at once.

### 7. Privacy

- The panel only reads bookmarks and writes nothing. In a private window it works the same: the
  bookmarks are the normal profile's, opening one opens it in the private tab, as the bookmarks bar
  does today.

### 8. Code layout

- New folder `qml/bookmarks/panel/` (the panel, its list level, its folder level, its rows),
  following the Extensions panel's split. Files and functions within the AGENTS.md limits.
- `BookmarkManager.recentBookmarks(limit)`: a new invokable returning the last `limit` bookmarks
  by `id` (not folders), with the same fields as `search()`. Port it in the Python
  `BookmarkManager` with a pytest test; `check-qml-api.py` must still pass.

## Acceptance criteria

- [ ] A Bookmarks button with the `bookmarks` icon sits before the main menu button and toggles
      the panel; Ctrl+B does too; the README shortcut table lists Ctrl+B.
- [ ] The address bar star uses `non-starred-symbolic` / `starred-symbolic`.
- [ ] Level 1, a folder, search results and the empty state match `prototypes/227*.qml`.
- [ ] Recently Added lists the 5 newest bookmarks (`recentBookmarks(5)`, tested).
- [ ] Opening, background opening, Open All in Tabs and Manage Bookmarks behave as in item 6.
- [ ] The whole panel works with the keyboard only, and every icon-only button has a tooltip and
      an accessible name.
- [ ] The Show Bookmarks Bar switch and Ctrl+Shift+B stay in sync.
- [ ] Nothing is written to disk by the panel, also in a private window.
- [ ] New strings in `qsTr()`; `i18n/*.ts` updated.
- [ ] Breeze and Breeze Dark both look right; long titles elide; 30 bookmarks in a folder scroll.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. With a new profile, open the panel: the empty state shows. Bookmark three pages with the star:
   the star fills, and they appear under Recently Added in that order (newest first).
2. Import the test bookmarks file from `tests/data/` (or create a folder "News" with 30 bookmarks
   in the Bookmarks window). Open Other Bookmarks → News: the list scrolls; Back returns.
3. Type "kde": only matching bookmarks show; Enter opens the first one in the current tab and the
   panel closes.
4. Ctrl+click a bookmark: it opens in a background tab and the panel stays open.
5. Open All in Tabs on a folder: every bookmark opens in a new tab.
6. Turn Show Bookmarks Bar off in the panel, then press Ctrl+Shift+B: the bar and the switch follow
   each other.
7. Keyboard only: Ctrl+B, type, Down, Enter; Ctrl+B, Down to a folder, Right, Left, Esc.
8. Open a private window and use the panel: same bookmarks, nothing new on disk.

## Out of scope

- Changes to the bookmarks bar itself (overflow menu, drag and drop, icon-only mode): rejected for
  now, see Decisions.
- Editing, moving or deleting bookmarks in the panel (the Bookmarks window does that).
- A "most visited" or history section.
- A date column in the bookmarks table.

## Dependencies

- #174 (the Python port is finished, so `qml/` is open again).
- #2 Bookmarks, #183 Extensions panel (pattern).

## Prototype

- Overview: [`prototypes/227-bookmarks-panel.qml`](../../prototypes/227-bookmarks-panel.qml),
  [screenshot](../../prototypes/screenshots/227-bookmarks-panel.png).
- Folder: [`prototypes/227b-bookmarks-panel-folder.qml`](../../prototypes/227b-bookmarks-panel-folder.qml),
  [screenshot](../../prototypes/screenshots/227b-bookmarks-panel-folder.png).
- Search: [`prototypes/227c-bookmarks-panel-search.qml`](../../prototypes/227c-bookmarks-panel-search.qml),
  [screenshot](../../prototypes/screenshots/227c-bookmarks-panel-search.png).
- Empty: [`prototypes/227d-bookmarks-panel-empty.qml`](../../prototypes/227d-bookmarks-panel-empty.qml),
  [screenshot](../../prototypes/screenshots/227d-bookmarks-panel-empty.png).
- Shared mock: `prototypes/common/BookmarksPanelMock.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| Rework the bookmarks bar (overflow menu, drag and drop, folder actions) or a compact icon-only strip? | Not now. The maintainer chose the panel alone among three concepts: a smarter bar, an icon-only strip, and the panel. |
| Same icon for the panel button and the address bar star? | No. In the current Breeze `bookmarks`, `bookmarks-organize` and `bookmark-toolbar` are the same ribbon, so two ribbons side by side would mean two different things. The star becomes `non-starred-symbolic` / `starred-symbolic`, the symbol users know for "bookmark this page", and the ribbon is the panel. |
| "Manage Bookmarks" icon in the footer? | `configure`, not another ribbon, so the footer does not repeat the toolbar button. |
| How is "recent" decided without a date column? | By the highest bookmark `id`, which grows with every new bookmark. No schema change. |
| Does opening a bookmark close the panel? | Yes for a normal open (the user goes to the page); no for a background open (the user may open several). Unlike the Extensions panel, whose actions are repeated on the same page. |
