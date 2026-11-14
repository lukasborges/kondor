# Python port 9/12: Extensions: manifest, package, state, install and manager (#171)

> **Issue:** [#171](https://github.com/lukasborges/kondor/issues/171) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 7, 8 and 9, "Rules for every phase"), the phase 2 spec [`0164-python-core.md`](0164-python-core.md) and the phase 7 spec [`0169-python-browser-profile-address-session.md`](0169-python-browser-profile-address-session.md) (its "Decisions" on web profiles and `userScripts`) first. This file details phase 9 and must follow the umbrella. Only the architect edits it.

## Objective

Port the installed-extensions half of `src/extensions/` to Python, and port its tests:

- **Same QML API:** `ExtensionManager` is a QML singleton (and list model) in `Kondor` 1.0. `check-qml-api.py` pairs it with its C++ twin.
- **Same data:** the Python app reads and writes the same extension folders under `AppDataLocation/extensions/`, the same `Extensions/<id>/…` keys in `~/.config/KDE/Kondor.conf`, the same `extension_storage` table and the same `Extensions/Pinned` setting, so extensions installed by the C++ app keep working, with their settings, sites and storage.
- **Same packages:** `.kondorext` packages and user scripts are unpacked, validated and installed with the same rules, limits and error texts; `zipfile` replaces KArchive (umbrella item 7).
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Phases 2-8** added `kondor/core/` (`Settings`, `Database`, `sql`, `qmlregistration`), the fixtures of `pytests/conftest.py` (`isolated_profile`, `qapp_cls` with `QtWebEngineQuick.initialize()`, `kondor_types`, `kondor_engine`, `staged_build`, `staged_resources`) and `pytests/qmlsupport.py`. Phase 7 (#169) added `kondor/browser/profile/pagescripts.py`, whose `user_scripts(profile)` and `insert_script(collection, script)` reach `QQuickWebEngineProfile.userScripts`, which PySide6 6.11.2 does not expose (see its "Decisions"). `scripts/build.py` already stages `:/scripts/extensionruntime.js` and `:/scripts/usergm.js` in `build/python/kondor.rcc`. The `extension_storage` table is created by the ported migration step 5. `Settings` already has `pinnedExtensions` and `extensionsAutoUpdate`.
- **No `browser/` dependency:** none of the files below includes `browser/` (checked on `main` at 1396781), so this phase needs only #164.
- **The scope** (about 3,600 lines with headers):

  | C++ folder / files | What it does |
  | --- | --- |
  | `manifest/` `localizedmanifest`, `manifesticon`, `manifestsections`, `manifestvalidator`, `stringlistfield` | `manifest.json` validation (first error wins, fixed English texts), localized strings (`key[pt_BR]`, `key[pt]`, `key`), settings schema and defaults, action items, the icon (theme name, or an `.svg` / `.png` of at least 64 px inside the package) |
  | `package/` `extensionpackage`, `packagearchive`, `packagefile.h`, `packagelimits`, `packagepath`, `packagesuffix` | `ExtensionPackage::load(directory)` and `unpack(zip, directory)`; limits 200 files and 5 MiB; safe relative paths; `PackageFile`, `StagedPackage`; the `.kondorext` suffix |
  | `state/` `extensionaccess.h`, `extensionpins`, `extensionsettings`, `extensionstate`, `extensionstorage` | `ExtensionAccess`; pins in `Settings.pinnedExtensions`; `sanitizeSetting` per setting type; `ExtensionState` over `QSettings("KDE", "Kondor")` `Extensions/<id>/{Enabled,PrivateAllowed,Source,DisabledSites,Settings/<key>}`; `ExtensionStorage` over the `extension_storage` table with a 1 MiB quota |
  | `scripts/` `contentscriptbuilder`, `contentscriptreader`, `matchpatternglobs`, `profilescripts` | content script source and `QWebEngineScript` per manifest entry; reading `contentScripts[i]`; match patterns as globs; inserting and replacing the scripts in every registered profile, once per event-loop turn |
  | `userscripts/` `userscriptdownload`, `userscriptmetadata`, `userscriptpackage`, `userscriptversion` | fetching a `.user.js` and its `@require`s (5 MiB in total), parsing the `==UserScript==` block, turning it into a temporary `.kondorext`, version normalizing and comparing |
  | `install/` `extensioninstaller`, `extensionloader`, `permissiondescription` | staging under `extensions/.staging-<uuid>`, commit through `<id>.new` / `<id>.old`; loading unpacked Chromium extensions into the persistent profile (`--load-extension`-like, Qt 6.10 `QWebEngineExtensionManager`); the permission lines shown before install |
  | `action/actionitemdisplay` | action items for display: theme icon or empty, native shortcut text from a `keys` setting |
  | `extensionmanager.{h,cpp}`, `extensionmodel`, `extensionqueries`, `extensionconfiguration`, `extensioninstall`, `extensionscripts`, `extensionupdate`, `installedextension.h`, `installresult.h`, `install/extensionuserscripts.cpp` | the `ExtensionManager` singleton: list model, install flow (`pendingInstall` preview, confirm, cancel), enable, remove, configuration, sites, pins, action lists, scripts, tokens, update refusals |

- **Not in this phase:** `catalog/` (`CatalogEntry`, `ExtensionCatalog`, its model and actions, `CatalogUpdater`), `install/packagedownload` and `userscripts/userscriptupdater`: phase 10 (#172). `bridge/` and the page tests: phase 10b (#218).
- **Two calls into phase 10 code**, resolved here (see "Decisions"):
  - `ExtensionManager::updatePackage` uses the static `ExtensionCatalog::isSilentUpdate`. It becomes `kondor.extensions.state.extensionaccess.is_silent_update`, which phase 10's catalog imports.
  - `ExtensionManager::inspectUserScript` downloads with `ExtensionCatalog::instance()->network()`. The Python manager owns its own `QNetworkAccessManager` (an optional constructor argument, as `SearchSuggestions` in phase 7). Phase 10 may make the catalog share it.
- **Tests to port** (every case; UI tests load the staged QML through `kondor_engine`):

  | C++ test | Cases |
  | --- | --- |
  | `manifest/tst_manifestvalidator` | `acceptsTheBaseManifest`, `acceptsKeysSettingOfKeysType`, `reportsTheFirstErrorWithTodaysText` (every row) |
  | `package/tst_extensionpackage` | `validSample`, `invalidFixtures` (4 rows), `tooManyFiles`, `tooLargePackage`, `tooLargeArchive`, `unsafeArchiveEntry`, `localizedStrings`, `permissionLinesForSites`, `permissionLinesForCapabilities` |
  | `state/tst_extensionsettings` | `sanitizesEachSettingType` (rows), `clampsNumbersToMinAndMax` (rows) |
  | `state/tst_extensionstorage` | `valuesKeepTheirJsonType`, `quotaCountsTheOtherKeysOnly`, `removeExtensionKeepsOtherExtensions` |
  | `state/tst_extensionpins` | `pinnedExtensionsKeepPinOrder`, `setPinnedIgnoresDuplicates`, `removeUnpinsExtension`, `pinnedHidesExtensionsNotAllowedInPrivate`, `actionExtensionsAreSortedByName` |
  | `scripts/tst_contentscriptbuilder` | `sourceMatchesTheRecordedScript`, `cssOnlyScriptHasNoJavaScriptBlock` |
  | `scripts/tst_extensionscripts` | `scriptMetadata`, `scriptsForNormalProfile`, `runAtMapping` (3 rows), `privateProfileScripts`, `disabledSiteIsInScript` |
  | `userscripts/tst_userscriptmetadata` | `readsEveryKey`, `mapsRunAt`, `refusesInvalidScripts`, `listsUnsupportedFeaturesInFileOrder`, `takesTheFirstHomepageKey`, `normalizesVersions`, `comparesVersions` (all rows) |
  | `userscripts/tst_userscriptpackage` | `idIsStableForNameAndNamespace`, `manifestLoadsBackWithIncludeAndUserScript`, `includeGlobsDescribeSiteAccess` (4 rows), `installsFileWithRequirement`, `refusesInvalidFile`, `identicalScriptOffersReplace` |
  | `install/tst_extensioninstall` | `inspectFileShowsPreview`, `confirmInstallInstallsTheExtension`, `reloadFindsTheInstall`, `inspectAgainOffersReplacing`, `notAZipShowsError`, `zipWithoutManifestShowsError` |
  | `install/tst_extensionreplace` | `replaceKeepsState`, `packageForAnotherIdIsRefused`, `removeDeletesEverything`, `settingsAreSanitized`, `unchangedSettingsEmitNothing` |
  | `install/tst_extensionloader` | `loadsAnUnpackedExtension`, `contentScriptRuns`, `privateProfilesGetNoExtensions` |
  | `action/tst_actionitemdisplay` | `shortcutShowsCurrentKeysValue`, `itemWithoutKeysSettingHasNoShortcut`, `unparsableKeysValueHasNoShortcut`, `missingThemeIconIsDropped`, `iconPathOrUrlIsDropped` |
  | `tst_extensiondialogs` (QML `ExtensionSettingsDialog.qml`, `InstallExtensionDialog.qml`) | `configureDialogWritesValuesOnAccept`, `restoreDefaultsStaysPending`, `installDialogShowsPendingInstall`, `closingTheInstallDialogDropsThePendingInstall`, `notAnExtensionShowsOnlyTheError` |

  Moved to later phases: `tst_extensionsui` (`ExtensionsPage.qml` uses `ExtensionCatalog`) and `tst_userscriptupdate` (`UserScriptUpdater`, `ExtensionCatalog.checkForUpdates`) go to #172; `tst_userscriptpages` (bridge page harness), `tst_extensionspanel`, `tst_extensionsreloadbar` and `tst_pinnedtoolbar` (they build a `Tab`) go to #218, which waits for #170 and #172.
- **Test data:** `tests/data/extensions/` (`sample/`, `bad-id/`, `dotdot/`, `missing-file/`, `sample-content-script.js`) and `tests/data/extension/` (the unpacked Chromium test extension of `tst_extensionloader`) are copied unchanged to `pytests/data/extensions/` and `pytests/data/extension/` (umbrella item 2).

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior, error texts and edge cases as the C++, with the Python conventions of umbrella item 3. A C++ helper namespace becomes a module of functions; a C++ struct becomes a dataclass with the same fields in snake_case.

### 1. Layout

```
kondor/extensions/
  __init__.py
  qmltypes.py
  extensionmanager.py        ExtensionManager (QAbstractListModel): signals, properties, slots
  extensionmodel.py          roles: enum, names, readers
  extensionqueries.py        action lists, pins, tokens, access
  extensionconfiguration.py  settings values, configuration, sites, originOf
  extensioninstall.py        previews, staging, confirm/cancel, user script staging
  extensionscripts.py        scripts_for, script_source
  extensionupdate.py         install_package, update_package refusals
  installedextension.py      InstalledExtension and the entry list
  installresult.py           InstallResult
  action/      actionitemdisplay.py
  install/     extensioninstaller.py, extensionloader.py, permissiondescription.py
  manifest/    localizedmanifest.py, manifesticon.py, manifestsections.py, manifestvalidator.py, stringlistfield.py, jsonvalue.py
  package/     extensionpackage.py, packagearchive.py, packagefile.py, packagelimits.py, packagepath.py, packagesuffix.py
  scripts/     contentscriptbuilder.py, contentscriptreader.py, matchpatternglobs.py, profilescripts.py
  state/       extensionaccess.py, extensionpins.py, extensionsettings.py, extensionstate.py, extensionstorage.py
  userscripts/ userscriptdownload.py, userscriptmetadata.py, userscriptpackage.py, userscriptversion.py
```

Every sub-folder has an empty `__init__.py`. `install/extensionuserscripts.cpp` holds `ExtensionManager` methods only; they go to `extensioninstall.py`. Further splits for the size limits are allowed when these modules keep their names. Phase 10 adds `catalog/`, `install/packagedownload.py` and `userscripts/userscriptupdater.py`; phase 10b adds `bridge/`.

### 2. `ExtensionManager` across modules

The C++ class is spread over eight `.cpp` files. In Python:

- **`extensionmanager.py`** holds the one `QAbstractListModel` subclass: its signals, the three properties, every slot and the snake_case API of item 3, the model overrides (`rowCount`, `data`, `roleNames`), `instance()` and the row bookkeeping (`beginInsertRows`, `dataChanged`, …). Each method is a few lines that delegate.
- **The other root modules** hold the logic as module functions (or one small helper class each) that take the manager's state as arguments: the entry list, the `ExtensionState`, the locale. They never emit signals; the manager does.
- **Composition, not mixins:** do not spread `Slot`s or `Signal`s over mixin classes.
- **`InstalledExtension`** is a dataclass (`package`, `enabled = True`, `private_allowed = False`, `source = ""`, `token = ""`, `update_available = False`, `update_needs_review = False`). `installedextension.py` also holds the list helpers `index_of(entries, id)` and `find(entries, id)`.
- **`InstallResult`** is a dataclass (`is_installed`, `needs_review`, `error`) with `is_refused()`.

### 3. QML names and types

- **Properties:** `count` (`int`, notify `countChanged`), `revision` (`int`, notify `revisionChanged`), `pendingInstall` (`"QVariantMap"`, notify `pendingInstallChanged`).
- **Signals:** `countChanged`, `revisionChanged`, `pendingInstallChanged`, `settingsChanged(str)`, `manageRequested`, `extensionRemoved(str)`.
- **Slots:**
  - `inspectFile(str)`, `inspectUserScript(QUrl)`, `reviewUserScriptUpdate(str)`, `isUserScriptUrl(QUrl) -> bool`;
  - `confirmInstall()`, `cancelInstall()`;
  - `isInstalled(str) -> bool`, `installedVersion(str) -> str`, `setEnabled(str, bool)`, `remove(str)`, `setUpdateInfo(str, bool, bool)`;
  - `configurationFor(str) -> "QVariantMap"`, `applyConfiguration(str, "QVariantMap")`, `settingValues(str) -> "QVariantMap"`;
  - `actionExtensions(bool) -> "QVariantList"`, `hasActionExtensions(bool) -> bool`, `pinnedActionExtensions(bool) -> "QVariantList"`, `isPinned(str) -> bool`, `setPinned(str, bool)`;
  - `siteEnabled(str, QUrl) -> bool`, `setSiteEnabled(str, QUrl, bool)`, `originOf(QUrl) -> str`.

  `isUserScriptUrl` and `originOf` are static in C++. In Python they are slots that call the module functions `is_user_script_url(url)` and `origin_of(url)`, which other Python code uses directly.
- **Roles** (`IntEnum` from `Qt.ItemDataRole.UserRole + 1`, same order and names as C++): `id`, `name`, `description`, `version`, `author`, `homepage`, `iconSource`, `enabled`, `privateAllowed`, `permissions` (the permission lines), `hasSettings`, `hasAction`, `source`, `updateAvailable`, `updateNeedsReview`. `name` and `description` use the manager's locale.
- **Snake case API** for the code QML does not see (phases 10, 10b and 11 call it): `extensions_directory()` (static), `set_locale`, `reload`, `user_script_ids`, `user_script_of`, `prepare_install(file)`, `open_package_file(path)`, `is_package_file(path)` (static), `install_package(file, expected_id)`, `update_package(file, expected_id)`, `source`, `installed_access`, `register_profile`, `scripts_for(private_profile)`, `script_source(id, index, private_profile)`, `rebuild_scripts`, `check_token`, `is_active`, `has_permission`, `display_name`.
- **Instance:** `ExtensionManager(network: QNetworkAccessManager | None = None)`. It creates the `ExtensionState`, the `ProfileScripts` (parented to it) and the network manager when none is given (parented to it), then calls `reload()`, as the C++ constructor does. `instance()` creates it on first use. Importing any module must not create it, any profile or any network manager (`check-qml-api.py` imports `qmltypes.py` without a `QCoreApplication`).
- **No destructor port:** `~ExtensionManager` discards the staged package, but the C++ singleton is never deleted, so the destructor never runs. Python adds no `aboutToQuit` hook for it.

### 4. JSON with Qt semantics

Manifests, the user script manifest, storage values and the content script configuration go through `QJsonDocument`, as in C++, so the accepted input and the written bytes stay Qt's (phase 7 decision). PySide6 6.11.2 turns a `QJsonObject` into a `dict` and back. `manifest/jsonvalue.py` holds the `QJsonValue` rules the validator relies on, over the resulting Python values:

- **Undefined** is a missing key, **null** is `None`.
- **`isDouble`** is an `int` or `float` that is not a `bool`; `toInt()` is the value when it is integral, else 0.
- **`toString()`**, **`toArray()`**, **`toObject()`** and **`toBool()`** give `""`, `[]`, `{}` and `False` for a value of another type.

`readStringList` keeps its C++ rules: missing or `null` → empty (or `required`), a list → each element must be a non-empty string (`[i]: must be a non-empty string`), anything else → `must be a list of strings`.

### 5. Packages (`package/`)

- **`ExtensionPackage.load(directory) -> tuple[ExtensionPackage, str]`** (the package and the error, `""` when valid; the C++ `QString *error` out-parameter). `directory()` is `QDir(directory).absolutePath()`. Order: the size limits on the directory, then `manifest.json` (`manifest.json: file not found`, `manifest.json: invalid JSON: <reason>` with Qt's `errorString()` or `not an object`), then `ManifestValidator`.
- **`measureDirectory`** uses `QDirIterator(directory, QDir.Filter.Files | QDir.Filter.NoSymLinks, QDirIterator.IteratorFlag.Subdirectories)`, so hidden files and links are not counted, as in C++.
- **Accessors**, with the C++ names in snake_case: `id`, `version`, `author`, `homepage`, `name(locale)`, `description(locale)`, `permissions`, `has_permission`, `content_scripts`, `all_matches`, `all_includes` (unique, in order), `access()`, `user_script()`, `icon_source`, `settings_schema(locale)`, `setting_defaults()`, `has_settings()`, `has_action()`, `action_items(locale)`, `action_site_toggle()`, `read_file(relative_path)` (empty `bytes` for an invalid package or an unsafe path). Statics: `is_valid_id`, `localized`, `permission_entries`, `permission_lines`, `is_subset`, `MAX_PACKAGE_BYTES = 5 * 1024 * 1024`, `MAX_PACKAGE_FILES = 200`.
- **`ExtensionContentScript`** is a dataclass: `matches`, `include`, `exclude`, `js`, `css` (lists), `run_at = "document-idle"`, `all_frames = False`.
- **`packagearchive.unpack(zip_path, directory) -> str`** (empty on success) with `zipfile`:
  1. Open it. `zipfile.BadZipFile` or `OSError` → `The file is not a valid ZIP archive`.
  2. List the file entries in archive order, skipping directory entries. Each name must pass `is_safe_relative_path` (else `Unsafe file name in the package: <name>`). Add `ZipInfo.file_size` and one file to the running size, and stop at the first `packageLimitError`. Nothing is written before the whole listing passes.
  3. `QDir().mkpath(directory)` (else `Cannot create <directory>`).
  4. Write every entry that is not a symbolic link (Unix mode `S_IFLNK` in `external_attr >> 16`), creating parent folders. A failed write, or a `BadZipFile` raised while reading (a bad CRC), gives `Cannot write <name>`.

  Error texts are translated with `QCoreApplication.translate("ExtensionPackage", …)`, as in C++.
- **`packagepath`**: `is_safe_relative_path` (no leading `/`, no `\`, not `QDir.isAbsolutePath`, no `:`, no empty or `..` part) and `package_file_error(directory, path, where)` (`invalid path`, or `file not found` when it is not a regular file or is a link). **`packagesuffix.has_package_suffix`**: `.kondorext`, case-insensitive. **`PackageFile`** (`zip_path`, `source`, `label = ""`, `is_temporary = False`) and **`StagedPackage`** (`directory`, `package`, `file`) are dataclasses.

### 6. Manifest (`manifest/`)

- **`ManifestValidator(directory).validate(manifest) -> ValidManifest | None`**, with `error()`. Same checks in the same order and same texts (`kondor`, required and optional strings, `id`, `version`, `permissions` limited to `tabs`, `downloads` and `notifications`, `contentScripts` through `ContentScriptReader`, `settings`, `action`, `icon`). The first failing check sets the error.
- **Regular expressions** go through `QRegularExpression` with the C++ patterns (`^[a-z0-9][a-z0-9-]{1,47}$`, `^\d+\.\d+\.\d+$`), so `\d` and the anchors match what C++ accepts.
- **`localizedmanifest`:**
  - `localized(object, key, locale)` tries `key[<locale>]`, then `key[<language>]`, then `key`. An empty locale means `QLocale.system().name()`.
  - `settings_schema`, `setting_defaults` and `action_items` return the same maps. A setting map is the setting object plus the localized `label`, and the localized `choices` when it has any.
- **`manifesticon.resolve_manifest_icon(directory, icon) -> tuple[str | None, str]`** (the icon source and the error):
  - empty → `preferences-plugin`;
  - not `.svg` / `.png` → the name as is;
  - else the file must pass `package_file_error`, and a PNG must load with `QImage` at 64 × 64 px or more;
  - the source is then `QUrl.fromLocalFile(<absolute path>).toString()`.
- **`manifestsections`:**
  - the setting checks: unique `key`, a known `type` (`bool`, `number`, `string`, `text`, `choice`, `color`, `keys`), a `label`, and `choices` for a `choice`;
  - the action item checks: a unique `id` with a `title`, and a `keysSetting` that names a `keys` setting;
  - `manifest_error(message)` adds the `manifest.json: ` prefix.

### 7. State (`state/`)

- **`ExtensionAccess`** is a dataclass (`matches`, `permissions`, `includes`). `is_silent_update(update, installed)` is `ExtensionPackage.is_subset` on all three lists (the C++ `ExtensionCatalog::isSilentUpdate`).
- **`ExtensionState`** has its own `QSettings("KDE", "Kondor")`, keys `Extensions/<id>/<name>`:
  - defaults: `Enabled` true, `PrivateAllowed` false, `Source` `file`;
  - `DisabledSites` is a string list, removed when it is empty;
  - settings live under `Settings/<key>`;
  - `remove_extension` removes the `Extensions/<id>` group.

  Booleans and lists read back as `QSettings` stores them: read with `type=bool` / the string-list conversion `Settings` already uses, so a value written by the C++ app (`true`, a single-item list) reads the same.
- **`extensionsettings.sanitize_setting(setting, value)`:**
  - `bool`: a `bool`, or the text `true` / `false`, else the default's truth;
  - `number`: anything that `QVariant::toDouble` accepts (an `int`, a `float` that is not a `bool`, or a numeric string), clamped to `min` / `max`, else the default;
  - `choice`: a value equal to one of the `choices[].value`, else the default;
  - every other type: a `str`, else the default.

  Port the `_data` rows exactly. Where a row shows a `QVariant` conversion Python does not have, the test documents the chosen mapping.
- **`extensionstorage`** keeps the SQL text and the semantics:
  - values are stored as the compact JSON of a one-element array;
  - the quota is 1 MiB over `LENGTH(CAST(key AS BLOB)) + LENGTH(CAST(value AS BLOB))` of the other keys, plus the UTF-8 sizes of the new key and value;
  - the errors `Storage is not available` and `The extension's storage is full (limit: 1 MiB)` use the context `ExtensionManager`;
  - `StorageWrite` is a dataclass (`is_written`, `error`);
  - every query goes through `kondor.core.database.sql`.
- **`extensionpins`:** `is_pinned`, `set_pinned` (append once, or remove every copy) and `only_pinned(entries)` (in pin order) over `Settings.instance().pinnedExtensions`.

### 8. Scripts (`scripts/`)

- **`contentscriptbuilder`:**
  - `content_script_source(context)` must be **byte-identical** to the C++ output: the `==UserScript==` block (`@match` lines, or `@include` globs when `include` is not empty, then `@exclude`, `@run-at`), then the body (`const __cfg = <compact JSON>`, the runtime from `:/scripts/extensionruntime.js`, the site check, the style injector, the wrapped `js` files).
  - The configuration object goes through `QJsonDocument`, with sorted keys, as `QJsonObject` writes them. The `sample-content-script.js` fixture checks it.
  - A missing runtime resource warns once (`Extension runtime script not found: extensions are off`) and counts as empty.
- **`content_script(context) -> QWebEngineScript`:** name `kondor-ext:<id>:<index>`, `ApplicationWorld`, `runsOnSubFrames` = `all_frames`. `document-start` → `DocumentCreation`, `document-end` → `DocumentReady`, anything else → `Deferred`. `ContentScriptContext` is a dataclass with the C++ fields.
- **`contentscriptreader`** and **`matchpatternglobs`** follow the C++ (`<all_urls>` → `*`; `*` scheme → `http` and `https`; `*.host` → also `host`; every host → also `host:*`).
- **`ProfileScripts(manager)`** (a `QObject` parented to the manager):
  - `register_profile(profile)` ignores `None`, remembers the profile and applies the scripts.
  - Applying gets the collection with `pagescripts.user_scripts(profile)`, removes the scripts it inserted before, then inserts `manager.scripts_for(profile.isOffTheRecord())`, each through `QMetaObject.invokeMethod(collection, "remove" / "insert", Q_ARG(QWebEngineScript, script))`.
  - `rebuild_once_after_several_changes()` queues one `rebuild_all` (`QTimer.singleShot(0, …)`), however many changes arrive in the same turn.
  - Profiles are keyed by identity and dropped on `destroyed`, so a dead wrapper is never used.

### 9. User scripts (`userscripts/`)

- **`userscriptmetadata.parse_user_script_metadata(source) -> tuple[UserScriptMetadata | None, str]`:**
  - It uses the C++ regular expressions through `QRegularExpression`, and the same first-value-wins string fields and appended list fields (`exclude-match` → `excludes`).
  - Homepage keys (`homepageURL`, `homepage`, `website`) keep the first one.
  - `run-at` maps to `document-start`, `document-end` (also `document-body`) or `document-idle`; `noframes` sets `all_frames` false; `resource` sets `uses_resource`.
  - The error texts use the context `UserScript`.
  - `unsupported_features()` keeps file order and appends `@resource` last; `wants_notifications()` is unchanged.
- **`userscriptversion`:** `normalized_user_script_version` and `is_newer_user_script_version`, with the C++ part rules (leading digits as a number, then the rest compared like `QString::compare`, which is ordinal).
- **`userscriptpackage`:**
  - `user_script_id` is `user-` plus the first 16 hex digits of the SHA-256 of `namespace\nname`.
  - `user_script_manifest(source)` builds the same object: `kondor` 1, the normalized version, icon `text-x-javascript`, `notifications` only for `GM.notification` / `GM_notification`, one content script with `gm.js`, `require-<n>.js` and `script.js`, the `userScript` section, and the optional fields only when they are not empty.
  - `user_script_download_url` is unchanged.
  - `write_user_script_package(source) -> tuple[str | None, str]` writes the zip with `zipfile` (deflated) into a `QTemporaryFile(QDir.tempPath() + "/kondor-userscript-XXXXXX.kondorext")` that is not auto-removed. The `manifest.json` comes from `QJsonDocument(...).toJson()` (indented, as `KZip::writeFile` gets it). `gm.js` is the `__userScript` declaration plus `:/scripts/usergm.js`; `kondorVersion` is `QCoreApplication.applicationVersion()`. On failure the file is removed and the error is `Cannot create the package`.
- **`UserScriptDownload(network, parent)`** (a `QObject`) with `start(url)`, `start_metadata_only(url)` and `finished = Signal(object, str)` (the `UserScriptSource` dataclass and the error):
  - only `http`, `https` and local files are fetched (`Unsupported address: <url>`);
  - requests use `NoLessSafeRedirectPolicy`;
  - the replies of the script and its `@require`s (resolved against the install URL, fetched in order) share one 5 MiB budget, and the reply is aborted on `downloadProgress` above it (`The script is larger than 5 MiB`);
  - on a network error the error is the reply's `errorString()`;
  - after `finished` it calls `deleteLater()`.

  Module functions `is_web_url` and `is_fetchable_user_script_url`.

### 10. Install (`install/`) and action items

- **`ExtensionInstaller(extensions_directory)`** (a plain class, as in C++):
  - `stage(file) -> tuple[StagedPackage | None, str]` creates the folder (`Cannot create <dir>`), unpacks into `.staging-<uuid without braces>` and loads it, and removes the staging folder on failure.
  - `commit(staged) -> str` removes any `<id>.new` / `<id>.old` first, moves staging → `.new`, existing → `.old`, `.new` → final, and on failure puts `.old` back. The errors are `Cannot install into <dir>` and `Cannot replace <dir>`, with the context `ExtensionManager`.
  - `discard(staged)` removes the staging folder, and the zip when it is temporary.

  Renames use `QDir().rename`, as in C++.
- **`ExtensionLoader(parent)`** (a `QObject`) with `loadFinished = Signal(str, bool)`, `is_supported()` and `load(profile, directories)`:
  - an empty list does nothing;
  - a `None` or off-the-record profile warns `Extensions are never loaded into private profiles`;
  - a profile without `extensionManager()` warns `Extensions are not supported by this Qt WebEngine build`;
  - otherwise it connects `loadFinished`, maps each info back to the requested directory through `QDir.cleanPath`, enables a loaded extension that is not enabled, logs `Extension loaded: …` / `Extension failed: …` and emits `loadFinished`.

  It logs with a `QLoggingCategory("kondor.extensions")`. `is_supported()` is true when PySide6 exposes `QWebEngineExtensionManager` (6.11.2 does).
- **`permissiondescription`:** `parse_pattern`, `permission_entries` and `permission_lines`, with the same site summary:
  - all sites, or up to three hosts plus `%1 and %n more`, translated with the plural form: `QCoreApplication.translate("ExtensionPackage", "%1 and %n more", None, n)`;
  - then the `tabs`, `downloads` and `notifications` lines with their icons.
- **`actionitemdisplay.for_display(items, setting_values)`:**
  - the icon stays only when it is a plain name (`^[A-Za-z0-9_.-]+$`) and `QIcon.hasThemeIcon` finds it;
  - the shortcut is the `keysSetting` value parsed with `QKeySequence.fromString(…, PortableText)` and shown with `NativeText`, or `""` when it is empty or `Qt.Key_unknown`.

### 11. Manager behavior

Port each C++ method with the same order of effects, signals and `revision` bumps:

- **`reload()`:**
  - scans `extensions_directory()` folders by name;
  - deletes the leftovers of an interrupted install (`*.new`, `*.old`, names that start with `.`);
  - loads each folder whose package is valid and whose id equals the folder name, else warns `Extension <name> ignored: <reason>` (`directory name differs from id` when the reason is empty);
  - builds each entry from `ExtensionState`, with a new UUID token;
  - resets the model, emits `countChanged` and calls `changed()` (`revision + 1`, `revisionChanged`, `rebuild_scripts()`).
- **Install flow** (`extensioninstall.py`):
  - `inspectFile` strips a `file:` URL and sends a `.user.js` to `inspectUserScript`;
  - `prepare_install` discards the previous staging, then stages and sets the preview or the failed preview, with the same map keys (`valid`, `fileName`, `isUserScript`, `error`, `id`, `name`, `version`, `author`, `iconSource`, `permissions`, `fromFile`, `installedVersion`, `unsupportedFeatures`);
  - `confirmInstall`, `cancelInstall` and `open_package_file` (which also emits `manageRequested`);
  - `add_installed` reloads the package from its final folder, stores its source, puts the entry (replacing a row emits `dataChanged` and `settingsChanged`, appending emits `countChanged`) and calls `changed()`.
- **User scripts:**
  - `inspectUserScript(url)` starts a `UserScriptDownload` on the manager's network and emits `manageRequested`;
  - on `finished` the manager writes the package and calls `prepare_install(PackageFile(path, "userscript", <file name of the install URL>, True))`, or sets a failed preview;
  - `reviewUserScriptUpdate(id)` inspects `user_script_download_url(user_script_of(id))`;
  - `user_script_ids()` lists the ids whose source is `userscript`.
- **`install_package` / `update_package`** (`extensionupdate.py`):
  - both refuse a package for another id (`The package is for “%1”, not “%2”`, context `ExtensionManager`);
  - `update_package` also refuses, with `needs_review` set, a package that asks for more access than the installed one (`not is_silent_update`): `The package asks for more permissions than the installed version`;
  - after a refusal or a failed install the staging is discarded.
- **Configuration** (`extensionconfiguration.py`):
  - `settingValues` is the defaults overlaid with the sanitized stored values;
  - `configurationFor` returns `name`, `iconSource`, `privateAllowed`, `disabledSites` and `settings` (the schema with `value`);
  - `applyConfiguration` stores the settings (sanitized; it reports a change only when a value differs), `privateAllowed` and `disabledSites`, syncs, emits `dataChanged` for `privateAllowed`, calls `changed()` when anything changed and emits `settingsChanged(id)` when a setting changed;
  - `originOf` is `scheme://host` lower-cased, plus `:port` when there is one, for `http` / `https` with a host only;
  - `siteEnabled` and `setSiteEnabled` follow the C++, and `setSiteEnabled` calls `changed()`.
- **Entries:**
  - `setEnabled` stores, syncs, emits `dataChanged` for `enabled` and calls `changed()`;
  - `remove` removes the row, the folder, the state, the storage and the pin, emits `extensionRemoved` and calls `changed()`;
  - `setUpdateInfo` emits `dataChanged` for the two update roles only when a value changes.
- **Queries** (`extensionqueries.py`):
  - `actionExtensions(isPrivate)` lists the enabled extensions with an action (in private only when allowed) as `{id, name, iconSource, siteToggle (false in private), items}`, with `items` from `for_display`, sorted by name with `QString::localeAwareCompare` semantics (`QCollator` for the current locale);
  - `pinnedActionExtensions` keeps pin order;
  - `check_token`, `is_active`, `has_permission` and `display_name` (the id when it is unknown) follow the C++.
- **Scripts** (`extensionscripts.py`):
  - `scripts_for(private_profile)` covers every enabled entry (in private only when allowed) and every content script, with the entry's token, the locale, the setting values and the disabled sites;
  - `script_source` returns `""` for an unknown id or index.
- **Privacy:** private profiles get only the scripts of extensions allowed in private, `ExtensionLoader` never loads into an off-the-record profile, and nothing here records what a private tab visits (umbrella item 3).

### 12. `qmltypes.py`

```python
QML_TYPES = (QmlType(ExtensionManager, "ExtensionManager", QmlKind.SINGLETON),)
```

with `register_types()` as in the other features. `pytests/core/test_singletons.py` finds it through `kondor_types` with no change.

### 13. Tests

Each C++ case becomes a test with the same intent (umbrella item 9). Data-driven cases become `pytest.mark.parametrize` with the same rows and ids. Test functions have at most 20 lines. **No test talks to the internet:** user script downloads use a local HTTP server or `file:` URLs.

```
pytests/extensions/
  __init__.py
  extensionsharness.py        data_dir, write_file, zip_directory, make_variant, pack_variant,
                              sample_package, install_sample, install_named, install_plain,
                              apply_settings, allow_in_private_windows, remove_every_extension
  pageserver.py               a QTcpServer that serves fixed bodies (the C++ pageserver.h)
  conftest.py                 fixtures: work directory, a manager reset after each test
  test_extensiondialogs.py
  action/      test_actionitemdisplay.py
  install/     test_extensioninstall.py, test_extensionreplace.py, test_extensionloader.py, test_extensioninstaller.py
  manifest/    test_manifestvalidator.py
  package/     test_extensionpackage.py, test_packagearchive.py
  scripts/     test_contentscriptbuilder.py, test_extensionscripts.py, test_profilescripts.py
  state/       test_extensionpins.py, test_extensionsettings.py, test_extensionstorage.py, test_extensionstate.py
  userscripts/ test_userscriptmetadata.py, test_userscriptpackage.py, test_userscriptdownload.py
```

- **The harness** mirrors `extensionsharness.h`, with `zipfile` instead of `KZip`. `remove_every_extension` cancels the pending install, removes every row, resets the locale to `en` and clears `Settings.pinnedExtensions`. It runs after every test that installs.
- **New tests** for code the C++ tests only reach indirectly:
  - **`test_packagearchive.py`:**
    - `test_rejects_an_absolute_entry`;
    - `test_skips_symbolic_links` (a zip entry with `S_IFLNK` mode is counted and not written);
    - `test_writes_nested_files`;
    - `test_not_a_zip_is_refused`.
  - **`test_extensioninstaller.py`:**
    - `test_commit_replaces_the_existing_folder` (no `.new` / `.old` left);
    - `test_failed_stage_leaves_no_staging_folder`;
    - `test_discard_removes_a_temporary_zip`.
  - **`test_extensionstate.py`:**
    - `test_defaults` (enabled, not private, source `file`);
    - `test_empty_disabled_sites_remove_the_key`;
    - `test_reads_values_written_by_qsettings_as_cpp_does`: write `true` and a one-item list through a fresh `QSettings("KDE", "Kondor")`, then read them back as `bool` and `list`.
  - **`test_profilescripts.py`** (`pytest.mark.no_qt_log`, as the phase 7 profile tests):
    - `test_registered_profile_gets_the_scripts`: install the sample, register an off-the-record profile with `allow_in_private_windows`, and the collection has `kondor-ext:sample:0`;
    - `test_rebuild_replaces_instead_of_adding` (two changes in one turn, one script after `qtbot.wait`);
    - `test_private_profile_skips_extensions_not_allowed`.
  - **`test_userscriptdownload.py`** (with `pageserver.py`):
    - `test_fetches_the_script_and_its_requirements_in_order`;
    - `test_metadata_only_skips_requirements`;
    - `test_unsupported_scheme_fails` (`ftp:`);
    - `test_oversized_script_fails`: a body above 5 MiB gives `The script is larger than 5 MiB`.
- **`test_extensionloader.py`** keeps the three C++ cases with `pytests/data/extension/` and a `WebEngineView` from inline QML. It is marked `no_qt_log` and is skipped (with the reason) only when `ExtensionLoader.is_supported()` is false.
- **`test_extensiondialogs.py`** loads `ExtensionSettingsDialog` and `InstallExtensionDialog` from inline QML in `kondor_engine`, as the C++ harness does, and drives them with `QMetaObject.invokeMethod`. If one of them needs a type that is not ported yet, the test moves to the phase that ports that type (umbrella item 9). Ask (`question`) first.

### 14. API check result

After this phase, `python3 scripts/check-qml-api.py` reports **one more** class checked (`ExtensionManager`) and one fewer not ported than on the PR's base, and exits 0.

## Acceptance criteria

- [ ] `kondor/extensions/` has the modules of item 1, and its `qmltypes.py` registers `ExtensionManager` as a singleton.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports one more class checked than on the base, with no problems.
- [ ] Every C++ case of the fourteen test files in "Context" has its pytest twin, and the new tests of item 13 exist and pass with `scripts/run-pytests.sh`. No test reaches the internet.
- [ ] `content_script_source` reproduces `pytests/data/extensions/sample-content-script.js` byte for byte (test).
- [ ] Every manifest and package error text of the C++ tests is reproduced exactly (tests).
- [ ] An extension installed by the C++ app is listed, enabled, configured and runs in the Python manager, and one installed by the Python manager loads in the C++ app (manual test).
- [ ] Private profiles get only the scripts of extensions allowed in private, and `ExtensionLoader` never loads into them (tests).
- [ ] The `build` job is green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt` or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md) shared by every step. The snippet is a short Python script that creates a `QApplication` after `QtWebEngineQuick.initialize()`, sets organization `KDE` and application `Kondor`, registers `build/python/kondor.rcc` and calls every ported `register_types()`.

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && scripts/run-pytests.sh && python3 scripts/check-qml-api.py`: all pass, and the last reports one more class than `main`.
2. **C++ → Python:**
   1. Run the C++ app (built from `main`) on the isolated profile and install the sample package (`python3 -c` with `zipfile` over `tests/data/extensions/sample`) with Settings → Extensions → Install from File….
   2. Change its "greeting" setting, turn it off on `https://kde.org`, allow it in private windows, pin it, and quit.
   3. With the snippet, `ExtensionManager.instance()` has one row `sample`. `configurationFor("sample")` shows the new greeting, `privateAllowed` true and `disabledSites` `["https://kde.org"]`. `isPinned("sample")` is true, and `scripts_for(True)` has `kondor-ext:sample:0`.
3. **Python → C++:**
   1. With the snippet, `install_package(PackageFile(<zip of a variant with id "second">, "file"), "second")` returns `is_installed`.
   2. `applyConfiguration("second", {"settings": {"greeting": "ola"}})`.
   3. Start the C++ app: Settings → Extensions lists both, and "second" shows `ola` in its settings dialog.
4. **User script:**
   1. Serve a `.user.js` with one `@require` from `python3 -m http.server` in a temp folder, and call `inspectUserScript` on its `http://127.0.0.1:<port>/…` URL.
   2. `pendingInstall` becomes valid with `isUserScript` true. `confirmInstall()` installs a `user-…` extension with `gm.js`, `require-1.js` and `script.js`.
   3. The C++ app lists it after a restart.
5. **Leftovers:** create `extensions/sample.new` and `extensions/.staging-x` by hand. `reload()` deletes both and keeps `sample`.
6. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- `catalog/`, `install/packagedownload`, `userscripts/userscriptupdater` and the tests that need them (`tst_extensionsui`, `tst_userscriptupdate`): phase 10 (#172).
- `bridge/` and the tests that need a `Tab` or the page harness (`tst_userscriptpages`, `tst_extensionspanel`, `tst_extensionsreloadbar`, `tst_pinnedtoolbar`): phase 10b (#218).
- Calling `register_types()` from an app entry point, `register_profile` wiring and `ExtensionLoader` command-line wiring: phase 11 (#173).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests or the workflows.
- Changes to `kondor/core/`, `kondor/browser/`, the other ported features, `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker, unless a phase-9 file shows a bug in them. In that case, ask first (`question`).
- New behavior: no new manifest keys, permissions, limits, setting types or user script grants; no change to the package format, the state keys or the storage quota.
- Translating Python strings, or running `pyside6-lupdate` (phase 12). Python keeps the C++ contexts (`ExtensionPackage`, `ExtensionManager`, `UserScript`).

## Dependencies

#164 (core), merged. Umbrella #162. It needs nothing from `browser/` except the merged phase 7 helper `pagescripts.user_scripts`, which is already on `main`. It may run in parallel with #170.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| Where does the phase 9 / phase 10 line run? | Phase 9 ports the whole `ExtensionManager`, with its model, queries, configuration, install and update refusals, so `check-qml-api.py` can pair the full class. It also ports what the manager needs: `action/actionitemdisplay` and `is_silent_update`. Phase 10 (#172) keeps `catalog/`, `install/packagedownload` and `userscripts/userscriptupdater`. This replaces the rougher split in the #172 issue body ("the model and the queries"). |
| `ExtensionCatalog::isSilentUpdate` is needed before the catalog exists. | It moves to `state/extensionaccess.py` as `is_silent_update(update, installed)`, next to `ExtensionAccess`. Phase 10's `ExtensionCatalog` imports it instead of defining its own. |
| `inspectUserScript` downloads with the catalog's network manager. | The Python manager takes an optional `QNetworkAccessManager` and creates its own when none is given. The catalog's manager has no custom cache, cookie jar or proxy, so a second default one changes nothing the user sees. Phase 10 may share one. |
| How is a C++ class spread over eight `.cpp` files split in Python? | One `QAbstractListModel` subclass in `extensionmanager.py` with thin slots, plus module functions in the files with the C++ names (composition). Mixins that carry `Slot`s or `Signal`s are not used: PySide6 only registers them reliably on the `QObject` subclass itself. |
| `~ExtensionManager` discards the staged package. | Not ported: the C++ singleton is created with `new` and never deleted, so the destructor never runs. |
| `zipfile` versus KArchive (umbrella item 7). | The whole listing is checked before anything is written. Entries are checked in archive order with the declared `file_size`, links are counted but not written, and the C++ error texts are kept. |
| Which UI tests belong to this phase? | Only `tst_extensiondialogs`, whose dialogs need just `ExtensionManager` and `Settings`. `ExtensionsPage` needs `ExtensionCatalog` (#172). The panel, reload bar and pinned toolbar tests build a `Tab`, so they go to #218, which waits for #170 and #172. |
