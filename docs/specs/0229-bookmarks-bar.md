# Bookmarks bar: overflow menu, drag and drop and folder actions (#229)

> **Issue:** [#229](https://github.com/lukasborges/kondor/issues/229) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Make the optional bookmarks bar useful for the people who turn it on. The default way to reach
bookmarks is the Bookmarks panel (#227); the bar stays **off by default**
(`Settings.showBookmarksBar` defaults to `false`), and this issue does not change that.

Today the bar is a flat row of buttons: items that do not fit are cut off, nothing can be dragged
onto it or moved on it, folders only list their items, and right-click does nothing.

## Context

- **Bar:** `qml/bookmarks/bar/BookmarksBar.qml` (a `ToolBar`, a `Repeater` over
  `BookmarkManager.toolbarModel`, `ToolButton` delegates with `SiteIcon` or the `folder` icon, the
  title elided at `gridUnit * 14`, middle click opens in a background tab). Folders open
  `BookmarkMenu.qml`.
- **`BookmarkManager`:** `addBookmark(url, title, folderId)`, `move(id, newParentId, newPosition)`,
  `remove(id)`, `rename(id, title)`, `setUrl(id, url)`, `folderContents(folderId)`,
  `toolbarFolderId()`.
- **Bookmarks window:** drag and drop in `qml/bookmarks/drag/` (`BookmarkDragController`,
  `BookmarkDropTargets`, `BookmarkDragPreview`), and the dialogs in `qml/bookmarks/dialogs/`
  (`RenameBookmarkDialog`, `DeleteBookmarkDialog`). Reuse them; do not write a second drag system
  or second dialogs.
- **When:** after #174 (`qml/` freeze during the Python port).

## Design / behavior

### 1. Folders

- A folder button shows `folder`, the title and a small `arrow-down` after it
  (`prototypes/229-bookmarks-bar-folder.qml`).
- Its menu lists the folder's items as today, then a separator and:
  - **Open All in Tabs (N)** (`tab-new`): opens the N bookmarks of the folder (not of subfolders)
    in new background tabs. Hidden when N is 0.
  - **Add This Page Here** (`bookmark-new`): adds the current page to this folder with its title.
    Hidden on pages with no web address (New Tab page) and when the page is already in this folder.

### 2. Overflow

- The bar shows as many items as fit. When some do not fit, a `ToolButton` with
  `arrow-right-double` appears at the end ("More Bookmarks", tooltip and accessible name) and
  opens a `Menu` with the left-out items, in order, folders as submenus
  (`prototypes/229b-bookmarks-bar-overflow.qml`).
- The button is hidden when everything fits. Resizing the window moves items between the bar and
  the menu at once.

### 3. Drag and drop

- **Reorder:** drag a bar item left or right; a 2 px `highlightColor` line shows where it will
  land; dropping calls `BookmarkManager.move()`. Dropping on a folder button moves the item into
  that folder (the button highlights while hovered).
- **Add a link:** drag a link from a page (or a URL from another app, `text/uri-list` or a URL in
  `text/plain`) onto the bar: the same line shows the spot; dropping adds a bookmark there with
  the link text as its title (the URL when there is none).
- Esc or dropping outside cancels. A drop never reloads or navigates the page.

### 4. Context menu (`prototypes/229c-bookmarks-bar-context.qml`)

- Right-click on a bookmark: **Open in New Tab** (`tab-new`), **Open in New Window**
  (`window-new`), separator, **Edit…** (`document-edit`, the existing rename/address dialog),
  **Delete** (`edit-delete`, the existing confirmation).
- Right-click on a folder: **Open All in Tabs (N)**, **Rename…**, **Delete**.
- Right-click on empty bar space: **Add This Page** and **Manage Bookmarks…**.

### 5. Keyboard and accessibility

- Every bar item keeps `Accessible.name` (title); folders say "folder" in the accessible
  description. The context menu opens with the Menu key / Shift+F10 on a focused item.

### 6. Privacy

- In a private window the bar may open bookmarks, but **Add This Page Here**, **Add This Page** and
  dropping links are not offered: they would write to disk from a private window. Reordering
  existing bookmarks is still allowed.

## Acceptance criteria

- [ ] Folder buttons show the arrow; their menu has Open All in Tabs (N) and Add This Page Here
      with the rules of item 1 (`229-bookmarks-bar-folder.qml`).
- [ ] With more items than fit, the » button appears with the rest; it is hidden when all fit;
      resizing updates it (`229b-bookmarks-bar-overflow.qml`).
- [ ] Items reorder by dragging, can be dropped into folders, and links dropped from a page become
      bookmarks at the drop position, all with the drop line.
- [ ] The context menus of item 4 work and reuse the existing dialogs (`229c-bookmarks-bar-context.qml`).
- [ ] Private windows offer no action that adds a bookmark.
- [ ] `showBookmarksBar` still defaults to `false`.
- [ ] Breeze and Breeze Dark; right-to-left puts the » button on the left.
- [ ] New strings in `qsTr()`; `i18n/*.ts` updated.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Turn the bar on (Ctrl+Shift+B). Add 12 bookmarks to the Bookmarks Toolbar folder, one of them a
   folder with 4 bookmarks.
2. Narrow the window: the » button appears with the left-out items; widen it: it goes away.
3. Open the folder: Open All in Tabs (4) opens four background tabs; Add This Page Here adds the
   current page.
4. Drag a bar item to another spot, then onto the folder; drag a link from a page onto the bar.
5. Right-click a bookmark: Edit… and Delete use the existing dialogs.
6. In a private window: no Add actions, and dropping a link adds nothing.

## Out of scope

- The Bookmarks panel (#227) and turning the bar on by default.
- Dragging a tab onto the bar (the tab strip's drag stays internal).
- An icon-only mode of the bar.

## Dependencies

- #174 (the `qml/` freeze ends).
- #2 Bookmarks; the drag and drop and dialogs of the Bookmarks window.

## Prototype

- Folder menu: [`prototypes/229-bookmarks-bar-folder.qml`](../../prototypes/229-bookmarks-bar-folder.qml),
  [screenshot](../../prototypes/screenshots/229-bookmarks-bar-folder.png).
- Overflow and drop line: [`prototypes/229b-bookmarks-bar-overflow.qml`](../../prototypes/229b-bookmarks-bar-overflow.qml),
  [screenshot](../../prototypes/screenshots/229b-bookmarks-bar-overflow.png).
- Context menu: [`prototypes/229c-bookmarks-bar-context.qml`](../../prototypes/229c-bookmarks-bar-context.qml),
  [screenshot](../../prototypes/screenshots/229c-bookmarks-bar-context.png).
- Shared mock: `prototypes/common/BookmarksBarMock.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| Panel or bar as the default way to bookmarks? | The panel (#227), chosen by the maintainer. The bar stays off by default and gets these improvements for those who turn it on. |
| Show the » button all the time? | No: only when something is left out, so a short bar has no dead button. |
| An icon-only strip of favorites? | Rejected by the maintainer among the three concepts. |
| Adding from a private window? | Not offered: it would write to disk from a private window (AGENTS.md hard rule). |
