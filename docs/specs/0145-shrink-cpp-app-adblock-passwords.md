# Refactor: shrink C++ in the app, adblock and passwords folders (#145)

> **Issue:** [#145](https://github.com/lukasborges/kondor/issues/145) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first, especially "Code quality". This file is the source of truth for the issue; only the architect edits it.

## Objective

Clear every C++ entry of `src/app/`, `src/adblock/` and `src/passwords/` in
`scripts/code-quality-baseline.json` (82 entries), so that these three folders follow AGENTS.md →
"Code quality". **Kondor behaves exactly as before.** Command-line options, the single-instance
socket name and message format, `Kondor.conf` keys, the filter list cache, the KWallet folder and
map layout, and every QML-visible API stay the same.

`src/passwords/passwords.js` belongs to #139 and is not touched here.

## Context

- **Baseline entries in scope** (`origin/main` after #144):

  | Folder | Entries |
  | --- | --- |
  | `app` | **files:** `main.cpp` 243, `windowmanager.cpp` 256. **functions:** `main` 187 (nesting 3), `WindowManager::handleSingleInstanceMessage` 40, `createWindow` 38 (4 parameters), `openStartupWindows` 32 (nesting 3), `component` 16, `raiseWindow` 13, `windowForRequest` 11, `SingleInstance::readFrom` 22, `serverName` 22, `start` 18, `decodeMessage` 17, `sendMessage` 14, `encodeMessage` 12, `handleNewConnection` 12, `startupUrlForArgument` 11 (4 parameters). **comments:** `main.cpp` 35, `singleinstance.cpp` 23, `singleinstance.h` 18, `windowmanager.cpp` 20, `windowmanager.h` 17, `startupurl.h` 4, `startupurl.cpp` 3, `startupargs.h` 2, `aboutinfo.{h,cpp}` 1 each |
  | `adblock` | **files:** `filterengine.cpp` 336, `adblockmanager.cpp` 259. **functions:** `FilterEngine::addRule` 85 (nesting 4), `matchesAny` 38 (nesting 3), `matchesPattern` 30 (nesting 4), `optionsMatch` 20, `shouldBlock` 19, `tokenOf` 17, `matchSegmentAt` 16, `urlTokens` 15, `kindForOption` 11, `AdBlockInterceptor::interceptRequest` 44, `AdBlockManager::AdBlockManager` 29, `download` 28 (nesting 3), `setAllowed` 25, `loadCachedLists` 18. **comments:** `filterengine.{h,cpp}` 15 each, `adblockmanager.h` 13, `adblockmanager.cpp` 6, `adblockinterceptor.h` 6 |
  | `passwords` | **files:** `passwordstore.cpp` 413, `passwordimport.cpp` 202. **functions:** `PasswordStore::prepareImport` 76, `commitImport` 35 (nesting 3), `ensureOpen` 21, `credentialsFor` 14, `onWalletOpened` 14, `reloadUsernames` 14, `remove` 13, `entries` 11, `save` 11, `state` 11, `PasswordImport::parse` 71 (nesting 3), `parseCsv` 57 (nesting 4), `formatName` 15, `detectFormat` 13, `PasswordBridge::formSubmitted` 22. **comments:** `passwordstore.h` 34, `passwordbridge.h` 10, `passwordimport.h` 5, `passwordstore.cpp`, `passwordbridge.cpp`, `passwordimport.cpp` 2 each |

- **Why the code is long:** `main()` does everything in one block; `PasswordStore` repeats the
  `setFolder(kFolder)` / `readMap(...) != 0` KWallet boilerplate in eight places; `FilterEngine`
  parses a rule in one 85-line function and scans alphanumeric runs twice (`tokenOf`, `urlTokens`).
- **Tests today:** `tests/adblock/tst_filterengine.cpp` (anchors, exceptions, third-party, types,
  wildcards, `^`, skipped rules), `tests/app/tst_singleinstance.cpp` (socket name, message format,
  forwarding), `tests/app/tst_startupurl.cpp`, `tests/passwords/tst_passwordimport.cpp` (CSV
  formats, quoting, duplicates), `tests/passwords/tst_passwordstore.cpp` (origins, closed state).
  **Nothing tests** the ad-block allow list, the `domain=` option, the country-code first-party
  rule, the extension-package routing of `WindowManager`, or the import counting and merging of
  `PasswordStore` (they need KWallet today).

## Design / behavior

Limits for every new or changed function: body ≤ 10 lines, ≤ 3 parameters, nesting ≤ 2. Every file
≤ 200 lines. No comments (AGENTS.md → "Names instead of comments"): every "why" comment of today
becomes a name (for example `restrictSocketToCurrentUser()`, `isAnotherInstanceListening()`,
`passActivationTokenToCompositor()`, `keepGoodCachedList()`). The **file, class and function names
below are binding**. How the rest is split inside them is up to you, as long as the limits hold. If a
listed file still goes over 200 lines, split it again in the same folder and say so in the PR. Never
merge two rows into one file.

### 1. App (`src/app/`)

| File | Holds |
| --- | --- |
| `main.cpp` | `main()` only, ≤ 10 lines, calling the steps below in today's order: message handler, `AA_ShareOpenGLContexts`, dictionaries path, `QtWebEngineQuick::initialize()`, AppImage portal, `QApplication`, identity, command line, single instance (exits with 0 when forwarded), translations and style, ad blocker start, extensions, engine and windows, catalog auto-update, `return 1` when no window opened, else `app.exec()`. |
| `messagehandler.{h,cpp}` | `installMessageHandler()`: today's filter (drops debug/info except the `kondor.extensions` category, prints the rest to stderr and flushes). |
| `environment.{h,cpp}` | `prepareEnvironment()` (everything before `QApplication`: dictionaries path from `/proc/self/exe` with the same two candidates and the `QTWEBENGINE_DICTIONARIES_PATH` override, `QtWebEngineQuick::initialize()`, `PLASMA_INTEGRATION_USE_PORTAL` inside an AppImage). |
| `commandline.{h,cpp}` | `struct CommandLine { QList<QUrl> urls; bool isPrivate; bool newWindow; bool newInstance; QStringList extensionDirectories; }` and `CommandLine parseCommandLine(const QCoreApplication &app)`. Same options, value names, descriptions, help and version. It resolves the positional arguments with `startupUrlsForArguments` (below). |
| `appidentity.{h,cpp}` | `setUpIdentity()` (organization, application name and version, desktop file name with `FLATPAK_ID`, window icon) and `setUpLanguageAndStyle(QApplication &app)` (Kondor and Qt translators, owned by `app`; display name with the same `QCoreApplication::translate("Kondor", "Kondor Browser")` and its `//:` note; `org.kde.desktop` style with the `Fusion` fallback). |
| `faviconimageprovider.{h,cpp}` | `FaviconImageProvider`, moved out of `main.cpp` unchanged. |
| `startupurl.{h,cpp}` | `struct StartupContext { QString workingDirectory; QUrl homePage; QString searchTemplate; }`, `startupUrlForArgument(const QString &argument, const StartupContext &context)` (same rules), and `startupUrlsForArguments(const QStringList &arguments)` (current directory and `Settings` home page / search template, empty results skipped). |
| `singleinstancemessage.{h,cpp}` | `SingleInstanceMessage` (same fields, still `Q_DECLARE_METATYPE`) with `QByteArray toJsonLine() const` and `static SingleInstanceMessage fromJsonLine(const QByteArray &line)`, replacing `SingleInstance::encodeMessage` / `decodeMessage`. Same JSON keys, encoded URLs, trailing `\n`, and the same "invalid → empty message" rule. |
| `singleinstance.{h,cpp}` | `SingleInstance` with the same `serverName()`, `sendMessage`, `start`, `StartResult` and `messageReceived`. `serverName` split into the profile hash and the runtime directory (Flatpak `app/<id>` sub-directory). `readFrom` split into buffering (1 MiB limit, same warning) and emitting every complete line. Same socket options, same timeouts (500 ms), same connect-first start order. |
| `windowmanager.{h,cpp}` | `WindowManager` with the same QML API (`newWindow`, `closeWindow`, `windowCount`) and the same C++ API (`setEngine`, `handleSingleInstanceMessage`, `openStartupWindows`). `createWindow` takes `struct WindowContents { bool isPrivate = false; QList<QUrl> urls; QStringList titles; int currentIndex = -1; }`. The window list, the active-window tracking and `windowForRequest` stay here. |
| `windowlaunch.cpp` | Implements `WindowManager::handleSingleInstanceMessage`, `openStartupWindows` and `showExtensionPackage`, split into small steps: open the restored session windows, open the command-line window, route extension packages to a normal window. |
| `extensionpackages.{h,cpp}` | `QStringList takeExtensionPackages(QList<QUrl> &urls)`: removes local `.kondorext` files from the list (in order) and returns their paths. |
| `windowactivation.{h,cpp}` | `raiseWindow(QObject *window, const QByteArray &activationToken)`: sets `XDG_ACTIVATION_TOKEN` when the token is not empty, then `raise()` and `requestActivate()`. |

`startupargs.{h,cpp}` and `aboutinfo.{h,cpp}` only lose their comments.

### 2. Ad blocker (`src/adblock/`)

| File | Holds |
| --- | --- |
| `filterengine.{h,cpp}` | `FilterEngine` with the same public API (`ResourceKind`, `addList`, `addRule`, `ruleCount`, `shouldBlock`), still immutable once built and shared with the IO thread. It indexes parsed rules (`||host` rules by host, others by token or in the "other" list) and matches a request: domain rules for the host and each parent domain, then token rules (each URL token once), then the other rules; blocked when a blocking rule matches and no exception does. |
| `filterrule.{h,cpp}` | `struct FilterRule` (today's `Rule`, plus `QString host` for `||` rules) and `std::optional<FilterRule> parseFilterRule(const QString &line)`, split into: skipping comments, `[` headers and cosmetic rules; the `@@` exception prefix; the options after the last `$`; skipping `/regex/` rules; the `||`, `|` and trailing `|` anchors; the host of a `||` rule (it ends at `^ / * : ? |` and must contain a dot). |
| `filteroptions.{h,cpp}` | `bool applyFilterOptions(const QString &options, FilterRule &rule)` (`third-party`, `~third-party`, `domain=` with `~` exclusions, the five resource types as a data table, `false` for any unknown or negated type option) and `bool optionsMatch(const FilterRule &rule, const FilterRequest &request)` split into type, party and domain checks. |
| `filterpattern.{h,cpp}` | `matchesPattern(rule, text, isUnanchoredSearch)` split into matching the first segment and searching the later ones; `matchSegmentAt`; the `^` separator rule; **one** alphanumeric-run scanner used by both `tokenOf` and `urlTokens`; `registrableDomain` (same two-letter-TLD heuristic) and `hostMatches`. |
| `filterrequest.h` | `struct FilterRequest` (today's `Request`) and `FilterRequest makeFilterRequest(const QUrl &url, const QString &firstPartyHost, FilterEngine::ResourceKind kind)` (inline or in `filterpattern.cpp`; your choice). Same lower-casing, fragment removal and `rest` after the host. |
| `adblockinterceptor.{h,cpp}` | `interceptRequest` split into: the main-frame `pageStarted` signal, the resource kind as a data table, reading the engine unless the first-party host is allowed (under the read lock), and blocking. |
| `adblockallowlist.{h,cpp}` | `AdBlockAllowList`, a value class over the session sets: `isAllowed(host)`, `setPersistent(host, allowed)` (writes `Settings::adBlockAllowList`, drops any session choice for the host), `setForSession(host, allowed)` (never writes `Settings`; a session block only overrides a host that is on the persistent list), `hosts()` (the set the interceptor gets). Hosts are lower-cased; an empty host is ignored. |
| `filterlists.{h,cpp}` | The list table (EasyList, EasyPrivacy: URL and file name), the cache directory, `isCacheStale(const QDateTime &lastUpdate)` (4 days or a missing file) and `parseFilterLists(const QStringList &files)` → `std::shared_ptr<const FilterEngine>` (run off the GUI thread as today). |
| `filterlistdownloader.{h,cpp}` | `FilterListDownloader` (`QObject`): `update()`, `isUpdating()`, `updatingChanged()` and `finished(bool isAnyListCurrent)`. Same request (redirect policy, 60 s timeout, `If-Modified-Since` from the cached file), same rules: a 200 body over 1024 bytes replaces the cache with `QSaveFile`, a 304 counts as current, anything else keeps the cached file. |
| `adblockmanager.{h,cpp}` | `AdBlockManager` with the same QML and C++ API (`enabled`, `updating`, `lastUpdate`, `install`, `start`, `isAllowed`, `setAllowed`, `blockedCount`, `updateLists`, `setEngine`, `cacheDirectory`, the five signals). It wires `Settings`, the interceptor counters, `AdBlockAllowList`, `FilterListDownloader` (on `finished(true)`: store the update time and reload the cache) and the background loader (a reload requested while loading runs after it). |

### 3. Passwords (`src/passwords/`)

| File | Holds |
| --- | --- |
| `passwordorigin.{h,cpp}` | Namespace `PasswordOrigin`: `originOf`, `canSaveFor`, `originFromInput`, `hostOfOrigin`, unchanged. `PasswordStore` keeps its static `Q_INVOKABLE` functions of the same names (QML calls them), as one-line calls. |
| `walletfolder.{h,cpp}` | `WalletFolder`, a thin wrapper over an open `KWallet::Wallet *` and the `Kondor` folder: `std::optional<QMap<QString, QString>> logins(origin)`, `bool writeLogins(origin, logins)`, `bool removeOrigin(origin)`, `QStringList origins()`. It selects the folder before each call. Every KWallet read and write of `PasswordStore` goes through it. |
| `passwordclipboard.{h,cpp}` | `PasswordClipboard` (`QObject`): `copy(secret)` and the 30-second clear that only clears the clipboard when it still holds that secret. |
| `passwordimportfile.{h,cpp}` | `struct ImportFile { QByteArray data; QString error; }` and `ImportFile readImportFile(const QUrl &file)`: same checks and errors (`unreadable`, `tooLarge` at 20 MiB, read limit + 1 byte). Callers still zero the bytes after parsing, as today. |
| `passwordimportplan.{h,cpp}` | Pure functions, no KWallet: `struct ImportSummary { int newCount; int identicalCount; int conflictCount; int conflictSites; }`; `ImportSummary summarizeImport(const QList<PasswordImport::Login> &logins, const SavedLogins &saved)`; `int mergeLogins(QMap<QString, QString> &saved, const QList<PasswordImport::Login> &logins, bool replaceConflicts)` (returns how many entries it changed; identical logins and, unless replacing, conflicts are left alone). `SavedLogins` is `QHash<QString, QMap<QString, QString>>` (origin → username → password). |
| `passwordstore.{h,cpp}` | `PasswordStore` with the same QML API (`state`, `entries`, `ensureOpen`, `retry`, `password`, `contains`, `save`, `remove`, `copyPassword`, `prepareImport`, `commitImport`, `cancelImport`, `moveImportFileToTrash`, the static origin helpers, `changed`, `stateChanged`) and C++ API (`usernames`, `credentialsFor`, `isOpen`, the notice flag). `state()` is a data table. `prepareImport` = check the wallet, `readImportFile`, `PasswordImport::parse`, read the saved maps of the imported origins, `summarizeImport`, build the same `QVariantMap` (same keys and error strings). `commitImport` = group by origin, `mergeLogins`, write changed maps, `-1` on any failed write. If `passwordstore.cpp` is still over 200 lines, move the import functions to `passwordstoreimport.cpp` (it implements `PasswordStore`). |
| `csvreader.{h,cpp}` | `QList<QStringList> readCsvRows(const QByteArray &data)`: today's RFC 4180 reader (BOM dropped, `""` escapes, LF/CRLF/CR line ends, blank rows dropped), written as a small state class whose per-character steps fit the limits. |
| `passwordimport.{h,cpp}` | `PasswordImport::parse` and `formatName` with the same results, split into: normalizing the header, finding the site/user/password/type columns (the column-name lists become data), reading one row (skips counted as today), and adding a login with the same origin+username de-duplication (the last password wins). `formatName` and `detectFormat` become data tables. |
| `passwordbridge.{h,cpp}` | `formSubmitted` split into: whether saving may be offered (private tab, empty password, origin, setting, never-save list), the one-time wallet-unavailable notice, and whether that exact login is already saved. |

### 4. Tests first

Before moving code, add these tests and check that they pass on `main`'s behavior (where the
function under test is new, write the test once it exists, and its cases must also hold for `main`).
Then keep them green. Each test function body is at most 20 lines, each test file is registered in
`tests/CMakeLists.txt`, and tests use the isolated test locations as the existing ones do:

- `tests/adblock/tst_filterengine.cpp`:
  - `domainOptionIncludesAndExcludesSites`;
  - `countryCodeSecondLevelDomainIsFirstParty` (`cdn.example.co.uk` on `www.example.co.uk` is not third-party);
  - `endAnchorRequiresTheEndOfTheAddress`.
- `tests/adblock/tst_adblockallowlist.cpp` (through `AdBlockManager`'s public API, so it runs on `main`):
  - `sessionAllowDoesNotTouchSettings`;
  - `sessionBlockOverridesThePersistentList`;
  - `persistentChoiceReplacesTheSessionChoice`.
- `tests/app/tst_extensionpackages.cpp`:
  - `takesLocalPackagesOutOfTheUrls`;
  - `keepsRemoteUrlsThatLookLikePackages`.
- `tests/app/tst_startupurl.cpp`:
  - `skipsEmptyArguments` (for `startupUrlsForArguments`).
- `tests/passwords/tst_passwordimportplan.cpp`:
  - `countsNewIdenticalAndConflictingLogins`;
  - `countsEachConflictingSiteOnce`;
  - `mergeKeepsConflictsUnlessReplacing`;
  - `mergeLeavesIdenticalLoginsUnchanged`.
- `tests/passwords/tst_passwordimportfile.cpp`:
  - `rejectsFilesOverTheSizeLimit`;
  - `rejectsMissingAndRemoteFiles`.

All existing tests keep passing. `tst_singleinstance.cpp` switches to
`SingleInstanceMessage::toJsonLine` / `fromJsonLine`, and `tst_startupurl.cpp` to `StartupContext`;
nothing else in them changes.

### 5. Baseline, CMake, translations

- Remove every C++ entry of `src/app/`, `src/adblock/` and `src/passwords/` from
  `scripts/code-quality-baseline.json` (the `passwords.js` entries stay for #139). New files add no
  entries, and the baseline only shrinks. `python3 scripts/check-code-quality.py` passes.
- Register every new source file in `cmake/KondorSources.cmake` (add groups for the ad blocker and
  the password store if test targets need them) and in every test target that compiles the files it
  now depends on.
- No user-visible string changes. The "Kondor Browser" display name keeps its `Kondor` context and
  `//:` note. Run `update_translations`: only `<location>` lines may change in `i18n/*.ts`, with no
  `unfinished`, `vanished` or `obsolete` messages.
- No README change.

## Acceptance criteria

- [ ] Every file named in §1–§3 exists. Every `.cpp`/`.h` in `src/app/`, `src/adblock/` and
      `src/passwords/` is ≤ 200 lines, and every function in them is ≤ 10 lines, has ≤ 3 parameters
      and nests ≤ 2 deep.
- [ ] No comments in those folders' C++ files (except `//:` translator notes, SPDX lines and "why"
      comments that link a bug report).
- [ ] The baseline has no C++ entry of those folders; `python3 scripts/check-code-quality.py` passes.
- [ ] `main()` is ≤ 10 lines; `FaviconImageProvider` lives in its own file.
- [ ] `PasswordStore` has no direct `KWallet::Wallet` `readMap`/`writeMap`/`removeEntry` call outside
      `WalletFolder`; the alphanumeric-run scan exists once in `filterpattern.cpp`.
- [ ] The 15 test functions of §4 exist, and all `ctest` tests pass.
- [ ] Command-line options and help text, the single-instance socket name and message format,
      `Kondor.conf` keys, the filter list URLs and cache files, the KWallet folder and map layout,
      the import result map, and the QML API of `WindowManager`, `AdBlockManager` and
      `PasswordStore` are unchanged.
- [ ] Private-tab rules hold: no password prompt, script or saving for private tabs; a private
      tab's ad-block allow/block choice never reaches `Kondor.conf`; downloads of private profiles
      keep their private flag.
- [ ] Clean build with no new warnings; the offscreen smoke test shows no QML errors; no
      `unfinished` messages in `i18n/*.ts`.
- [ ] The manual test below behaves as on `main`.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, see AGENTS.md; `KONDOR_NO_KWALLET=1` for step 5 if you do not want to touch your wallet):

1. `./build/kondor --help` and `--version` print the same text as on `main`.
2. Start `./build/kondor https://example.com`. With it running, `./build/kondor https://kde.org`
   opens a new tab in that window and exits at once; `--new-window https://kde.org` opens a second
   window; `--private https://kde.org` opens a private window. `--new-instance` starts a second
   process.
3. Set "On startup" to restore the last session, open two windows with tabs, quit and start again:
   both windows come back. Opening a `.kondorext` file with `./build/kondor <file>` shows the
   extension install dialog in a normal window.
4. With the ad blocker on, visit a page with ads (for example `https://www.speedtest.net/`): the
   "Ad and Tracker Blocking" button shows "Blocked on this page: N". Turning off "Blocking enabled
   on this site" persists after a restart; in a private window, the same switch does not change
   `Kondor.conf`. "Update Lists Now" in Settings finishes and updates the date.
5. Submit a login form (for example `https://the-internet.herokuapp.com/login` with `tomsmith` /
   `SuperSecretPassword!`): the save bar (or the wallet-unavailable notice) appears as on `main`.
   In Settings → Passwords, import the CSV files of `tests/data/passwords/`: the review dialog shows the
   same counts as on `main`, and importing again reports identical logins.
6. Copy a saved password from Settings → Passwords: it is pasted fine and gone from the clipboard
   after 30 seconds.

## Out of scope

- Any change in behavior, wording, options, settings keys, socket format, cache files or wallet
  layout. If you find a bug, report it as a question on the issue; do not fix it here.
- `src/passwords/passwords.js` and every QML file (#139).
- Other C++ folders: `extensions` (#146). `browser`, `core`, `bookmarks`, `history` and `downloads`
  only change where a call site of a renamed function lives (there should be none).
- Baseline entries of test files that already exist (only new or changed test functions must follow
  the 20-line limit).

## Dependencies

- #138 (`cmake/KondorSources.cmake`), #144 (`browser` split), merged.

## Prototype

None: no visible change.

## Decisions

| Question | Decision |
| --- | --- |
| Why a `WalletFolder` wrapper? | Eight `PasswordStore` functions repeat "select the folder, read the map, check the return code". One wrapper with `std::optional` results removes that boilerplate, as `Sql` did for `QSqlQuery` in #138, and keeps KWallet calls in one place. |
| Why pull import counting and merging out of `PasswordStore`? | They are the risky part of the import (#106) and today need a real wallet to test. As pure functions over `QMap`s they get unit tests (§4) without KWallet. |
| Why do `encodeMessage`/`decodeMessage` move to `SingleInstanceMessage`? | They only work on the message, not on the socket. As methods of the message they leave `SingleInstance` with the socket work. Only `tst_singleinstance.cpp` calls them. |
| Why may `windowlaunch.cpp` implement `WindowManager`? | As `tabcommands.cpp` in #144: one class, split by responsibility into two files, because the launch routing alone would push `windowmanager.cpp` past 200 lines. |
