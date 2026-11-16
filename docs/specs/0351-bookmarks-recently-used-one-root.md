# Bookmarks: Recently Used in the panel and one root folder (#351)

> **Issue:** [#351](https://github.com/lukasborges/kondor/issues/351) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

The maintainer's feedback on the Bookmarks panel (#227):

- **Recently Added** is of little use: what a person wants again is what they opened lately.
  It becomes **Recently Used**.
- **Other Bookmarks** goes away. Kondor keeps one root folder, **Bookmarks Toolbar**, and the panel
  shows its contents directly, so the first level already lists the folders and bookmarks instead
  of two rows that must be opened first.

## Context

- Python app only (C++ removed in #174). No port twin.
- Panel: `qml/bookmarks/panel/` (`BookmarksPanelEntries.qml` builds level 1 from
  `BookmarkManager.recentBookmarks(5)` and two root rows).
- Roots: `bookmarks.special` is `'toolbar'` or `'other'` (`databasemigrations.create_root_folders`,
  `storage/bookmarkfolderlist.SPECIAL_ROOTS`, `storage/rootfoldernames.py`).
  `BookmarkManager.otherFolderId()` is the target of the address bar star
  (`bar/BookmarkEditorPopup.qml`), the default selection of the Bookmarks window
  (`BookmarkSelection.qml`), the fallback after a delete (`dialogs/DeleteBookmarkDialog.qml`), the
  fallback of `bookmarkchecks.folder_or_other_bookmarks` and the parent of the "Imported" folder of
  the HTML import (`htmlimport/bookmarkhtmlimporter.py`).
- History: table `history(url, title, visited_at)`, written only from normal tabs.

## Design / behavior

### 1. Recently Used (`prototypes/351-bookmarks-panel-recently-used.qml`)

- The first section of level 1 is **Recently Used**: the 5 bookmarks (not folders) whose URL has
  the most recent visit in history, newest first. A bookmark never visited is not listed; when none
  is, the section and its header are hidden.
- `BookmarkManager.recentlyUsedBookmarks(limit)` replaces `recentBookmarks(limit)` (remove the old
  one and its tests): one SQL query joining `bookmarks.url` to `history.url` (exact string match),
  grouped by bookmark, ordered by `MAX(visited_at) DESC`; same fields as `search()`. A URL
  bookmarked twice shows once.
- Rows look and behave like today's Recently Added rows.
- The list is rebuilt each time the panel opens, besides `bookmarksChanged`, so a page visited a
  moment ago is there.

### 2. One root folder

- **Migration** (next `SCHEMA_VERSION`, in one transaction): the children of the `other` root move
  to the end of the `toolbar` root, keeping their order; then the `other` row is deleted. New
  databases create only the toolbar root.
- Remove `otherFolderId()`, `"other"` from `SPECIAL_ROOTS` and from `rootfoldernames.py`, and the
  "Other Bookmarks" string (drop it from `i18n/*.ts`).
- Every former use of the other root uses the toolbar root (`toolbarFolderId()`): the star adds new
  bookmarks at the **end** of the Bookmarks Toolbar; the Bookmarks window opens on it; a delete
  falls back to it; the HTML import puts its "Imported" folder at its end.
- The Bookmarks window folder tree shows the single root **Bookmarks Toolbar**.

### 3. Panel level 1

- Under Recently Used, a section header **Bookmarks Toolbar**, then the root's contents in the same
  order as the bar: folders with their item count, dimmed, and the `go-next-symbolic` arrow
  (opening in place, as today), and bookmarks with their favicon.
- The "Folders" header and the two root rows are gone. Search, level 2, the footer, keyboard and
  Esc stay as in #227.
- Empty state: unchanged, shown when the root has no items.

### 4. Privacy

- Private tabs write no history, so they never feed Recently Used. In a private window the panel
  shows the normal profile's bookmarks and Recently Used, as it already shows its bookmarks; it
  writes nothing.
- Clearing history empties Recently Used.

## Acceptance criteria

- [ ] Level 1 matches `prototypes/351-bookmarks-panel-recently-used.png`.
- [ ] Recently Used lists up to 5 visited bookmarks, newest visit first; unvisited bookmarks and
      folders never appear; the section hides when empty (pytest for the query).
- [ ] A database with items in Other Bookmarks is migrated: they are at the end of the Bookmarks
      Toolbar in their order, the `other` row is gone (pytest).
- [ ] The star, the Bookmarks window, the delete fallback and the HTML import use the toolbar root;
      no `otherFolderId` and no "Other Bookmarks" string remain.
- [ ] Translations complete (`update_translations`, no `unfinished`).
- [ ] The Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`,
      `check-qml-api.py`, `check-code-quality.py --changed origin/main`).

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Start Kondor on a profile made with `main` before this change, with a bookmark in Other
   Bookmarks. Start the new build: the bookmark is now the last item of the Bookmarks Toolbar.
2. Open the panel: no Recently Used yet (or only visited ones); the Bookmarks Toolbar section lists
   the root's folders and bookmarks; a folder opens in place, Back returns.
3. Visit two bookmarked pages, open the panel: they are under Recently Used, the last one first.
4. Bookmark a new page with the star: it appears at the end of the Bookmarks Toolbar section and
   of the bar.
5. Open the Bookmarks window: only Bookmarks Toolbar in the tree.
6. In a private window, visit a bookmarked page: Recently Used does not change.

## Out of scope

- Renaming the root folder.
- A setting to choose where the star saves.
- Normalizing URLs for the history match (`http` vs `https`, trailing slash).

## Dependencies

- #227 Bookmarks panel, #229 Bookmarks bar improvements (both done).

## Prototype

- [`prototypes/351-bookmarks-panel-recently-used.qml`](../../prototypes/351-bookmarks-panel-recently-used.qml),
  [screenshot](../../prototypes/screenshots/351-bookmarks-panel-recently-used.png)
  (`common/BookmarksPanelMock.qml`, `oneRoot: true`).

## Decisions

| Question | Decision |
| --- | --- |
| Recently Added or Recently Used? | Recently Used, the maintainer's choice: recently added bookmarks were rarely what was wanted. "Used" means the URL's last visit in history, so a bookmark opened by typing its address counts too, and nothing new is stored. A `last_used` column updated only when opened from bookmark UI was rejected: more writes, and it misses typed visits. |
| Keep Other Bookmarks? | No, the maintainer's choice: one root, the Bookmarks Toolbar. Its items move to the end of the toolbar, nothing is lost. New bookmarks from the star go to the end of the toolbar, so with the bar on they show there (the bar's overflow menu, #229, holds the rest). |
| Heading of the root's contents in the panel? | "Bookmarks Toolbar", the root's name everywhere else, rather than "Folders" (the section now lists bookmarks too) or a new "Bookmarks" name the Bookmarks window would not use. |
| Separate issues for the two changes? | One issue: both change level 1 of the panel and `BookmarksPanelEntries.qml`. |
