# Refactor: split SettingsWindow.qml and BookmarksWindow.qml (#137)

> **Issue:** [#137](https://github.com/lukasborges/kondor/issues/137) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first, especially "Code quality". This file is the source of truth for the issue; only the architect edits it.

## Objective

`qml/settings/SettingsWindow.qml` (1 011 lines) and `qml/bookmarks/BookmarksWindow.qml` (962
lines) are the two biggest QML files left after #136. Split each into small components that do one
thing, so that every file follows AGENTS.md → "Code quality". **Both windows behave exactly as
before.**

## Context

- **`SettingsWindow.qml` today** (`origin/main` after #136):

  | Lines | Part |
  | --- | --- |
  | 15–31 | Window properties, `tabModel`, `onClosing` (hide and discard) |
  | 33–133 | `pages` (title, icon, search keywords, component), `currentPage`, `syncingPageList`, `generalTab`, `passwordsTab`, `modified`, `defaultsEnabled`, `visiblePages`, list sync |
  | 135–161 | `pending`: one property per option (15 options) |
  | 163–314 | `readSettings`, `refresh`, `sameList`, `pageAtDefaults`, `restoreDefaults`, `applyChanges`, `acceptAndClose`, `discardChanges`: each one lists the 15 options by hand, and the two `switch` blocks map page indices to options |
  | 316–361 | `ensureVisiblePage`, `showWindow`, `showPage`, `openSitePermissions`, `localPath` |
  | 363–371 | `Find` and `Cancel` shortcuts |
  | 373–440 | Sidebar: search field and `pageList` |
  | 442–503 | Page heading, the General and Passwords `TabBar`s, `pageStack` |
  | 505–541 | Defaults / OK / Apply / Cancel |
  | 543–996 | Page components: General (Startup, New Tabs), Search, Downloads, Spelling, Privacy, Passwords (`PasswordsPage`), Extensions (`ExtensionsPage`) |
  | 998–1011 | Site permissions window on demand, download `FolderDialog` |

- **`BookmarksWindow.qml` today:**

  | Lines | Part |
  | --- | --- |
  | 13–90 | Window properties, selection (`selectedFolderId`, `selectedItemId`), `filter`, 12 drag properties, `folders`, `itemModel`, filter sync, `onClosing`, `showWindow` |
  | 91–141 | `selectedInfo`, `openBookmark`, `hasItemSelection`, `currentItemInfo`, `actionTarget`, `actionIsFolder` |
  | 142–178 | `canMoveInto`, `canDropInto`, `isInSubtree` |
  | 180–348 | Drag and drop: `beginDrag`, `moveDragProxy`, `finishDrag`, `endDrag`, `clearDropTarget`, `moveInto`, `moveToPosition`, `updateFolderDrop`, `updateItemDrop`, `dropIndicatorY` |
  | 350–391 | `moveToTargets`, `moveSelected`, `openCurrentItem` |
  | 393–479 | `ToolBar`: New Folder, Rename, Delete, Move Up, Move Down, Import from HTML…, search field |
  | 480–551 | Folder tree pane and its `DropArea` |
  | 551–744 | Item list pane: the row delegate (icon, title, URL, `DragHandler`, `MouseArea`), its `DropArea`, the drop indicator |
  | 745–811 | Search `Timer`, drag preview (`dragProxy`) |
  | 813–846 | Item context menu with "Move To" |
  | 848–962 | New Folder, Rename and Delete dialogs, import `FileDialog` |

- **Baseline entries** in `scripts/code-quality-baseline.json`:
  - `SettingsWindow.qml`: `comments` 46, `file-length` 1 011, `function-length` for
    `applyChanges`, `pageAtDefaults`, `readSettings`, `refresh`, `restoreDefaults`.
  - `BookmarksWindow.qml`: `comments` 95, `file-length` 962, `function-length` for `beginDrag`,
    `dropIndicatorY`, `isInSubtree`, `moveSelected`, `moveToTargets`, `onAccepted#4`,
    `onClicked#4`, `openBookmark`, `updateFolderDrop`, `updateItemDrop`.
- **Who uses the windows from outside:** `qml/app/WindowDialogs.qml` creates both with
  `tabModel: root.tabs` and calls `settingsWindow.showWindow()`, `settingsWindow.showPage("extensions")`
  and `bookmarksWindow.showWindow()`.
- **Tests that touch them:**
  - `tests/settings/tst_settingswindow.cpp` loads `SettingsWindow.qml`; it calls `showWindow`,
    `discardChanges`, `applyChanges`, `acceptAndClose`, `restoreDefaults`; reads and writes
    `currentPage`; reads `modified`, `defaultsEnabled`; finds `pageList`, `pageHeading`, `pageStack`
    by `objectName`; and finds the pending object as the only child with a `searchEngine` property.
  - `tests/bookmarks/tst_bookmarkswindow.cpp` loads `BookmarksWindow.qml` with `tabModel` and
    `selectedFolderId`; reads `selectedFolderId` and `selectedItemId`; finds
    `dragPreviewTitle` by `objectName`; and evaluates the ids `itemList`, `folderList` and
    `dragProxy` in the window's QML context. Those ids move to other files, so the test must
    find them by `objectName` instead (§4).
- **Shared helper:** `qml/common/LocalPath.qml` (`fromUrl(url)`) already does what
  `SettingsWindow.localPath` does. Reuse it.
- **Translations:** `qsTr()` uses the QML file name as its context. A message that moves to another
  file gets a new context in `i18n/*.ts`.

## Design / behavior

### 1. Settings components (`qml/settings/`)

Each file at most 200 lines; every function and handler at most 10 lines of body, at most 3
parameters, nesting depth 2; no comments. The names are binding; the split of the functions inside a
component is up to you, as long as the limits hold.

| File | Holds |
| --- | --- |
| `SettingsWindow.qml` | The `ApplicationWindow`: the public API of §3, `onClosing`, the two `Shortcut`s, one `SettingsDraft`, one `SettingsPages`, and the composition of the components below. Only one-line forwarding functions. |
| `SettingsDraft.qml` | A `QtObject` with the 15 option properties (same names and types as today's `pending`), `readonly property var optionNames` (the 15 names), and `read()`, `isModified()`, `apply()`, `isAtDefaults(names)`, `restoreDefaults(names)`. Each function loops over names with `Settings[name]` / `Settings.defaultValue(name)`; one helper compares two values, treating arrays (`spellCheckLanguages`) element by element like today's `sameList`. Emits `valuesChanged()` when any option changes, as today. |
| `SettingsPages.qml` | A `QtObject` with `pages`: the seven entries in today's order, each with `id` (`"general"`, `"search"`, `"downloads"`, `"privacy"`, `"passwords"`, `"extensions"`, `"spelling"`), `title`, `icon`, `keywords` (same `qsTr` strings) and `options` (the option names that page's Defaults button resets). The `component` of each entry is set by `SettingsWindow`. `indexOf(pageId)` and `matching(text)` (today's `visiblePages` filter). |
| `SettingsSidebar.qml` | The sidebar `Rectangle`: search field and `pageList` (same `objectName`), `visiblePages`, the list sync (`syncingPageList`, `ensureVisiblePage`, `finishPageListSync`), `focusSearch()` and `clearSearch()`. |
| `SettingsPageHeader.qml` | `pageHeading` (same `objectName`), the General and Passwords `TabBar`s and the separator. |
| `SettingsButtonBar.qml` | Defaults / OK / Apply / Cancel; signals `defaultsClicked`, `okClicked`, `applyClicked`, `cancelClicked`. |
| `GeneralSettingsPage.qml` | The General page `StackLayout` (Startup, New Tabs). |
| `SearchSettingsPage.qml` | The Search page. |
| `DownloadsSettingsPage.qml` | The Downloads page and its `FolderDialog`, using `LocalPath.fromUrl`. |
| `PrivacySettingsPage.qml` | The Privacy page, including the on-demand `SitePermissionsDialog` behind "Manage Site Permissions…". |
| `SpellingSettingsPage.qml` | The Spelling page. |

`PasswordsPage` and `ExtensionsPage` stay as they are; `SettingsWindow` binds them to the draft as
today. Every page component receives the draft as `required property SettingsDraft draft` and
edits only it.

With `options` per page, `pageAtDefaults()` becomes `draft.isAtDefaults(pages[currentPage].options)`
and `restoreDefaults()` becomes `draft.restoreDefaults(pages[currentPage].options)`: no `switch`
on page indices remains.

### 2. Bookmarks components (`qml/bookmarks/`)

Same limits as §1.

| File | Holds |
| --- | --- |
| `BookmarksWindow.qml` | The `ApplicationWindow`: the public API of §3, `folders`, `itemModel`, the filter sync (`filteredModel`), `onClosing`, `showWindow()`, and the composition. |
| `BookmarkSelection.qml` | A `QtObject`: `selectedInfo`, `hasItemSelection`, `currentItemInfo`, `actionTarget`, `actionIsFolder`, `openBookmark(url, background)`, `openCurrentItem()`, `moveSelected(delta)` (it reports the new row through a `rowMoved(row)` signal instead of touching `itemList`). |
| `BookmarkFolderTree.qml` | A `QtObject` over `folders`: `isInSubtree(folderId, ancestorId)`, `canMoveInto(itemId, isFolder, folderId)`, `moveTargets(itemId, parentId, isFolder)` (today's `moveToTargets`), `moveInto(id, isFolder, folderId)`. |
| `BookmarkDragController.qml` | The drag state (`draggedId`, `draggedIsFolder`, the preview properties, `dropFolderId`, `dropPosition`), `canDropInto`, `beginDrag`, `moveDragProxy`, `finishDrag`, `endDrag`, `clearDropTarget`. Group the preview properties in one `draggedRow` object if that keeps `beginDrag` within the limits. |
| `BookmarkDropTargets.qml` | `updateFolderDrop(y)`, `updateItemDrop(y)`, `dropIndicatorY()`, `moveToPosition(id, position)`, with one shared helper that finds the row of a `ListView` under `y` and the ratio inside it (today written twice). |
| `BookmarkDragPreview.qml` | The drag preview `Item`, with `objectName: "dragProxy"`; keeps `dragPreviewTitle`. |
| `BookmarksToolBar.qml` | The `ToolBar` (New Folder, Rename, Delete, Move Up, Move Down, Import from HTML…, search field), the search `Timer` and the import `FileDialog`. |
| `BookmarkFolderPane.qml` | The folder tree `ListView` (`objectName: "folderList"`) and its `DropArea`. |
| `BookmarkItemPane.qml` | The item `ListView` (`objectName: "itemList"`), its `DropArea` and the drop indicator. |
| `BookmarkItemDelegate.qml` | One row of the item list: icon, title, URL, `DragHandler`, `MouseArea`. Today's 32-line `onClicked` becomes small named functions (pick the row, open the context menu, open a folder, open in the background on middle click or Ctrl+click, single-click activation). |
| `BookmarkItemContextMenu.qml` | The context menu with "Move To", fed by `BookmarkFolderTree.moveTargets`. |
| `NewBookmarkFolderDialog.qml` | The New Folder dialog. |
| `RenameBookmarkDialog.qml` | The Rename dialog. |
| `DeleteBookmarkDialog.qml` | The `ConfirmDialog` for deleting a bookmark or folder. |

If a file of §1 or §2 still goes over 200 lines, split it again inside the same feature folder and
say so in the PR. Do not merge two rows of a table into one file.

### 3. Public API (unchanged)

- `SettingsWindow`: `tabModel`, `currentPage` (read/write), `modified`, `defaultsEnabled`,
  `generalTab`, `passwordsTab`, `showWindow()`, `showPage(pageId)`, `applyChanges()`,
  `acceptAndClose()`, `discardChanges()`, `restoreDefaults()`. The draft is a child of the window
  and the only object with a `searchEngine` property, so `pendingOf()` in the test still finds it.
- `BookmarksWindow`: `tabModel`, `selectedFolderId` (read/write, settable at creation),
  `selectedItemId`, `filter`, `showWindow()`.

`WindowDialogs.qml` does not change.

### 4. Wiring and tests

- Components receive what they need through `required property` (for example
  `required property SettingsDraft draft`, `required property BookmarkDragController drag`). They do
  not reach into ids of other files.
- Private tabs: `openBookmark` keeps opening a background tab in a new private profile when the
  current tab is private, exactly as today.
- **Tests first.** Before moving code, add these tests on `main`'s behavior, then keep them green:
  - `tst_settingswindow`: `everyPageDefaultsResetOnlyItsOptions` (data-driven over the seven
    pages: change one option on every page, press Defaults on one page, only that page's options
    return to their defaults and `defaultsEnabled` turns false).
  - `tst_bookmarkswindow`:
    - `moveDownReordersTheSelectedItem` (Move Down on a picked row moves it one place and keeps it
      picked);
    - `returnOnAFolderRowOpensThatFolder`;
    - `searchFiltersTheSelectedFolder` (after the timer, only matching rows remain; switching
      folders clears the filter of the previous model);
    - `moveToMenuSkipsParentAndOwnSubtree`.
- Update `tst_bookmarkswindow` to find `itemList`, `folderList` and `dragProxy` with
  `findChild(objectName)` instead of evaluating ids in the window's context.
- All existing tests keep passing.

### 5. Baseline, translations, README

- Remove every `SettingsWindow.qml` and `BookmarksWindow.qml` entry from
  `scripts/code-quality-baseline.json`. The new files add no entries; the tests you add follow the
  20-line test limit. `python3 scripts/check-code-quality.py` passes.
- Register every new file in `QML_FILES` in `CMakeLists.txt`.
- Run `cmake --build build --target update_translations`. Copy the existing translation of every
  moved message into its new context in **every** `i18n/*.ts` file, so no message is `unfinished`.
  Drop the `vanished`/`obsolete` entries the move leaves behind. No source string changes.
- No README change.

## Acceptance criteria

- [ ] The 11 files of §1 and the 14 files of §2 exist, each at most 200 lines; the two window
      files keep only their public API (§3), their state and the composition.
- [ ] `python3 scripts/check-code-quality.py` passes; the baseline has no entry for
      `SettingsWindow.qml`, `BookmarksWindow.qml` or any new file.
- [ ] No comments in the new or changed QML files; no `switch` on page indices in the settings code.
- [ ] The five new tests of §4 exist; `tst_bookmarkswindow` finds the lists by `objectName`; all
      `ctest` tests pass.
- [ ] No string changes; every `i18n/*.ts` file has no `unfinished` message.
- [ ] Clean build, no new warnings; the offscreen smoke test shows no QML errors.
- [ ] The manual test below behaves as on `main`.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, see AGENTS.md):

1. Open Settings (Ctrl+,). Click every sidebar page and use Up/Down in the list. Type `cook` in the
   search field: only Privacy remains. Ctrl+F focuses the search field.
2. Change the home page and the search engine: Apply turns on; Apply writes them; Cancel after
   another change drops it; reopening shows the saved values. OK applies and closes.
3. On each page change an option and press Defaults: only that page's options reset.
4. Downloads: choose a folder with "…"; the path shows without `file://`. Privacy: "Manage Site
   Permissions…" opens the permissions window. "Manage Extensions…" in the toolbar extensions menu
   opens Settings on the Extensions page.
5. Open Manage Bookmarks (Ctrl+Shift+O). Create, rename and delete a folder and a bookmark; move a
   bookmark up and down; use "Move To" from the context menu; search; import an HTML file.
6. Drag a bookmark between rows, onto a folder row, and onto a folder in the tree; the preview
   follows the pointer and the drop line shows.
7. Click a folder row in the list (the tree selects it). Double-click a bookmark (opens in the current
   tab); middle-click or Ctrl+click one (opens in a background tab).
   From a private tab, middle-click opens a private tab and nothing is written to history.

## Out of scope

- Any change in behavior, wording, icons or layout. If you find a bug, report it as a question on
  the issue; do not fix it here.
- Other files over the limits (C++: #138; the rest of the QML, including `PasswordsPage.qml`,
  `ExtensionsPage.qml`, `WebViewTab.qml`: #139).
- Changing `WindowDialogs.qml`, `BookmarkManager` or `Settings`.

## Dependencies

- #135 (feature folders, checker and baseline) and #136 (split `BrowserWindow.qml`), merged.

## Prototype

None: no visible change. Both windows must look the same as on `main`
(`prototypes/screenshots` for #57 and #2 stay the visual reference).

## Decisions

| Question | Decision |
| --- | --- |
| How do the settings functions lose their 15-line option lists? | `SettingsDraft` loops over option names with `Settings[name]`, and each page lists its own `options`, so Defaults no longer maps page indices with a `switch` (which today must match the page order by hand). |
| How does the bookmarks test reach the lists after the split? | By `objectName` (`itemList`, `folderList`, `dragProxy`), not by ids evaluated in the window's context. |
| A new path helper for the download folder? | No: reuse `qml/common/LocalPath.qml`. |
