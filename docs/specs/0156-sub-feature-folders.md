# Sub-feature folders (#156)

> **Issue:** [#156](https://github.com/lukasborges/kondor/issues/156) · **Priority:** P1 (high) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Make every folder small enough to take in at a glance, as the maintainer wants:

- **Layout:** crowded feature folders are split into sub-feature folders.
- **Rule:** no folder in `src/`, `qml/` or `tests/` holds more than **10 files**.
- **Check:** `scripts/check-code-quality.py` enforces the rule in CI.

## Context

- **Layout after #135:** one level of feature folders. Several of them are still crowded:

  | Folder | Files |
  | --- | --- |
  | `src/extensions/` | 69 |
  | `src/browser/` | 40 |
  | `qml/browser/` | 37 |
  | `src/app/` | 30 |
  | `tests/browser/` | 26 |
  | `tests/extensions/` | 25 |
  | `src/passwords/` | 23 |
  | `src/core/`, `src/adblock/` | 20, 19 |
  | `qml/app/`, `qml/bookmarks/` | 18 each |
  | `src/bookmarks/` | 17 |
  | `qml/passwords/`, `qml/settings/`, `tests/bookmarks/` | 14, 12, 11 |

- **QML module:** all QML files are still types of the one module `Kondor`, whatever their folder.
  A file sees types from other folders through `import Kondor` (already in every file since #135).
- **Includes:** `src` is an include directory, so includes read `#include "<folder>/<file>.h"`.

## Design / behavior

### 1. Rule

- **Limit:** a folder holds at most **10 files**. Sub-folders do not count as files.
- **Scope:** every folder under `src/`, `qml/` and `tests/`, at any depth, except `tests/data/`
  and its sub-folders (test fixtures).
- **Depth:** at most two levels below `src/`, `qml/` or `tests/`, so `src/browser/tabs/features/`
  is the deepest allowed.
- **Names:** sub-folder names are lowercase, one word where possible, and name a sub-feature, not a
  layer (`import/`, `catalog/`, `tabstrip/`; not `utils/`, `helpers/`, `models/`).
- **Kept as is:** file names and class names. A file keeps its name and only moves.

### 2. C++ layout (`src/`)

Paths are relative to `src/`. `x` means `x.h` + `x.cpp`. A folder not listed keeps its files.

| Folder | Files |
| --- | --- |
| `adblock/` | `adblockmanager`, `adblockinterceptor`, `adblockallowlist` |
| `adblock/filters/` | `filterengine`, `filteroptions`, `filterpattern`, `filterrule`, `filterrequest.h` |
| `adblock/lists/` | `filterlists`, `filterlistdownloader` |
| `app/` | `main.cpp`, `aboutinfo` |
| `app/startup/` | `appstartup`, `appidentity`, `environment`, `messagehandler` |
| `app/commandline/` | `commandline`, `startupargs`, `startupurl`, `extensionpackages` |
| `app/instance/` | `singleinstance`, `singleinstancemessage`, `windowactivation` |
| `app/windows/` | `windowmanager`, `windowlaunch.cpp` |
| `bookmarks/` | `bookmarkmanager`, `bookmarkmodel`, `bookmarkrow.h` |
| `bookmarks/storage/` | `bookmarkqueries`, `bookmarkchecks`, `bookmarkfoldertree` |
| `bookmarks/import/` | `bookmarkhtmlimporter`, `bookmarkhtmlparser`, `bookmarkhtmltext` |
| `browser/` | `zoommanager` |
| `browser/tabs/` | `tab.h`, `tab.cpp`, `tabcommands.cpp`, `assignandnotify.h`, `tabmodel`, `tabmodelclosing.cpp`, `closedtabs` |
| `browser/tabs/features/` | `tabsecurity`, `tabpermissions`, `tabpasswords`, `tabextensionitems` |
| `browser/address/` | `addressresolver`, `searchsuggestions`, `suggestionlist` |
| `browser/profile/` | `profilemanager`, `profilesetup`, `pagescripts`, `certificateoverrides` |
| `browser/session/` | `sessionmanager`, `sessionformat`, `sessionwindow.h` |
| `browser/favicons/` | `faviconstore`, `faviconimageprovider` (moved from `app/`) |
| `core/` | `notifier`, `filehelper` |
| `core/database/` | `database`, `databasemigrations`, `sql`, `defaultbookmarks` |
| `core/settings/` | `settings.h`, `settings.cpp`, `settingsdefaults`, `searchengines`, `spellcheckdictionaries` |
| `passwords/` | `passwordstore.h`, `passwordstore.cpp`, `passwordstoreimport.cpp`, `passwordstorewallet.cpp`, `walletfolder`, `passwordorigin`, `passwordclipboard` |
| `passwords/import/` | `csvreader`, `passwordimport`, `passwordimportcolumns`, `passwordimportfile`, `passwordimportplan` |
| `passwords/bridge/` | `passwordbridge`, `passwords.js` |
| `extensions/` | `extensionmanager.h`, `extensionmanager.cpp`, `extensionmodel.cpp`, `extensionqueries.cpp`, `extensionconfiguration.cpp`, `extensioninstall.cpp`, `extensionupdate.cpp`, `extensionscripts.cpp`, `installedextension.h`, `installresult.h` |
| `extensions/state/` | `extensionstate`, `extensionsettings`, `extensionstorage`, `extensionaccess.h` |
| `extensions/catalog/` | `catalogentry`, `catalogupdater`, `extensioncatalog.h`, `extensioncatalog.cpp`, `extensioncatalogactions.cpp`, `extensioncatalogmodel.cpp` |
| `extensions/package/` | `extensionpackage`, `packagearchive.cpp`, `packagefile.h`, `packagelimits`, `packagepath`, `packagesuffix` |
| `extensions/install/` | `extensioninstaller`, `packagedownload`, `extensionloader`, `permissiondescription` |
| `extensions/manifest/` | `manifestvalidator`, `manifestsections`, `manifesticon`, `localizedmanifest`, `stringlistfield` |
| `extensions/scripts/` | `contentscriptbuilder`, `contentscriptreader`, `profilescripts` |
| `extensions/bridge/` | `extensionbridge`, `bridgecalls`, `extensioncall`, `extensionpageapi`, `channel.js`, `extensionruntime.js` |

`downloads/` (8) and `history/` (8) stay as they are.

### 3. QML layout (`qml/`)

| Folder | Files |
| --- | --- |
| `app/` | `BrowserWindow`, `BrowserActions`, `BrowserShortcuts`, `NavigationToolBar`, `PageArea` |
| `app/menu/` | `MainMenu`, `HistoryMenu`, `ZoomMenuRow` |
| `app/window/` | `FullScreenController`, `PageFileDialogs`, `WindowCloseGuard`, `WindowDialogs`, `WindowTabController` |
| `app/about/` | `AboutWindow`, `AboutTab`, `AuthorsTab`, `ComponentsTab`, `LicenseWindow` |
| `bookmarks/` | `BookmarksWindow`, `BookmarksToolBar`, `BookmarkFolderPane`, `BookmarkFolderTree`, `BookmarkItemPane`, `BookmarkItemDelegate`, `BookmarkItemContextMenu`, `BookmarkSelection` |
| `bookmarks/bar/` | `BookmarksBar`, `BookmarkButton`, `BookmarkMenu`, `BookmarkEditorPopup` |
| `bookmarks/drag/` | `BookmarkDragController`, `BookmarkDragPreview`, `BookmarkDropTargets` |
| `bookmarks/dialogs/` | `DeleteBookmarkDialog`, `NewBookmarkFolderDialog`, `RenameBookmarkDialog` |
| `browser/` | `ZoomButton` |
| `browser/tabstrip/` | `TabStrip`, `TabButtonDelegate`, `TabContextMenu`, `TabDragHandler`, `TabSlideAnimation`, `TabStripScrollButton`, `TabStripScroller`, `TabStripTaps`, `TabStripWheel`, `TabWidthFreeze` |
| `browser/address/` | `AddressBar`, `AddressBarButtons`, `AddressCompleter`, `AddressSuggestions` |
| `browser/view/` | `WebViewTab`, `PageView`, `PageOutput`, `PageScriptBridges`, `PageZoom`, `TabCommands`, `CertificateErrorHandler`, `FullScreenHint`, `FindBar` |
| `browser/pages/` | `NewTabPage`, `TopSitesGrid`, `TopSiteMenu`, `CertificateErrorPage`, `CrashedPage` |
| `browser/contextmenu/` | `PageContextMenu`, `PageMenuActions`, `PageMenuEntries`, `SpellCheckLanguagesMenu` |
| `browser/reader/` | `ReaderButton`, `ReaderControls`, `ReaderMode`, `ReaderStyle` |
| `passwords/` | `PasswordsPage`, `PasswordsFrame`, `SavedPasswordsTab`, `SavedPasswordsList`, `SavedPasswordDelegate`, `RevealedPasswords`, `RowToolButton`, `NeverSavedTab`, `AddPasswordDialog` |
| `passwords/import/` | `ImportPasswordsDialog`, `ImportMessage`, `ImportResult` |
| `passwords/bar/` | `PasswordBar`, `PasswordButton` |
| `settings/` | `SettingsWindow`, `SettingsButtonBar`, `SettingsDraft`, `SettingsPageHeader`, `SettingsPages`, `SettingsPageStack`, `SettingsSidebar` |
| `settings/pages/` | `GeneralSettingsPage`, `PrivacySettingsPage`, `SearchSettingsPage`, `DownloadsSettingsPage`, `SpellingSettingsPage` |

`adblock/`, `common/`, `downloads/`, `extensions/`, `history/` and `site/` stay as they are.

### 4. Tests (`tests/`)

- **Mirror:** a test moves to the folder that mirrors the code it tests. For example,
  `tst_tabstrip*.cpp` and `tst_tabdrag*.cpp` go to `tests/browser/tabstrip/`,
  `tst_manifestvalidator.cpp` goes to `tests/extensions/manifest/`, and
  `tst_bookmarkhtmlimport*.cpp` goes to `tests/bookmarks/import/`.
- **Harnesses:** a harness header (`*harness.h`, `pageserver.h`, `*cases.h`) moves with the tests
  that include it. If tests in several folders use it, it stays in the nearest common folder.
- **Limit:** the same 10-file rule applies. If a mirrored folder is still too large, split it by
  the subject in the test names (for example `tests/extensions/bridge/` and
  `tests/extensions/catalog/`).
- **Unchanged:** `tests/data/` and the test names.

### 5. Build and paths

- **CMake:** update `SOURCES` and `QML_FILES` in `CMakeLists.txt`, and the test sources and every
  `KONDOR_QML_DIR "/<folder>/<File>.qml"` path in `tests/CMakeLists.txt`.
- **Includes:** update every `#include` to the new `"<folder>/<sub>/<file>.h"` path.
- **Other paths:** fix every hard-coded `qrc:` or `.qml` path in C++ and QML, and every resource
  path of `channel.js`, `extensionruntime.js` and `passwords.js`.
- **Translations:** re-run `update_translations`. Only the location lines change.
- **Packaging:** check `release.yml`, the Flatpak manifest and the AppImage script for moved paths.
- **Commits:**
  1. `git mv` only, so `git log --follow` keeps the history;
  2. includes, CMake, paths and translations;
  3. the checker rule and its tests.

### 6. Checker

`scripts/check-code-quality.py` gains the rule, and its own code follows the limits.

- **Rule:** for each folder in scope, count the regular files directly in it. More than 10 is a
  violation: `path/: folder files: <n> > 10`.
- **Depth:** a folder more than two levels below `src/`, `qml/` or `tests/` is a violation:
  `path/: folder depth: <n> > 2`.
- **No baseline:** this issue leaves no offender, so folder rules never use the baseline. An
  existing baseline file stays valid.
- **`--changed <ref>`:** checks the folders that contain a changed file.
- **Tests:** add cases to `scripts/tests/test_check_code_quality.py` for 10 files (passes),
  11 files (fails), `tests/data/` (ignored) and depth 3 (fails).

### 7. Docs

- **AGENTS.md:** the architect updates "Architecture" and "Code quality" with this spec (see the
  commit that adds it). The developer changes nothing there.
- **README.md:** in "Development", the paragraph on the checker mentions the folder rule.

## Acceptance criteria

- [ ] `src/`, `qml/` and `tests/` follow the tables and rules above. No folder in scope holds more
  than 10 files, and none is deeper than two levels.
- [ ] `git log --follow` works for moved files.
- [ ] The app, the tests and the smoke test behave exactly as before, and CI is green.
- [ ] The checker reports an 11th file in a folder and a third folder level, with unit tests.

## Manual test

1. Build and run on an isolated profile. Open:
   - Settings, with each page;
   - Bookmarks, History, Downloads and Passwords;
   - Extensions, and install one from a file;
   - a private window;
   - a site with a permission prompt.

   No QML error appears on stderr.
2. Add an 11th file to `src/history/`: the checker fails. Remove it: the checker passes.

## Out of scope

- renaming files or classes, and any behavior or UI change;
- moving files between features, except `faviconimageprovider` (listed above);
- `prototypes/`, `scripts/` and `packaging/`.

## Dependencies

#135 (merged). Start after the issue in review (#154) is merged.

## Prototype

No UI, so there is no prototype.

## Decisions

| Question | Decision |
| --- | --- |
| How many files per folder? | At most 10, as the maintainer asked for less crowded folders. A `.h` + `.cpp` pair counts as two files, so a folder holds about five classes. |
| Drop the feature prefix from file names (`bookmarks/import/htmlparser.cpp`)? | No. A file stays named after its class, as in Qt and KDE code, and the move keeps history simple. |
| How deep? | At most two levels below `src/`, `qml/` or `tests/`. Deeper trees cost more than they explain. |
| Merge `src/<feature>` and `qml/<feature>`? | No. Keeping C++ and QML apart is the Qt convention, and merging would make the folders larger again. |
