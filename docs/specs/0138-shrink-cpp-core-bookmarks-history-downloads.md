# Refactor: shrink C++ in the core, bookmarks, history and downloads folders (#138)

> **Issue:** [#138](https://github.com/lukasborges/kondor/issues/138) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first, especially "Code quality". This file is the source of truth for the issue; only the architect edits it.

## Objective

Clear every baseline entry of `src/core/`, `src/bookmarks/`, `src/history/` and `src/downloads/`
in `scripts/code-quality-baseline.json` (73 entries, 3 501 lines), so that these four folders follow
AGENTS.md → "Code quality". Create the shared SQL helper that the later C++ slices reuse.
**Kondor behaves exactly as before.** The database schema, the `Kondor.conf` keys and every
QML-visible API stay the same.

The rest of the C++ code is split into its own issues, one feature-folder slice per PR:
#144 (`browser`), #145 (`app`, `adblock`, `passwords`), #146 (`extensions`). JavaScript files under
`src/` belong to #139.

## Context

- **Baseline entries in scope** (`origin/main` after #137):

  | Folder | Entries |
  | --- | --- |
  | `core` | **files:** `database.cpp` 285, `settings.cpp` 499. **functions:** `Database::migrate` 109 (nesting 3), `seedDefaultBookmarks` 43 (nesting 3), `defaultBookmarks` 34, `Database::Database` 27, `Settings::defaultValue` 49, `availableSpellCheckLanguages` 20, `searchEngineName` 13, `searchUrlTemplate` 13, `Notifier::notify` 20. **comments:** `database.cpp` 20, `database.h` 4, `filehelper.h` 9, `notifier.cpp` 9, `notifier.h` 4, `settings.cpp` 6, `settings.h` 21 |
  | `bookmarks` | **file:** `bookmarkmanager.cpp` 728. **functions:** `importHtml` 139 (nesting 3), `folders` 59, `move` 49, `search` 33, `decodeEntities` 31, `renumber` 29, `insertRow` 23 (5 parameters), `folderContents` 22, `remove` 21, `bookmark` 20, `addBookmark` 19, `addFolder` 16, `rename` 14, `setUrl` 14, `firstFreePosition` 13, `bookmarkIdFor` 11, `BookmarkModel::refresh` 37 (nesting 3), `BookmarkModel::data` 18. **comments:** `bookmarkmanager.cpp` 12, `bookmarkmanager.h` 20, `bookmarkmodel.h` 5 |
  | `history` | **file:** `historymanager.cpp` 353. **functions:** `topSites` 110 (nesting 3), `suggest` 32, `addVisit` 31, `recentToday` 22, `updateTitle` 21, `hostCompletion` 15, `HistoryModel::refresh` 35 (nesting 3), `HistoryModel::data` 20. **comments:** `historymanager.cpp` 12, `historymanager.h` 14, `historymodel.cpp` 1, `historymodel.h` 5 |
  | `downloads` | **file:** `downloadmanager.cpp` 487. **functions:** `DownloadModel::connectDownload` 74, `DownloadModel::data` 51 (nesting 3), `DownloadManager::handleRequest` 45, `activeProgress` 20, `showInFolder` 19, `addDownload` 17, `roleNames` 14, `clearFinished` 11, `hasFinishedDownloads` 11. **comments:** `downloadmanager.cpp` 8, `downloadmanager.h` 10 |

- **Why most functions are long:** `QSqlQuery` boilerplate. Every query takes `Database::instance()`,
  checks `isValid()`, `prepare`s, binds values one by one, `exec`s and loops `next()`. There are
  18 such blocks in `bookmarkmanager.cpp`, 11 in `historymanager.cpp` and 7 in `database.cpp`, and
  more in `faviconstore.cpp` and `extensionmanager.cpp` (#144, #146).
- **Tests today:** `tests/bookmarks/tst_bookmarks.cpp` covers the bookmark tree, moves, search,
  default bookmarks and `importNetscapeHtml`. `tests/history/tst_topsites.cpp` covers `topSites`,
  `hostCompletion`, `recentToday` and `suggest`. `tests/core/tst_settings.cpp` covers defaults.
  **Nothing tests** the database migration, `HistoryManager` writes (`addVisit`, `updateTitle`,
  `removeEntry`, `clearSince`), or any download logic.

## Design / behavior

Limits for every new or changed function: body ≤ 10 lines, ≤ 3 parameters, nesting ≤ 2. Every file
≤ 200 lines. No comments (AGENTS.md → "Names instead of comments"). The **file and class names below
are binding**. How the functions are split inside them is up to you, as long as the limits hold. If a
listed file still goes over 200 lines, split it again in the same folder and say so in the PR. Never
merge two rows into one file.

### 1. Shared SQL helper (`src/core/sql.{h,cpp}`, new shared building block)

A namespace `Sql`, not a class, with free functions over `Database::instance()->handle()`:

| Function | Contract |
| --- | --- |
| `std::optional<QSqlQuery> Sql::run(const QString &statement, const QVariantList &values = {})` | Fails (`std::nullopt`) when the database is not valid or `prepare`/`exec` fails. Otherwise returns the executed query, positioned before the first row. Binds `values` in order. |
| `QList<qint64> Sql::ids(const QString &statement, const QVariantList &values = {})` | The first column of every row as `qint64`; empty on failure. |
| `bool Sql::inTransaction(const std::function<bool()> &work)` | `transaction()`, runs `work`, `commit()`s when it returns true, otherwise `rollback()`s. Returns whether the commit happened. |
| `QVariant Sql::idOrNull(qint64 id)` | `id` when `> 0`, else a null `QVariant` (the `parent_id IS NULL` roots). |

Every query in the four folders goes through these functions; no other `QSqlQuery` boilerplate is
left in them. Add the block to the AGENTS.md → "Shared building blocks" table (done by the architect
with this spec). #144 and #146 will reuse it.

### 2. Core (`src/core/`)

| File | Holds |
| --- | --- |
| `database.{h,cpp}` | `Database` as today (`instance`, `isValid`, `handle`), the opening code split into small steps, and `migrate()`. `migrate()` walks a table of migration steps `{version, function}` in order, inside one `Sql::inTransaction`, and sets `PRAGMA user_version` last, as today. A failed step logs the same `qWarning` and leaves the version unchanged. |
| `databasemigrations.{h,cpp}` | One function per schema version: `createHistoryTable` (v1), `createBookmarksTable` and `createRootFolders` (v2), `createFaviconsTable` (v3), `seedDefaultBookmarks` (v4), `createExtensionStorageTable` (v5). Same SQL text as today. |
| `defaultbookmarks.{h,cpp}` | The default bookmark list as a `static const` array of `{title, url}` values, not a function returning a list. Keep the same titles, URLs and order. |
| `settings.{h,cpp}` | The `Settings` singleton with the same `Q_PROPERTY`s, signals and `Q_INVOKABLE`s. Every setter is a one-line call to one private helper that compares, stores, `sync()`s and emits (≤ 3 parameters: group the storage key and the change signal in an option struct). The constructor reads every option through one helper (`m_readerFontSize` keeps its `qBound(12, …, 32)`). |
| `settingsdefaults.{h,cpp}` | `defaultValue(name)` as a lookup table keyed by option name (`QHash<QString, QVariant>`, or a function per entry), plus the spell-check default (system language when its dictionary exists, else `en-US`). `Settings::defaultValue` forwards to it. |
| `spellcheckdictionaries.{h,cpp}` | `dictionariesPath()`, `dictionaryCodes()`, and the list behind `availableSpellCheckLanguages()`. |
| `searchengines.{h,cpp}` | The engine id → URL template and engine id → display name mappings behind `searchUrlTemplate()` and `searchEngineName()`, as data tables, not `if` chains. |
| `notifier.{h,cpp}` | `notify` split into building the D-Bus arguments and sending them. |
| `filehelper.h` | Comments removed (the names already say it). |

**`Kondor.conf` compatibility (hard rule):** each option keeps its current storage key, including the
keys that differ from the property name (for example `passwordNeverSaveSites`). A user's saved
settings must load unchanged.

### 3. Bookmarks (`src/bookmarks/`)

| File | Holds |
| --- | --- |
| `bookmarkmanager.{h,cpp}` | The `BookmarkManager` QML singleton with the **same public API**: the writes (`addBookmark`, `addFolder`, `rename`, `setUrl`, `move`, `remove`) and `notifyChanged()`. Read and tree calls forward one line each to the classes below. `importHtml(fileUrl)` reads the file, then hands it to the parser and the importer. |
| `bookmarkqueries.{h,cpp}` | Read-only queries: `bookmark(id)`, `folderContents`, `childCount`, `search`, `bookmarkIdFor`, `isBookmarked`, `specialFolderId`. |
| `bookmarkfoldertree.{h,cpp}` | `folders()` (the depth-first flat list: special roots first, then other top-level folders, then children by `position, id`), `isInSubtree(folderId, ancestorId)` (today's recursive CTE in `move`), `renumber`, `firstFreePosition`. |
| `bookmarkrow.h` | `struct BookmarkRow { bool isFolder; QString title; QUrl url; qint64 parentId; int position; }`, which replaces the 5 parameters of `insertRow`. |
| `bookmarkhtmlparser.{h,cpp}` | `BookmarkHtmlParser::parse(const QString &html)` returns a value tree `ImportedBookmark { bool isFolder; QString title; QUrl url; QList<ImportedBookmark> children; }` plus the bookmark count. No raw owning pointers or `qDeleteAll`. It holds the tag scanner (`<!-- -->` skipping, `<H3>`, `<DL>`, `</DL>`, `<A HREF>`), `decodeEntities`, `cleanTitle` and `attributeValue`. It has no database access. |
| `bookmarkhtmlimporter.{h,cpp}` | Inserts a parsed tree under a new "Imported" folder at the end of "Other Bookmarks", inside one `Sql::inTransaction`. Same all-or-nothing rule as today: if any row fails, roll back and return 0. |
| `bookmarkmodel.{h,cpp}` | `refresh` and `data` split into small functions; no comments in the header. |

### 4. History (`src/history/`)

| File | Holds |
| --- | --- |
| `historymanager.{h,cpp}` | The `HistoryManager` QML singleton with the same API. Writes: `addVisit` (merge with the latest visit within `kRecentVisitWindowMs`, else insert), `updateTitle`, `removeEntry`, `clearAll`, `clearSince` (both still clear `FaviconStore`). Queries forward to the classes below. |
| `historysearch.{h,cpp}` | `suggest`, `recentToday`, `hostCompletion`, with the same SQL (including the `LIKE` wildcard escaping). |
| `topsitesranking.{h,cpp}` | `topSites(limit)` in small steps: read visits in the 90-day window → accumulate per host (strip `www.`, http/https only, first non-empty title per URL) → drop hidden hosts → pick each host's best URL (most visits, then latest) → sort (score, then latest visit) → convert the first `limit` to `{url, title, host}` maps. |
| `historymodel.{h,cpp}` | `refresh` and `data` split into small functions; no comments in the header. |

### 5. Downloads (`src/downloads/`)

| File | Holds |
| --- | --- |
| `downloadmanager.{h,cpp}` | `DownloadManager` only: `handleRequest` split into choosing the target (the "Save Page As" exception), connecting the finished/failed notifications, and asking or accepting; plus `pause`, `resume`, `cancel`, `openFile`, `showInFolder` (small steps), `removeFromList`, `clearFinished`, `openDownloadsFolder`. |
| `downloadmodel.{h,cpp}` | `DownloadModel` moved out of `downloadmanager.{h,cpp}`. `connectDownload` makes one `connect` per signal to a named private handler (`onReceivedBytesChanged`, `onStateChanged`, `onPausedChanged`, `onDownloadDestroyed`, …). `data()` dispatches roles to small functions (`progressOf`, `speedTextOf`, `mimeIconNameOf`). `roleNames()` returns a `static const` table. |
| `transferspeed.{h,cpp}` | A value class for today's `speed` / `lastReceivedBytes` / `speedTimer` triple: `restart(receivedBytes)`, `update(receivedBytes, elapsedMs)` (recomputes only after ≥ 1000 ms, as today), `stop()`, `bytesPerSecond()`. It does not depend on WebEngine, so it can be tested. |

### 6. Tests first

Before moving code, add these tests and check that they pass on `main`'s behavior. Then keep them
green. Each test function body is at most 20 lines, and each one is registered in
`tests/CMakeLists.txt`:

- `tests/core/tst_database.cpp`: `upgradesVersionOneFileKeepingHistory`. Before the first
  `Database::instance()`, write a version-1 file (a `history` table with one row, `user_version` 1)
  at the test location. After opening it, the row is still there, `user_version` is 5, the
  `bookmarks`, `favicons` and `extension_storage` tables exist, and both root folders exist.
- `tests/history/tst_historymanager.cpp`:
  - `addVisitIgnoresUnsupportedSchemes`;
  - `revisitWithinWindowUpdatesTitleOnly`;
  - `updateTitleLeavesOlderVisitsUntouched`;
  - `clearSinceKeepsOlderVisits`;
  - `removeEntryDeletesOnlyThatRow`.
- `tests/bookmarks/tst_bookmarkhtmlparser.cpp` (it tests the parser directly, so write it once the
  parser exists; its cases must also hold through `importHtml` on `main`):
  - `parsesNestedFolders`;
  - `skipsCommentsAndUnsupportedSchemes`;
  - `decodesEntitiesInTitles`;
  - `usesUrlWhenTitleIsEmpty`.
- `tests/downloads/tst_transferspeed.cpp`:
  - `reportsBytesPerSecondAfterOneSecond`;
  - `keepsSpeedWithinOneSecond`;
  - `stopResetsSpeed`.
- `tests/core/tst_settings.cpp`: `storageKeysStayTheSame` (data-driven over every option: set a
  non-default value, then the raw `QSettings` key holds it) and `readerFontSizeIsClamped`.

All existing tests keep passing. Tests use the isolated test locations, as the existing ones do.

### 7. Baseline, CMake, translations

- Remove every `src/core/`, `src/bookmarks/`, `src/history/` and `src/downloads/` entry from
  `scripts/code-quality-baseline.json`. New files add no entries, and the baseline only shrinks.
  `python3 scripts/check-code-quality.py` passes.
- Register every new source file in `qt_add_qml_module(... SOURCES ...)` in `CMakeLists.txt`, and in
  every test target that compiles the files it now depends on.
- Strings: `DownloadManager`'s `tr("Download completed")` and `tr("Download failed")` keep their
  context (`DownloadManager`). If you move a `tr()` to another class, its context changes: run
  `update_translations` and copy the existing translations into the new context in every
  `i18n/*.ts`, with no `unfinished` messages and no `vanished`/`obsolete` leftovers. No source
  string changes.
- No README change.

## Acceptance criteria

- [ ] `src/core/sql.{h,cpp}` exists with the four functions of §1, and no `QSqlQuery` boilerplate is
      left outside it in the four folders.
- [ ] Every file named in §2–§5 exists. Every `.cpp`/`.h` in the four folders is ≤ 200 lines, and
      every function in them is ≤ 10 lines, has ≤ 3 parameters and nests ≤ 2 deep.
- [ ] No comments in the four folders (except `//:` translator notes, SPDX lines and "why" comments
      that link a bug report).
- [ ] The baseline has no entry for the four folders; `python3 scripts/check-code-quality.py`
      passes.
- [ ] The 15 test functions of §6 exist (counting `storageKeysStayTheSame` once), and all `ctest`
      tests pass.
- [ ] Database schema, `PRAGMA user_version` (5), `Kondor.conf` keys and the QML-visible API of
      `Settings`, `BookmarkManager`, `HistoryManager`, `DownloadManager`, `Notifier` are unchanged.
- [ ] Clean build with no new warnings; the offscreen smoke test shows no QML errors; no
      `unfinished` messages in `i18n/*.ts`.
- [ ] The manual test below behaves as on `main`.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, see AGENTS.md):

1. First start: the Bookmarks Toolbar shows the default bookmarks. Visit two sites, then restart.
   History (Ctrl+H) lists the visits, and the New Tab page shows them as top sites.
2. Type part of a visited address in the address bar: history suggestions and the inline host
   completion appear.
3. Manage Bookmarks: add, rename, move (Up/Down, "Move To", drag) and delete bookmarks and a folder.
   Import a Firefox or Chrome HTML export: an "Imported" folder appears under "Other Bookmarks"
   with the same tree.
4. Settings: change the home page, search engine and spelling languages, press OK and restart:
   the values are kept. Defaults still restores each page.
5. Download a file (for example a release asset from GitHub). Progress and speed show in the
   downloads popup, and pause/resume works. When it finishes, a "Download completed" notification
   appears, and "Show in Folder" opens the folder. With "Ask where to save each file" on, the
   save dialog opens.
6. In a private window, visit a site and download a file. Nothing appears in History. After
   quitting and restarting Kondor, the private download is no longer in the downloads list.

## Out of scope

- Any change in behavior, wording, schema, settings keys or QML-visible API. If you find a bug,
  report it as a question on the issue; do not fix it here.
- Other C++ folders: `browser` (#144), `app`, `adblock`, `passwords` (#145), `extensions` (#146).
  They may keep their own `QSqlQuery` code until their slice.
- JavaScript under `src/` and every QML file (#139).
- Baseline entries of test files that already exist (only the new tests must follow the 20-line
  limit).

## Dependencies

- #135 (feature folders, checker and baseline), merged.

## Prototype

None: no visible change.

## Decisions

| Question | Decision |
| --- | --- |
| One PR for all ~11 500 lines of C++? | No. #138 covers `core`, `bookmarks`, `history` and `downloads` (3 501 lines, 73 entries). The other folders are #144, #145 and #146, one feature-folder slice per PR, so each review stays readable. JavaScript under `src/` goes with #139. |
| How do the SQL functions get under 10 lines? | One shared `Sql` helper in `core` (§1) does the prepare, bind, exec and transaction work. It is a new shared building block, so the later slices reuse it instead of copying the boilerplate. |
| How is the download speed logic tested without WebEngine? | `TransferSpeed` is a plain value class that takes the elapsed time as a parameter. |
