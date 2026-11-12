# Refactor: shrink the test files (#151)

> **Issue:** [#151](https://github.com/lukasborges/kondor/issues/151) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first, especially "Code quality". This file is the source of truth for the issue; only the architect edits it.

## Objective

Clear the last 82 entries of `scripts/code-quality-baseline.json`, all of them in `tests/**`, so that
the baseline is empty (`{}`) and every file of the repository follows AGENTS.md → "Code quality".
**Every test keeps checking exactly what it checks today**: no assertion, data row or test case is
dropped or weakened, and no production code changes.

## Context

- **Baseline after #139** (`origin/main` at `6113734`): 15 `comments`, 10 `file-length`,
  53 `function-length`, 2 `nesting`, 2 `parameters` entries, all in `tests/**`.
- **Limits for tests** (`scripts/codequality/rules.py`): function body ≤ **20** lines (this includes
  `main`, `initTestCase`, `init`, `*_data` and helpers in `tests/`), ≤ 3 parameters, nesting ≤ 2,
  file ≤ 200 lines (also `.h` harness headers), no comments.
- **Large files:**

  | File | Lines | Long functions (body lines) | Comments |
  | --- | --- | --- | --- |
  | `extensions/tst_extensions.cpp` | 1 355 | `contentScriptRunsInPages` 143, `catalogUpdates` 62, `bridgeTabCommands` 48, `toolbarMenuEntries` 48, `installFromFile` 40, `bridgeStorageReadOnlyInPrivate` 36, `bridgeEnforcesPermissions` 32, `configureDialogWritesValues` 32, `installDialogShowsPendingInstall` 30, `replaceKeepsState` 29, `writeCatalog` 27 (7 parameters), `invalidFileShowsError` 25, `catalogLoadsAndInstalls` 24, `permissionLines`, `scriptMetadata`, `settingsAreSanitized` 21; `PageServer::start` nesting 3 | 82 |
  | `browser/tst_tabstrip.cpp` | 565 | `draggedTabFollowsThePointerAndReordersLive` 40, `init` 29, `scrolledOutTabsAreClipped` 29, `draggingToTheEdgeAutoScrolls` 27, `closingWithTheMouseKeepsTheWidth` 25 | 22 |
  | `bookmarks/tst_bookmarks.cpp` | 512 | `importNetscapeHtml` 73, `defaultBookmarksOnFirstRun` 46, `existingBookmarksAreNotReplaced` 46, `moveBetweenFolders` 34, `deletedDefaultsStayDeleted` 29, `moveIntoAnotherFolderAtEnd` 25, `searchBookmarksFindsTitlesAndUrls` 25, `main` 22, `addAndFindBookmarks` 21 | 30 |
  | `settings/tst_settingswindow.cpp` | 410 | `searchFiltersPages` 24, `clickingSidebarSwitchesPages` 23, `pendingChangesAreDiscarded` 22 | — |
  | `browser/tst_tabmodel.cpp` | 385 | — | 5 |
  | `bookmarks/tst_bookmarkswindow.cpp` | 325 | `dragBetweenRows` 36, `clicksStillSelect` 33, `dragIntoTreeFolder` 32, `dragOntoFolderRow` 27 | — |
  | `app/tst_mainmenu.cpp` | 306 | `initTestCase` 24, `rowsAndOrder` 23 | 8 |
  | `browser/tst_addresssuggestions.cpp` | 287 | `addsBookmarksHistoryAndNetworkSuggestions` 65, `visitAndSearchRows` 36, `initTestCase` 22 | 9 |
  | `site/tst_sitepermissions.cpp` | 251 | `dialogListsAndRevokesDecisions` 35, `requestBarShowsAndAnswersThePendingPermission` 33, `answersQueuedPermissionsInOrder` 32, `navigatingWithinSameOriginKeepsPendingPermissions` 23 | 8 |
  | `history/tst_topsites.cpp` | 217 | `groupsByHostAndSortsByVisits` 21 | 4 |

- **Other entries:** `extensions/tst_extensionloader.cpp` (`contentScriptRuns` 53, nesting 3;
  5 comments), `browser/tst_addressresolver.cpp` (`resolvesAddress_data` 45),
  `core/tst_settings.cpp` (`defaultValue_data` 36, `freshSettingsUseDefaults` 25; 2 comments),
  `browser/tst_sessionmanager.cpp` (`keepsTheSessionWhenOnlyPrivateWindowsRemain` 22; 4 comments),
  `app/tst_singleinstance.cpp` (`forwardsMessageToRunningInstance` 23; 2 comments),
  `adblock/tst_filterengine.cpp` (`blocked` 4 parameters), and comments only in
  `browser/tst_faviconstore.cpp` (6), `browser/tst_zoommanager.cpp` (2), `passwords/tst_passwordstore.cpp` (2).
- **Existing harness headers** to copy the style from: `tests/browser/addressbarharness.h`,
  `tests/bookmarks/bookmarkswindowharness.h`, `tests/browser/pagecontextmenucases.h`.
- **Duplicated helpers today:** `findByClassName` (`tst_settingswindow`, `tst_sitepermissions`),
  `registerSingleton` (`tst_settingswindow`, `addressbarharness.h`), and the "temporary
  `XDG_*` home" block at the start of most `main` functions.

## Design / behavior

### 1. How a file is split

- **One executable per test target, as today.** A split file becomes several `.cpp` files of the same
  `qt_add_executable` in `tests/CMakeLists.txt` (each test executable recompiles its production
  sources, so new executables would make the build slower and heavier; see "Decisions"). `ctest`
  keeps the same test names.
- Each new `.cpp` holds **one test class** (`QObject` with `Q_OBJECT`, ending with
  `#include "<file>.moc"`) and one free function `int run<Class>(int argc, char *argv[])` that runs
  it with `QTest::qExec`. The file that keeps the original name holds `main`: it prepares the
  application exactly as today (WebEngine initialization, isolated home, style, organization and
  application names, any child mode such as `--migrate`) and returns non-zero if any `run…` does.
  The `run…` functions are declared in the harness header of the folder.
- Shared fixtures, helper functions and constants go into **harness headers** in the same folder
  (`<name>harness.h`, `inline` functions or small classes). A header is ≤ 200 lines; split it by
  responsibility if not.
- **One behavior per test.** A long test that checks several behaviors (each "step" comment of today
  marks one) becomes several test functions named after the behavior, each preparing its own state
  through the harness. A long test that checks one behavior gets named helpers (arrange, act,
  verify steps) in the harness. The comment's information goes into the new names.
- A long `*_data` table is split into named row groups (`addSchemeRows()`, `addHostRows()`, …) called
  in today's order, each ≤ 20 lines; the rows and their names do not change.
- `QTest::qWait` delays and `…_WITH_TIMEOUT` values stay as they are.

The **file names below are binding**; how the tests are distributed inside a row's files is up to you
as long as every file stays ≤ 200 lines. If a file still goes over, split it again in the same folder
and say so in the PR.

### 2. Files

| Today | Becomes |
| --- | --- |
| `extensions/tst_extensions.cpp` | `tst_extensions.cpp` (`main`); `extensionsharness.h` (`dataDir`, `writeFile`, `zipDirectory`, `sha256Of`, `samplePackage`, `installSample`, removing every installed extension, the QML type registration); `pageserver.h` (`PageServer`, `start` split into accepting a connection and answering one request); `catalogharness.h` (`writeCatalog`, `refreshCatalog`); one file per today's section: `tst_extensionpackage.cpp` (package validation), `tst_extensionscripts.cpp` (content scripts), `tst_extensioninstall.cpp` (install, update, remove), `tst_extensionbridge.cpp` (storage and bridge), `tst_extensioncatalog.cpp` (updates and catalog), `tst_extensionsui.cpp` (toolbar menu, dialogs, Extensions page), `tst_extensionpages.cpp` (the real page). |
| | `contentScriptRunsInPages` becomes one test per behavior, with the page view and its helpers (`attribute`, `evaluate`, `waitLoaded`) in `extensionpageharness.h`: `runsInNormalPagesWithSettingsAndStorage`, `settingChangeReachesTheOpenPage`, `toolbarActionReachesTheExtension`, `excludedPathDoesNotRunIt`, `privatePagesNeedPermissionAndGetReadOnlyStorage`, `disabledSiteDoesNotRunIt`. |
| | `writeCatalog` takes one `CatalogFixture` struct (`root`, `version`, `permissions`, `checksum` and `size` overrides, `std::optional<QStringList> catalogPermissions` instead of the list + flag pair), so it has ≤ 3 parameters. |
| `browser/tst_tabstrip.cpp` | `tst_tabstrip.cpp` (`main`); `tabstripharness.h` (today's `initTestCase`, `init` split into named steps, `cleanup`, `addTabs`, `resizeStrip`, drag helpers); `tst_tabstripwidths.cpp` (widths, scroll buttons, current tab visible, closing with the mouse, pinned width, clipping); `tst_tabdrag.cpp` (following the pointer, clamping, scrolled strip, auto-scroll, pinned section); `tst_tabdragrelease.cpp` (short move is a click, closing after a click, release animation, current tab after release, closing the dragged tab). |
| `bookmarks/tst_bookmarks.cpp` | `tst_bookmarks.cpp` (`main`; the `--migrate` child mode as a named function); `bookmarksprofileharness.h` (`profileDatabasePath`, open/close, `migrateProfile`, `countRows`); `tst_defaultbookmarks.cpp` (first run, existing bookmarks kept, deleted defaults stay deleted); `tst_bookmarktree.cpp` (root folders, add/find, search, moves, refused move, model, cascading remove); `tst_bookmarkimport.cpp` (`importNetscapeHtml` split into: imports every bookmark, rebuilds the folder tree under "Other Bookmarks", appends the "Imported" folder, decodes entities above U+FFFF). |
| `settings/tst_settingswindow.cpp` | `tst_settingswindow.cpp` (`main`); `settingswindowharness.h` (`pendingOf`, `createWindow`, `visiblePageCount`, `sidebarEntry`, `typeText`, `searchFor`, the `verify…` helpers, `changedOptionPerPage`); `tst_settingsapply.cpp` (discard, Apply, OK, page defaults, wallet state); `tst_settingsnavigation.cpp` (sidebar clicks, arrow keys, search). |
| `browser/tst_tabmodel.cpp` | `tst_tabmodel.cpp` (`main`, add/close/current index, private tabs and windows, pinning and moving); `tst_recentlyclosedtabs.cpp` (reopening and the recently closed list); `tst_tabnewtabpage.cpp` (the New Tab page tests). |
| `bookmarks/tst_bookmarkswindow.cpp` | `tst_bookmarkswindow.cpp` (`main`, dialogs, keyboard, search, Move To menu); `tst_bookmarkswindowdrag.cpp` (the four drag tests and `clicksStillSelect`); new drag helpers go into `bookmarkswindowharness.h`. |
| `app/tst_mainmenu.cpp` | `tst_mainmenu.cpp` (the tests); `mainmenuharness.h` (`collectWarnings`, `EmptyImageProvider`, the engine and window setup of `initTestCase`/`init`, `rowsOf`, `sequencesIn`). `rowsAndOrder` compares against named expected-row lists. |
| `browser/tst_addresssuggestions.cpp` | `tst_addresssuggestions.cpp` (the tests); `addresssuggestionsharness.h` (setup of `initTestCase`, `createPopup`, `addHistory`, the bookmark and network-suggestion fixtures). `addsBookmarksHistoryAndNetworkSuggestions` becomes `addsBookmarkRows`, `addsHistoryRows`, `addsNetworkSuggestionRows` and `keepsTheRowOrder`; `visitAndSearchRows` is split by behavior the same way. |
| `site/tst_sitepermissions.cpp` | `tst_sitepermissions.cpp` (`main`, profile and queue tests); `sitepermissionsharness.h` (setup, a helper that queues permission requests, the bar and dialog loaders); `tst_sitepermissionsui.cpp` (request bar and dialog tests). |
| `history/tst_topsites.cpp` | `tst_topsites.cpp` (`main`, top sites: grouping, `www`, hidden hosts, 90 days); `topsitesharness.h` (`init`, `addVisit`); `tst_historysuggestions.cpp` (`suggest…`, host completion, recent today). |

### 3. Shared test helpers

- `tests/common/qmltesthelpers.h`: `findByClassName` and `registerSingleton<T>`, used by
  `settingswindowharness.h`, `sitepermissionsharness.h` and `addressbarharness.h` (remove their
  copies).
- `tests/common/isolatedhome.h`: `bool useIsolatedHome(const QTemporaryDir &home)` setting
  `XDG_DATA_HOME`, `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` to the directory, as today. Every `main`
  this issue touches uses it; the others may stay as they are.
- Add `${CMAKE_CURRENT_SOURCE_DIR}` to the include directories of the targets that include
  `common/…`.

### 4. The other entries

- `tst_extensionloader.cpp::contentScriptRuns`: the view QML as a named constant, the local server
  and the wait as named helpers; the `#if KONDOR_HAVE_EXTENSIONS` branch stays (move it around a
  helper call if that lowers the nesting).
- `tst_addressresolver.cpp::resolvesAddress_data`, `tst_settings.cpp::defaultValue_data`: row groups
  (§1). `freshSettingsUseDefaults`, `keepsTheSessionWhenOnlyPrivateWindowsRemain`,
  `forwardsMessageToRunningInstance`: named helpers.
- `tst_filterengine.cpp::blocked(engine, request)`: a small `Request { url, page, kind = Script }`
  struct; every call keeps its values.
- Remove every comment in the files above (translator notes do not apply; a "why" comment survives
  only if it links a bug report).

### 5. Baseline and README

- `scripts/code-quality-baseline.json` becomes `{}`. `python3 scripts/check-code-quality.py` passes.
- No README change, no translation change, no change under `src/`, `qml/` or `i18n/`.

## Acceptance criteria

- [ ] Every file named in §2 and §3 exists and is registered in `tests/CMakeLists.txt`; no new test
      executable or `ctest` name was added.
- [ ] Every file under `tests/` is ≤ 200 lines; every function in it is ≤ 20 lines, has ≤ 3
      parameters and nests ≤ 2 deep; no comments.
- [ ] `scripts/code-quality-baseline.json` is `{}`; `python3 scripts/check-code-quality.py` passes.
- [ ] No assertion was dropped: the PR body has a table with, for each original file, the number of
      `QVERIFY*`/`QCOMPARE*`/`QTRY_*` macros, `QTest::newRow`/`addRow` rows and test functions before
      and after (after ≥ before, every difference explained).
- [ ] `contentScriptRunsInPages`, `importNetscapeHtml` and `addsBookmarksHistoryAndNetworkSuggestions`
      are split into the test functions named in §2.
- [ ] `findByClassName` and `registerSingleton` exist only in `tests/common/qmltesthelpers.h`.
- [ ] `git diff origin/main --stat -- src qml i18n README.md` is empty.
- [ ] Clean build with no new warnings; all `ctest` tests pass, and the number of executed test
      functions reported by QTest is at least today's.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary directory,
see AGENTS.md): build, run `ctest --output-on-failure` twice in a row (no test depends on the order
or on a previous run), then run `./build/tests/tst_extensions -functions` and `./build/tests/tst_tabstrip
-functions` and check that every test of today is listed under its new class. The offscreen smoke
test of the app still shows no QML errors.

## Out of scope

- Any change to production code (`src/`, `qml/`), translations or README. If a test reveals a bug,
  report it as a question on the issue; do not fix it here.
- New test cases beyond the splits named here, and changing what a test checks.
- New test executables, a static library of shared sources, or any other restructuring of
  `tests/CMakeLists.txt` beyond adding the new files and include directories.
- Test files that are not in the baseline, except for using the shared helpers of §3 where a copy is
  removed.
- The extensions repository (`lukasborges/kondor-extensions`).

## Dependencies

- #135 (checker and baseline) and #139 (last non-test entries), merged.

## Prototype

None: no visible change.

## Decisions

| Question | Decision |
| --- | --- |
| Split files into new executables or keep one per target? | Keep one executable per target. Every test executable recompiles its production sources (AGENTS.md → "Build and run"); seven more `tst_extensions`-like targets would make CI and the agent loops much slower and heavier. Several test classes in one executable, each run with `QTest::qExec` from `main`, keep the files small and the `ctest` names unchanged. |
| Where do helpers used by several feature folders go? | `tests/common/`, like `qml/common/`: only the helpers that are copied today (`findByClassName`, `registerSingleton`) and the isolated home used by every touched `main`. |
| How is "no assertion dropped" checked? | By the before/after counts of assertion macros, data rows and test functions in the PR body, which the reviewer re-counts. |
