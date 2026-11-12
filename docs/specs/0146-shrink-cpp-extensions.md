# Refactor: shrink C++ in the extensions folder (#146)

> **Issue:** [#146](https://github.com/lukasborges/kondor/issues/146) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first, especially "Code quality". This file is the source of truth for the issue; only the architect edits it.

## Objective

Clear every C++ entry of `src/extensions/` in `scripts/code-quality-baseline.json` (69 entries), so
that the folder follows AGENTS.md → "Code quality". **Kondor behaves exactly as before.** The
manifest format and its error messages, the package limits, the install directory layout
(`<id>`, `.new`, `.old`, `.staging-<uuid>`), the `Kondor.conf` keys under `Extensions/<id>/`, the
`extension_storage` table, the generated content scripts, the catalog format and cache file, and
every user-visible string stay the same.

`src/extensions/channel.js` and `src/extensions/extensionruntime.js` belong to #139. The only change
allowed in them is the one call of `api.request` in `extensionruntime.js` (§4).

## Context

- **Baseline entries in scope** (`origin/main` after #145):

  | File | Entries |
  | --- | --- |
  | `extensionmanager.{h,cpp}` | **files:** `.cpp` 931, `.h` 209. **functions:** `scriptSource` 62, `commit` 53, `storageSet` 38 (4 parameters), `applyConfiguration` 32 (4 parameters), `installPackage` 26 (5 parameters), `reload` 25, `sanitize` 25, `data` 23, `stage` 22 (4 parameters), `remove` 21, `confirmInstall` 19, `configurationFor` 17, `roleNames` 17, `prepareInstall` 16 (4 parameters), `setSiteEnabled` 16, `previewOf` 14, `actionExtensions` 13, `buildScript` 13, `settingValues` 13, `storageGet` 13, `rebuildScripts` 12, `storageKeys` 11. **comments:** `.h` 42, `.cpp` 20 |
  | `extensionpackage.{h,cpp}` | **files:** `.cpp` 607. **functions:** `load` 228 (nesting 3), `unpack` 76 (nesting 3), `permissionEntries` 35 (nesting 3), `settingsSchema` 21 (nesting 3), `actionItems` 13, `parsePattern` 13, `readStringList` 22 (6 parameters). **comments:** `.h` 20, `.cpp` 12 |
  | `extensioncatalog.{h,cpp}` | **files:** `.cpp` 444. **functions:** `fetchPackage` 61, `loadCatalog` 46, `applyUpdates` 41 (nesting 3), `refresh` 33, `ExtensionCatalog` 17, `checkForUpdates` 17, `data` 17, `startAutoUpdate` 16 (nesting 3), `install` 15, `isSilentUpdate` (4 parameters). **comments:** `.h` 22, `.cpp` 8 |
  | `extensionbridge.{h,cpp}` | **functions:** `ExtensionBridge::request` 99 (4 parameters), `ExtensionPageApi::request` (4 parameters). **comments:** `.h` 8, `.cpp` 3 |
  | `extensionloader.{h,cpp}` | **functions:** `load` 48. **comments:** `.h` 12, `.cpp` 4 |

- **Why the code is long:** `ExtensionManager` is a list model, an installer, a settings store, a
  content-script generator, a profile script registrar and a key-value storage in one class;
  `ExtensionPackage::load` validates the whole manifest in one function; `ExtensionBridge::request`
  is one `if` chain over every page API method; `fetchPackage` and `applyUpdates` nest lambdas.
- **Tests today:** `tests/extensions/tst_extensions.cpp` (manifest fixtures, limits, unsafe
  archives, localization, permission lines, script metadata, `runAt`, private profiles, install,
  replace, remove, settings sanitizing, storage quota, the bridge, the catalog and updates, the
  QML pages, a content script in a real page) and `tests/extensions/tst_extensionloader.cpp`.
  `tst_extensions.cpp` is over the file limit and in the baseline: **do not add test functions to
  it** (the file would grow past its baseline). New tests go in new files (§5).

## Design / behavior

Limits for every new or changed function: body ≤ 10 lines, ≤ 3 parameters, nesting ≤ 2. Every file
≤ 200 lines. No comments (AGENTS.md → "Names instead of comments"): every "why" comment of today
becomes a name (for example `removeInterruptedInstalls()`, `enableSoContentScriptsRun()`,
`rebuildOnceAfterSeveralChanges()`, `refuseArchiveBeforeWriting()`). The **file, class, struct and
function names below are binding**. How the rest is split inside them is up to you, as long as the
limits hold. If a listed file still goes over 200 lines, split it again in the same folder and say so
in the PR. Never merge two rows into one file.

**Translations keep their context.** Every `tr()` string keeps today's context (`ExtensionPackage`,
`ExtensionManager` or `ExtensionCatalog`) and its `//:` note, wherever the code moves: use
`Q_DECLARE_TR_FUNCTIONS(<today's class>)` in a helper class, or
`QCoreApplication::translate("<today's class>", …)` in a free function. After
`update_translations`, only `<location>` lines may change in `i18n/*.ts`.

### 1. Packages

| File | Holds |
| --- | --- |
| `extensionpackage.{h,cpp}` | `ExtensionPackage`, the same value class and public API (`load`, `unpack`, `isValidId`, `localized`, `permissionEntries`, `permissionLines`, `isSubset`, every accessor, `readFile`, `kMaxPackageBytes`, `kMaxPackageFiles`). `load` = check the size limits, read `manifest.json`, `ManifestValidator`, keep the result. The static functions moved below stay as one-line calls. |
| `packagepath.{h,cpp}` | `bool isSafeRelativePath(const QString &path)` (same rules), used by the validator, the archive and `readFile`. |
| `packagelimits.{h,cpp}` | `struct PackageSize { qint64 bytes; int files; }`, `PackageSize measureDirectory(const QString &directory)` (regular files, no symlinks, sub-directories) and `QString packageLimitError(const PackageSize &size)` (empty when within the limits; same two messages, files checked first). `unpack` uses the same error function. |
| `stringlistfield.{h,cpp}` | `struct StringListField { QString key; QString path; bool isRequired = false; }` and `std::optional<QStringList> readStringList(const QJsonObject &object, const StringListField &field, QString &error)`, replacing today's 6-parameter function with the same three messages. The `permissions` key keeps its short message (`manifest.json: permissions: …`), without today's string replacement trick. |
| `manifestvalidator.{h,cpp}` | `ManifestValidator`: `std::optional<ValidManifest> validate(const QJsonObject &manifest)` and `QString error() const`, where `struct ValidManifest { QStringList permissions; QList<ExtensionContentScript> contentScripts; QString iconSource; }`. Steps in today's order, each its own function: the `kondor` API version, required string fields (`id`, `name`, `version`) and optional ones (`description`, `author`, `homepage`, `license`, `icon`) as data lists, the id pattern, the version pattern, known permissions, content scripts, settings, the action, the icon. The first error wins, with today's exact text. |
| `contentscriptreader.{h,cpp}` | Reads one `contentScripts[i]` entry: its four string lists, "matches must not be empty", "needs at least one js or css file", every `js`/`css` file checked (safe path, regular file, not a symlink), `runAt` against a data list of the three values, `allFrames`. |
| `manifesticon.{h,cpp}` | The icon rule: none → `preferences-plugin`; `.svg`/`.png` → a checked package file (a PNG at least 64 × 64 px) as a file URL; anything else → a Breeze icon name. |
| `manifestsections.{h,cpp}` | The settings checks (unique non-empty `key`, known `type` from a data list, `label` required, `choices` required for `choice`) and the action checks (unique `id` and a `title` per item). |
| `packagearchive.{h,cpp}` | Implements `ExtensionPackage::unpack`: `listArchiveFiles` walks the ZIP first and refuses an unsafe name, too many files or too many bytes before anything is written (recursion through a named function instead of today's self-calling lambda); `writeArchiveFiles` creates the directories and writes every non-symlink file. Same messages and the same "invalid ZIP" check for a missing root. |
| `permissiondescription.{h,cpp}` | `permissionEntries` / `permissionLines` split into: the site-access line (all sites, or the first three hosts plus "%1 and %n more" with its `//:` note), and the permission lines as a data table (`tabs`, `downloads`, `notifications` → icon and text). `parsePattern` moves here. |
| `localizedmanifest.{h,cpp}` | `localized` (same lookup order), `settingsSchema` (with the localized `choices` built by its own function), `settingDefaults` and `actionItems`. `ExtensionPackage` keeps its member functions of the same names as one-line calls. |

### 2. Installed extensions

| File | Holds |
| --- | --- |
| `extensionmanager.{h,cpp}` | `ExtensionManager`, the QML singleton and list model: `instance`, `create`, the model functions (`data` and `roleNames` as data tables), `reload` (leftover `.new`/`.old`/`.`-prefixed directories removed, invalid or misnamed packages skipped with the same warning), the installed queries (`isInstalled`, `installedVersion`, `source`, `installedMatches`, `installedPermissions`, `displayName`, `checkToken`, `isActive`, `hasPermission`), `setEnabled`, `remove`, `setUpdateInfo`, `changed()`. Header ≤ 200 lines: the `Roles` enum and the QML API stay here; private structs move to their own headers. |
| `installedextension.h` | `struct InstalledExtension` (today's `Entry`). |
| `extensionstate.{h,cpp}` | `ExtensionState`, over the same `QSettings` (`KDE`/`Kondor`) and the same keys `Extensions/<id>/Enabled`, `PrivateAllowed`, `Source`, `DisabledSites` (removed when empty), `Settings/<key>`: one getter and setter per key, `removeExtension(id)`, `sync()`. No other code builds these keys. |
| `extensionsettings.{h,cpp}` | `QVariant sanitizeSetting(const QVariantMap &setting, const QVariant &value)` split per type (`bool`, `number` with `min`/`max`, `choice`, and the string types), with the type → function choice as a data table. |
| `extensionconfiguration.cpp` | Implements `ExtensionManager::configurationFor`, `applyConfiguration`, `settingValues`, `actionExtensions`, `hasActionExtensions`, `originOf`, `siteEnabled` and `setSiteEnabled`. Same maps, same "changed only when something differs" rules and the same `settingsChanged` signal. |
| `extensioninstaller.{h,cpp}` | `ExtensionInstaller`: `std::optional<StagedPackage> stage(const PackageFile &file, QString &error)` (unpack into `<extensions>/.staging-<uuid>` and load it; the directory removed on failure), `bool commit(const StagedPackage &staged, QString &error)` (today's `.new` → rename the old one to `.old` → rename `.new` into place → roll back on failure, same messages), `discard(const StagedPackage &staged)` (removes the directory, and the ZIP when `isTemporary`). |
| `packagefile.h` | `struct PackageFile { QString zipPath; QString source; QString label; bool isTemporary = false; }` and `struct StagedPackage { QString directory; ExtensionPackage package; PackageFile file; }`. |
| `extensioninstall.cpp` | Implements the install API of `ExtensionManager`: `inspectFile`, `openPackageFile`, `isPackageFile`, `prepareInstall(const PackageFile &file)` (was 4 parameters), `confirmInstall`, `cancelInstall`, the preview map (same keys) and adding or replacing the model row after a commit (a replaced extension keeps its state and gets a new token). |
| `extensionupdate.cpp` | Implements `InstallResult installPackage(const PackageFile &file, const QString &expectedId)` (no permission check, as today with `needsReview == nullptr`) and `InstallResult updatePackage(const PackageFile &file, const QString &expectedId)` (also refuses a package that asks for more sites or permissions than the installed one: `needsReview` set, nothing installed). `struct InstallResult { bool isInstalled = false; bool needsReview = false; QString error; }`. Same messages for a wrong id and broader permissions. |
| `contentscriptbuilder.{h,cpp}` | `struct ContentScriptContext { const ExtensionPackage *package; int index; QString token; QString locale; bool isPrivate; QVariantMap settings; QStringList disabledSites; }`, `QString contentScriptSource(const ContentScriptContext &context)` and `QWebEngineScript contentScript(const ContentScriptContext &context)`. The source is built from small functions: the `==UserScript==` metadata block, the configuration object, the runtime, the site check, the style injector, the JavaScript files. The injection point comes from a `runAt` data table. **The generated source is byte-identical to today's.** The style injector's JavaScript may move to a resource file (`:/scripts/extensionstyles.js`, registered next to `extensionruntime.js`) or stay a string; your choice. `ExtensionManager::scriptSource` and `scriptsFor` stay public and become short calls. |
| `profilescripts.{h,cpp}` | `ProfileScripts` (`QObject`, owned by `ExtensionManager`): `registerProfile`, the scripts inserted per profile, and the queued rebuild that runs once after several changes. It asks the manager for `scriptsFor(isOffTheRecord)`. `ExtensionManager::registerProfile` and `rebuildScripts` stay as one-line calls (`appstartup.cpp` connects to `registerProfile`). |
| `extensionstorage.{h,cpp}` | Namespace `ExtensionStorage` over the `Sql` helper (#138), same table and SQL: `QJsonValue value(id, key)`, `StorageWrite setValue(id, key, value)` with `struct StorageWrite { bool isWritten = false; QString error; }` (same 1 MiB quota over the other keys plus this one, same messages, the SQL error text on failure), `removeValue(id, key)`, `QStringList keys(id)` (sorted), `removeExtension(id)`. `ExtensionManager::storageGet`/`storageSet`/`storageRemove`/`storageKeys` are removed: the bridge and `remove` call `ExtensionStorage`. `kStorageQuota` moves to the namespace. |

### 3. Catalog

| File | Holds |
| --- | --- |
| `extensioncatalog.{h,cpp}` | `ExtensionCatalog`, with the same QML and C++ API (`state`, `errorString`, `installingId`, `installError`, `refresh`, `install`, `startAutoUpdate`, `checkForUpdates`, `contributingUrl`, `catalogUrl`, `setCatalogUrl`, `cacheFile`, `loadCatalog`, `isSilentUpdate`, the four signals, the roles). `data`/`roleNames` as data tables. `refresh` split into the request, the failure (`error` when nothing is loaded yet, else `ready` with the message) and the success (write the cache, `ready`, apply updates). |
| `catalogentry.{h,cpp}` | `struct CatalogEntry` (today's `Entry`), `std::optional<CatalogEntry> parseCatalogEntry(const QJsonObject &object, const QUrl &catalogUrl)` (same skip rule, lower-case SHA-256, relative package and icon URLs resolved against the catalog URL, the icon rule) and `std::optional<QList<CatalogEntry>> parseCatalog(const QByteArray &json, QString &error)` (same two messages). |
| `extensionaccess.h` | `struct ExtensionAccess { QStringList matches; QStringList permissions; }`. `isSilentUpdate(const ExtensionAccess &update, const ExtensionAccess &installed)` replaces the 4-parameter version; `ExtensionManager` gets `ExtensionAccess installedAccess(id)` (keep `installedMatches`/`installedPermissions` only if something still needs them). |
| `packagedownload.{h,cpp}` | `PackageDownload` (`QObject`, deletes itself when done), replacing `fetchPackage` and its shared-pointer lambdas: `start(const CatalogEntry &entry)`, signal `finished(const QString &path, const QString &error)`. Same temporary file template, same redirect policy, same size limit (`min(entry size, 5 MiB)` or 5 MiB, aborted as soon as it is exceeded), same SHA-256 check, the file removed on any failure, same messages. |
| `catalogupdater.{h,cpp}` | `CatalogUpdater` (`QObject`, owned by `ExtensionCatalog`): the 24-hour timer, the reaction to `Settings::extensionsAutoUpdate` (start + check, or stop), the 5-second delayed first check, "nothing from the catalog is installed → only emit `updatesChecked`", and applying updates: per entry, `UpdateDecision decideUpdate(...)` (`NotInstalledFromCatalog`, `UpToDate`, `NeedsReview`, `Silent`) from a small function, then `setUpdateInfo`, and the silent download + `updatePackage` with the same warnings. `updatesChecked` is emitted at the same moments as today. |

### 4. Page API

| File | Holds |
| --- | --- |
| `extensioncall.{h,cpp}` | `struct ExtensionCall { QString extensionId; QString token; QString method; QJsonArray arguments; }`, `ExtensionCall parseExtensionCall(const QString &requestJson)` (missing or wrong-typed fields become empty; a non-array `arguments` becomes an empty array, as today), `QString okReply(const QJsonValue &value)` and `QString errorReply(const QString &message)` (same compact JSON). |
| `extensionpageapi.{h,cpp}` | `ExtensionPageApi`, moved out of the bridge: `Q_INVOKABLE QString request(const QString &requestJson)`, where the JSON is `{"id", "token", "method", "arguments"}`. `extensionruntime.js` sends that object (its one `api.request(…)` call changes, nothing else in it). It is still the only object on the web channel. |
| `extensionbridge.{h,cpp}` | `ExtensionBridge` with the same QML API (`tab`, `pageApi()`) and `QString request(const ExtensionCall &call)`: the same checks in the same order with the same messages (no tab, token, turned off), then a method → handler data table. |
| `bridgecalls.{h,cpp}` | The handlers, one small function each, with a `struct BridgeContext { Tab *tab; ExtensionCall call; }` (or equivalent): storage (`get`, `keys`, `set`, `remove`; read-only in a private tab; the key must be a string), `action.setChecked`, the `tabs.*` commands as a data table after the `tabs` permission check, `tabs.open` and `download` (http/https only, same messages), `notify` (same title format and icon). A missing permission gives the same "Permission denied" message; an unknown method gives "Unknown method: %1", including an unknown `tabs.*` one after the permission check. |

### 5. Developer loader

`extensionloader.{h,cpp}`: `load` split into refusing private or unsupported profiles, mapping the
requested directories by clean absolute path, the `loadFinished` handling (enable a loaded but
disabled extension, log the same lines on `kondor.extensions`, emit `loadFinished`) and starting the
loads. The two build variants (`KONDOR_HAVE_EXTENSIONS`) keep their behavior and messages.

### 6. Tests first

Before moving code, add these tests and check that they pass on `main`'s behavior (where the function
under test is new, write the test once it exists; its cases must also hold for `main`). Then keep
them green. Each test function body is at most 20 lines, each test file is registered in
`tests/CMakeLists.txt`, and tests use the isolated test locations as the existing ones do:

- `tests/extensions/tst_contentscriptbuilder.cpp`:
  - `sourceMatchesTheRecordedScript`: the source of the `sample` extension's first content script
    (locale `en`, private, default settings, one disabled site) equals
    `tests/data/extensions/sample-content-script.js`, **recorded from `main` before the refactor**,
    with the token replaced by `@TOKEN@` on both sides;
  - `cssOnlyScriptHasNoJavaScriptBlock`.
- `tests/extensions/tst_extensionstorage.cpp`:
  - `valuesKeepTheirJsonType`;
  - `quotaCountsTheOtherKeysOnly`;
  - `removeExtensionKeepsOtherExtensions`.
- `tests/extensions/tst_extensioncall.cpp`:
  - `parsesTheRequestObject`;
  - `malformedRequestGivesEmptyFields`;
  - `bridgeRejectsUnknownTabsMethodAfterPermissionCheck`.
- `tests/extensions/tst_catalogentry.cpp`:
  - `resolvesRelativePackageAndIconUrls`;
  - `skipsEntriesWithoutIdVersionOrPackage`;
  - `keepsIconNamesAsTheyAre`.
- `tests/extensions/tst_extensionsettings.cpp`:
  - `sanitizesEachSettingType` (data-driven: every type, a good and a bad value);
  - `clampsNumbersToMinAndMax`.
- `tests/extensions/tst_manifestvalidator.cpp`:
  - `reportsTheFirstErrorWithTodaysText` (data-driven: at least one manifest per validation step,
    with today's exact message).

All existing tests keep passing. In `tst_extensions.cpp`, only call sites change (`installPackage`
with `PackageFile` and `InstallResult`, `applyConfiguration` with its map, `ExtensionStorage`
instead of `storage*`, `ExtensionCall` in the bridge tests, `isSilentUpdate` with
`ExtensionAccess`); no test function there may grow, and none is added.

### 7. QML, baseline, CMake, translations

- `ExtensionManager.applyConfiguration(id, configuration)` (was 4 parameters) takes
  `{ settings: {…}, privateAllowed: bool, disabledSites: […] }`. Its one QML call in
  `qml/extensions/ExtensionSettingsDialog.qml` changes to pass that map; no other QML change.
- Remove every entry of `src/extensions/*.{h,cpp}` from `scripts/code-quality-baseline.json` (the
  `.js` entries stay for #139). New files add no entries, and the baseline only shrinks.
  `python3 scripts/check-code-quality.py` passes.
- Register every new source file in `CMakeLists.txt` / `cmake/KondorSources.cmake` and in
  `KONDOR_EXTENSION_PACKAGE_SOURCES` (or a new group) for the test targets that need them.
- No user-visible string changes (see "Translations keep their context" above). Run
  `update_translations`: only `<location>` lines may change in `i18n/*.ts`, with no `unfinished`,
  `vanished` or `obsolete` messages.
- `docs/extensions/api.md` does not document the bridge request format; no docs or README change.

## Acceptance criteria

- [ ] Every file named in §1–§4 exists. Every `.cpp`/`.h` in `src/extensions/` is ≤ 200 lines, and
      every function in it is ≤ 10 lines, has ≤ 3 parameters and nests ≤ 2 deep.
- [ ] No comments in `src/extensions/*.{h,cpp}` (except `//:` translator notes, SPDX lines and
      "why" comments that link a bug report).
- [ ] The baseline has no entry of `src/extensions/*.{h,cpp}`; `python3
      scripts/check-code-quality.py` passes.
- [ ] `ExtensionManager` has no SQL, no `Extensions/…` key strings, no archive code and no script
      text; `ExtensionStorage` uses `Sql`; `isSafeRelativePath` exists once.
- [ ] The 14 test functions of §6 exist, `sample-content-script.js` was recorded from `main`, and
      all `ctest` tests pass.
- [ ] Manifest error messages, package limits, the install directory layout, the `Kondor.conf`
      keys, the `extension_storage` table and quota, the generated content scripts, the catalog
      format and cache file, and the QML API of `ExtensionManager` (except `applyConfiguration`'s
      parameters) and `ExtensionCatalog` are unchanged.
- [ ] Private-tab rules hold: extensions run in private tabs only when allowed; storage is
      read-only there; the developer loader refuses private profiles.
- [ ] Clean build with no new warnings; the offscreen smoke test shows no QML errors; only
      `<location>` lines change in `i18n/*.ts`, with no `unfinished` messages.
- [ ] The manual test below behaves as on `main`.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, see AGENTS.md):

1. Pack the sample (`tests/data/extensions/sample`) into a `.kondorext` ZIP and use Settings →
   Extensions → "Install from File…": the install dialog shows the same name, icon and permission
   lines as on `main`. Install it.
2. Open a page the sample matches: its style and script run. Open "Configure…", change a setting and
   disable the extension on that site with the toolbar menu: the page follows after a reload, and
   `Kondor.conf` has the same `Extensions/sample/…` keys as on `main`.
3. Allow it in private windows and open the page in a private window: it runs; any storage write
   from it fails with "Storage is read-only in private windows".
4. Install the same file again (replace): settings and the enabled state are kept. Remove it: its
   directory, its `Kondor.conf` group and its storage rows are gone.
5. Install a broken package (for example `tests/data/extensions/dotdot` zipped): the dialog shows
   the same error as on `main`.
6. Open "Get Extensions…" with `KONDOR_EXTENSIONS_CATALOG_URL` pointing to a local catalog (as the
   tests do) or the published one: the list loads, an entry installs after the confirmation dialog,
   and with "Update extensions automatically" on, a newer catalog version with the same permissions
   updates silently while one asking for more shows "needs review".
7. `./build/kondor --load-extension <unpacked Chrome extension>` logs the same lines as on `main`.

## Out of scope

- Any change in behavior, wording, manifest format, limits, settings keys, storage, script text,
  catalog format or cache. If you find a bug, report it as a question on the issue; do not fix it
  here.
- `channel.js`, `extensionruntime.js` (except its one `api.request` call) and every QML file
  (except the one `applyConfiguration` call) — #139.
- Other C++ folders. `app` and `browser` only change where a call site of a changed function lives.
- Baseline entries of test files that already exist (only new test functions must follow the
  20-line limit; changed ones must not grow).
- The extensions repository (`lukasborges/kondor-extensions`).

## Dependencies

- #138 (`Sql`, `cmake/KondorSources.cmake`), #144 (`browser` split), #145 (`app` split), merged.

## Prototype

None: no visible change.

## Decisions

| Question | Decision |
| --- | --- |
| Why does the page API take one JSON object? | `ExtensionPageApi::request` is called from JavaScript over the web channel, so its parameters cannot be grouped in a C++ struct. One `{id, token, method, arguments}` object keeps it within 3 parameters with a one-line change in `extensionruntime.js`; the checks (token, active, permission) stay in C++ and in the same order. |
| Why does `applyConfiguration` change its QML signature? | It has 4 parameters, over the limit. The three values come from one dialog and belong together as its configuration map; only one QML call site changes. |
| Why split `installPackage` into `installPackage` and `updatePackage`? | Today a `bool *needsReview` that may be null decides whether permissions are checked: a hidden flag argument. Two named functions with one `InstallResult` say which check runs. |
| Why record the content script source from `main`? | `scriptSource` is rewritten from one 62-line function into many; a byte-for-byte comparison with today's output is the only way to show that pages get exactly the same script. |
| Why keep the `tr()` contexts? | Moving strings to new classes would orphan every translation in `i18n/*.ts`. Keeping the context means the refactor changes no translation. |
| Why no new tests in `tst_extensions.cpp`? | It is over the file limit and in the baseline, which can only shrink: any added line fails the checker. New tests get their own files, which also keeps them readable. |
