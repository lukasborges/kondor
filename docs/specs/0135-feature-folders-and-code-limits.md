# Feature folders and Clean Code limits (#135)

> **Issue:** [#135](https://github.com/lukasborges/kondor/issues/135) · **Priority:** P1 (high) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Make the code easy to read and change by organizing it the way the maintainer likes: Clean Code
taken to the extreme.
- **Feature folders:** `src/`, `qml/` and `tests/` are split into feature folders.
- **Limits:** the rules in AGENTS.md → "Code quality" (tiny functions, small files, almost no
  comments) become checkable.
- **Ratchet:** a CI check enforces them with a baseline that can only shrink. New and changed code
  follows the limits at once, and the existing offenders are fixed by the follow-up refactoring
  issues #136–#139.

## Context

- **Today's layout:** everything is flat: 25 C++ units in `src/` (plus `src/adblock/` and
  `src/passwords/`), 39 QML files in `qml/`, 22 tests in `tests/`.
- **Largest files:**

  | File | Lines |
  | --- | --- |
  | `qml/BrowserWindow.qml` | 1 458 |
  | `qml/SettingsWindow.qml` | 971 |
  | `qml/BookmarksWindow.qml` | 959 |
  | `src/bookmarkmanager.cpp` | 728 |

- **Longest functions:** `BookmarkManager::importHtml` has 141 lines. `HistoryManager::topSites`,
  `Database::migrate`, `buildRows()` in `AddressSuggestions.qml` and `perform()` in
  `PageContextMenu.qml` each have more than 80.
- **QML module:** one module, `Kondor` (`qt_add_qml_module(kondor URI Kondor … QML_FILES qml/…)`).
  Files in subfolders of the module stay types of the same module. Their resource path becomes
  `qrc:/qt/qml/Kondor/qml/<folder>/<File>.qml`, and a file only sees types from other folders
  through `import Kondor`.
- **Tests load QML by path:** `KONDOR_QML_DIR "/SettingsWindow.qml"`, … in
  `tst_settingswindow.cpp`, `tst_sitepermissions.cpp`, `tst_mainmenu.cpp`,
  `tst_bookmarkswindow.cpp`, `tst_addresssuggestions.cpp` and `tst_tabstrip.cpp`.
- **Ordering with #107:** #107 (PR #134) adds `src/extensions/` and new QML files. This issue
  starts after it is merged and moves those files too.

## Design / behavior

### 1. Folder layout

Use `git mv` so history follows the files. Tests mirror `src/`, as `tests/<folder>/tst_*.cpp`;
`tests/data/` stays.

| Folder | C++ (`src/<folder>/`) | QML (`qml/<folder>/`) |
| --- | --- | --- |
| `app` | `main.cpp`, `startupargs`, `startupurl`, `singleinstance`, `windowmanager`, `aboutinfo` | `BrowserWindow`, `AboutWindow`, `MainMenu` |
| `core` | `database`, `settings`, `notifier`, `filehelper` | — |
| `browser` | `tab`, `tabmodel`, `profilemanager`, `zoommanager`, `addressresolver`, `searchsuggestions`, `sessionmanager`, `faviconstore` | `WebViewTab`, `TabStrip`, `TabButtonDelegate`, `TabContextMenu`, `PageContextMenu`, `FindBar`, `FullScreenHint`, `CertificateErrorPage`, `CrashedPage`, `ReaderControls`, `NewTabPage`, `AddressSuggestions` |
| `site` | — | `SiteInfoPopup`, `PermissionBar`, `PermissionTypeInfo`, `SitePermissionsDialog` |
| `bookmarks` | `bookmarkmanager`, `bookmarkmodel` | `BookmarksWindow`, `BookmarksBar`, `BookmarkMenu` |
| `history` | `historymanager`, `historymodel` | `HistoryWindow` |
| `downloads` | `downloadmanager` | `DownloadsPopup` |
| `passwords` | (already there) | `PasswordsPage`, `PasswordBar`, `AddPasswordDialog`, `ImportPasswordsDialog` |
| `adblock` | (already there) | `AdBlockPopup` |
| `extensions` | `extensionloader` (#88) and the #107 files | the #107 QML files |
| `settings` | — | `SettingsWindow` |
| `common` | — | `InlineBar`, `SiteIcon`, `SiteMenuItem` (and `ConfirmDialog` if #120 is merged) |

A file that is not listed (added after this spec) goes to its feature's folder. Ask a question if
that is unclear.

- **CMake:** update `CMakeLists.txt` (`SOURCES`, `QML_FILES`, include directories: add `src` so
  includes read `#include "bookmarks/bookmarkmanager.h"`) and `tests/CMakeLists.txt` (sources and
  `KONDOR_QML_DIR "/<folder>/<File>.qml"`). Update every `#include` to the `<folder>/<file>.h`
  form.
- **QML imports:** every QML file that uses another Kondor type gets `import Kondor`. Today three
  files lack it: `InlineBar`, `PermissionTypeInfo` and `FullScreenHint`.
- **Paths elsewhere:** fix every hard-coded `qrc:` or `.qml` path in C++ and QML. Also fix:
  - `i18n` sources: re-run `update_translations`. Only the location lines change; no message
    changes.
  - `release.yml`, the Flatpak manifest and the AppImage script, if any of them names a moved path.
- **Behavior:** the move commit changes paths only. A second commit fixes includes, CMake and
  imports. No behavior changes in this issue.

### 2. Rules

The architect adds the rules to AGENTS.md → "Code quality" with this issue. They apply to
`src/**/*.{cpp,h,js}`, `qml/**/*.qml` and `tests/**/*.cpp`.

| Rule | Limit |
| --- | --- |
| Function or method body: C++, JS, a QML `function`, or a QML signal handler block `onX: { … }` | ≤ **10** lines (aim for 5). Tests: ≤ 20. |
| Parameters | ≤ **3** |
| Nesting inside a function (blocks, loops, lambdas) | ≤ **2** levels |
| File | ≤ **200** lines |
| Comments | none, except `//:` and `//~` translator notes, a comment that links a bug report (`bugreports.qt.io`, `bugs.kde.org`, `invent.kde.org/…/issues`, `github.com/…/issues`) to explain a workaround, and SPDX license lines |

### 3. Checker

`scripts/check-code-quality.py` uses the Python 3 stdlib only, and its own code follows the same
limits.

- **Scanning:**
  - Each file is read once and its comments and strings are stripped with a small tokenizer.
    C++ and JS share it: `//`, `/* */`, `'…'`, `"…"`, template strings, and `R"(…)"` raw
    strings.
  - Function bodies are found by matching braces:
    - **C++:** a `{` that follows a `)` (optionally followed by `const`, `override`, `noexcept`,
      `final`, `-> type`, or a constructor initializer list) at namespace or class scope.
    - **QML/JS:** `function name(…) {`, and `onX: {` / `onX: function(…) {` handlers.
  - Lambdas and nested functions count toward the enclosing function. They also count as a
    nesting level.
  - Body lines are the lines between the braces, blank lines included.
- **Function key:** `path::Class::method` for C++, `path::name` for QML/JS functions, and
  `path::onX#n` for the n-th handler with that name.
- **Output:** one line per violation, as `path:line: <rule>: <value> > <limit> (<key>)`. The exit
  code is 1 if there is any.
- **Baseline:** `scripts/code-quality-baseline.json` maps each key, or `path` for file length and
  comment count, to today's value.
  - A violation listed in the baseline passes while its value is ≤ the baseline. It fails when the
    value grows.
  - An entry whose value is now within the limit fails with "fixed: remove it from the baseline",
    so the baseline only shrinks.
  - `--update-baseline` rewrites the values downward and removes fixed entries. It refuses to add
    entries or raise values: new code can never enter the baseline.
  - The baseline is generated once in this issue (`--init-baseline`, which is allowed only when
    the file does not exist).
- **`--changed <git ref>`:** reports only the files that differ from the ref, so it is quick
  locally. CI runs the full check.
- **Tests:** `scripts/tests/test_check_code_quality.py` (unittest), with small fixtures for each
  rule and for each baseline transition (passes, grows, fixed, new). It runs in CI.
- **CI:** a step "Code quality" in `build.yml`, before the build: the unittest, then
  `python3 scripts/check-code-quality.py`.

### 4. Docs

- `README.md`, "Development": one paragraph pointing to AGENTS.md → "Code quality" and the checker.
- The developer delivery checklist in AGENTS.md (architect) gains the step "run
  `scripts/check-code-quality.py --changed origin/main`".

## Acceptance criteria

- [ ] `src/`, `qml/` and `tests/` follow the layout table. `git log --follow` works for moved files.
- [ ] The app, the tests and the smoke test behave exactly as before. CI is green.
- [ ] The checker enforces every rule of item 2 and the baseline ratchet, and has its unit tests.
- [ ] `code-quality-baseline.json` lists today's offenders only. A new long function, file or
  comment makes CI fail.

## Manual test

1. Build and run on an isolated profile. Open:
   - Settings, with each page;
   - Bookmarks, History and Downloads;
   - a private window;
   - a site with a permission prompt.

   No QML error appears on stderr.
2. Add a 12-line function to any C++ file: the checker fails. Remove it: the checker passes.
3. Shorten a baseline function below 10 lines: the checker says "fixed: remove it from the
   baseline". `--update-baseline` removes it.

## Out of scope

- refactoring the offenders (#136–#139), and any behavior or UI change;
- `prototypes/`, `scripts/*.sh` and `packaging/` (not checked);
- clang-tidy, clang-format and qmllint (possible later).

## Dependencies

#107 (PR #134) merged first, so its files move too.

## Prototype

No UI, so there is no prototype.

## Decisions

| Question | Decision |
| --- | --- |
| How strict? | Extreme, as the maintainer prefers: 10-line functions, 200-line files, no comments except bug-linked workarounds and translator notes. |
| Fix all offenders at once? | No: a shrinking baseline keeps CI green, and the follow-up issues #136–#139 refactor the hotspots one by one without changing behavior. |
| Folders by layer or by feature? | By feature, mirrored in `src/`, `qml/` and `tests/`: a change to one feature stays in one folder name. |
| Do brace initializers count as nesting? (review of PR #141) | No. Nesting counts blocks (`if`, loops, `switch`, `try`, plain `{ }` blocks), lambdas and nested functions only. Brace-init lists such as `return {{TabRole, "tab"}};` or `QJsonObject{{…}, {…}}` are not a nesting level. |
| Do arrow functions count as functions? (review of PR #141) | Yes. A QML handler written as `onX: (…) => { … }` is a handler like `onX: function(…) { … }`, and a JS/QML arrow function with a block body (`const f = (a) => { … }`) outside any other function is a function; inside one it counts toward the enclosing function and as a nesting level. |
