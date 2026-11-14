# Python port 7/12: Browser profile, address and session (#169)

> **Issue:** [#169](https://github.com/lukasborges/kondor/issues/169) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 8 and 9, "Rules for every phase") and the phase 2 spec [`0164-python-core.md`](0164-python-core.md) first. This file details phase 7 and must follow the umbrella. Only the architect edits it.

## Objective

Port the part of `src/browser/` that does not need `Tab` or `TabModel` to Python, and port its tests:

- **Same QML API:** `ProfileManager`, `SearchSuggestions` and `ZoomManager` are QML singletons in `Kondor` 1.0. `check-qml-api.py` pairs them with their C++ twins.
- **Same data:** the Python app opens the same persistent web profile (storage name `kondor`, so cookies, logins and web storage carry over), reads and writes the same per-site zoom keys in `~/.config/KDE/Kondor.conf`, and reads and writes the same `session.json` format.
- **Same profiles:** every profile gets the same setup as in C++ (user agent, accept language, download path, spell check, ad blocker, download and notification routing, page scripts), and private profiles are off-the-record with permissions in memory.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Phase 2 (#164)** added `kondor/core/` (`Settings`, `Database`, `Notifier`, `qmlregistration`) and the pytest fixtures `isolated_profile`, `kondor_types`, `kondor_engine`, `qml_engine`, `staged_build` and `staged_resources`, plus `pytests/qmlsupport.py` (`create_object`, `load_component`, `error_text`, `captured_messages`). Phase 3 (#165) added `AdBlockManager.install(profile)`. Phase 4 (#166) added `DownloadManager.handle_request(download, is_private)`, `HistoryManager.clearAll()`, `kondor/browser/favicons/` and `kondor/browser/qmltypes.py` (which this phase extends). Phase 5 (#167) added `BookmarkManager`. Phase 6 (#168) touches only `kondor/passwords/` and may run in parallel.
- **The scope** (about 1,100 lines with headers):

  | C++ file | What it does |
  | --- | --- |
  | `browser/address/addressresolver.{h,cpp}` | `addressUrl`, `searchUrl`, `resolveAddress`: typed text → URL (host pattern, private IPv4 ranges and `localhost` get `http://`, explicit schemes go through `QUrl::fromUserInput`, everything else searches) |
  | `browser/address/suggestionlist.{h,cpp}` | `suggestionsFromJson`: the OpenSearch suggestions JSON (`["q",["a","b",…]]`) → at most 6 non-empty strings |
  | `browser/address/searchsuggestions.{h,cpp}` | QML singleton `SearchSuggestions`: invokables `request(text)`, `cancel()`; signal `suggestionsReady(QString text, QStringList items)`. One `QNetworkAccessManager`, one in-flight reply, the Google or DuckDuckGo endpoint by `Settings.searchEngine` |
  | `browser/profile/profilemanager.{h,cpp}` | QML singleton `ProfileManager`: property `homePage` (notify `homePageChanged`); invokables `defaultProfile()`, `createPrivateProfile()`, `resolveAddress(text)`, `addressUrl(text)`, `searchUrl(text)`, `clearCookiesAndCacheNow()`; signals `homePageChanged`, `profileCreated(QQuickWebEngineProfile *)`. C++-only API used by `TabSecurity` (phase 8) and `AppStartup` (phase 11): `markCertificateOverridden`, `isCertificateOverridden`, `profiles()`. Applies `Settings` changes (download directory, spell check) to every profile and clears cookies, cache and history on quit when `clearDataOnExit` is on |
  | `browser/profile/profilesetup.{h,cpp}` | `ProfileSetup::apply(profile)`: user agent, accept language, download path, spell check, ad blocker, download and notification routing; `applySpellCheck(profile)` |
  | `browser/profile/pagescripts.{h,cpp}` | `PageScripts::install(profile)`: the `kondor-channel` script (Qt's `qwebchannel.js` + `channel.js`, document creation) on every profile and the `kondor-passwords` script (`usernamefield.js` + `passwords.js`, document ready) on persistent profiles only |
  | `browser/profile/certificateoverrides.{h,cpp}` | `CertificateOverrides`: the hosts whose certificate error the user accepted, per profile, lower-cased; forgotten when the profile is destroyed |
  | `browser/session/sessionformat.{h,cpp}`, `sessionwindow.h` | `SessionTab`, `SessionWindow`; `SessionFormat::toJson(windows)` (version 2, compact, an empty URL written as `about:newtab`) and `fromJson(json)` (versions 1 and 2; invalid, unsupported and tab-less windows dropped, with a `qWarning`) |
  | `browser/tabs/closedtabs.{h,cpp}` | `ClosedTab`, `ClosedTabs`: the last 20 closed tabs of a `TabModel`, newest first in `toVariantList()` (`url`, `title`), `take(indexFromNewest)` |
  | `browser/zoommanager.{h,cpp}` | QML singleton `ZoomManager`: invokables `hostOf(url)`, `zoomFor(host)`, `setZoomFor(host, factor)`, `step(current, direction)`; signal `zoomChanged(QString host, qreal factor)`; the 15 zoom levels; per-site factors in `QSettings("KDE", "Kondor")` under `SiteZoom/<host>` |

- **Not in this phase:** `browser/tabs/tab*`, `browser/tabs/tabmodel*`, `browser/tabs/features/`, `browser/tabs/assignandnotify.h` (a template only `Tab` uses) and `browser/session/sessionmanager` (needs `Tab` and `TabModel`): phase 8 (#170). `browser/favicons/`: done in phase 4.
- **Tests to port** (every case; UI tests load the staged QML through `kondor_engine`):

  | C++ test | Cases |
  | --- | --- |
  | `tests/browser/address/tst_addressresolver.cpp` | `resolvesAddress` (20 rows), `addressUrls` (10 rows), `searchUrls` (5 rows) |
  | `tests/browser/address/tst_suggestionlist.cpp` | `keepsAtMostSixSuggestions`, `skipsEmptyAndNonStringEntries`, `returnsNothingForUnexpectedJson` |
  | `tests/browser/address/tst_addresssuggestions.cpp` (QML `browser/address/AddressSuggestions.qml`, which uses `BookmarkManager.search`, `HistoryManager.suggest`, `ProfileManager.addressUrl` / `searchUrl` and `Settings.searchEngineName`) | `visitRowComesFirst`, `searchRowFollowsTheVisitRow`, `searchRowShowsTheTypedText`, `plainWordOffersOnlyTheSearchRow`, `blankTextHasNoRows`, `addsBookmarkRows`, `addsHistoryRows`, `addsNetworkSuggestionRows`, `editingTheTextDropsNetworkSuggestions`, `keepsTheRowOrder`, `limitsRowsAndSkipsDuplicates`, `activateEmitsTheRowUrl` |
  | `tests/browser/tst_zoommanager.cpp` | `hostOf`, `saveAndReset`, `stepLevels` |
  | `tests/site/tst_permissiontypeinfo.cpp` (QML `site/PermissionTypeInfo.qml`, which needs no Python type) | `everyTypeHasIconLabelAndSentence` (11 rows), `hostComesFromTheOrigin` |
  | `tests/site/tst_sitepermissions.cpp` | only `profilesStoreNormalDecisionsAndKeepPrivateOnesInMemory`, which uses `ProfileManager` alone |

  The `Tab`-based tests move to phase 8 (#170): `tst_addressbar` (with `tests/data/AddressBarHost.qml`), `tst_recentlyclosedtabs`, `tst_pagecontextmenu`, `tst_sessionmanager`, the other four cases of `tst_sitepermissions` and all of `tst_sitepermissionsui`. The umbrella's phase table says so.
- **Qt WebEngine in tests:** this is the first phase whose tests create a real `QQuickWebEngineProfile`. The C++ tests that do (`tst_sitepermissions`, `tst_sessionmanager`) call `QCoreApplication::setAttribute(Qt::AA_ShareOpenGLContexts)` and `QtWebEngineQuick::initialize()` before the application object and run with `QTWEBENGINE_DISABLE_SANDBOX=1`. `packaging/python-proof/proof.py` shows the same order in Python.
- **Resources:** `scripts/build.py` stages `src/passwords/bridge/passwords.js`, `usernamefield.js` and `src/extensions/bridge/channel.js` under `:/scripts/` in `build/python/kondor.rcc` (`scripts/staging/resources.py`), which the `staged_resources` fixture registers and the app will register in phase 11. `:/qtwebchannel/qwebchannel.js` lives inside Qt's WebChannel library, which Qt WebEngine loads.

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior and edge cases as the C++, with the Python conventions of umbrella item 3. A C++ helper namespace becomes a module of functions.

### 1. Layout

```
kondor/browser/
  __init__.py
  qmltypes.py
  zoommanager.py
  address/
    __init__.py
    addressresolver.py
    searchsuggestions.py
    suggestionlist.py
  favicons/            (phase 4, unchanged)
  profile/
    __init__.py
    certificateoverrides.py
    pagescripts.py
    profilemanager.py
    profilesetup.py
  session/
    __init__.py
    sessionformat.py
    sessionwindow.py
  tabs/
    __init__.py
    closedtabs.py
```

The modules keep their C++ base names. Further splits for the size limits are allowed when the modules above keep their names (for example `profilecookies.py` for the cookie helpers of `profilemanager.cpp`). Phase 8 adds `tab*.py`, `tabmodel*.py`, `tabs/features/` and `session/sessionmanager.py` next to them.

### 2. `qmltypes.py`

```python
QML_TYPES = (
    QmlType(FaviconStore, "FaviconStore", QmlKind.SINGLETON),
    QmlType(ProfileManager, "ProfileManager", QmlKind.SINGLETON),
    QmlType(SearchSuggestions, "SearchSuggestions", QmlKind.SINGLETON),
    QmlType(ZoomManager, "ZoomManager", QmlKind.SINGLETON),
)
```

`register_types()` stays as it is. Importing the module must not create any instance, profile or network manager (`check-qml-api.py` imports it without a `QCoreApplication`).

### 3. Names and types

- **QML names:** the names QML sees keep their C++ names: `homePage`, `defaultProfile`, `createPrivateProfile`, `resolveAddress`, `addressUrl`, `searchUrl`, `clearCookiesAndCacheNow`, `profileCreated`, `request`, `cancel`, `suggestionsReady`, `hostOf`, `zoomFor`, `setZoomFor`, `step`, `zoomChanged`.
- **Slot and signal types:** `defaultProfile` and `createPrivateProfile` are `Slot(result=QQuickWebEngineProfile)`; `resolveAddress`, `addressUrl` and `searchUrl` are `Slot(str, result=QUrl)`; `profileCreated = Signal(QQuickWebEngineProfile)`; `suggestionsReady = Signal(str, "QStringList")`; `hostOf` is `Slot(QUrl, result=str)`; `zoomFor` is `Slot(str, result=float)`; `setZoomFor` is `Slot(str, float)`; `step` is `Slot(float, int, result=float)`; `zoomChanged = Signal(str, float)` (`check-qml-api.py` maps `qreal` to `double`).
- **Snake case** for everything QML does not see (umbrella item 3): `mark_certificate_overridden`, `is_certificate_overridden`, `profiles()` on the manager; `addressresolver.address_url`, `search_url`, `resolve_address`; `suggestionlist.suggestions_from_json`; `profilesetup.apply`, `apply_spell_check`; `pagescripts.install`; `sessionformat.to_json`, `from_json`; `CertificateOverrides.mark`, `is_overridden`, `forget`; `ClosedTabs.remember`, `take`, `is_empty`, `size`, `to_variant_list`; `zoommanager.LEVELS`.
- **Value types:** `SessionTab(url: QUrl, title: str)`, `SessionWindow(tabs: list[SessionTab], current_index: int)` and `ClosedTab(url: QUrl, title: str, index: int)` are dataclasses with the C++ fields. `ClosedTabs.MAX_CLOSED_TABS = 20`.
- **Strings:** nothing in these files is translated in C++, and nothing in this phase calls `translate`. The `qWarning` texts stay the same (`Kondor: ignoring invalid session file: …`, `Kondor: ignoring unsupported session file version`, `Cannot install the page script …`, `Web channel script resources not found: autofill and extensions are off`, `Password script resource not found: autofill is off`), written with `qWarning` from `PySide6.QtCore`.

### 4. Address resolving

`addressresolver.py` follows `addressresolver.cpp`:

- `address_url(text)`: trimmed; empty → `QUrl()`; an explicit scheme (`://` anywhere, or a `about:` / `data:` prefix) → `QUrl.fromUserInput(input)`; otherwise the host pattern of `urlForHostPattern` (the same regular expression, through `QRegularExpression` so the character classes match the C++), prefixed with `http://` when the host is `localhost` (case-insensitive) or an IPv4 address in `127/8`, `10/8`, `192.168/16` or `172.16/12`, else `https://`; no match → `QUrl()`.
- `search_url(text, search_template)`: the template with `%1` replaced by `QUrl.toPercentEncoding(text.strip())` decoded as UTF-8 (`str.replace`, as `QString::replace`, replaces every `%1`).
- `resolve_address(text, home_page: QUrl, search_template)`: blank → `home_page`; else `address_url`, or `search_url` when that is empty.
- Trimming is `str.strip()`, the twin of `QString::trimmed` for the whitespace the tests use.

### 5. `SearchSuggestions`

- **Endpoints**, as `endpointFor`: `google` → `https://suggestqueries.google.com/complete/search` with `client=firefox`; anything else → `https://duckduckgo.com/ac/` with `type=list`. `endpoint_url(text)` adds the endpoint parameter and then `q=<text>` with `QUrlQuery`, so the encoding stays Qt's.
- **Request:** `User-Agent: Kondor Browser` and `QNetworkRequest.Attribute.RedirectPolicyAttribute` = `QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy`.
- **`request(text)`:** trims, cancels the in-flight reply, does nothing for an empty text, else remembers the text and sends. **`cancel()`:** aborts and deletes the in-flight reply, if any, and forgets it first so its `finished` is ignored.
- **Reply:** only the current reply counts; on `finished`, forget it, `deleteLater`, and emit `suggestionsReady(pending_text, items)` with `suggestions_from_json(readAll())` on `NoError`, else `[]`.
- **Instance:** the constructor takes an optional `QNetworkAccessManager` (tests pass a fake, item 11); `SearchSuggestions.instance()` creates a real one, parented to the singleton. The constructor must not send anything.

`suggestionlist.py`: `suggestions_from_json(body: bytes) -> list[str]` parses with `QJsonDocument.fromJson` (so the accepted JSON is Qt's); the root must be an array whose second element is an array; keep the non-empty strings, at most 6.

### 6. `ProfileManager`

- **Instance and settings:** the constructor connects `Settings.homePageChanged` to `homePageChanged`, `downloadDirectoryChanged` to `apply_download_directory`, and `spellCheckEnabledChanged` / `spellCheckLanguagesChanged` to `apply_spell_check`, plus `QCoreApplication.instance().aboutToQuit` to `clear_data_on_exit`, as `DownloadManager` does. It creates no profile.
- **`defaultProfile()`:** created on first use: a `QQuickWebEngineProfile` with the manager as **parent** (so QML never takes ownership of it; a parentless `QObject` returned from a slot is garbage-collected by the QML engine), `setStorageName("kondor")` (what `WebEngineProfile { storageName: "kondor" }` does; the result is not off-the-record and keeps `persistentStoragePath` under `AppDataLocation/QtWebEngine/kondor`), `AllowPersistentCookies`, `PersistentPermissionsPolicy.StoreOnDisk`, then `setup_profile`, then the third-party cookie filter.
- **`createPrivateProfile()`:** a parentless-constructed `QQuickWebEngineProfile` with the manager as parent, `NoPersistentCookies`, `PersistentPermissionsPolicy.StoreInMemory`; appended to the private list and removed from it on `destroyed`; then `setup_profile`. It is off-the-record (test).
- **`setup_profile(profile)`:** `pagescripts.install`, `profilesetup.apply`, forget its certificate overrides on `destroyed`, then emit `profileCreated(profile)`.
- **Cookie filter:** `profile.cookieStore().setCookieFilter(callback)` where the callback returns `not request.thirdParty or not Settings.instance().blockThirdPartyCookies`, read on every call, as in C++.
- **`clearCookiesAndCacheNow()`:** `clearHttpCache()` and `cookieStore().deleteAllCookies()` on `defaultProfile()` (which creates it). **`clear_data_on_exit()`:** only when `Settings.clearDataOnExit` is on: the same on the default profile if it exists, then `HistoryManager.instance().clearAll()`.
- **`apply_download_directory()`** sets `downloadPath` on every profile; **`apply_spell_check()`** calls `profilesetup.apply_spell_check` on every profile. **`profiles()`** is the default profile (when created) followed by the private ones.
- **`homePage`** reads `Settings.homePage`; **`resolveAddress(text)`** is `resolve_address(text, QUrl(home_page), Settings.searchUrlTemplate)`; **`addressUrl`** and **`searchUrl`** call the module functions with the same template.
- **Certificate overrides** are a `CertificateOverrides` owned by the manager: `mark(profile, host)` ignores a `None` profile or an empty host and stores the host lower-cased; `is_overridden(profile, host)` is `False` for those and otherwise checks the lower-cased host; `forget(profile)`. Keyed by profile identity (`id(profile)` or the object itself in a `dict`; the entry goes with `forget` on `destroyed`, so a dead wrapper is never read).

### 7. `profilesetup.py` and `pagescripts.py`

- **`apply(profile)`**, in the C++ order: user agent (replace the `QtWebEngine/<token>` of `httpUserAgent()` with `Kondor/0.1`, same regular expression `QtWebEngine/[^ ]+`), `setHttpAcceptLanguage(QLocale().bcp47Name())`, `setDownloadPath(Settings.downloadDirectory)`, `apply_spell_check`, `AdBlockManager.instance().install(profile)`, route downloads, route notifications.
- **`apply_spell_check(profile)`:** `setSpellCheckLanguages(Settings.spellCheckLanguages)` then `setSpellCheckEnabled(Settings.spellCheckEnabled)`, in that order.
- **Downloads:** `profile.downloadRequested` → `DownloadManager.instance().handle_request(download, profile.isOffTheRecord())`. **Notifications:** `profile.presentNotification` → `Notifier.instance().notify(title, message, "preferences-desktop-notification")` and `notification.show()`; a `None` notification is ignored.
- **`pagescripts.install(profile)`:** read `:/qtwebchannel/qwebchannel.js` and `:/scripts/channel.js` with `QFile`; when either is missing, warn and stop (no passwords script either, as in C++). Build the `kondor-channel` script (`QWebEngineScript`: name, source `webchannel + "\n" + channel`, `InjectionPoint.DocumentCreation`, `ScriptWorldId.ApplicationWorld`, `runsOnSubFrames` true) and insert it into `profile.userScripts()`; then, only when the profile is not off-the-record, `kondor-passwords` (`:/scripts/usernamefield.js` + `"\n"` + `:/scripts/passwords.js`, `DocumentReady`, same world and sub-frames). A missing passwords resource warns and installs nothing. Insert with `profile.userScripts().insert(script)`; if PySide6 6.11.2 does not expose `QQuickWebEngineScriptCollection.insert`, use `QMetaObject.invokeMethod(collection, "insert", Q_ARG(QWebEngineScript, script))` as the C++ does, and record it in "Decisions". A failed insert warns `Cannot install the page script <name>`.
- **Resource availability:** `:/scripts/*.js` come from the staged `kondor.rcc`; `:/qtwebchannel/qwebchannel.js` is registered when Qt WebEngine's libraries load (`import PySide6.QtWebEngineQuick`, which `pagescripts.py` does anyway for the profile type). The test of item 11 checks both exist, so a missing resource is a test failure, not a silent warning.

### 8. Session format

`sessionformat.py` follows `sessionformat.cpp`, with `QJsonDocument` for both directions so the bytes and the accepted input match the C++ app:

- `to_json(windows: list[SessionWindow]) -> bytes`: `{"version": 2, "windows": [{"currentIndex": n, "tabs": [{"url": …, "title": …}, …]}, …]}` through `QJsonDocument.fromVariant(...).toJson(QJsonDocument.JsonFormat.Compact)`; an empty URL is written as `about:newtab`. `QJsonObject` keys are sorted, so the output is byte-identical to the C++ app's for the same windows (test).
- `from_json(json: bytes) -> list[SessionWindow]`: parse with `QJsonDocument.fromJson(json, error)`; not an object or a parse error → warn `Kondor: ignoring invalid session file: <errorString>` and return `[]`; `version` (`toInt()` semantics: missing or non-integer → 0) outside 1…2 → warn `Kondor: ignoring unsupported session file version` and return `[]`; version 1 reads the root as the single window; version 2 reads `windows`; each window takes `currentIndex` and its `tabs` (`url` `about:newtab` → empty `QUrl`); windows without tabs are dropped.

### 9. `ClosedTabs`

`remember(url, title, index)` appends and drops the oldest while over 20; `take(index_from_newest)` removes and returns the entry counted from the newest; `is_empty()`, `size()`; `to_variant_list()` lists newest first as `{"url": QUrl, "title": str}`. Who calls it (the `TabModel`, which skips private tabs) is phase 8.

### 10. `ZoomManager`

- `LEVELS = (0.3, 0.5, 0.67, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0)`; `EPSILON = 0.001`.
- Its own `QSettings("KDE", "Kondor")` (the same file as `Settings`), keys `SiteZoom/<host>` with `/` in the host replaced by `_`; `sync()` after every store.
- `hostOf(url)`: empty unless the scheme is `http` or `https`; else the host lower-cased.
- `zoomFor(host)`: `1.0` for an empty host; the stored value converted like `QVariant::toReal` (`float(value)`; a value that does not convert counts as `0.0`), and `1.0` unless it is above 0.
- `setZoomFor(host, factor)`: ignored for an empty host or when `abs(zoomFor(host) - factor) < EPSILON / 10`; a factor within `EPSILON` of 1.0 removes the key, else stores it; then emit `zoomChanged(host, 1.0 if default else factor)`.
- `step(current, direction)`: the first level above `current + EPSILON` (or the last level) for `direction > 0`; else the last level below `current - EPSILON` (or the first level).

### 11. Tests

Each C++ case becomes a test with the same intent (umbrella item 9); data-driven C++ cases become `pytest.mark.parametrize` with the same rows and ids. Test functions have at most 20 lines. **No test talks to the network**: `SearchSuggestions` is tested without sending, and `AddressSuggestions.qml` only reads `networkSuggestions` set by the test.

```
pytests/browser/
  __init__.py
  fakefaviconprovider.py       (phase 4)
  test_faviconstore.py         (phase 4)
  test_zoommanager.py
  address/
    __init__.py
    test_addressresolver.py
    test_addresssuggestions.py
    test_searchsuggestions.py
    test_suggestionlist.py
  profile/
    __init__.py
    test_certificateoverrides.py
    test_pagescripts.py
    test_profilemanager.py
    test_profilesetup.py
  session/
    __init__.py
    test_sessionformat.py
  tabs/
    __init__.py
    test_closedtabs.py
pytests/site/
  __init__.py
  test_permissiontypeinfo.py
```

- **`pytests/conftest.py`:** override pytest-qt's session fixture `qapp_cls` so that it calls `QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)` and `QtWebEngineQuick.initialize()` before returning the application class (pytest-qt creates the application from it after this fixture runs, which matches the C++ `main` order), and make `isolated_profile` also set `QTWEBENGINE_DISABLE_SANDBOX=1`, as the C++ `ctest` properties do. Every existing test keeps passing.
- **`test_addressresolver.py`:** the three C++ cases with their 35 rows, compared with `QUrl.toString(QUrl.ComponentFormattingOption.FullyEncoded)`.
- **`test_suggestionlist.py`:** the three C++ cases.
- **`fakenetwork.py`** (`pytests/browser/address/`): `FakeNetworkAccessManager(QNetworkAccessManager)` whose `get(request)` records the request and answers it locally: it calls the base `get` with a `data:` URL holding the body the test chose (`data:application/json,…`), which Qt serves without the network, or with a `foo://` URL to get a `ProtocolUnknownError` reply. Tests build `SearchSuggestions(fake)` directly, never the singleton.
- **`test_searchsuggestions.py`** (new):
  - `test_endpoint_follows_the_search_engine`: with `Settings.searchEngine` `google`, `endpoint_url("kde plasma")` is `https://suggestqueries.google.com/complete/search?client=firefox&q=kde%20plasma`; with `duckduckgo`, `https://duckduckgo.com/ac/?type=list&q=kde%20plasma`. Restore the setting afterwards.
  - `test_request_sets_the_user_agent_and_redirect_policy`: the recorded request has `User-Agent` `Kondor Browser` and the `NoLessSafeRedirectPolicy` attribute.
  - `test_reply_emits_the_parsed_suggestions`: a body `["kde",["kde plasma","kde neon"]]` gives `suggestionsReady("kde", ["kde plasma", "kde neon"])` (`qtbot.waitSignal`).
  - `test_failed_reply_emits_an_empty_list`.
  - `test_blank_text_sends_nothing_and_cancels`, `test_cancel_without_a_request_is_harmless`.
  - `test_reply_of_a_cancelled_request_is_ignored`: `cancel()` right after `request("kde")` leaves no `suggestionsReady` within 200 ms (`qtbot.assertNotEmitted`).
- **`test_addresssuggestions.py`:** the twelve C++ cases with the helpers of `addresssuggestionsharness.h` (`popup_typing`, `rows_of`, `field_of`, `has_row_with_icon`, `has_row_labeled`, `add_history`, `add_plasma_history`, `add_plasma_bookmark`) as module functions or a small fixture class; `SeededBookmarkFolder` becomes a fixture that removes the folder afterwards. The popup is loaded with `QQmlComponent(kondor_engine, QUrl.fromLocalFile(staged_build / "qml" / "Kondor" / "browser" / "address" / "AddressSuggestions.qml"))` as `test_downloadstatus.py` does. History rows are inserted through `kondor.core.database.sql.run`, as `pytests/history/historyrows.py` does; `clear_history` runs before every case.
- **`test_zoommanager.py`:** the three C++ cases, on `ZoomManager.instance()` with a fresh `QSettings("KDE", "Kondor")` to check the `SiteZoom/kde.org` key.
- **`test_certificateoverrides.py`** (new): `test_marks_hosts_case_insensitively_per_profile` (two `QObject`s as profiles), `test_ignores_missing_profile_and_empty_host`, `test_forget_drops_the_profile`.
- **`test_profilemanager.py`** (new, every test on `ProfileManager.instance()`; the default profile is created once per session):
  - `test_profiles_store_normal_decisions_and_keep_private_ones_in_memory`: the C++ case (default profile `StoreOnDisk`; private profile off-the-record and `StoreInMemory`).
  - `test_default_profile_is_the_persistent_kondor_profile`: `storageName()` is `kondor`, not off-the-record, `persistentCookiesPolicy()` is `AllowPersistentCookies`, `persistentStoragePath()` ends with `QtWebEngine/kondor` and lies under the isolated profile directory, the same object comes back on the second call, and its parent is the manager.
  - `test_private_profile_is_listed_until_destroyed`: `createPrivateProfile()` appears in `profiles()` after the default one; after `deleteLater()` and `qtbot.waitUntil`, it is gone.
  - `test_profile_created_is_emitted_for_every_profile` (`qtbot.waitSignal` on `profileCreated` around `createPrivateProfile()`).
  - `test_home_page_and_addresses_follow_settings`: set `Settings.homePage` to `https://home.example/` and `searchEngine` to `duckduckgo`: `homePageChanged` is emitted, `homePage` reads it, `resolveAddress("")` is the home page, `resolveAddress("kde")` is the DuckDuckGo search, `addressUrl("kde.org")` is `https://kde.org`, `searchUrl("a b")` uses the template. Restore the settings afterwards.
  - `test_certificate_overrides_are_per_profile_and_case_insensitive`: `mark_certificate_overridden(default, "KDE.org")`, then `is_certificate_overridden(default, "kde.org")` is `True` and `False` for a private profile.
  - `test_download_directory_change_reaches_every_profile`: set `Settings.downloadDirectory` to a `tmp_path`; the default and a private profile report it as `downloadPath()`. Restore afterwards.
  - `test_clear_data_on_exit_clears_history_only_when_enabled`: with `clearDataOnExit` off, emitting `QCoreApplication.instance().aboutToQuit` keeps a history row; with it on, the row is gone. Restore afterwards.
- **`test_profilesetup.py`** (new, on a fresh off-the-record `QQuickWebEngineProfile` parented to the test): `test_user_agent_names_kondor` (`httpUserAgent()` contains `Kondor/0.1` and not `QtWebEngine/`), `test_accept_language_is_the_locale` (`QLocale().bcp47Name()`), `test_download_path_and_spell_check_follow_settings` (set `spellCheckEnabled` `False` and `spellCheckLanguages` `["en-US"]`, apply, read back; restore afterwards). Download and notification routing need real requests and are covered by the manual test.
- **`test_pagescripts.py`** (new, with `staged_resources`): `test_resources_are_available` (`QFile.exists` for the four paths), `test_persistent_profile_gets_channel_and_passwords_scripts` (a `QQuickWebEngineProfile` with `setStorageName("pagescripts-test")`: `userScripts().find("kondor-channel")`, or the `collection` property filtered by name, has one script with `DocumentCreation`, `ApplicationWorld` and `runsOnSubFrames`; `kondor-passwords` has one with `DocumentReady`), `test_private_profile_gets_only_the_channel_script`.
- **`test_sessionformat.py`** (new):
  - `test_writes_the_compact_version_two_bytes`: one window, `current_index` 1, tabs `https://a.example/` "A" and an empty URL "" give exactly `{"version":2,"windows":[{"currentIndex":1,"tabs":[{"title":"A","url":"https://a.example/"},{"title":"","url":"about:newtab"}]}]}`.
  - `test_round_trips`, `test_reads_the_version_one_format` (the `tst_sessionmanager` input), `test_ignores_invalid_and_future_files` (`not json`, version 3, version 2 with an empty `tabs`, each `[]`, and the first two warn through `captured_messages`), `test_reads_about_newtab_as_an_empty_url`.
- **`test_closedtabs.py`** (new): `test_lists_newest_first`, `test_keeps_at_most_the_limit` (21 entries keep the last 20), `test_take_counts_from_the_newest`, `test_is_empty_and_size`.
- **`test_permissiontypeinfo.py`:** the two C++ cases, loading the staged `site/PermissionTypeInfo.qml` in `kondor_engine` and calling `iconFor`, `labelFor`, `sentenceFor` and `hostFor` with `QMetaObject.invokeMethod` (or through a small inline QML wrapper, as the harness does for `selectedText`), parametrized over the 11 rows, with the `QWebEnginePermission.PermissionType` values from `PySide6.QtWebEngineCore` and 9999 for `unknown`.
- **`pytests/core/test_singletons.py`** needs no change: it finds the three new singletons through `kondor_types`.

### 12. API check result

After this phase, `python3 scripts/check-qml-api.py` reports **three more** classes checked and three fewer not ported than on the PR's base (`ProfileManager`, `SearchSuggestions`, `ZoomManager`), and exits 0.

## Acceptance criteria

- [ ] `kondor/browser/` has the modules of item 1, and its `qmltypes.py` registers the four singletons of item 2.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports three more classes checked than on the base, with no problems.
- [ ] Every C++ case of the six test files in "Context" has its pytest twin, and the new tests of item 11 exist and pass: `QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests`. No test reaches the network.
- [ ] The default profile is persistent (`kondor`), parented to the manager; private profiles are off-the-record with `StoreInMemory` permissions and get no passwords script (tests).
- [ ] `to_json` writes the fixed bytes of item 11, and a session written by the C++ app reads in Python (manual test).
- [ ] Per-site zoom set by the C++ app reads in Python and the other way round (manual test).
- [ ] The `python` and `build` jobs are green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt` or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md) shared by every step. The snippet is a short Python script that creates a `QGuiApplication` after `QtWebEngineQuick.initialize()`, sets organization `KDE` and application `Kondor`, and calls `register_types()` of `kondor.core`, `kondor.adblock`, `kondor.downloads`, `kondor.history`, `kondor.bookmarks` and `kondor.browser`.

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests && python3 scripts/check-qml-api.py`: all pass, and the last reports three more classes than `main`.
2. **Same profile:** run the C++ app (built from `main`) on the isolated profile, visit `https://kde.org`, set its zoom to 125 % (Ctrl++ twice), open two more tabs, and quit. Then, with the snippet: `ProfileManager.instance().defaultProfile().persistentStoragePath()` is the `QtWebEngine/kondor` directory the C++ app created (it holds `Cookies`), `storageName()` is `kondor`, `httpUserAgent()` contains `Kondor/0.1` and no `QtWebEngine/`, and `userScripts().find(...)` returns `kondor-channel` and `kondor-passwords`.
3. **Private profile:** `createPrivateProfile()` is off-the-record, has only `kondor-channel`, and nothing new appears under the profile directory afterwards.
4. **Zoom both ways:** the snippet reads `ZoomManager.instance().zoomFor("kde.org")` as `1.25`, then calls `setZoomFor("example.org", 1.5)`. Restart the C++ app: `example.org` opens at 150 % and `kde.org` still at 125 %.
5. **Session:** `sessionformat.from_json(Path(<AppDataLocation>/session.json).read_bytes())` gives one window with the three tabs of step 2, and `to_json` of it returns the same bytes the file holds.
6. **Suggestions (network):** `SearchSuggestions.instance().request("kde")` emits `suggestionsReady("kde", items)` with 1 to 6 items; after setting `Settings.searchEngine` to `google`, the request URL (print it from `send`) starts with `https://suggestqueries.google.com/`.
7. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- `Tab`, `TabModel`, `tabs/features/`, `assignandnotify.h`, `SessionManager` and the tests that need them (listed in "Context"): phase 8 (#170).
- Calling `register_types()` from an app entry point, loading the main window or restoring a session (phase 11).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests or the workflows.
- Changes to `kondor/core/`, `kondor/adblock/`, `kondor/downloads/`, `kondor/history/`, `kondor/bookmarks/`, `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker, unless a phase-7 file shows a bug in them. In that case, ask first (`question`). The `pytests/conftest.py` changes of item 11 are allowed.
- New behavior: no other suggestion endpoints, no change to the zoom levels, the session version, the user agent or the closed-tabs limit.
- Translating Python strings, or running `pyside6-lupdate` (phase 12).

## Dependencies

#165 (ad blocking) and #166 (downloads, history, favicons), both merged; #167 (bookmarks, merged) for the address suggestions test. Umbrella #162. May run in parallel with #168, which touches only `kondor/passwords/` and `pytests/passwords/`.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| Which `tests/site/` tests belong to this phase? | Only `tst_permissiontypeinfo` (pure QML) and the first case of `tst_sitepermissions` (`ProfileManager` alone). The other cases and `tst_sitepermissionsui` build a `Tab` and move to phase 8 (#170), like `tst_addressbar`, `tst_recentlyclosedtabs` and `tst_pagecontextmenu`. |
| `ClosedTabs` has no C++ unit test of its own. | Port the class now (it needs no `Tab`) with its own unit tests; `tst_recentlyclosedtabs`, which drives it through `TabModel`, moves to phase 8. |
| `assignandnotify.h`? | Not ported here: a template only `Tab` uses. Phase 8 decides how its setters emit on change. |
| How do tests create web profiles in the pytest process? | `pytests/conftest.py` overrides pytest-qt's `qapp_cls` to call `QtWebEngineQuick.initialize()` (and `AA_ShareOpenGLContexts`) before the application is created, and sets `QTWEBENGINE_DISABLE_SANDBOX=1`, as the C++ WebEngine tests do. |
| Who owns the profiles? | The manager, as in C++ (`parent`). A parentless `QObject` returned by a slot gets JavaScript ownership in QML and would be garbage-collected. |
| How is the persistent profile created? | A default-constructed `QQuickWebEngineProfile` with `setStorageName("kondor")`, which is what the QML `WebEngineProfile { storageName: … }` element does, so the storage path is the same as the C++ app's. |
| JSON through `QJsonDocument` or `json`? | `QJsonDocument` for the session format and the suggestion list, so the written bytes and the accepted input are the C++ app's. |
