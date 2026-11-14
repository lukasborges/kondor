# Python port 6/12: Password store (#168)

> **Issue:** [#168](https://github.com/lukasborges/kondor/issues/168) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 6, 8 and 9, "Rules for every phase") and the phase 2 spec [`0164-python-core.md`](0164-python-core.md) first. This file details phase 6 and must follow the umbrella. Only the architect edits it.

## Objective

Port `src/passwords/` (except `bridge/`) to Python, with KWallet reached over D-Bus, and port its tests:

- **Same QML API:** `PasswordStore` is a QML singleton in `Kondor` 1.0. `check-qml-api.py` pairs it with its C++ twin.
- **Same data:** the Python store reads and writes the same KWallet folder `Kondor`, with entries byte-compatible with `KWallet::Wallet::readMap` / `writeMap`, so passwords saved by the C++ app are read by the Python app and the other way round.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Phase 2 (#164)** added `kondor/core/` (`Settings`, `Database`, `Notifier`, `qmlregistration`) and the pytest fixtures `isolated_profile`, `kondor_types`, `kondor_engine` and `qml_engine`, plus `pytests/qmlsupport.py` (`create_object`, `captured_messages`). Phases 3 to 5 follow the same layout. `kondor/core/notifier.py` shows how to call a D-Bus method with typed arguments (`QMetaObject.invokeMethod` + `Q_ARG`). `kondor/adblock/lists/filterlistloader.py` shows the worker-thread pattern (a `threading.Thread` that hands its result to the UI thread through a private `Signal`).
- **`src/passwords/`** without `bridge/` (about 1,900 lines with headers):

  | C++ file | What it does |
  | --- | --- |
  | `passwordstore.{h,cpp}` | QML singleton `PasswordStore`: properties `state`, `entries`, `importPreparing`, `importRunning`, `importDone`, `importTotal`; static invokables `originOf`, `canSaveFor`, `originFromInput`, `hostOfOrigin`; invokables `ensureOpen`, `retry`, `password`, `contains`, `save`, `remove`, `copyPassword`, `prepareImport`, `commitImport`, `cancelImport`, `setImportPageOpen`, `takeImportResult`, `claimImportNotification`, `moveImportFileToTrash`; signals `stateChanged`, `changed`, `importPreparingChanged`, `importRunningChanged`, `importDoneChanged`, `importTotalChanged`, `importPrepared(QVariantMap)`, `importFinished(int)`. C++-only public API used by the bridge (phase 8): `isOpen`, `usernames`, `credentialsFor`, `copyText`, `unavailableNoticeShown`, `setUnavailableNoticeShown`. |
  | `passwordstorewallet.cpp` | the wallet state machine: `closed` → `opening` → `open` / `unavailable`; `KONDOR_NO_KWALLET=1` makes it `unavailable`; `retry`; forgetting a closed wallet |
  | `passwordstoreimport.cpp` | the import commands of `PasswordStore` |
  | `walletfolder.{h,cpp}` | the `Kondor` folder: `ensureExists`, `logins`, `allLogins`, `writeLogins`, `removeOrigin`, `origins` |
  | `passwordorigin.{h,cpp}` | `originOf`, `canSaveFor`, `originFromInput`, `hostOfOrigin` |
  | `passwordclipboard.{h,cpp}` | copies a secret with the `x-kde-passwordManagerHint: secret` MIME hint and clears it after 30 s if the clipboard still holds it; `copyText` copies plain text |
  | `csv/csvreader.{h,cpp}` | `readCsvRows`: RFC 4180-style reader (quotes, doubled quotes, CR/LF/CRLF, BOM) |
  | `csv/passwordimport.{h,cpp}` | `Format`, `Error`, `Login`, `Result`, `parse(csv)`, `formatName` |
  | `csv/passwordimportcolumns.{h,cpp}` | `Columns`, `normalizedHeader`, `findColumns`, `detectFormat` |
  | `csv/passwordimportfile.{h,cpp}` | `readImportFile`: local files only, 20 MiB limit, errors `unreadable` / `tooLarge` |
  | `csv/passwordimportplan.{h,cpp}` | `SavedLogins`, `ImportSummary`, `summarizeImport`, `mergeLogins` |
  | `import/importpreparation.{h,cpp}` | reads and parses the file on a worker thread, then describes it against the saved logins |
  | `import/importcommit.{h,cpp}` | writes the merged logins one origin per event-loop turn, with progress |
  | `import/importinfo.{h,cpp}` | the `QVariantMap` sent with `importPrepared` |
  | `import/importoutcome.{h,cpp}` | remembers the last result for the page and the one-time notification |
  | `import/pendingimport.h` | `PendingImport{logins, saved, replaceConflicts}` |

- **Tests to port:**

  | C++ test | Cases |
  | --- | --- |
  | `tests/passwords/tst_passwordstore.cpp` | `originOf` (6 rows), `canSaveFor` (5 rows), `originFromInput` (10 rows), `containsWhenClosed`, `startsClosed` |
  | `tests/passwords/tst_passwordclipboard.cpp` | `copyMarksPasswordSecret`, `copyTextHasNoSecretHint`, `copyTextIsNotCleared` |
  | `tests/passwords/tst_passwordimport.cpp` | `fixtures` (6 rows, files in `tests/data/passwords/`), `quotedFields`, `crlfAndBom`, `shortRows`, `bitwardenTwoUris`, `websiteColumn`, `skipsAndDuplicates`, `notAPasswordExport`, `emptyFile` |
  | `tests/passwords/tst_passwordimportfile.cpp` | `rejectsFilesOverTheSizeLimit`, `rejectsMissingAndRemoteFiles`, `readsSmallFiles` |
  | `tests/passwords/tst_passwordimportplan.cpp` | `countsNewIdenticalAndConflictingLogins`, `countsEachConflictingSiteOnce`, `mergeKeepsConflictsUnlessReplacing`, `mergeLeavesIdenticalLoginsUnchanged` |
  | `tests/passwords/tst_passwordimportasync.cpp` | `reportsProgressPerOrigin`, `countsWrittenLogins`, `failsWhenTheWalletRejectsAWrite`, `writesNothingForIdenticalLogins`, `prepareReturnsBeforeTheFileIsParsed`, `prepareDescribesTheFile`, `prepareFailsWhenTheWalletIsUnavailable`, `cancelDropsThePreparedLogins`, `cancelWhileReadingEmitsNothing` |
  | `tests/passwords/tst_passwordimportoutcome.cpp` | `isNotifiedOnceWhenThePageIsClosed`, `isNotNotifiedWhenThePageIsOpen`, `isTakenOnce` |
  | `tests/passwords/tst_passwordsui.cpp` (QML in `tests/extensions/extensionsuiharness.h`: `emptySavedPasswordsQml`, `savedPasswordsPopupQml`) | `emptyListButtonRequestsAdd`, `rowClickFillsAndCloses`, `copyButtonShowsCheckMarkAndStaysOpen`, `downKeyMovesToNextRow`, `escapeClosesAndFocusesPage` |

- **Not in this phase:** `src/passwords/bridge/` (`PasswordBridge`, `passwords.js`, `usernamefield.js`) and `tests/passwords/tst_passwordfill.cpp`, which tests `passwords.js`. They move with the bridge to phase 8 (#170), as the umbrella's phase table says.
- **KWallet over D-Bus** (`/usr/share/dbus-1/interfaces/kf6_org.kde.KWallet.xml`): service `org.kde.kwalletd6`, path `/modules/kwalletd6`, interface `org.kde.KWallet`. The methods this phase needs: `networkWallet() → s`, `openAsync(s wallet, x wId, s appid, b handleSession) → i transactionId`, `hasFolder(i, s, s) → b`, `createFolder(i, s, s) → b`, `entryList(i, s, s) → as`, `readMap(i, s, s key, s) → ay`, `mapList(i, s, s) → a{sv}`, `writeMap(i, s, s key, ay, s) → i`, `removeEntry(i, s, s key, s) → i`. Signals: `walletAsyncOpened(i tId, i handle)`, `walletClosedId(i handle)`, `applicationDisconnected(s wallet, s application)`.

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior and edge cases as the C++, with the Python conventions of umbrella item 3. A C++ helper namespace becomes a module of functions.

### 1. Layout

```
kondor/passwords/
  __init__.py
  qmltypes.py
  passwordstore.py
  passwordstoreimport.py
  passwordorigin.py
  passwordclipboard.py
  wallet/
    __init__.py
    walletservice.py
    kwalletservice.py
    walletmap.py
    walletfolder.py
    walletsession.py
  csvimport/
    __init__.py
    csvreader.py
    passwordimport.py
    passwordimportcolumns.py
    passwordimportfile.py
    passwordimportplan.py
  importing/
    __init__.py
    importcommit.py
    importinfo.py
    importoutcome.py
    importpreparation.py
    pendingimport.py
```

- `import` is a Python keyword, so the C++ `import/` folder becomes `importing/`.
- `csv/` would shadow the standard library's `csv` module for anyone running a file from that folder, so it becomes `csvimport/`.
- The modules keep their C++ base names. `wallet/` is new and holds the KWallet pieces (`walletfolder.py` moves there from the feature root, next to its D-Bus service).
- **Splitting `PasswordStore`:** a Python class cannot be spread over three files as the C++ one is. `PasswordStore` (`passwordstore.py`) keeps the whole QML API and only delegates. The wallet state machine of `passwordstorewallet.cpp` goes into `WalletSession` (`wallet/walletsession.py`). The import commands of `passwordstoreimport.cpp` go into `PasswordStoreImport` (`passwordstoreimport.py`). Further splits for the size limits are allowed when the modules above keep their names.

### 2. `qmltypes.py`

```python
QML_TYPES = (QmlType(PasswordStore, "PasswordStore", QmlKind.SINGLETON),)
```

With `register_types()`, as in `kondor/core/qmltypes.py`. Importing it must not create any instance or open any D-Bus connection.

### 3. Names and types

- **QML names:** the names QML sees keep their C++ names. The static C++ invokables (`originOf`, `canSaveFor`, `originFromInput`, `hostOfOrigin`) become ordinary slots of the instance that call the `passwordorigin` functions: QML calls them on the singleton.
- **Slot types:** `originOf(QUrl) → str`, `prepareImport(QUrl)`, `moveImportFileToTrash(QUrl) → bool`, `takeImportResult()` and `claimImportNotification()` → `"QVariantMap"`, `entries` → `"QVariantList"`, `importPrepared = Signal("QVariantMap")`, `importFinished = Signal(int)`.
- **Snake case** for everything QML does not see (umbrella item 3), including the C++-only public API the bridge will use in phase 8: `is_open()`, `usernames(origin) -> list[str]`, `credentials_for(origin) -> list[dict[str, str]]`, `copy_text(text)`, `unavailable_notice_shown()`, `set_unavailable_notice_shown()`. Module functions: `passwordorigin.origin_of`, `can_save_for`, `origin_from_input`, `host_of_origin`; `csvreader.read_csv_rows`; `passwordimport.parse`, `format_name`; `passwordimportcolumns.normalized_header`, `find_columns`, `detect_format`; `passwordimportfile.read_import_file`; `passwordimportplan.summarize_import`, `merge_logins`; `importinfo.import_failure`, `import_error_name`, `import_result`.
- **Value types:** `Format` and `Error` are `enum.Enum`s with the C++ members in the C++ order (`BITWARDEN`, `ONE_PASSWORD`, `FIREFOX`, `CHROME`, `KEEPASSXC`, `CSV`; `NONE`, `NOT_PASSWORD_EXPORT`, `EMPTY`). `Login`, `Columns`, `Result`, `ImportSummary`, `ImportFile`, `ParsedImport` and `PendingImport` are dataclasses with the C++ fields in snake case (`skipped_no_site`, `new_count`, `conflict_sites`, `replace_conflicts`, …). `SavedLogins` is `dict[str, dict[str, str]]` (origin → user name → password).
- **Map keys** sent to QML stay the C++ ones: `origin`, `host`, `username`, `password`; the import info keys `fileName`, `format`, `error`, `newCount`, `identicalCount`, `conflictCount`, `conflictSites`, `skippedNoSite`, `skippedNoCredentials`, `skippedNotLogin`; the outcome keys `count`, `fileName`. The error names are the C++ strings: `unreadable`, `tooLarge`, `notPasswordExport`, `empty`, `walletUnavailable`.
- **Strings:** `formatName` returns the C++ names (`Bitwarden`, `1Password`, `Firefox`, `Chrome`, `KeePassXC`, `CSV`). None of them is translated in C++, and nothing in this phase calls `translate`.

### 4. KWallet over D-Bus

- **`WalletService`** (`walletservice.py`): a `typing.Protocol` with what the store needs from KWallet, in the KWallet vocabulary:
  - `open_network_wallet() -> bool`: starts an asynchronous open; `False` when the call fails or returns a negative transaction id;
  - `has_folder(handle, folder)`, `create_folder(handle, folder)` → `bool`;
  - `read_map(handle, folder, key) -> bytes | None`, `map_list(handle, folder) -> dict[str, bytes] | None`, `entry_list(handle, folder) -> list[str]`;
  - `write_map(handle, folder, key, data: bytes) -> bool`, `remove_entry(handle, folder, key) -> bool`;
  - two Qt signals on the object: `opened(int handle)` (`-1` when the open failed) and `closed()`.

  `None` and `False` mean "the D-Bus call failed" (an error reply), as a non-zero return code or `!isOk` does in KWallet.
- **`KWalletService`** (`kwalletservice.py`) implements it on `org.kde.KWallet` with `QtDBus`:
  - `appid` is always `"Kondor"` (the C++ application name, which `KWallet::Wallet` sends), so the "Always Allow" choice the user made for the C++ app also covers the Python app.
  - **Typed arguments:** the D-Bus signature must match exactly, or `kwalletd6` answers "No such method". Send `wId` as a 64-bit integer (`x`) and every handle as a 32-bit one (`i`), for example with `QMetaObject.invokeMethod` and typed `Q_ARG`/`Q_RETURN_ARG` on the `QDBusInterface`, as `kondor/core/notifier.py` does, or with a `QDBusMessage` built with explicit types. A plain Python `int` is not enough.
  - **Opening:** `networkWallet()`, then `openAsync(wallet, 0, "Kondor", handleSession)`. `handleSession` is the value KF6Wallet's `Wallet::openWallet` sends (`true` in KF6 6.x); check it with `dbus-monitor` against the C++ app (manual test step 2) and use what the C++ app sends. Keep the transaction id; on `walletAsyncOpened(tId, handle)` with that id, emit `opened(handle)` (a negative handle is a failure) and remember the handle and the wallet name.
  - **Closing:** emit `closed()` on `walletClosedId(handle)` for the remembered handle, and on `applicationDisconnected(wallet, "Kondor")` for the remembered wallet, the two signals `KWallet::Wallet` turns into `walletClosed()`.
  - `mapList` returns `a{sv}`: accept each value as `QByteArray` or `bytes`.
- **`walletmap.py`**: the byte format of `KWallet::Wallet::readMap` / `writeMap`, a `QDataStream`-serialized `QMap<QString, QString>`:
  - `map_to_bytes(logins: dict[str, str]) -> bytes`: big-endian `quint32` count, then each key and value as a `QString` (`QDataStream.writeQString`), keys in `QMap` order, which is UTF-16 code-unit order (`sorted(..., key=lambda key: key.encode("utf-16-be"))`, not plain `sorted`, which differs above U+FFFF).
  - `map_from_bytes(data: bytes) -> dict[str, str]`: empty bytes give `{}`; pairs are accepted in any order; a truncated or corrupt stream gives `{}`, as `ds >> map` leaves an empty map and `KWallet::Wallet::readMap` still returns 0.
- **`WalletFolder`** (`walletfolder.py`): the C++ class over `(service, handle)` with the folder name `Kondor`. `ensure_exists`, `logins(origin) -> dict[str, str] | None` (`None` only when the D-Bus call failed; a missing entry reads as `{}`), `all_logins() -> SavedLogins | None` (through `map_list`), `write_logins`, `remove_origin`, `origins`. It serializes with `walletmap`.

### 5. `WalletSession` and `PasswordStore`

- **States:** `closed`, `opening`, `open`, `unavailable`, exposed as `state`. `setState` emits `stateChanged` and `changed` only when the state really changes.
- **`ensureOpen`:** only from `closed`. With `KONDOR_NO_KWALLET` set to a non-zero integer (`qEnvironmentVariableIntValue` semantics: `"1"` yes, `"0"`, `""` or `"abc"` no), go to `unavailable` without touching D-Bus. Otherwise go to `opening` and call `open_network_wallet()`; `False` → `unavailable`.
- **Opened:** on `opened(handle)`: a negative handle, or a folder that neither exists nor can be created, forgets the handle and goes to `unavailable`. Otherwise reload the user names, go to `open` and emit `changed` once more, as the C++ does.
- **Closed:** on `closed()`, forget the handle, clear the user names and go to `closed`.
- **`retry`:** ignored in `opening` and `open`; otherwise forget the handle, set the state to `closed` without emitting, and call `ensureOpen`.
- **User names:** a cache of origin → user names sorted case-insensitively (`key=str.casefold`), rebuilt from `all_logins()` after every change; origins with no logins are left out. `entries` lists one `{origin, host, username}` per cached user name; `contains` and `usernames` read the cache only. `password` and `credentials_for` read the wallet, only when `open`; `credentials_for` returns `[]` for an origin that is not in the cache, and the list is sorted by user name.
- **`save`:** refused (`False`) when not `open` or for an empty origin. Reads the origin's logins, sets the user name, writes them; `False` when the write fails; else reload the cache, emit `changed` and return `True`.
- **`remove`:** does nothing when not `open` or when the user name is not saved for the origin. Writes the remaining logins, or removes the entry when none is left; then reload and emit `changed`.
- **`copyPassword`:** copies the password with `PasswordClipboard.copy` when it is not empty. `copy_text` uses `copy_text`.
- **The unavailable notice flag** is a plain `bool` on the store, as in C++.
- **Instance:** `PasswordStore.instance()` creates one store with a `KWalletService`. The constructor takes an optional `WalletService`, so tests can pass a fake; it must not call D-Bus.

### 6. `PasswordClipboard`

- `copy(secret)`: a `QMimeData` with the text and `x-kde-passwordManagerHint` = `b"secret"`, set on `QGuiApplication.clipboard()`; remember the secret and start a single-shot timer (30,000 ms by default, a constructor argument for tests).
- On timeout: clear the clipboard only if its text still equals the remembered secret, then forget the secret.
- `copy_text(text)`: `clipboard.setText(text)`, with no hint and no timer change.

### 7. Origins

`passwordorigin.py` follows `passwordorigin.cpp`:

- `origin_of(url)`: lower-cased scheme, `http` or `https` only, a non-empty host; `QUrl.host(QUrl.ComponentFormattingOption.FullyEncoded)` lower-cased (so IDN hosts become `xn--…`), plus `:port` unless the port is `-1` or the scheme's default (80/443).
- `can_save_for(origin)`: `https` with a host, or `http` on `localhost` / `*.localhost`.
- `origin_from_input(text)`: trimmed; empty → `""`; prefix `https://` when `://` is missing; `origin_of`, then `""` unless `can_save_for`.
- `host_of_origin(origin)`: `QUrl(origin).host()`.

### 8. CSV import

- **Reader:** the character scanner of `csvreader.cpp`, state for state (quoted / unquoted field, `""` in quotes, `,`, `\n`, `\r`, `\r\n`; a row is kept only when it has content; a last row without a line break is kept). The bytes are decoded as UTF-8 with `errors="replace"` (like `QString::fromUtf8`), and one leading U+FEFF is dropped.
- **Columns:** `normalized_header` trims and lower-cases each name. `detect_format` checks the signatures in the C++ order (Bitwarden `login_password`; 1Password `otpauth`+`title`; Firefox `formactionorigin`; Firefox `httprealm`; KeePassXC `group`+`title`), then Chrome for exactly `name,url,username,password` with an optional `note`, else CSV. `find_columns` uses the C++ name lists in the C++ order.
- **Parse:** no rows → `EMPTY`; incomplete columns → `NOT_PASSWORD_EXPORT`; only a header → `EMPTY`. Each row: a `type` column that is not `login` (trimmed, lower-case) counts as `skipped_not_login`; no valid origin in the site cell (split on `[,\r\n]`, each part through `origin_from_input`, duplicates dropped) counts as `skipped_no_site`; an empty user name or password counts as `skipped_no_credentials` (once per row); otherwise one login per origin. A repeated origin + user name keeps its first position and takes the last password.
- **File:** `read_import_file(url: QUrl) -> ImportFile`: not a local file, not a regular file, or unopenable → `unreadable`; size above `20 * 1024 * 1024` → `tooLarge`; read at most limit + 1 bytes and refuse with `tooLarge` (after zeroing the buffer) when more came. Read into a `bytearray`, so it can be zeroed.
- **Plan:** `summarize_import` counts new, identical and conflicting logins against the saved ones, and the number of distinct conflicting origins. `merge_logins(saved: dict[str, str], logins, replace_conflicts) -> int` updates `saved` in place: new user names always, changed passwords only when replacing; it returns the number of changes.

### 9. Import flow

- **`ImportPreparation`:**
  - `start(url)` clears the pending import, remembers the file and reads + parses it on a worker thread (`threading.Thread(daemon=True)`, as `FilterListLoader` does), then emits `runningChanged`. The result always reaches the UI thread through a queued private signal, so `prepared` is never emitted inside `start`.
  - On the UI thread: describe the result (file error → failure; parse error → failure with `import_error_name`; saved logins unavailable → `walletUnavailable`; else keep `PendingImport(logins, saved)` and build `import_result`). Clear the running flag, emit `runningChanged`, then `prepared(info)`.
  - After parsing, zero the file bytes (`data[:] = bytes(len(data))`), as `source.data.fill('\0')` does.
  - `cancel()` drops the pending import; when running, it forgets the running job (a job counter or id) so its late result is ignored, and emits `runningChanged`. `is_running()` is `False` right after `cancel()`.
  - `take_pending()` returns the pending import and leaves an empty one.
- **`ImportCommit`:** groups the logins by origin; origins in sorted order; one origin per `QTimer.singleShot(0, …)`; for each origin, merge into a copy of the saved logins and write only when something changed; a failed write ends with `finished(-1)`; else `progressed` per origin and `finished(written)` at the end. `total()` and `done()` as in C++.
- **`ImportOutcome`:** `record`, `set_page_open`, `take` (returns the result and leaves `{}`), `claim_notification` (`{}` when there is no result, it was already claimed, the page is open, or the count is negative).
- **`PasswordStoreImport`** (the commands of `passwordstoreimport.cpp`):
  - `prepareImport(file)`: ignored while a commit runs; remembers `file.fileName()`; starts the preparation when the wallet is `open`, else emits `importPrepared(import_failure(file, "walletUnavailable"))` at once.
  - `commitImport(replace)`: ignored while a commit runs; takes the pending import, sets `replace_conflicts`, creates the `ImportCommit` with a writer that writes through `WalletFolder` (only when `open`), forwards `progressed` as `importDoneChanged`, emits `importRunningChanged`, `importDoneChanged`, `importTotalChanged`, and starts it.
  - On `finished(written)`: drop the commit, reload the user names and emit `changed`, record the outcome, emit the three progress signals, then `importFinished(written)`.
  - `cancelImport`, `setImportPageOpen`, `takeImportResult`, `claimImportNotification` as in C++. `importPreparing`, `importRunning`, `importDone` and `importTotal` read the preparation and the commit (0 without a commit).
  - `moveImportFileToTrash(file)`: `file.isLocalFile() and QFile.moveToTrash(file.toLocalFile())`.

### 10. Privacy

`PasswordStore` has no private-tab check in C++: the bridge (phase 8) and the QML decide. Keep that, and add no new callers. Nothing in this phase writes to disk: passwords go only to KWallet, and the import file is only read (or moved to the trash on request).

### 11. Tests

Each C++ case becomes a test with the same intent (umbrella item 9); data-driven C++ cases become `pytest.mark.parametrize` with the same rows and ids. Test functions have at most 20 lines. **No test talks to the real `kwalletd6`**: the store tests use a fake service, and `pytests/passwords/conftest.py` sets `KONDOR_NO_KWALLET=1` (autouse `monkeypatch`) so that an accidental `ensureOpen` on the real singleton never reaches D-Bus.

```
pytests/passwords/
  __init__.py
  conftest.py
  fakewallet.py
  test_passwordstore.py
  test_passwordstorewallet.py
  test_passwordclipboard.py
  test_walletmap.py
  test_passwordsui.py
  csvimport/
    __init__.py
    test_passwordimport.py
    test_passwordimportfile.py
    test_passwordimportplan.py
  importing/
    __init__.py
    test_passwordimportasync.py
    test_passwordimportoutcome.py
pytests/data/passwords/   (copies of tests/data/passwords/*.csv)
```

- **`fakewallet.py`:** `FakeWallet`, a `QObject` that implements `WalletService` in memory (folders, and entries as bytes), with switches for the failure paths: the open fails, the folder cannot be created, writes fail. `open_network_wallet()` emits `opened` through `QTimer.singleShot(0, …)`, so the store sees `opening` first. A `close()` helper emits `closed`.
- **`test_passwordstore.py`:** the C++ cases: `test_origin_of`, `test_can_save_for`, `test_origin_from_input` (parametrized with the C++ rows, through the `PasswordStore` slots), `test_contains_when_closed`, `test_starts_closed` (on `PasswordStore.instance()`).
- **`test_passwordstorewallet.py`** (new, with `FakeWallet` and `qtbot`):
  - `test_opens_through_opening_to_open`: `ensureOpen` gives `opening`, then `open`; the `Kondor` folder exists afterwards.
  - `test_disabled_by_environment_is_unavailable`: with `KONDOR_NO_KWALLET=1`, `ensureOpen` gives `unavailable` and the fake was never asked to open.
  - `test_failed_open_is_unavailable` and `test_folder_that_cannot_be_created_is_unavailable`.
  - `test_save_lists_the_entry_and_reads_the_password`: after `save`, `entries`, `contains`, `usernames` (sorted case-insensitively) and `password` agree, and `changed` was emitted.
  - `test_save_is_refused_when_closed_or_without_origin` and `test_save_reports_a_failed_write`.
  - `test_remove_last_login_removes_the_entry`: the fake has no `https://example.com` entry afterwards.
  - `test_saved_bytes_are_kwallet_maps`: the bytes the fake received decode with `map_from_bytes` to the saved logins.
  - `test_closed_wallet_forgets_the_logins`: after the fake emits `closed`, the state is `closed` and `entries` is empty.
  - `test_retry_after_unavailable_opens_again`.
  - `test_credentials_for_needs_a_cached_origin`.
  - `test_import_commit_writes_through_the_wallet`: `prepareImport` of a CSV file, wait for `importPrepared`, `commitImport(False)`, wait for `importFinished` with the number of new logins; `entries` lists them, and `importRunning` is back to `False`.
  - `test_prepare_import_without_wallet_fails_at_once`: with the store `closed`, `importPrepared` carries `walletUnavailable` and was emitted before `prepareImport` returned.
- **`test_walletmap.py`** (new):
  - `test_writes_the_qdatastream_bytes`: `{"ann": "pw"}` is `00000001 00000006 0061006e006e 00000004 00700077` (hex).
  - `test_orders_keys_like_qmap`: keys `"b"`, `"a"`, `"\U0001F600"`, `"�"` are written as `a`, `b`, `\U0001F600`, `�` (UTF-16 order).
  - `test_round_trips`, `test_reads_empty_bytes_as_empty`, `test_reads_truncated_bytes_as_empty`, `test_reads_null_strings_as_empty` (a key or value written with length `0xFFFFFFFF`).
- **`test_passwordclipboard.py`:** the three C++ cases (`qtbot.wait(100)` with a 20 ms timer for the last one).
- **`csvimport/`:** the nine `tst_passwordimport` cases (fixtures read from `pytests/data/passwords/`), the three `tst_passwordimportfile` cases (`tmp_path`; the large file made with `truncate`), and the four `tst_passwordimportplan` cases.
- **`importing/`:** the nine `tst_passwordimportasync` cases (`qtbot.waitSignal`, and `qtbot.assertNotEmitted` / a 300 ms wait for `cancelWhileReadingEmitsNothing`), and the three `tst_passwordimportoutcome` cases.
- **`test_passwordsui.py`:** the five `tst_passwordsui` cases, with the two QML documents of `extensionsuiharness.h` copied as strings (they use stub tabs, so they need only `PasswordStore` and the staged QML), loaded through `kondor_engine`. Small helpers for "find the item with this text", "find the items with this `objectName`" and "click the centre of an item" (`QTest.mouseClick` on the window) live in the test module, or in `pytests/qmlsupport.py` if they are short.
- **`pytests/core/test_singletons.py`** needs no change: it finds the new singleton through `kondor_types`.

### 12. API check result

After this phase, `python3 scripts/check-qml-api.py` reports **one more** class checked and one fewer not ported than on the PR's base (`PasswordStore`; `PasswordBridge` stays unported until phase 8), and exits 0.

## Acceptance criteria

- [ ] `kondor/passwords/` has the modules of item 1, and its `qmltypes.py` registers `PasswordStore`.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports one more class checked than on the base, with no problems.
- [ ] Every C++ case of the eight test files in "Context" has its pytest twin, and the new tests of item 11 exist and pass: `QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests`. No test talks to the real `kwalletd6`.
- [ ] `walletmap` writes the fixed bytes of item 11, and a password saved by the C++ app reads in Python and the other way round (manual test).
- [ ] The `python` and `build` jobs are green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt` or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec and a running Plasma session with KWallet enabled, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md). KWallet itself is the user's: save only test entries on `https://kondor-test.example`, and remove them at the end.

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests && python3 scripts/check-qml-api.py`: all pass, and the last reports one more class than `main`.
2. **Same D-Bus calls:** run `dbus-monitor "interface='org.kde.KWallet'"` while the C++ app (built from `main`) opens Settings → Passwords, and again while a short Python snippet from the PR checkout calls `PasswordStore.instance().ensureOpen()` (`QGuiApplication` with organization `KDE` and application `Kondor`). The `openAsync` arguments (`appid`, `wId` type, `handleSession`) and the folder are the same.
3. **Written by C++, read by Python:** in the C++ app, add a password for `https://kondor-test.example`, user `cpp-user`, password `from C++ é😀`. With the snippet, after `state` is `open`, `entries` lists it and `password("https://kondor-test.example", "cpp-user")` is `from C++ é😀`.
4. **Written by Python, read by C++:** with the snippet, `save("https://kondor-test.example", "py-user", "from Python ü")`. Restart the C++ app: Settings → Passwords lists both users for `kondor-test.example`, and revealing `py-user` shows `from Python ü`.
5. **Import:** with the snippet, `prepareImport` of `pytests/data/passwords/chrome.csv` reports `format` `Chrome` and `newCount` 2; `commitImport(False)` ends with `importFinished(2)`.
6. **Closing:** close the wallet from KWalletManager while the snippet runs: `state` becomes `closed` and `entries` is empty.
7. Remove the test entries (C++ app or snippet), and run `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- `src/passwords/bridge/` and `tst_passwordfill`: phase 8 (#170), with `Tab`.
- Calling `register_types()` from an app entry point (phase 11).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests or the workflows.
- Changes to `kondor/core/`, `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker, unless a phase-6 file shows a bug in them. In that case, ask first (`question`).
- New behavior: no other secret backends (Secret Service, files), no export, no new import formats, no change to the import limits or to the clipboard timeout.
- Translating Python strings, or running `pyside6-lupdate` (phase 12).

## Dependencies

#164 (core, merged). Umbrella #162. May run in parallel with #167, which touches other folders.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| `import` is a keyword and `csv` shadows a standard module: what are the folders called? | `importing/` and `csvimport/` (also under `pytests/passwords/`). The modules keep their C++ base names. |
| The C++ `PasswordStore` is spread over three `.cpp` files; Python cannot do that. | `PasswordStore` keeps the QML API and delegates to `WalletSession` (wallet state) and `PasswordStoreImport` (import commands), split by the same responsibilities as the C++ files. |
| How do the store tests run without KWallet? | A `WalletService` protocol with a real `KWalletService` (D-Bus) and an in-memory `FakeWallet` in `pytests/`. The byte format is tested on its own against fixed bytes (umbrella item 6). Real KWallet is only in the manual test. |
| `openAsync`'s `handleSession`: the umbrella said `false`. | Send what KF6Wallet's `Wallet::openWallet` sends (`true` in KF6), confirmed with `dbus-monitor` against the C++ app in manual test step 2; umbrella item 6 updated. |
| `allLogins` uses `KWallet::Wallet::mapList`, not `readMap`. | Use the D-Bus `mapList(handle, folder, appid)` (not the deprecated `readMapList`), and accept `QByteArray` or `bytes` values. |
| Where does `tst_passwordsui` go? | This phase: its QML uses stub tabs and needs only `PasswordStore`. `tst_passwordfill` tests `passwords.js` and moves with the bridge to phase 8. |
| Worker thread for the file parse? | `threading.Thread` with a queued signal back to the UI thread, the pattern of `FilterListLoader` (#165). PySide6 has no generic `QtConcurrent::run`. |
