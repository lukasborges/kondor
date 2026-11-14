# Python port 10/12: Extensions: catalog, actions and updates (#172)

> **Issue:** [#172](https://github.com/lukasborges/kondor/issues/172) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 8 and 9, "Rules for every phase") and the phase 9 spec [`0171-python-extensions-core.md`](0171-python-extensions-core.md) first. This phase builds on phase 9's `ExtensionManager`, harness and conventions. This file details phase 10 and must follow the umbrella. Only the architect edits it.

## Objective

Port the catalog half of `src/extensions/` to Python, and port its tests:

- **Same QML API:** `ExtensionCatalog` is a QML singleton (and list model) in `Kondor` 1.0. `check-qml-api.py` pairs it with its C++ twin.
- **Same behavior:** the catalog is fetched, cached, listed and installed from, and catalog extensions and user scripts update themselves, with the same rules (silent update only when the access does not grow), limits (5 MiB, the advertised size, SHA-256) and error texts as the C++.
- **Same data:** the same cache file `CacheLocation/extensions-catalog.json`, the same default catalog URL and `KONDOR_EXTENSIONS_CATALOG_URL` override, and the same `Source` value `catalog` in the extension state. A catalog cached by the C++ app is shown by the Python app, and the other way round.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Phase 9 (#171)** adds `kondor/extensions/` with `ExtensionManager` and its snake_case API (`prepare_install`, `install_package`, `update_package`, `source`, `installed_version`, `installed_access`, `user_script_ids`, `user_script_of`), `state/extensionaccess.py` with `ExtensionAccess` and `is_silent_update`, `package/` (`ExtensionPackage.localized`, `ExtensionPackage.is_valid_id`, `MAX_PACKAGE_BYTES`, `PackageFile`), `userscripts/` (`UserScriptDownload`, `UserScriptSource`, `is_web_url`, `user_script_download_url`, `write_user_script_package`, `is_newer_user_script_version`), `manifest/jsonvalue.py`, and the test harness `pytests/extensions/extensionsharness.py`, `pageserver.py` and `conftest.py`. `Settings` already has `extensionsAutoUpdate`.
- **The scope** (about 970 lines with headers):

  | C++ files | What it does |
  | --- | --- |
  | `catalog/catalogentry.{h,cpp}` | `CatalogEntry`; `parseCatalogEntry` (valid id, version and package, else skipped; package and icon resolved against the catalog URL; `sha256` lower-cased), `parseCatalog` (format `version` 1 with an `extensions` array), `isNewerVersion` (`QVersionNumber`) |
  | `catalog/extensioncatalog.{h,cpp}` | the `ExtensionCatalog` singleton: state, cache file, catalog URL, `loadCatalog`, `contributingUrl`, following the manager's changes |
  | `catalog/extensioncatalogactions.cpp` | `refresh` (one request at a time, cache write, then updates), `install` (download, then the manager's install preview) |
  | `catalog/extensioncatalogmodel.cpp` | the roles, and `dataChanged` for `installed` / `updateAvailable` when installed extensions change |
  | `catalog/catalogupdater.{h,cpp}` | `decideUpdate`; `CatalogUpdater`: daily timer, first check after 5 s, reaction to `extensionsAutoUpdate`, silent download and update, update flags |
  | `install/packagedownload.{h,cpp}` | `PackageDownload`: download into a `kondor-extension-XXXXXX.kondorext` temporary file, size limit, SHA-256 check |
  | `userscripts/userscriptupdater.{h,cpp}` | `UserScriptUpdater`: check `updateURL` (or `downloadURL`), fetch the full script when needed, update or flag for review |

- **The QML that uses it:** `ExtensionCatalogDialog.qml` (`state`, `installError`, `installingId`, `refresh()`, `install()`, `contributingUrl()`, the model), `ExtensionDelegate.qml` (`install()` for an update) and `ExtensionsPage.qml`, which holds both. `src/app/startup/appstartup.cpp` calls `startAutoUpdate()`; that call is wired in phase 11 (#173).
- **Tests to port** (every case; UI tests load the staged QML through `kondor_engine`):

  | C++ test | Cases |
  | --- | --- |
  | `catalog/tst_catalogentry` | `resolvesRelativePackageAndIconUrls`, `skipsEntriesWithoutIdVersionOrPackage` (3 rows), `keepsIconNamesAsTheyAre` |
  | `catalog/tst_extensioncatalog` | `silentUpdateRule`, `catalogListsEntries`, `catalogInstallAsksForConfirmation`, `catalogRejectsBadChecksum`, `catalogRejectsOversizedPackage` |
  | `catalog/tst_extensionupdates` | `newerVersionWithoutNewPermissionsInstallsItself`, `newPermissionOnlyMarksUpdateForReview`, `catalogClaimingOldPermissionsIsNotSilent`, `updateAsksFirstWithReplacementText`, `nothingUpdatesWhenAutomaticUpdatesAreOff`, `fileInstallsAreNeverUpdatedAutomatically` |
  | `userscripts/tst_userscriptupdate` | `silentUpdateKeepsAccess`, `broaderUpdateNeedsReview` |
  | `tst_extensionsui` (QML `ExtensionsPage.qml`) | `extensionsPageListsInstalled`, `emptyListButtonOpensCatalog` |

  `tst_extensions.cpp` is only the C++ runner that calls every `runTest…`; pytest needs no twin. The remaining extension UI tests (`tst_userscriptpages`, `tst_extensionspanel`, `tst_extensionsreloadbar`, `tst_pinnedtoolbar`) and the bridge tests belong to phase 10b (#218).

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior, error texts and edge cases as the C++, with the Python conventions of umbrella item 3 and the patterns of phase 9 (a helper namespace becomes a module of functions, a struct becomes a dataclass, composition instead of mixins).

### 1. Layout

```
kondor/extensions/
  qmltypes.py                    + ExtensionCatalog
  catalog/
    __init__.py
    catalogentry.py              CatalogEntry, parse_catalog_entry, parse_catalog, is_newer_version
    extensioncatalog.py          ExtensionCatalog (QAbstractListModel): signals, properties, slots, model overrides
    extensioncatalogactions.py   refresh and install flows, cache write
    extensioncatalogmodel.py     roles: enum, names, readers
    catalogupdater.py            UpdateDecision, decide_update, CatalogUpdater
  install/
    packagedownload.py           PackageDownload
  userscripts/
    userscriptupdater.py         UserScriptUpdater
```

No file of phase 9 changes except `qmltypes.py` (one more `QmlType`). Further splits for the size limits are allowed when these modules keep their names.

### 2. `CatalogEntry` (`catalog/catalogentry.py`)

- **`CatalogEntry`** is a dataclass with the C++ fields in snake_case: `id`, `json` (the entry object as a `dict`), `version`, `matches`, `permissions`, `package` (`QUrl`), `sha256`, `size = 0`, `icon_source = ""`.
- **`parse_catalog_entry(object, catalog_url) -> CatalogEntry | None`:**
  - `matches` and `permissions` keep only the string items of an array (anything else gives `[]`);
  - `sha256` is lower-cased; `size` is the number as an `int` (0 when it is missing or not a number);
  - `None` when `ExtensionPackage.is_valid_id(id)` fails, or `version` or `package` is empty;
  - `package` is `catalog_url.resolved(QUrl(package))`;
  - the icon: empty → `preferences-plugin`; a value with `/` or `.` → `catalog_url.resolved(QUrl(icon)).toString()`; anything else as is.

  The `QJsonValue` conversions follow `manifest/jsonvalue.py` (phase 9 item 4).
- **`parse_catalog(json: bytes, catalog_url) -> tuple[list[CatalogEntry] | None, str]`** (the entries and the error, `""` on success; the C++ `QString &error` out-parameter):
  - parsed with `QJsonDocument.fromJson`; a parse error or a non-object gives `The catalog is not valid JSON`;
  - `version` other than the integer 1, or `extensions` that is not an array, gives `The catalog has an unsupported format`;
  - otherwise every array item that parses, in order (a non-object item counts as `{}`, so it is skipped).

  Texts use `QCoreApplication.translate("ExtensionCatalog", …)`.
- **`is_newer_version(candidate, installed)`** compares with `QVersionNumber.fromString`, as C++ does (if PySide6 returns a `(version, suffix index)` tuple, take the version).

### 3. `ExtensionCatalog` across modules

- **`extensioncatalog.py`** holds the one `QAbstractListModel` subclass: signals, the four properties, the slots, the snake_case API, the model overrides (`rowCount`, `data`, `roleNames`), `instance()`, the setters that emit only on change (`set_state(state, error="")`, `set_installing`, `set_install_error`) and `emit_all_changed`. Each method is a few lines that delegate.
- **`extensioncatalogactions.py`** holds the refresh and install flows as module functions that take the catalog; **`extensioncatalogmodel.py`** the roles and their readers. They never emit signals themselves; they call the catalog's setters.
- **Properties:** `state` (`str`, notify `stateChanged`), `errorString` (`str`, notify `stateChanged`), `installingId` (`str`, notify `installingChanged`), `installError` (`str`, notify `installErrorChanged`). The state is one of `idle` (start), `loading`, `ready`, `error`.
- **Signals:** `stateChanged`, `installingChanged`, `installErrorChanged`, `updatesChecked`.
- **Slots:** `refresh()`, `install(str)`, `contributingUrl() -> QUrl` (`https://github.com/lukasborges/kondor-extensions/blob/main/CONTRIBUTING.md`).
- **Roles** (`IntEnum` from `Qt.ItemDataRole.UserRole + 1`, same order and names as C++): `id`, `name` and `description` (`ExtensionPackage.localized(entry.json, key)` with the system locale, as C++ calls it without a locale), `version`, `author` (the `author` string), `iconSource`, `installed` (installed and the catalog version is not newer), `updateAvailable` (installed and the catalog version is newer). `installed` and `updateAvailable` read `ExtensionManager.instance()`.
- **Snake case API** (phase 11 and the tests call it): `catalog_url()` (the URL set with `set_catalog_url` when it is valid, else `KONDOR_EXTENSIONS_CATALOG_URL` when it is set and not empty, else `https://lukasborges.github.io/kondor-extensions/catalog.json`), `set_catalog_url(url)`, `cache_file()` (static: `QStandardPaths.writableLocation(CacheLocation) + "/extensions-catalog.json"`), `load_catalog(json: bytes) -> str` (the error, `""` on success; on success it resets the model with the new entries), `start_auto_update()`, `check_for_updates()`, `network()`, `find(id) -> CatalogEntry | None`, `entries()`.
- **Instance:** `ExtensionCatalog()` creates its own `QNetworkAccessManager` and the `CatalogUpdater` (both parented to it), follows the manager (`revisionChanged`, `modelReset`, `rowsInserted`, `rowsRemoved` → `emit_all_changed`, which emits `dataChanged` over every row for the two installed roles when there are rows), shows the cached catalog (a readable cache that loads sets the state to `ready` without emitting) and forwards the updater's `updatesChecked`. `instance()` creates it on first use. Importing any module must not create it, the manager or a network manager.
- **No `isSilentUpdate` here:** the catalog code calls phase 9's `is_silent_update` (phase 9 "Decisions"). The `silentUpdateRule` case tests that function.

### 4. Refresh and install (`catalog/extensioncatalogactions.py`)

- **`refresh`:**
  1. While a refresh reply is pending, do nothing.
  2. `set_state("loading")`, then `GET catalog_url()` with `RedirectPolicyAttribute` = `NoLessSafeRedirectPolicy` and `CacheLoadControlAttribute` = `AlwaysNetwork`. Keep the reply until it finishes.
  3. On `finished`: forget the reply and `deleteLater()` it. A network error fails with `errorString()`; a body that `load_catalog` refuses fails with its error.
  4. **Failure:** `set_state("error" if there are no entries else "ready", message)`, then emit `updatesChecked`.
  5. **Success:** write the body to `cache_file()` (create its folder; a cache that cannot be opened is skipped silently), `set_state("ready")`, then `updater.apply_updates(entries)`.
- **`install(id)`:**
  - nothing when the id is not in the catalog or another install is running (`installingId` not empty);
  - else `set_install_error("")`, `set_installing(id)` and start a `PackageDownload` (parented to the catalog) for the entry, with the localized name kept for the messages;
  - on `finished(path, error)`: `set_installing("")`; on failure `set_install_error` with `Could not download “%1”: %2` (context `ExtensionCatalog`, name and error); on success `ExtensionManager.instance().prepare_install(PackageFile(path, "catalog", name, True))`.

### 5. `PackageDownload` (`install/packagedownload.py`)

A `QObject(parent)` with `start(entry)` and `finished = Signal(str, str)` (the path, `""` on failure, and the error):

- **The file:** a `QTemporaryFile(QDir.tempPath() + "/kondor-extension-XXXXXX.kondorext")` that is not auto-removed.
- **`start`:** `GET entry.package` with `NoLessSafeRedirectPolicy`. The limit is `min(entry.size, MAX_PACKAGE_BYTES)` when `entry.size > 0`, else `MAX_PACKAGE_BYTES`. When the file cannot be opened: abort the reply, `deleteLater()` it and finish with `Cannot create a temporary file`.
- **`readyRead`:** add the chunk to the received count; while it is within the limit, write it; above it, remember `The package is larger than expected` and abort the reply.
- **`finished`:** `deleteLater()` the reply, write what is left, close the file, then the first error of: the remembered failure, the reply's `errorString()` when it has an error, the checksum (`Cannot read the downloaded package` when the file cannot be read again, `The downloaded package does not match its checksum` when the lower-case hex SHA-256 of the file (`QCryptographicHash`) differs from `entry.sha256`). On an error the file is removed.
- **Finish:** emit `finished`, then `deleteLater()` itself.

Texts use the context `ExtensionCatalog`.

### 6. Updates (`catalog/catalogupdater.py`)

- **`UpdateDecision`** is an `Enum` with `NOT_INSTALLED_FROM_CATALOG`, `UP_TO_DATE`, `NEEDS_REVIEW`, `SILENT`.
- **`decide_update(entry, manager)`:**
  - not installed, or its source is not `catalog` → `NOT_INSTALLED_FROM_CATALOG`;
  - `is_newer_version(entry.version, installed version)` false → `UP_TO_DATE`;
  - `is_silent_update(ExtensionAccess(entry.matches, entry.permissions), manager.installed_access(id))` → `SILENT`, else `NEEDS_REVIEW`. The update's includes are empty, as in C++.
- **`CatalogUpdater(catalog, network)`** (a `QObject` parented to the catalog) owns a `UserScriptUpdater(network, self)` and a `QTimer` (24 h, `24 * 60 * 60 * 1000` ms) whose `timeout` calls `check_for_updates`:
  - **`start_auto_update()`:** connects `Settings.instance().extensionsAutoUpdateChanged` to `react_to_setting_change` once; when auto update is on, starts the timer and calls `check_for_updates` after 5 s (`QTimer.singleShot(5000, self, …)`).
  - **`react_to_setting_change()`:** off → stop the timer; on → start it and check now.
  - **`check_for_updates()`:** off → stop the timer and return. Else `UserScriptUpdater.check_all()`, then `catalog.refresh()` when any manager row has the source `catalog`, else emit `updatesChecked`.
  - **`apply_updates(entries)`:** for each entry, by decision: none; `UP_TO_DATE` → `setUpdateInfo(id, False, False)`; `NEEDS_REVIEW` → `setUpdateInfo(id, True, True)`; `SILENT` → `setUpdateInfo(id, True, False)` and download silently. Then emit `updatesChecked`.
  - **Silent download:** skipped when auto update is off or the id is already updating. Otherwise it marks the id, starts a `PackageDownload` (parented to the updater), and on `finished` unmarks it. A failed download logs `Extension <id>: update failed: <error>`. Otherwise it calls `manager.update_package(PackageFile(path, "catalog", "", False), id)`, records the result, removes the file and emits `updatesChecked`.
  - **Recording a result:** installed → `setUpdateInfo(id, False, False)`; `needs_review` → `setUpdateInfo(id, True, True)`; else log `Extension <id>: update failed: <error>`.

  Warnings go through the `kondor.extensions` logging category of phase 9, with the C++ texts.

### 7. `UserScriptUpdater` (`userscripts/userscriptupdater.py`)

A `QObject(parent)` with the network manager it is given and `check_all()`:

- **`check_all()`** checks every id of `ExtensionManager.instance().user_script_ids()`.
- **`check(id)`:**
  - the check URL is the `userScript` section's `updateURL`, or its `downloadURL` when that is empty, and only when `is_web_url` accepts it;
  - skip when there is none or the id is already being checked;
  - mark the id and start a `UserScriptDownload`: a full `start(url)` when the check URL equals `user_script_download_url(user_script)`, else `start_metadata_only(url)`.
- **On the check's `finished`:**
  - unmark the id, and stop on an error;
  - stop unless `is_newer_user_script_version(metadata.version, installed version)`, where the installed version is the `userScript` section's `version`;
  - install the source when its `install_url` equals the download URL and it is complete (`UserScriptSource.is_complete()`, the C++ `isComplete()`);
  - otherwise fetch the full script from the download URL first, and install it when that succeeds.
- **Install:** `write_user_script_package(source)`; on failure log `User script <id>: update failed: <error>`. Otherwise `update_package(PackageFile(path, "userscript", "", True), id)`, record the result as in item 6 (with the `User script` prefix in the log), and remove the file.

### 8. `qmltypes.py`

```python
QML_TYPES = (
    QmlType(ExtensionManager, "ExtensionManager", QmlKind.SINGLETON),
    QmlType(ExtensionCatalog, "ExtensionCatalog", QmlKind.SINGLETON),
)
```

`pytests/core/test_singletons.py` finds the new singleton through `kondor_types` with no change.

### 9. Tests

Each C++ case becomes a test with the same intent (umbrella item 9). Data-driven cases become `pytest.mark.parametrize` with the same rows and ids. Test functions have at most 20 lines. **No test talks to the internet:** catalogs and packages are local `file:` URLs, user scripts come from a local server, and a fixture points the catalog at a local file before any test that may refresh it (the catalog dialog refreshes when it opens).

```
pytests/extensions/
  test_extensionsui.py
  catalog/
    __init__.py
    catalogharness.py          CatalogFixture, catalog_fixture, pack_catalog_package, catalog_entry,
                               write_catalog, refresh_catalog, wait_for_pending_install,
                               install_from_catalog, is_update_waiting_for_review, installed_sample_version
    conftest.py                fixtures: catalog root folder, catalog URL reset, auto update on
    test_catalogentry.py
    test_extensioncatalog.py
    test_extensionupdates.py
    test_catalogupdater.py
    test_packagedownload.py
  userscripts/
    test_userscriptupdate.py
```

- **The harness** mirrors `catalogharness.h` (the fixture is a dataclass with the same fields and defaults). `sha256_of(path)` joins `extensionsharness.py`, next to the helpers it mirrors from `extensionsharness.h`. Waits use `qtbot.waitUntil(…, timeout=10000)`. `remove_every_extension` runs after every test that installs.
- **The script server:** reuse phase 9's `pageserver.py` when it already serves a body per path and answers `404` for an unknown path. Otherwise add that to it (it is phase 9 test code in the same feature folder) rather than adding a second server.
- **New tests** for code the C++ tests only reach indirectly:
  - **`test_catalogentry.py`:**
    - `test_invalid_json_is_refused`;
    - `test_unsupported_format_is_refused` (`version` 2, and `extensions` that is an object);
    - `test_compares_versions` (rows: `1.10.0` newer than `1.9.0`, `1.0` not newer than `1.0.0`, `2.0.0` not newer than `2.0.0`).
  - **`test_catalogupdater.py`** (the sample installed with `install_sample(work, source)`):
    - `test_decides_each_update` (rows: not installed, source `file`, same version, newer with the same access → silent, newer with a new permission → needs review);
    - `test_check_without_catalog_installs_emits_updates_checked_without_refreshing` (the state stays as it was);
    - `test_check_does_nothing_when_auto_update_is_off`.
  - **`test_extensioncatalog.py`**, besides the C++ cases:
    - `test_failed_refresh_keeps_the_entries` (a valid catalog, then a missing file: state `ready` with an `errorString`);
    - `test_failed_first_refresh_is_an_error` (a fresh `ExtensionCatalog()` with no cache, a missing file: state `error`);
    - `test_cached_catalog_is_shown_at_start` (write `cache_file()`, build a fresh `ExtensionCatalog()`: state `ready`, one row).
  - **`test_packagedownload.py`:**
    - `test_downloads_into_a_kept_temporary_package` (the path ends in `.kondorext` and exists after `finished`);
    - `test_checksum_mismatch_removes_the_file`;
    - `test_body_above_the_advertised_size_is_refused` (`The package is larger than expected`);
    - `test_missing_package_reports_the_network_error`.
- **`test_extensionsui.py`** loads `ExtensionsPage` from inline QML in `kondor_engine`, as the C++ harness does, and finds items by `objectName` and text like the phase 9 dialog tests. `emptyListButtonOpensCatalog` points the catalog at a missing local file first. If the page needs a type that is not ported yet, ask (`question`) before moving the test (umbrella item 9).
- **Fresh catalogs** built in a test are deleted (`deleteLater`) at its end, so only the singleton stays connected to the manager.

### 10. API check result

After this phase, `python3 scripts/check-qml-api.py` reports **one more** class checked (`ExtensionCatalog`) and one fewer not ported than on the PR's base, and exits 0.

## Acceptance criteria

- [ ] `kondor/extensions/` has the modules of item 1, and `qmltypes.py` registers `ExtensionCatalog` as a singleton next to `ExtensionManager`.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports one more class checked than on the base, with no problems.
- [ ] Every C++ case of the five test files in "Context" has its pytest twin, and the new tests of item 9 exist and pass with `scripts/run-pytests.sh`. No test reaches the internet.
- [ ] A package with a wrong checksum or above its advertised size is never offered for install, and its temporary file is removed (tests).
- [ ] A catalog or user script update that asks for more access only sets `updateNeedsReview`; one that does not installs itself; nothing updates when `extensionsAutoUpdate` is off or the extension was installed from a file (tests).
- [ ] A catalog cached by the C++ app is shown by the Python catalog, and an extension installed from the catalog by the C++ app is updated by the Python updater (manual test).
- [ ] The `build` job is green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt` or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md) shared by every step. The snippet is the phase 9 one (a `QApplication` after `QtWebEngineQuick.initialize()`, organization `KDE`, application `Kondor`, `build/python/kondor.rcc` registered, every ported `register_types()` called), run with `KONDOR_EXTENSIONS_CATALOG_URL` set to the local catalog below.

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && scripts/run-pytests.sh && python3 scripts/check-qml-api.py`: all pass, and the last reports one more class than `main`.
2. **A local catalog:** in a temp folder, pack the sample (`zipfile` over `tests/data/extensions/sample`) as version 1.0.0 into `packages/`, write a `catalog.json` for it like `catalogharness.py` does, and serve the folder with `python3 -m http.server`.
3. **C++ → Python:**
   1. Start the C++ app (built from `main`) with the same `KONDOR_EXTENSIONS_CATALOG_URL`. Open Settings → Extensions → Get New Extensions…, install the sample and quit.
   2. With the snippet, `ExtensionCatalog.instance().state` is `ready` with one row before any refresh (the C++ cache), and its `installed` role is true.
4. **Updates in Python:**
   1. Repack the sample as 1.1.0 with the same permissions and update the catalog entry.
   2. With `Settings.extensionsAutoUpdate` on, `check_for_updates()` installs 1.1.0 silently.
   3. Repack it as 1.2.0 with the `downloads` permission: the row gets `updateNeedsReview`, the version stays 1.1.0, and `install("sample")` then `confirmInstall()` installs 1.2.0.
5. **Install errors:** change the entry's `sha256` to 64 zeros, then `install("sample")`. `installError` mentions the checksum, `pendingInstall` stays empty, and no `kondor-extension-*.kondorext` is left in the temp folder.
6. **Python → C++:** start the C++ app again. It lists the sample at 1.2.0, and its catalog dialog shows the catalog the Python app cached.
7. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- `bridge/`, the extension JS resources and the tests that need a `Tab` or the page harness (`tst_userscriptpages`, `tst_extensionspanel`, `tst_extensionsreloadbar`, `tst_pinnedtoolbar`, the bridge tests): phase 10b (#218).
- Calling `start_auto_update()` or `register_types()` from an app entry point: phase 11 (#173).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests or the workflows.
- Changes to phase 9 modules other than `qmltypes.py`, or to `kondor/core/`, `kondor/browser/`, the other ported features, `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker. If a phase-10 file shows a bug in them, ask first (`question`). The only phase 9 test code that may change is item 9's `sha256_of` and the script server.
- Sharing one network manager between `ExtensionManager` and `ExtensionCatalog` (see "Decisions").
- New behavior: no new catalog fields or format version, no change to the update interval, the first-check delay, the size limit, the checksum, the cache file or the default URL.
- Translating Python strings, or running `pyside6-lupdate` (phase 12). Python keeps the C++ context `ExtensionCatalog`.

## Dependencies

#171 (phase 9: `ExtensionManager`, packages, user scripts, the harness). Umbrella #162. Phase 10b (#218) waits for this phase.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| What is left for phase 10 after phase 9? | `catalog/`, `install/packagedownload` and `userscripts/userscriptupdater`, with `tst_catalogentry`, `tst_extensioncatalog`, `tst_extensionupdates`, `tst_userscriptupdate` and `tst_extensionsui` (phase 9 "Decisions"). This replaces the issue body's "the model and the queries", which phase 9 took. |
| Does the catalog share the manager's network manager, as phase 9 allowed? | No. The catalog creates its own, as the C++ catalog does, and hands it to `CatalogUpdater`, `PackageDownload` and `UserScriptUpdater`. Phase 9's manager keeps its own for `inspectUserScript`. Neither has a custom cache, cookie jar or proxy, so the user sees no difference, and phase 9 code stays unchanged. |
| Where does `isSilentUpdate` live? | In phase 9's `state/extensionaccess.py` as `is_silent_update`. The catalog has no static of that name (it is not in the QML API), and `silentUpdateRule` tests that function. |
| How is `ExtensionCatalog` split over four `.cpp` files in Python? | One `QAbstractListModel` subclass in `extensioncatalog.py` with thin slots, plus module functions in `extensioncatalogactions.py` and `extensioncatalogmodel.py` (the phase 9 rule: composition, no mixins carrying `Slot`s or `Signal`s). |
| `tst_extensions.cpp` has no twin? | It is the C++ runner that executes every extension test class in one binary; pytest collects the modules itself. |
| How do the catalog tests stay offline? | Every catalog and package is a local `file:` URL, as in the C++ harness. A fixture also sets the catalog URL before each test, because the singleton outlives tests and `ExtensionCatalogDialog` refreshes when it opens. With the default URL, that refresh would reach GitHub Pages. |
| A second server for user script updates (`scriptserver.h`)? | No: phase 9's `pageserver.py` already serves bodies per path for the user script download tests. It is extended there if it lacks a `404` for unknown paths, so there is no duplicate. |
