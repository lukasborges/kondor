# Python port 5/12: Bookmarks (#167)

> **Issue:** [#167](https://github.com/lukasborges/kondor/issues/167) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 8 and 9, "Rules for every phase") and the phase 2 spec [`0164-python-core.md`](0164-python-core.md) first. This file details phase 5 and must follow the umbrella. Only the architect edits it.

## Objective

Port `src/bookmarks/` to Python, and port its tests:

- **Same QML API:** `BookmarkManager` is a QML singleton in `Kondor` 1.0 and `BookmarkModel` an uncreatable type. `check-qml-api.py` pairs both with their C++ twins.
- **Same data:** the Python classes read and write the `bookmarks` table of the same `kondor.sqlite` as the C++ app, with the same statements, and import the same HTML files.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Phase 2 (#164, merged in 69ebf86)** added `kondor/core/`: `Database` (with `reset_instance()` for tests), `sql` (`run`, `ids`, `in_transaction`, `id_or_null`), `Settings`, the default bookmarks migration (`kondor/core/database/defaultbookmarks.py`) and the pytest fixtures `isolated_profile`, `kondor_types` and `kondor_engine`. Phase 3 (#165) is merged. Phase 4 (#166, downloads and history) may run in parallel; it touches none of the files below.
- **`src/bookmarks/`** (1,024 lines):

  | C++ file | What it does |
  | --- | --- |
  | `bookmarkmanager.{h,cpp}` | QML singleton `BookmarkManager`: `toolbarModel` (constant), `folders` and `revision` (notify `bookmarksChanged`); invokables `isBookmarked`, `search(text, limit = 4)`, `bookmarkIdFor`, `addBookmark`, `addFolder`, `rename`, `setUrl`, `move`, `remove`, `importHtml`, `toolbarFolderId`, `otherFolderId`, `modelForFolder`, `folderContents`, `bookmark`, `childCount`, `ctrlPressed`. Every successful change bumps `revision`, refreshes the toolbar model and every folder model, and emits `bookmarksChanged`. |
  | `bookmarkmodel.{h,cpp}` | `QML_UNCREATABLE` list model of one folder: `folderId`, `filter`, `count`; roles `id`, `parentId`, `title`, `url`, `isFolder`; invokables `urlAt`, `idAt`, `isFolderAt`, `rowOf`; slot `refresh` |
  | `bookmarkrow.h` | struct `BookmarkRow{isFolder, title, url, parentId, position}` and `isSupportedBookmarkUrl` (`http`, `https`, `file`, not empty) |
  | `storage/bookmarkqueries.{h,cpp}` | namespace: `bookmark`, `folderContents`, `childCount`, `search`, `bookmarkIdFor`, `isBookmarked`, `specialFolderId`, `likePattern` |
  | `storage/bookmarkfoldertree.{h,cpp}` | namespace: `folders` (depth-first folder list, toolbar then Other Bookmarks then other roots), `isInSubtree`, `renumber`, `firstFreePosition`, `insertRow`, `reparent`, `removeSubtree` |
  | `storage/bookmarkchecks.{h,cpp}` | namespace: `isFolderId`, `folderOrOtherBookmarks`, `isSpecialRow`, `canMove` |
  | `import/bookmarkhtmlparser.{h,cpp}` | `ImportedBookmark{isFolder, title, url, children}`, `ParsedBookmarks{root, bookmarkCount}`, `parse(html)`: a tag scanner for Netscape bookmark files |
  | `import/bookmarkhtmltext.{h,cpp}` | namespace: `decodeEntities`, `cleanTitle`, `attributeValue` |
  | `import/bookmarkhtmlimporter.{h,cpp}` | `import(parsed)`: an `Imported` folder at the end of Other Bookmarks with the parsed tree, in one transaction; returns the number of bookmarks, or 0 when anything fails |

- **Tests to port:**

  | C++ test | Cases |
  | --- | --- |
  | `tests/bookmarks/tst_defaultbookmarks.cpp` + `bookmarksprofileharness.h` | `toolbarHoldsSiteBookmarksThenFolders`, `defaultFoldersHaveTheirSizes`, `defaultFoldersHoldTheirBookmarks`, `otherBookmarksStaysEmpty`, `existingBookmarksAreNotReplaced`, `deletedDefaultsStayDeleted` |
  | `tests/bookmarks/tst_bookmarktree.cpp` + `bookmarktreeharness.h` | `rootFolders`, `addAndFindBookmarks`, `searchBookmarksFindsTitlesAndUrls`, `moveBetweenFolders`, `sortingInsideAFolderMovesTheSecondItemAboveTheFirst`, `modelReportsTheMovedRow`, `folderCannotMoveIntoItself`, `moveIntoAnotherFolderAtEnd`, `refuseMovingFolderIntoChild`, `modelFollowsSelectedFolder`, `removeFolderCascades` |
  | `tests/bookmarks/import/tst_bookmarkhtmlparser.cpp` | `parsesNestedFolders`, `skipsCommentsAndUnsupportedSchemes`, `decodesEntitiesInTitles`, `usesUrlWhenTitleIsEmpty` |
  | `tests/bookmarks/import/tst_bookmarkimport.cpp` + `bookmarkimportharness.h` | `importsEveryBookmark`, `rebuildsTheFolderTreeUnderOtherBookmarks`, `appendsTheImportedFolder`, `decodesEntitiesAboveTheBasicPlane` |

- **Not in this phase:** `tests/bookmarks/tst_bookmarkswindow.cpp` and `tst_bookmarkswindowdrag.cpp` load `BookmarksWindow.qml` with a `TabModel` and `ProfileManager`. Those types are ported in phases 7 and 8, so by the umbrella's UI-test rule these two tests move to phase 8 (#170).

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior, statements and edge cases as the C++, with the Python conventions of umbrella item 3. A C++ helper namespace becomes a module of functions.

### 1. Layout

```
kondor/bookmarks/
  __init__.py
  qmltypes.py
  bookmarkmanager.py
  bookmarkmodel.py
  bookmarkrow.py
  storage/
    __init__.py
    bookmarkqueries.py
    bookmarkfoldertree.py
    bookmarkchecks.py
  htmlimport/
    __init__.py
    bookmarkhtmlparser.py
    bookmarkhtmltext.py
    bookmarkhtmlimporter.py
```

`import` is a Python keyword, so the C++ `import/` folder becomes `htmlimport/`. Further splits for the size limits are allowed if the existing modules keep their C++ base names (for example `bookmarkedits.py` for `rename`…`remove` helpers, or `bookmarkfolderlist.py` for `folders()`).

### 2. `qmltypes.py`

```python
QML_TYPES = (
    QmlType(BookmarkManager, "BookmarkManager", QmlKind.SINGLETON),
    QmlType(BookmarkModel, "BookmarkModel", QmlKind.UNCREATABLE),
)
```

With `register_types()`, as in `kondor/core/qmltypes.py`. Importing it must not create any instance (`check-qml-api.py` imports it without a `QCoreApplication`).

### 3. Names and types

- **Snake case** for everything QML does not see (umbrella item 3): `refresh` stays (it is a public slot in C++), and every module-level function is snake case (`bookmarkqueries.special_folder_id`, `like_pattern`, `bookmarkfoldertree.first_free_position`, `insert_row`, `is_in_subtree`, `remove_subtree`, `bookmarkchecks.folder_or_other_bookmarks`, `can_move`, `bookmarkhtmltext.clean_title`, `attribute_value`, `decode_entities`, `bookmarkhtmlparser.parse`, `bookmarkhtmlimporter.import_bookmarks`, …).
- **`BookmarkRow`, `ImportedBookmark`, `ParsedBookmarks`:** frozen or plain `dataclass`es with the same fields in snake case (`is_folder`, `parent_id`, `bookmark_count`; `children` is a `list` with `field(default_factory=list)`). `is_supported_bookmark_url(url: QUrl) -> bool` lives in `bookmarkrow.py`.
- **64-bit ids:** every id argument and id result QML sees is `qint64` in C++ (`bookmarkIdFor`, `addBookmark`, `addFolder`, `rename`, `setUrl`, `move`, `remove`, `toolbarFolderId`, `otherFolderId`, `modelForFolder`, `folderContents`, `bookmark`, `childCount`, `BookmarkModel.idAt`, `rowOf`, and the `folderId` property). Declare them with `"qint64"` in `Slot(...)`, `result=` and `Property(...)`, because `int` is 32-bit in PySide6. `move`'s position and the row arguments stay `int`.
- **`search`:** QML calls it with one or two arguments (the C++ default is `limit = 4`). The Python slot accepts both counts, so `check-qml-api.py` sees 1 and 2.
- **Return types:** `folders`, `search` and `folderContents` return lists of dicts (`QVariantList` of maps), `bookmark` a dict (`QVariantMap`, empty when the row does not exist), `modelForFolder` and `toolbarModel` a `BookmarkModel`. The keys are the C++ ones (`id`, `parentId`, `title`, `url`, `isFolder`, `position`, `special`, `depth`, `type`).
- **NULL columns** read as the C++ conversion would: `""` for text (`url` of a folder, `special` of a normal row), `0` for integers (`parent_id` of a root row), `False` for booleans. Write one small reader per row shape, as in `bookmarkqueries.cpp`; do not let `None` reach QML.
- **`BookmarkModel.Roles`** keeps its C++ names and values (`IdRole = Qt.UserRole + 1`, …).
- **Translations:** `QCoreApplication.translate("BookmarkManager", "New Folder")`, so the `.ts` context stays the same (umbrella item 8). The `Imported` folder title is not translated in C++ and stays a plain string.
- **Warnings:** `insert_row` reports a failed insert with `qWarning(f"Bookmarks: failed to insert {title}")`, as `kondor/core/database/database.py` does.

### 4. Storage

- **Statements:** every SQL statement of `bookmarkmanager.cpp`, `bookmarkmodel.cpp`, `bookmarkqueries.cpp` and `bookmarkfoldertree.cpp`, character for character, through `kondor.core.database.sql`. That includes the `ESCAPE '\'` clauses (a Python string needs `"\\"` for them) and the two `WITH RECURSIVE` statements.
- **`like_pattern`:** escape `\` first, then `%` and `_`, and wrap in `%…%`. Phase 4 adds the same function as `historysearch.like_pattern`; each phase keeps its own module function, as the C++ does (do not import across features before both are merged).
- **Parent ids:** a parent id `<= 0` means a root row: `parent_id IS NULL` in the sibling statements, `sql.id_or_null` when writing. `move` and `addFolder` clamp a negative parent to 0 (`qMax`).
- **`renumber(parent_id, moved_id, moved_position)`:** sibling ids in `position, id` order; when `moved_id > 0`, remove it and insert it at `moved_position`, clamped to `0…len`, or at the end when `moved_position < 0`; then write positions `0…n-1`.
- **`insert_row`:** `url` is NULL for a folder or an invalid URL, else `QUrl.toString()`; `created_at` is the current time in ms; returns `lastInsertId()` as `int`, or `-1` on failure.
- **`folders()`:** toolbar, then Other Bookmarks (each only when it exists), then the other root folders (`parent_id IS NULL AND special IS NULL`, `position, id`) not already listed; each root depth-first through its child folders, with `depth` from 0.

### 5. `BookmarkManager`

- **Instance:** `instance()` creates it once; the constructor creates `toolbarModel` (parented to the manager) and sets its `folderId` to `toolbarFolderId()`. `modelForFolder` returns `toolbarModel` for the toolbar id, else one cached `BookmarkModel` per folder id (parented to the manager, `folderId` set on creation).
- **Changes** (`addBookmark`, `addFolder`, `rename`, `setUrl`, `move`, `remove`, `importHtml`) keep every guard of the C++:
  - `addBookmark`: unsupported URL → `-1`; the folder falls back to Other Bookmarks when the id is not a folder; a blank title becomes `url.toString()`; the row goes after its last sibling.
  - `addFolder`: a positive parent that is not a folder → `-1`; a blank title becomes `New Folder` (translated).
  - `rename` ignores a blank title; `setUrl` ignores unsupported URLs and folders (`AND is_folder = 0`); both notify only when a row changed (`numRowsAffected() > 0`).
  - `move`: refused for a missing or special row, a parent that is not a folder, or a folder into its own subtree; renumbers the new parent with the moved row placed, and the old parent when it differs.
  - `remove`: refused for a missing or special row; deletes the subtree and renumbers the old parent.
  - `importHtml(fileUrl)`: reads the local file as UTF-8 (an unreadable file reads as `""`, which imports nothing), parses, imports, and notifies when the count is above 0. Decode with `errors="replace"`, as `QString::fromUtf8` replaces invalid bytes.
- **Notify:** bump `revision`, set `toolbarModel.folderId` to `toolbarFolderId()` again, refresh it and every cached folder model, emit `bookmarksChanged`.
- **`ctrlPressed`:** `bool(QGuiApplication.queryKeyboardModifiers() & Qt.KeyboardModifier.ControlModifier)`.

### 6. `BookmarkModel`

- `folderId` (`qint64`, default `-1`) and `filter` (`str`) emit their change signal and `refresh()` only when the value changes. A `folderId < 0` gives no rows.
- `refresh()` loads the rows first, then `beginResetModel()` / `endResetModel()`, then emits `countChanged`.
- A trimmed, non-empty filter adds the `title LIKE ? … OR url LIKE ? …` clause with `like_pattern`.
- Roles: `id` and `parentId` (`int`), `title`, `url` (`QUrl(text).toString()`), `isFolder` (`bool`). `urlAt`, `idAt`, `isFolderAt` return `""`, `-1`, `False` outside the rows; `rowOf` returns `-1` for an unknown id.

### 7. HTML import

- **Parser:** the same scanner as `bookmarkhtmlparser.cpp`: skip `<!-- … -->`; read tags; `<h3>` starts a folder whose title is the text up to `</h3` (case-insensitive) and becomes the pending folder; `<dl>` enters the pending folder (or stays in the current one), `</dl>` leaves it, never above the root; `<a>` adds a link when its `href` (trimmed) is a supported URL, with the text up to `</a` as title, or the URL when the title is empty. Stop at an unterminated tag. Folders keep their position in the tree through index paths, as in C++, or through direct references to the `ImportedBookmark` objects; the result must be the same.
- **Case-insensitive search:** use `re.compile(r"</h3", re.IGNORECASE).search(html, pos)` (and `</a`), not `html.lower().find(...)`, because lower-casing can change the string's length and break the indices.
- **Text:**
  - `clean_title`: drop `<[^>]*>`, `decode_entities`, then simplify white space (`" ".join(text.split())`, like `QString::simplified`).
  - `decode_entities`: the seven named entities of `bookmarkhtmltext.cpp`, replaced in that order, then `&#(x?)([0-9a-fA-F]+);`: base 16 with `x`, else 10; a value that does not parse in that base (`&#12a;`), is 0, is above `0x10FFFF` or is a surrogate stays as written; else `chr(value)`.
  - `attribute_value(tag, name)`: `\bname\s*=\s*(?:"([^"]*)"|'([^']*)')`, case-insensitive; the double-quoted group when it is not empty, else the single-quoted one; `""` when nothing matches.
- **Importer:** `import_bookmarks(parsed) -> int`: 0 when `bookmark_count == 0`; else, inside `sql.in_transaction`, insert the `Imported` folder at the end of Other Bookmarks and the tree under it (positions counted per parent from 0); commit only when every bookmark was inserted. Returns the number inserted, or 0 when the transaction was rolled back.

### 8. Privacy

`BookmarkManager` has no private-tab check in C++: the QML callers decide. Keep that, and add no new callers. Nothing in this phase writes anything but the `bookmarks` table.

### 9. Tests

Each C++ case becomes a test with the same intent (umbrella item 9). Test functions have at most 20 lines.

**Database state:** the C++ cases share one database and run in order. In pytest, every bookmark test that touches the database uses a `fresh_bookmarks` fixture: `Database.reset_instance()`, delete `kondor.sqlite` in the isolated profile, open it again (so the default bookmarks are inserted), and `Database.reset_instance()` after the test, as `pytests/core/test_database.py`'s `database_file` fixture does. A fresh file gets the same ids, so the `BookmarkManager` singleton and its toolbar model stay valid. Tests do not depend on each other's rows.

```
pytests/bookmarks/
  __init__.py
  conftest.py
  bookmarkrows.py
  test_defaultbookmarks.py
  test_bookmarktree.py
  test_bookmarkmanager.py
  test_bookmarkmodel.py
  htmlimport/
    __init__.py
    sampleexport.py
    test_bookmarkhtmlparser.py
    test_bookmarkimport.py
```

- **`conftest.py`:** the `fresh_bookmarks` fixture (it depends on `kondor_types`, so the singletons exist).
- **`bookmarkrows.py`** (twin of `bookmarktreeharness.h` and the SQL helpers of `bookmarksprofileharness.h`): `add_page`, `add_folder_in_other`, `parent_of`, `add_folder_with_page`, `reordered_folder`, `add_search_fixture`, `count_rows`, `count_titled`, `write_version_two_file(path)`, `delete_qt_docs_default(path)`. Helpers that open their own connection use a separate connection name and remove it afterwards.
- **`test_defaultbookmarks.py`:** the six C++ cases. `existingBookmarksAreNotReplaced` and `deletedDefaultsStayDeleted` run the migration in-process with `Database.reset_instance()` instead of a child process: write the version-2 file (or delete `Qt Docs`) with a separate connection, then open `Database.instance()` again and check `PRAGMA user_version` is 5 and the row counts are those of the C++ test.
- **`test_bookmarktree.py`:** the eleven C++ cases, with the C++ assertions (`searchBookmarksFindsTitlesAndUrls` keeps its three checks: by title, by URL, folders skipped and `limit` honored).
- **`sampleexport.py`:** the `sampleBookmarksHtml` text of `bookmarkimportharness.h`, `write_sample_export(path)`, and `imported_folder_id`, `imported_toolbar_id`, `nested_folder_id`.
- **`test_bookmarkhtmlparser.py`:** the four C++ cases, with no database.
- **`test_bookmarkimport.py`:** the four C++ cases. A module fixture imports the sample once into a fresh database (through `tmp_path` and `QUrl.fromLocalFile`) and records `childCount(otherFolderId())` before it.
- **`test_bookmarkmanager.py`** (new):
  - `test_add_bookmark_refuses_unsupported_schemes`: `place:type=6` and `javascript:alert(1)` return `-1`.
  - `test_add_bookmark_falls_back_to_other_bookmarks`: a bookmark id or `0` as folder lands in Other Bookmarks.
  - `test_add_folder_names_a_blank_title_new_folder`.
  - `test_rename_ignores_a_blank_title` and `test_set_url_ignores_folders`.
  - `test_remove_refuses_special_folders`: removing Other Bookmarks leaves it in place.
  - `test_changes_bump_revision_and_emit_once`: one `addBookmark` emits `bookmarksChanged` once and raises `revision` by one; a refused change emits nothing (`qtbot`).
  - `test_import_of_a_missing_file_imports_nothing`: `importHtml` of a missing path returns 0 and adds no `Imported` folder.
  - `test_ids_from_qml_are_64_bit`: from QML (`kondor_engine`), `BookmarkManager.childCount(4294967296 + BookmarkManager.toolbarFolderId())` is 0 (a 32-bit slot fails or wraps it to the toolbar id, which has 6 children); and `BookmarkManager.search("kde")` works with one argument.
- **`test_bookmarkmodel.py`** (new):
  - `test_filter_matches_title_or_url_and_escapes_wildcards`: in a folder with `100% Linux` and `Other`, filter `%` matches only the first.
  - `test_accessors_are_empty_outside_the_rows` (`urlAt`, `idAt`, `isFolderAt`, `rowOf`).
  - `test_negative_folder_id_has_no_rows`.
  - `test_change_refreshes_folder_models`: a model from `modelForFolder` sees a bookmark added through the manager, and `countChanged` is emitted.
- **`pytests/core/test_singletons.py`** needs no change: it finds the new singleton through `kondor_types`.

### 10. API check result

After this phase, `python3 scripts/check-qml-api.py` reports **two more** classes checked and two fewer not ported than on the PR's base, and exits 0.

## Acceptance criteria

- [ ] `kondor/bookmarks/` has the modules of item 1, and its `qmltypes.py` registers the two types of item 2.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports two more classes checked than on the base, with no problems.
- [ ] Every C++ case of the four test files in "Context" has its pytest twin, and the new tests of item 9 exist and pass: `QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests`.
- [ ] Ids are 64-bit from QML; `search` accepts one or two arguments.
- [ ] The SQL statements are those of the C++ files, character for character.
- [ ] The `python` and `build` jobs are green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt` or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md):

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests && python3 scripts/check-qml-api.py`: all pass, and the last reports two more classes than `main`.
2. **Profile written by C++, read by Python:** build `main` with CMake and start `./build/kondor` on the temporary profile. Bookmark `https://kde.org/applications/` into a new folder `Test` under Other Bookmarks, move `Planet KDE` to the end of the toolbar, and import an HTML export (Firefox or the sample of `bookmarkimportharness.h`) from the Bookmarks window. Quit. With the same `XDG_*` variables, a short Python snippet run from the PR checkout (`QGuiApplication` with organization `KDE` and application `Kondor`) must show:
   - `BookmarkManager.instance().folders` lists the same folders, in the same order and depths, as the C++ Bookmarks window's tree;
   - `folderContents(toolbarFolderId())` ends with `Planet KDE`;
   - `search("kde")` matches what the C++ address bar suggests for bookmarks.
3. **Profile written by Python, read by C++:** with the snippet, `addFolder("From Python", otherFolderId())`, add a bookmark in it, and `importHtml` the sample file. Start `./build/kondor` on the same profile: the Bookmarks window shows `From Python` with its bookmark and a second `Imported` folder, and the star in the address bar is filled on the bookmarked page.
4. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- `tst_bookmarkswindow` and `tst_bookmarkswindowdrag`: they move to phase 8 (#170), which ports `TabModel`.
- Calling `register_types()` from an app entry point (phase 11).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests or the workflows.
- Changes to `kondor/core/` (including `defaultbookmarks.py` and the migrations), `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker, unless a phase-5 file shows a bug in them. In that case, ask first (`question`).
- New behavior: no private-tab checks, no export, no import formats other than the Netscape HTML file, no deduplication on import.
- Translating Python strings, or running `pyside6-lupdate` (phase 12).

## Dependencies

#164 (core, merged). Umbrella #162. Runs in parallel with #166, which touches other folders.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| `import` is a Python keyword: what is the folder called? | `kondor/bookmarks/htmlimport/` (and `pytests/bookmarks/htmlimport/`). The modules keep their C++ base names. |
| Where do the Bookmarks window tests go? | Phase 8 (#170): they need `TabModel` and `ProfileManager` (umbrella rule for UI tests). |
| The C++ tests share one database in order; how do the pytest twins get a known tree? | A `fresh_bookmarks` fixture recreates `kondor.sqlite` with the default bookmarks for each test, as `test_database.py` does. A fresh file gets the same ids, so the singleton stays valid. |
| The C++ migration tests start a child process; the Python twins? | In-process, with `Database.reset_instance()`: the Python `Database` was built for that in phase 2. |
| Share `like_pattern` with history (phase 4)? | No: each feature keeps its own, as the C++ does. A shared helper would be a redesign and couples two phases running in parallel. |
