# Python port 10b/12: Extensions: bridge (#218)

> **Issue:** [#218](https://github.com/lukasborges/kondor/issues/218) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 8 and 9, "Rules for every phase"), the phase 8 spec [`0170-python-tabs.md`](0170-python-tabs.md) (`Tab`, `TabModel`, `TabExtensionItems`, `TabSiteReload`, and `PasswordBridge`, the model for this bridge), the phase 9 spec [`0171-python-extensions-core.md`](0171-python-extensions-core.md) and the phase 10 spec [`0172-python-extensions-catalog.md`](0172-python-extensions-catalog.md) first. This phase builds on their modules, harnesses and conventions. This file details phase 10b and must follow the umbrella. Only the architect edits it.

## Objective

Port `src/extensions/bridge/` to Python, and port the extension tests that need a `Tab`, a web page or the extensions panel:

- **Same QML API:** `ExtensionBridge` is a creatable QML type in `Kondor` 1.0, with the same `tab` property and `pageApi()` invokable. `check-qml-api.py` pairs it with its C++ twin.
- **Same page API:** the object `PageScriptBridges.qml` registers on the web channel as `kondorExtensions` has the same `request(requestJson)` method. The unchanged `extensionruntime.js` and `channel.js` talk to the Python bridge exactly as they talk to the C++ one: same request object, same reply object, same error texts.
- **Same rules:** the token check, the turned-off and private-window checks, the permission per method, read-only storage in private windows and the `http`/`https`-only rule for `tabs.open` and `download` are the C++ ones.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes. The JS resources stay as they are.

## Context

- **Earlier phases.**
  - Phase 7 (#169) added `ProfileManager` (`defaultProfile()`, `createPrivateProfile()`, signal `profileCreated`) and `pagescripts.install(profile)`, which puts the `kondor-channel` script (Qt's `qwebchannel.js` + `channel.js`) on every profile. `scripts/build.py` already stages `:/scripts/channel.js`, `:/scripts/extensionruntime.js` and `:/scripts/usergm.js` in `build/python/kondor.rcc`.
  - Phase 8 (#170) added `Tab` (`Tab(profile, parent=None)`, `isPrivate`, the command slots `goBack`, `goForward`, `reload`, `closeTab`, `selectNeighborTab`, `openTab`, `downloadUrl` and their `…Requested` signals), `TabExtensionItems` (`tab.extensionItems`), `TabSiteReload`, `TabModel`, and `PasswordBridge` / `PasswordPageApi` in `kondor/passwords/bridge/`.
  - Phase 9 (#171) added `ExtensionManager` with `check_token`, `is_active`, `has_permission`, `display_name`, `register_profile`, `script_source`, `install_package`, `applyConfiguration`, `setEnabled`, `setSiteEnabled`, `setPinned`, `settingValues`; `state/extensionstorage.py` (the C++ `ExtensionStorage` functions in snake_case, returning `StorageWrite(is_written, error)` on writes); `userscripts/` (`parse_user_script_metadata`, `write_user_script_package`, `user_script_id`, `UserScriptSource`); and the test harness `pytests/extensions/extensionsharness.py`, `pageserver.py`, `conftest.py`.
  - Phase 10 (#172) added `ExtensionCatalog`, `pytests/extensions/catalog/`, `pytests/extensions/test_extensionsui.py`, and may have extended `pageserver.py`.
- **The scope** (about 525 lines with headers and JS):

  | C++ / JS file | What it does |
  | --- | --- |
  | `bridge/extensioncall.{h,cpp}` | `ExtensionCall` (`extensionId`, `token`, `method`, `arguments`); `parseExtensionCall(requestJson)` (fields from the JSON object `id`, `token`, `method`, `arguments`; anything malformed gives empty fields); `okReply(value = null)` and `errorReply(message)` (compact JSON `{"ok":true,"value":…}` / `{"error":…,"ok":false}`) |
  | `bridge/extensionbridge.{h,cpp}` | `ExtensionBridge` (`QML_ELEMENT`): property `tab` (a `QPointer<Tab>`, notify `tabChanged`), invokable `pageApi()`, C++-only `request(call)`. Refusals in order: no tab (`No tab`), a bad token (`Invalid extension token`), not active for the tab's privacy (`The extension is turned off`); then `handleBridgeCall` |
  | `bridge/extensionpageapi.{h,cpp}` | `ExtensionPageApi` (not a QML type, parented to the bridge): invokable `request(requestJson)` → `bridge.request(parseExtensionCall(requestJson))` |
  | `bridge/bridgecalls.{h,cpp}` | `BridgeContext` (`tab`, `call`); `handleBridgeCall`: the permission check, then the method table (`storage.get`, `storage.keys`, `storage.set`, `storage.remove`, `action.setChecked`, `tabs.back`, `tabs.forward`, `tabs.reload`, `tabs.close`, `tabs.next`, `tabs.previous`, `tabs.open`, `download`, `notify`), else `Unknown method: <method>` |
  | `bridge/channel.js`, `bridge/extensionruntime.js` | the page side; already staged, not ported (they are JS) |

- **The QML that uses it:** `qml/browser/view/PageScriptBridges.qml` creates `ExtensionBridge { tab: root.tab }` and calls `registerObject("kondorExtensions", extensionBridge.pageApi())`.
- **Tests to port** (every case):

  | C++ test | Cases |
  | --- | --- |
  | `bridge/tst_extensioncall` | `parsesTheRequestObject`, `malformedRequestGivesEmptyFields` (3 inputs), `bridgeRejectsUnknownTabsMethodAfterPermissionCheck` |
  | `bridge/tst_extensionbridge` | `storageQuota`, `storageIsPerExtension`, `bridgeRejectsWrongToken`, `bridgeRefusesDownloadWithoutPermission`, `bridgeRefusesTabsWithoutPermission`, `bridgeOffExtension` |
  | `bridge/tst_extensionbridgetabs` | `privateBridgeReadsButCannotWrite`, `privateBridgeRefusedWhenNotAllowed`, `tabCommandsEmitSignals`, `tabOpenAcceptsOnlyWebAddresses`, `unknownMethodIsRefused`, `toolbarItemCheckedStateIsPerTab` |
  | `bridge/tst_extensionpages` (real pages through the web channel) | `runsInNormalPagesWithSettingsAndStorage`, `settingChangeReachesTheOpenPage`, `toolbarActionReachesTheExtension`, `excludedPathDoesNotRunIt`, `privatePagesNeedPermissionAndGetReadOnlyStorage`, `disabledSiteDoesNotRunIt` |
  | `userscripts/tst_userscriptpages` | `runsStylesAndStoresValues`, `doesNotRunInPrivateProfile`, `runsWhereMatchOrIncludeAgrees` |
  | `tst_extensionspanel` (QML `ExtensionsPanel`, `SiteReloadBar`) | `listShowsOneRowPerExtension`, `rowIsDimmedWhenOffOnSite`, `rowOpensActions`, `backReturnsToListAndFocusesRow`, `actionKeepsPanelOpen`, `checkableActionShowsState`, `runOnSiteSwitchShowsReloadBar`, `privateTabHasNoSiteSwitchAndNoPin`, `hostIsHiddenOnNonWebPage`, `openAtShowsActions`, `pinButtonTogglesPin`, `actionRowShowsShortcut`, `checkableRowShowsShortcut`, `shortcutFollowsChangedSetting` |
  | `tst_extensionsreloadbar` | `reloadButtonRequestsReload`, `startingToLoadHidesReloadBar`, `togglingBackHidesReloadBar` |
  | `tst_pinnedtoolbar` (QML `ExtensionsToolButtons`) | `pinnedExtensionShowsVisibleButton`, `unpinRemovesButton`, `pinnedButtonOpensPanelOnExtension`, `pinnedFileIconFitsToolBarIconBox`, `pinnedThemeIconHasExtensionsButtonIconSize` |

  With their helpers `bridge/bridgeharness.h`, `bridge/extensionpageharness.h`, `extensionsuiharness.h` (the panel, reload bar and tool bar parts) and `panelfixture.h`. After this phase every C++ extension test has a pytest twin.

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior, error texts and edge cases as the C++, with the Python conventions of umbrella item 3 and the patterns of phases 8 and 9 (a struct becomes a dataclass, a helper namespace a module of functions, a C++ function table a `dict`).

### 1. Layout

```
kondor/extensions/
  qmltypes.py              + ExtensionBridge
  bridge/
    __init__.py
    extensioncall.py       ExtensionCall, parse_extension_call, ok_reply, error_reply, argument helpers
    bridgecalls.py         BridgeContext, handle_bridge_call, the method table, permission check
    bridgestorage.py       the storage.* and action.setChecked handlers
    bridgetabs.py          the tabs.*, download and notify handlers
    extensionbridge.py     ExtensionBridge
    extensionpageapi.py    ExtensionPageApi
```

No other `kondor/` module changes except `qmltypes.py` (one more `QmlType`). The split of the handlers over `bridgestorage.py` and `bridgetabs.py` is a suggestion for the size limits; the other module names are fixed.

### 2. `ExtensionCall` (`bridge/extensioncall.py`)

- **`ExtensionCall`** is a frozen dataclass: `extension_id: str`, `token: str`, `method: str`, `arguments: list[object]` (JSON values as `json.loads` gives them).
- **`parse_extension_call(request_json: str) -> ExtensionCall`**, as `QJsonDocument::fromJson(...).object()` and `QJsonValue::toString()` / `toArray()` behave:
  - `json.loads` failing, or a top-level value that is not an object, counts as `{}`;
  - `id`, `token` and `method` are the value when it is a `str`, else `""` (so `{"id":3}` gives `""`);
  - `arguments` is the value when it is a `list`, else `[]`.
- **Argument helpers** (C++ `arguments.at(i)` returns `undefined` past the end, never throws):
  - `argument(call, index) -> object` gives `None` past the end;
  - `string_argument(call, index) -> str` gives the value when it is a `str`, else `""`;
  - `bool_argument(call, index) -> bool` is `True` only for the JSON `true` (`QJsonValue::toBool`).
- **Replies** are compact JSON with sorted keys, as `QJsonDocument(QJsonObject).toJson(Compact)` writes them:
  - `ok_reply(value=None)` → `{"ok":true,"value":<value>}` (`null` when `None`);
  - `error_reply(message)` → `{"error":"<message>","ok":false}`;
  - written with `json.dumps(…, separators=(",", ":"), sort_keys=True, ensure_ascii=False)`. A `float` with an integral value is written as an integer, as Qt does (`42`, not `42.0`); convert it before dumping.

### 3. `handle_bridge_call` (`bridge/bridgecalls.py`)

- **`BridgeContext`** is a frozen dataclass: `tab: Tab`, `call: ExtensionCall`.
- **The method table** is a `dict[str, BridgeMethod]`, where `BridgeMethod` is a `NamedTuple` (`permission: str`, `handler: Callable[[BridgeContext], str]`), with the 14 rows of `kMethods` in the same order and permissions (`""` for storage and `action.setChecked`, `tabs` for every `tabs.*`, `downloads` for `download`, `notifications` for `notify`).
- **`required_permission(method)`:** `tabs` for any method that starts with `tabs.` (also unknown ones), else the row's permission, else `""`.
- **`handle_bridge_call(context) -> str`:**
  1. when the permission is not empty and `ExtensionManager.instance().has_permission(id, permission)` is false: `Permission denied: this needs the "<permission>" permission`;
  2. else the row's handler;
  3. else `Unknown method: <method>`.

  So `tabs.nope` without the `tabs` permission is denied, and with it is unknown (the `bridgeRejectsUnknownTabsMethodAfterPermissionCheck` case).
- **Handlers** (every text is the C++ one, untranslated, as C++ does not translate them):

  | Method | Behavior |
  | --- | --- |
  | `storage.get` | `The key must be a string` unless argument 0 is a `str`; else `ok_reply(value(id, key))` (`null` for a missing key) |
  | `storage.keys` | `ok_reply(keys(id))` (a JSON array of strings) |
  | `storage.set` | `Storage is read-only in private windows` when `tab.isPrivate`; then the key check; then `set_value(id, key, argument 1)`: `ok_reply()` when written, else `error_reply(write.error)` |
  | `storage.remove` | the same two refusals; then `remove_value(id, key)` and `ok_reply()` |
  | `action.setChecked` | `tab.extensionItems.setChecked(id, string_argument 0, bool_argument 1)`, `ok_reply()` |
  | `tabs.back`, `tabs.forward`, `tabs.reload`, `tabs.close`, `tabs.next`, `tabs.previous` | one table `dict[str, Callable[[Tab], None]]` calling `goBack()`, `goForward()`, `reload()`, `closeTab()`, `selectNeighborTab(1)`, `selectNeighborTab(-1)`; `ok_reply()` |
  | `tabs.open` | `QUrl(string_argument 0, QUrl.ParsingMode.StrictMode)`; unless it is valid with the scheme `http` or `https`: `Only http and https addresses can be opened`; else `tab.openTab(url, bool_argument 1)`, `ok_reply()` |
  | `download` | the same URL check with `Only http and https addresses can be downloaded`; else `tab.downloadUrl(url, string_argument 1)`, `ok_reply()` |
  | `notify` | `Notifier.instance().notify("<display_name(id)>: <string_argument 0>", string_argument 1, "preferences-plugin")`, `ok_reply()` |

  The storage handlers call phase 9's `state/extensionstorage.py` functions; they never write SQL. JSON values pass through unchanged between the call and the storage (phase 9 stores them as the compact JSON of a one-element array).

### 4. `ExtensionBridge` and `ExtensionPageApi`

- **`ExtensionBridge(parent=None)`** (`QObject`):
  - creates its `ExtensionPageApi(self)`;
  - property `tab` (type `Tab`, read/write, notify `tabChanged`), emitting only on a change; when the tab is destroyed, the bridge forgets it, the same way phase 8's `PasswordBridge` does (`QPointer`);
  - `pageApi` is `Slot(result=QObject)` and returns the API object;
  - C++-only `request(call: ExtensionCall) -> str`: the refusal, else `handle_bridge_call(BridgeContext(tab, call))`.
- **`refusal_for(call) -> str`** (`""` when allowed), in order: no tab → `No tab`; `not check_token(id, token)` → `Invalid extension token`; `not is_active(id, tab.isPrivate)` → `The extension is turned off`. Every refusal is an `error_reply`.
- **`ExtensionPageApi(bridge)`** (`QObject`, parent: the bridge): `request` is `Slot(str, result=str)` and returns `bridge.request(parse_extension_call(request_json))`. The web channel publishes its `QMetaObject`, so the method name and signature are what `extensionruntime.js` calls (`api.request(payload, callback)`). It is not a QML type.
- **Imports:** `extensionpageapi.py` must not import `extensionbridge.py` at run time (use `TYPE_CHECKING`); importing any module creates no manager, notifier or tab.

### 5. `qmltypes.py`

`QmlType(ExtensionBridge, "ExtensionBridge", QmlKind.CREATABLE)` joins the extension types of phases 9 and 10.

### 6. Tests

Each C++ case becomes a test with the same intent (umbrella item 9). Data-driven cases become `pytest.mark.parametrize` with the same rows and ids. Test functions have at most 20 lines. **No test talks to the internet:** pages come from phase 9's `pageserver.py` on `127.0.0.1`.

```
pytests/extensions/
  bridge/
    __init__.py
    bridgeharness.py           BridgeClient, BridgeFixture (fixture), token_of, sample_token, error_of
    extensionpageharness.py    PAGE_VIEW_QML, Page, PageHost, load_url, evaluate, wait_loaded, attribute,
                               run_in_application_world
    conftest.py                fixtures: bridge fixture, page host, profiles registered with the manager
    test_extensioncall.py
    test_extensionbridge.py
    test_extensionbridgetabs.py
    test_extensionpages.py
    test_bridgecalls.py
  panel/
    __init__.py
    panelfixture.py            PANEL_WINDOW_QML, PanelFixture, install_keyed
    conftest.py
    test_extensionspanel.py
    test_extensionsreloadbar.py
    test_pinnedtoolbar.py
  userscripts/
    test_userscriptpages.py
```

- **Why sub-folders:** `pytests/extensions/` already holds six files after phase 10; five more would pass the 10-file limit. The panel, reload bar and tool bar tests go to `panel/`, after `qml/extensions/panel/`.
- **UI helpers:** `extensionsuiharness.h`'s `createInWindow`, `childObject`, `itemWithText`, `clickCenterOf` and `findByName` are reused from what phases 9 and 10 put in `pytests/qmlsupport.py` or their own harness. If a helper exists only inside a phase 9/10 test module, move it to `pytests/qmlsupport.py` rather than copying it (no duplication). That move is the only change allowed in phase 9/10 test code, besides `pageserver.py` below.
- **The bridge harness** mirrors `bridgeharness.h`: `BridgeClient(bridge, id, token)` with `call(method, args=[]) -> dict` (the parsed reply) and `is_ok(method, args=[])`; `token_of(id)` reads the `"token":"…"` value from `script_source(id, 0, True)`; the fixture creates a `Tab(None)` and a bridge on it, and destroys both after the test. `remove_every_extension` runs after every test that installs.
- **The page harness** mirrors `extensionpageharness.h`: the same inline `WebEngineView` QML (`webChannel`, `webChannelWorld: WebEngineScript.ApplicationWorld`, the `run(code)` and `load(address)` functions), a `QQuickWindow` of 400 × 300, a `Tab(profile, view)` and an `ExtensionBridge(view)` per page, and `registerObject("kondorExtensions", bridge.pageApi())` on the view's channel. Waits use `qtbot.waitUntil` with the C++ timeouts (30 s for a load, 10 s for an attribute, 5 s for `run`). Fixed waits (`QTest::qWait(500)`) become `qtbot.wait(500)`.
- **Profiles:** as in the C++ `initTestCase`, a module fixture connects `ProfileManager.instance().profileCreated` to `ExtensionManager.instance().register_profile`, registers `defaultProfile()`, and disconnects at the end. Each test gets a fresh `createPrivateProfile()`. The page tests need the `staged_resources` fixture (for `channel.js` and `extensionruntime.js`) and are marked `no_qt_log` like phase 7's profile tests (Chromium logs to the Qt message handler).
- **`pageserver.py`:** the page tests need any path (`/`, `/again`, `/after-toggle`, `/excluded/page`) to answer an HTML page, as `pageserver.h` does. If phase 9/10's server only serves known paths, add a default body to it rather than writing a second server.
- **`test_pinnedtoolbar.py`** calls `QAccessible.setActive(True)` once, finds the pinned button by its accessible name (`QAccessible.queryAccessibleInterface(item).text(QAccessible.Text.Name)`), and measures the painted icon on `window.grabWindow()` with the same 22 px box and the same background-pixel rule. `TabModel` is already registered by `kondor_types`; no extra `qmlRegisterType`.
- **`test_userscriptpages.py`** installs the same `kScript` text through phase 9's `parse_user_script_metadata`, `write_user_script_package` and `install_package(PackageFile(path, "userscript", "", True), user_script_id(metadata))`, and uses the page harness from `bridge/extensionpageharness.py`.
- **New tests** (`test_bridgecalls.py`) for code the C++ tests only reach indirectly:
  - `test_replies_are_compact_json_with_sorted_keys`: `ok_reply()` is `{"ok":true,"value":null}`, `ok_reply(42.0)` is `{"ok":true,"value":42}`, `error_reply("x")` is `{"error":"x","ok":false}`, and a non-ASCII string stays unescaped;
  - `test_missing_arguments_are_refused_not_raised` (rows: `storage.get` with `[]` → `The key must be a string`, `tabs.open` with `[]` → `Only http and https addresses can be opened`, `action.setChecked` with `[]` → ok);
  - `test_tab_commands_reach_back_and_forward` (`backRequested`, `forwardRequested`);
  - `test_download_reaches_the_tab` (the sample repacked with the `downloads` permission: `downloadUrlRequested` with the URL and file name; a `file:` URL is refused with `Only http and https addresses can be downloaded`);
  - `test_notify_prefixes_the_extension_name` (`Notifier.instance` patched with a recorder: title `Sample Extension: t`, body `b`, icon `preferences-plugin`);
  - `test_destroyed_tab_gives_no_tab` (delete the tab, process events: `No tab`);
  - `test_page_api_keeps_the_channel_name` (the API's `QMetaObject` has the method `request(QString)` returning `QString`, and `pageApi()` returns the same object every time);
  - `test_page_api_forwards_to_the_bridge` (a request JSON for `storage.keys` with the sample's token gives `{"ok":true,"value":[]}`).

### 7. API check result

After this phase, `python3 scripts/check-qml-api.py` reports **one more** class checked (`ExtensionBridge`) and one fewer not ported than on the PR's base, and exits 0. `ExtensionPageApi` stays counted as "not ported", because it is no QML type; `test_page_api_keeps_the_channel_name` checks its API instead.

## Acceptance criteria

- [ ] `kondor/extensions/bridge/` has the modules of item 1, and `qmltypes.py` registers `ExtensionBridge` as a creatable type.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports one more class checked than on the base, with no problems.
- [ ] Every C++ case of the eight test files in "Context" has its pytest twin, and the new tests of item 6 exist and pass with `scripts/run-pytests.sh`. No test reaches the internet.
- [ ] Privacy (tests): a private tab reads extension storage but never writes or removes it, and an extension not allowed in private windows gets no answer there; user scripts do not run in private profiles.
- [ ] Every refusal and error text is the C++ one, byte for byte.
- [ ] The sample extension runs on a real page loaded through the Python bridge, writes its storage and reacts to a setting change and a toolbar action (tests and manual test).
- [ ] The `build` job is green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the JS resources or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md) shared by every step. The snippet is the phase 9 one (a `QApplication` after `QtWebEngineQuick.initialize()`, organization `KDE`, application `Kondor`, `build/python/kondor.rcc` registered, every ported `register_types()` called).

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && scripts/run-pytests.sh && python3 scripts/check-qml-api.py`: all pass, and the last reports one more class than `main`.
2. **A page through the bridge:** in the snippet, install the sample (`zipfile` over `pytests/data/extensions/sample`), register `ProfileManager.instance().defaultProfile()` with the manager, serve a small HTML page from a temp folder with `python3 -m http.server --bind 127.0.0.1`, and load it in a `QQuickView` holding the inline `WebEngineView` of the page harness with a `Tab`, an `ExtensionBridge` and `registerObject("kondorExtensions", bridge.pageApi())`.
   1. `document.documentElement.getAttribute('data-kondor-sample')` is `hello` and `data-kondor-storage` is `ok`.
   2. `extensionstorage` `value("sample", "lastGreeting")` is `hello`.
3. **Python → C++:** start the C++ app (built from `main`) on the same profile. Settings → Extensions lists the sample, and opening the same page there shows the same attributes.
4. **Private window:** in the snippet, load the page with `createPrivateProfile()`: the attribute stays empty. Allow the sample in private windows (`applyConfiguration("sample", {"privateAllowed": True})`), reload: `data-kondor-private` is `true` and `data-kondor-storage` mentions `read-only`; the stored value is unchanged.
5. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- Calling `register_types()`, `register_profile` or `pagescripts.install` from an app entry point, and `PageScriptBridges.qml` running in the Python app: phase 11 (#173).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests, the JS resources (`channel.js`, `extensionruntime.js`, `usergm.js`) or the workflows.
- Changes to `kondor/` outside `kondor/extensions/bridge/` and `kondor/extensions/qmltypes.py`, to `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker. If a phase-10b file shows a bug in them, ask first (`question`). The only earlier test code that may change is the helper move to `pytests/qmlsupport.py` and the default body of `pageserver.py` (item 6).
- New bridge methods, new permissions, translated bridge texts, or a different reply format.
- Translating Python strings, or running `pyside6-lupdate` (phase 12).

## Dependencies

#170 (phase 8: `Tab`, `TabModel`, `TabExtensionItems`, `TabSiteReload`, the `PasswordBridge` pattern) and #172 (phase 10: the rest of `kondor/extensions/`, so every extension type the panel's QML may reach exists, and the last phase 9/10 test harness changes). Umbrella #162. Phase 11 (#173) waits for this phase.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| Why a phase 10b? | The bridge is the only extension code that uses `browser/tab*`. Splitting it out of #171/#172 (2026-11-14) lets phases 9 and 10 run without waiting for the tabs (#170). |
| Are `channel.js` and `extensionruntime.js` ported? | No. They are page-side JS that runs unchanged; phase 7 already stages them. This phase keeps their contract: the `request` method on the `kondorExtensions` channel object and the reply object. |
| How is the C++ `QJsonValue` handling kept in Python? | Arguments are plain `json.loads` values, read through helpers that copy `QJsonValue::toString` / `toBool` and `QJsonArray::at` past the end, so a missing or wrongly typed argument is refused or defaulted instead of raising. Replies use sorted keys and integral numbers, as `QJsonDocument` writes them. |
| Are the bridge's error texts translated? | No: C++ does not translate them, and the page's extension sees them as `Error` messages, not the user. |
| Where do the panel, reload bar and pinned tool bar tests go? | `pytests/extensions/panel/`, after `qml/extensions/panel/`, because `pytests/extensions/` would otherwise pass the 10-file limit. They need a `Tab` (phase 8), so they could not go with phase 9. |
| `storageQuota` and `storageIsPerExtension` test `ExtensionStorage`, not the bridge. | They are ported as they are, in `test_extensionbridge.py`, because they live in `tst_extensionbridge.cpp` (umbrella item 9: every C++ case keeps its file). They overlap phase 9's `test_extensionstorage.py` on purpose. |
