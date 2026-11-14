# Python port 8/12: Tabs (#170)

> **Issue:** [#170](https://github.com/lukasborges/kondor/issues/170) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 8 and 9, "Rules for every phase"), the phase 6 spec [`0168-python-passwords.md`](0168-python-passwords.md) and the phase 7 spec [`0169-python-browser-profile-address-session.md`](0169-python-browser-profile-address-session.md) first. This file details phase 8 and must follow the umbrella. Only the architect edits it.

## Objective

Port `Tab`, its feature groups, `TabModel`, `SessionManager` and `PasswordBridge` to Python, and port every test that needs them:

- **Same QML API:** `Tab`, `TabSecurity`, `TabPermissions`, `TabPasswords`, `TabSiteReload` and `TabExtensionItems` are uncreatable QML types, `TabModel` and `PasswordBridge` are creatable QML types, and `SessionManager` is a QML singleton, all in `Kondor` 1.0. `check-qml-api.py` pairs each one with its C++ twin.
- **Same behavior:** the Tab bridge pattern of AGENTS.md (state setters, `…Requested` command signals), the same tab order, pinning, closing and reopening rules, the same `session.json` written by the same triggers.
- **Same privacy:** private tabs are never remembered as closed tabs, never saved in the session, never offered password saving, filling or copying.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Earlier phases.** Phase 2 (#164) added `kondor/core/` and the pytest fixtures (`isolated_profile`, `kondor_types`, `kondor_engine`, `qml_engine`, `staged_build`, `staged_resources`, `desktop_style`) plus `pytests/qmlsupport.py`. Phase 6 (#168) added `kondor/passwords/` with the bridge API on `PasswordStore` (`is_open`, `usernames`, `credentials_for`, `copy_text`, `unavailable_notice_shown`, `set_unavailable_notice_shown`, slots `password`, `save`, `copyPassword`, `ensureOpen`) and the module functions `passwordorigin.origin_of`, `can_save_for` and `host_of_origin`, plus `pytests/passwords/fakewallet.py`. Phase 7 (#169) adds `kondor/browser/profile/` (`ProfileManager` with `defaultProfile()`, `createPrivateProfile()`, `mark_certificate_overridden`, `is_certificate_overridden`), `kondor/browser/session/` (`sessionformat.to_json` / `from_json`, `SessionTab`, `SessionWindow`), `kondor/browser/tabs/closedtabs.py` (`ClosedTabs`, `ClosedTab`), the `qapp_cls` override that initializes Qt WebEngine in `pytests/conftest.py`, and `QTWEBENGINE_DISABLE_SANDBOX=1` in `isolated_profile`.
- **The scope** (about 2,300 lines with headers):

  | C++ file | What it does |
  | --- | --- |
  | `browser/tabs/tab.{h,cpp}`, `tabcommands.cpp` | `Tab` (`QML_UNCREATABLE`): 21 read-only state properties with their change signals and `Q_INVOKABLE` setters, the constant `profile`, `isPrivate` and five feature groups, 23 command invokables that only emit their `…Requested` signal (plus `setPdfFinished` → `pdfFinished`), and the guarded commands `navigateTo`, `showNewTabPage`, `exitFullScreen`, `toggleReaderMode`. `setUrl` also leaves the New Tab page for a real page, denies pending permissions on an origin change, and updates `security` and `passwords`. `setPinned` is C++-only (the model calls it) |
  | `browser/tabs/assignandnotify.h` | `assignAndNotify(member, value, notify)`: assign and notify only on a real change; `qreal` compared with `qFuzzyCompare` |
  | `browser/tabs/tabmodel.{h,cpp}`, `tabmodelclosing.cpp` | `TabModel` (`QML_ELEMENT`, role `tab`): properties `count`, `currentIndex`, `currentTab`, `pinnedCount`, `canReopenClosedTab`, `recentlyClosed`, `privateTabs` (writable); invokables `addTab(isPrivate = false, initialUrl = QUrl())`, `addTabWithProfile`, `indexOfTab`, `closeTab`, `closeTabObject`, `reopenClosedTab()` / `reopenClosedTab(int)`, `moveTab`, `duplicateTab`, `closeOtherTabs`, `closeTabsToTheRight`, `setPinned`, `setCurrentIndex` |
  | `browser/tabs/features/tabsecurity.{h,cpp}` | `TabSecurity`: `state` (`local`, `insecure`, `secure`, `error`), the pending certificate error (`certificateErrorPending`, `…Url`, `…Description`, `…Overridable`), `setPendingCertificateError`, `acceptCertificateError`, `rejectCertificateError` and their `…Requested` signals; overrides go through `ProfileManager` |
  | `browser/tabs/features/tabpermissions.{h,cpp}` | `TabPermissions`: a queue of `QWebEnginePermission`; `pending` (the first one as a `QVariant`, or invalid), `enqueue`, `answer(grant)`, C++-only `denyAll()` |
  | `browser/tabs/features/tabpasswords.{h,cpp}` | `TabPasswords`: `prompt` (`""`, `save`, `walletUnavailable`), `promptUsername`, `promptHost`, `host`, `usernames`; invokables `savePending`, `neverSavePending`, `dismissPrompt`, `fill`, `copyUsername`, `copyPassword`; C++-only `offerSave`, `showWalletNotice`, `updateUsernamesFor`; signal `fillRequested`. Every action is a no-op on a private tab |
  | `browser/tabs/features/tabsitereload.{h,cpp}` | `TabSiteReload`: the extension toggles since the last load (`isPending`, `extensionName`, `willRun`; `recordToggle`, `dismiss`; signal `changed`) |
  | `browser/tabs/features/tabextensionitems.{h,cpp}` | `TabExtensionItems`: checked state of extension menu items per tab (`isChecked`, `setChecked`, `trigger`; signals `changed`, `triggered`) |
  | `browser/session/sessionmanager.{h,cpp}` | QML singleton `SessionManager`: `watch(model)`, `save(model)`; C++-only `savedWindows()`. Saves `AppDataLocation/session.json` 2 s after a change (count, current index, rows removed or inserted, a tab's `urlChanged`), on quit, and on `save`; skips private tabs, writes nothing while only private windows remain, writes with `QSaveFile` |
  | `passwords/bridge/passwordbridge.{h,cpp}` | `PasswordBridge` (`QML_ELEMENT`): property `tab` (a `QPointer<Tab>`), invokables `pageApi()` and `fill(username)`. `PasswordPageApi` (not a QML type; the object `PageScriptBridges.qml` registers as `kondorPasswords` on the web channel): invokables `formSubmitted(origin, username, password)` and `credentialsFor(origin)`; signals `credentialsChanged`, `fillRequested(origin, username, password)` |

- **Who uses them in QML:** `qml/app/BrowserWindow.qml` creates `TabModel {}`; many files declare `required property TabModel tabs`; `qml/browser/view/PageView.qml` calls `tab.permissions.enqueue(permission)`; `qml/site/PermissionBar.qml` reads `tab.permissions.pending` (`origin`, `permissionType`) and calls `answer`; `qml/browser/view/PageScriptBridges.qml` creates `PasswordBridge {}` and registers `pageApi()`; `qml/app/window/WindowTabController.qml` and `WindowCloseGuard.qml` call `SessionManager.watch` / `save`. `src/app/windows/windowlaunch.cpp` (phase 11) reads `savedWindows()`.
- **Tests to port** (every case; UI tests load the staged QML through `kondor_engine`):

  | C++ test | Cases |
  | --- | --- |
  | `tests/browser/tabs/tst_tabmodel.cpp` | `startsEmpty`, `addsAndActivatesTabs`, `closingCurrentMiddleSelectsNext`, `closingCurrentLastSelectsPrevious`, `closingBeforeCurrentShiftsIndex`, `closingAllTabsClearsCurrent`, `setCurrentIndexIgnoresOutOfRange`, `privateTabUsesAnotherProfile`, `privateWindowKeepsEveryTabPrivate` |
  | `tests/browser/tabs/tst_tabnewtabpage.cpp` | `tabsStartOnNewTabPage`, `emptyNavigationDoesNothing`, `navigateLeavesNewTabPage`, `showNewTabPageRestoresIt`, `aboutBlankKeepsNewTabPage`, `closedNewTabPageIsNotRemembered` |
  | `tests/browser/tabs/tst_tabpinning.cpp` | `pinningMovesTabToEndOfPinnedGroup`, `unpinningMovesTabToStartOfUnpinnedTabs`, `moveTabKeepsTheCurrentTabSelected` |
  | `tests/browser/tabs/tst_recentlyclosedtabs.cpp` | `reopenClosedTabRestoresPosition`, `privateTabsAreNotReopened`, `recentlyClosedListsNewestFirst`, `reopenClosedTabByIndex`, `privateTabsAreNotInRecentlyClosed`, `recentlyClosedKeepsAtMostTheLimit` |
  | `tests/browser/tabs/tst_tabsecurity.cpp` | `securityStateFollowsScheme`, `acceptingTheErrorClearsItAndAnswersTheView`, `overrideKeepsTheErrorStateWhenComingBack`, `overrideReachesEveryTabOfTheSameProfile`, `privateTabNeverInheritsTheOverride`, `rejectCertificateErrorClearsThePendingError` |
  | `tests/browser/tabs/tst_tabpasswords.cpp` | `privateTabNeverOffersToSave`, `neverSaveAddsTheOriginOnce`, `walletNoticeReplacesTheSavePrompt`, `dismissClearsThePrompt`, `privateTabDoesNotCopy`, `hostFollowsUrl` |
  | `tests/browser/tabstrip/` (harness `tabstripharness.h`, `qml/browser/tabstrip/TabStrip.qml`) | `tst_tabstripwidths` (11 cases), `tst_tabstripclosing` (5), `tst_tabdrag` (6), `tst_tabdragscroll` (3), `tst_tabdragrelease` (5), `tst_tabstripaccessibility` (1), `tst_tabstripscroll` (`newCurrentTabIsScrolledIntoView`, `emptyAreaIsOnlyOutsideTabsAndButtons`); `tst_tabstrip.cpp` is only their `main` |
  | `tests/browser/address/tst_addressbar.cpp` (harness `addressbarharness.h`, `tests/data/AddressBarHost.qml`) | `completesAKnownHostInline`, `backspaceAfterACompletionDoesNotCompleteAgain`, `downAndUpMoveThroughTheSuggestions`, `escapeRestoresTheTypedTextAndClosesTheSuggestions`, `enterNavigatesTheCurrentTab`, `switchingTheCurrentTabShowsItsUrl` |
  | `tests/browser/tst_pagecontextmenu.cpp` (cases in `pagecontextmenucases.h`) | `showsTheBlocksOfTheRequest` (every data row), `neverDoublesOrEndsWithASeparator` |
  | `tests/browser/tst_sessionmanager.cpp` | `savesEveryNormalWindow`, `keepsTheSessionWhenOnlyPrivateWindowsRemain`, `readsTheVersionOneFormat`, `ignoresInvalidAndFutureFiles`, `savesNewTabPageAsAboutNewTab` |
  | `tests/site/tst_sitepermissions.cpp` (harness `sitepermissionsharness.h`) | `answersQueuedPermissionsInOrder`, `navigatingAwayDeniesPendingPermissions`, `navigatingWithinSameOriginKeepsPendingPermissions`, `navigatingToAnotherOriginDeniesPendingPermissions` (the `ProfileManager` case is phase 7's) |
  | `tests/site/tst_sitepermissionsui.cpp` | `requestBarShowsThePendingPermission`, `answeringTheRequestBarGrantsAndHidesIt`, `dialogListsDecisions`, `dialogRevokesDecisions` |
  | `tests/passwords/tst_passwordfill.cpp` (tests `passwords.js` with a fake channel) | `fillsUsernameOnUsernameOnlyStep`, `fillsUsernameAndPasswordOnPasswordStep`, `fillsNothingWithoutUsernameField`, `looksUpCredentialsOnUsernameOnlyPage`, `doesNotLookUpCredentialsWithoutLoginField`, `looksUpCredentialsOnceWhenFieldAppearsLater` |

  `TabSiteReload`, `TabExtensionItems` and `PasswordBridge` have no C++ unit test of their own (the extension tests drive the first two in phases 10 and 10b): this phase adds Python unit tests for them (item 10).
- **Not in this phase:** the extension tests that build a `Tab` (`tests/extensions/bridge/tst_extensionbridgetabs.cpp`, `tst_extensionspanel`, `panelfixture.h`): phases 10 and 10b. `tests/app/` (window launch, which reads `savedWindows()`): phase 11.

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior and edge cases as the C++, with the Python conventions of umbrella item 3.

### 1. Layout

```
kondor/browser/tabs/
  __init__.py
  assignandnotify.py
  closedtabs.py          (phase 7, unchanged)
  tab.py                 Tab
  tabcommands.py         TabCommands
  tabloadstate.py        TabLoadState
  tabviewstate.py        TabViewState
  tabmodel.py            TabModel
  tabmodelclosing.py     TabModelClosing
  tabmodelrows.py        TabModelRows
  features/
    __init__.py
    tabextensionitems.py
    tabpasswords.py
    tabpermissions.py
    tabsecurity.py
    tabsitereload.py
kondor/browser/session/
  sessionmanager.py      (next to phase 7's sessionformat.py and sessionwindow.py)
kondor/passwords/bridge/
  __init__.py
  passwordbridge.py
  passwordpageapi.py
```

The bridge goes in its own `bridge/` sub-folder, as in `src/passwords/bridge/`. `kondor/browser/tabs/` ends with 10 files, the limit: do not add another one there.

### 2. Splitting `Tab` and `TabModel`

A Python class lives in one module, and `Tab` (about 100 members) and `TabModel` do not fit in 200 lines. Split each one into a **single-inheritance chain of `QObject` subclasses**, one module per link, and register only the last class:

- `TabCommands(QObject)`: the 24 command signals and the 19 slots that only emit them (`goBack` … `downloadUrl`, `setPdfFinished`).
- `TabLoadState(TabCommands)`: `title`, `iconUrl`, `progress`, `loading`, `canGoBack`, `canGoForward`, `zoomFactor` with their change signals and setters.
- `TabViewState(TabLoadState)`: `pinned`, `findMatches` / `findActiveMatch`, `isFullScreen`, `devToolsOpen`, `readerAvailable`, `readerActive`, `crashed` / `crashReason` / `crashExitCode` with their signals and setters.
- `Tab(TabViewState)`: the constructor, `profile`, `isPrivate`, `url`, `newTabPage`, the five feature groups, `setUrl`, `navigateTo`, `showNewTabPage`, `exitFullScreen`, `toggleReaderMode` and the C++-only `set_pinned`.
- `TabModelRows(QAbstractListModel)`: the tab list, `rowCount` / `data` / `roleNames` (`TAB_ROLE = Qt.ItemDataRole.UserRole + 1`, role name `tab`), `count`, `currentIndex`, `currentTab`, `pinnedCount`, `setCurrentIndex`, and the private helpers that insert and remove rows (`insert_tab`, `insert_row`, `remove_row`, `profile_for`, `fix_current_after_removal`, `keep_current_when_inserted_before`, `follow_current_tab`).
- `TabModelClosing(TabModelRows)`: `closeTab`, `closeTabObject`, `reopenClosedTab`, `closeOtherTabs`, `closeTabsToTheRight`, `canReopenClosedTab`, `recentlyClosed` and `remember_closed`, with the `ClosedTabs` of phase 7.
- `TabModel(TabModelClosing)`: `addTab`, `addTabWithProfile`, `indexOfTab`, `moveTab`, `duplicateTab`, `setPinned`, `privateTabs`.

Signals and properties declared on a base link are part of the final class's `QMetaObject`, so QML and `check-qml-api.py` see one `Tab` and one `TabModel` with the C++ members. The member split above is a suggestion: move members between links when the size limits need it, but keep the module names and register only `Tab` and `TabModel`. Python's `Tab` and `TabModel` take the same constructor arguments as C++ (`Tab(profile, parent=None)`, `TabModel(parent=None)`).

### 3. `qmltypes.py`

`kondor/browser/qmltypes.py` (phase 7's, extended):

```python
QmlType(Tab, "Tab", QmlKind.UNCREATABLE),
QmlType(TabSecurity, "TabSecurity", QmlKind.UNCREATABLE),
QmlType(TabPermissions, "TabPermissions", QmlKind.UNCREATABLE),
QmlType(TabPasswords, "TabPasswords", QmlKind.UNCREATABLE),
QmlType(TabSiteReload, "TabSiteReload", QmlKind.UNCREATABLE),
QmlType(TabExtensionItems, "TabExtensionItems", QmlKind.UNCREATABLE),
QmlType(TabModel, "TabModel", QmlKind.CREATABLE),
QmlType(SessionManager, "SessionManager", QmlKind.SINGLETON),
```

and `kondor/passwords/qmltypes.py` gets `QmlType(PasswordBridge, "PasswordBridge", QmlKind.CREATABLE)`. `PasswordPageApi` is not registered (it is not a QML type in C++ either). Importing these modules creates no instance.

### 4. Names and types

- **QML names** keep their C++ names exactly (umbrella item 3), including every setter `Tab` exposes as an invokable (`setTitle`, `setUrl`, `setFindResult`, `setCrashed`, …).
- **Property types:** `qreal` → `float`, `QUrl` → `QUrl`, `QStringList` → `"QStringList"`, `QVariantList` → `"QVariantList"`, `QVariant` → `"QVariant"`, `QQuickWebEngineProfile *` → `QQuickWebEngineProfile`, the feature groups and `currentTab` → their Python classes. Constant properties use `constant=True`; `privateTabs` and `PasswordBridge.tab` are writable.
- **Default arguments:** a C++ invokable with default arguments has one overload per argument count, and `check-qml-api.py` expects them all. Stack one `@Slot` per count on the same method: `setCrashed` takes 1, 2 or 3 arguments; `addTab` takes 0, 1 or 2; `reopenClosedTab` takes 0 or 1.
- **Returned objects:** `addTab` and `addTabWithProfile` are `Slot(…, result=Tab)` (or `QObject` if PySide6 refuses a Python class there; record it in "Decisions"). Every `Tab` is parented to its model, so QML never garbage-collects it (#169 decision "Who owns the profiles?"). `PasswordBridge.pageApi` is `Slot(result=QObject)`; the API object is parented to the bridge.
- **Snake case** for what QML does not see: `Tab.set_pinned`; `TabSecurity.update_for`, `clear_pending_certificate_error`; `TabPermissions.deny_all`; `TabPasswords.offer_save`, `show_wallet_notice`, `update_usernames_for`; `SessionManager.saved_windows()`; `PasswordBridge.form_submitted`, `credentials_for`.
- **`CertificateError`** becomes a frozen dataclass (`url: QUrl`, `description: str`, `overridable: bool`, defaults `QUrl()`, `""`, `False`), compared with `==`.
- **Strings:** nothing here is translated. The `qWarning` texts stay the same (`Kondor: cannot write the session file <path>`, `Kondor: cannot commit the session file <path>`).

### 5. `assignandnotify.py`

`assign_and_notify(owner, attribute, value, signal)`: when the stored value is the same, do nothing; else `setattr` and `signal.emit()`. "The same" is `==`, except for two `float`s, which use `qFuzzyCompare`'s rule: `abs(a - b) * 1e12 <= min(abs(a), abs(b))`. A unit test pins the float rule (`0.0` vs `0.0` is the same, `0.0` vs `1e-13` is not, `1.0` vs `1.0 + 1e-13` is).

### 6. `Tab` and its feature groups

Follow `tab.cpp`, `tabcommands.cpp` and the five `features/*.cpp` line by line:

- **Constructor:** `is_private = profile is not None and profile.isOffTheRecord()`; create `TabSecurity(profile, self)`, `TabPermissions(self)`, `TabPasswords(is_private, self)`, `TabSiteReload(self)`, `TabExtensionItems(self)`. Initial state: `newTabPage` `True`, `zoomFactor` `1.0`, `security.state` `local`, everything else empty, zero or `False`.
- **`setUrl(url)`**, in this order: a real page (not empty and not `about:blank`) leaves the New Tab page; an origin change (scheme and host compared case-insensitively, plus port; either URL empty counts as a change) calls `permissions.deny_all()`; then, only when the URL changed, store it, `security.update_for(url)`, `passwords.update_usernames_for(url)` and emit `urlChanged`.
- **`setLoading(True)`** dismisses `siteReload` first. **`setFindResult`** and **`setCrashed`** emit once for the whole group; `setCrashed(False, …)` clears the reason and exit code.
- **`navigateTo(url)`:** an empty URL does nothing; else clear the pending certificate error, leave the New Tab page, emit `navigationRequested(url)`. **`showNewTabPage()`:** nothing when already on it; else clear the pending error, set it, emit `newTabPageRequested`. **`exitFullScreen()`** emits only in full screen; **`toggleReaderMode()`** only when reader mode is available or active.
- **`TabSecurity`:** state from the scheme (pending error → `error`; `https` → `error` with a certificate override for the host on this tab's profile, else `secure`; `http` → `insecure`; anything else → `local`); `setPendingCertificateError` ignores the same error twice; `acceptCertificateError` marks the override (the error URL's host, or the page's host when empty) through `ProfileManager.instance().mark_certificate_overridden`, clears the error and emits `acceptCertificateErrorRequested`; `rejectCertificateError` clears it and emits `rejectCertificateErrorRequested`; both do nothing without a pending error.
- **`TabPermissions`:** a `list[QWebEnginePermission]`. `enqueue` ignores invalid permissions and emits `pendingChanged` only when the queue was empty; `answer(grant)` drops invalid permissions from the front, grants or denies the first valid one, and emits when it dropped or answered something; `deny_all()` denies every valid one, clears, and emits when the queue was not empty. `pending` returns the first permission as a `QVariant` QML can read (`permission.origin`, `permission.permissionType`), or `None`. `enqueue` is `Slot(QWebEnginePermission)` so `PageView.qml` can pass the permission it gets from `WebEngineView.permissionRequested`. If PySide6 cannot hand the gadget to QML or back, ask (`question`) before changing the API.
- **`TabPasswords`:** connects to `PasswordStore.instance().changed` only for a normal tab; `promptHost` and `host` use `passwordorigin.host_of_origin` / `origin_of`; `update_usernames_for` reads `PasswordStore.instance().usernames(origin)` only for a normal tab; `offer_save` and `show_wallet_notice` do nothing on a private tab; `savePending` only for prompt `save` and a normal tab; `neverSavePending` adds the origin once to `Settings.passwordNeverSaveSites`; `fill`, `copyUsername` and `copyPassword` do nothing on a private tab.
- **`TabSiteReload`** and **`TabExtensionItems`:** as in C++ (`recordToggle` drops a change toggled back to its first state; `trigger` flips a checkable item and emits `triggered(extensionId, itemId, checked)`; keys `"<extensionId>/<itemId>"`).

### 7. `TabModel`

Follow `tabmodel.cpp` and `tabmodelclosing.cpp`:

- **Profiles:** `profile_for(requested)`: the requested profile, or `ProfileManager.instance().defaultProfile()`; in a private window (`privateTabs`) a profile that is not off-the-record is replaced by `createPrivateProfile()`. `addTab(isPrivate, initialUrl)` uses `createPrivateProfile()` when `isPrivate` or `privateTabs`, else the default profile, and appends and activates. `addTabWithProfile(profile, url, background)` inserts after the current tab (after the pinned group when the current tab is pinned; at the end without a current tab) and activates unless `background`.
- **Inserting:** `Tab(profile, self)`, `setUrl(url)`, the row clamped to `0…count`, `beginInsertRows` / `endInsertRows`, `countChanged`, `pinnedCountChanged`; the current index shifts when the row is at or before it.
- **Moving and pinning:** `moveTab(from, to)` ignores invalid or equal indexes, uses `beginMoveRows(…, to + 1 if to > from else to)`, and keeps the same current tab selected. `setPinned(index, pinned)` sets the tab's `pinned`, moves it to the end of the pinned group (pin) or the start of the unpinned tabs (unpin), and emits `pinnedCountChanged`. `duplicateTab(index)` inserts a copy with the same profile and URL after it, activates it, and pins it when the source is pinned.
- **Closing:** `closeTab(index)` remembers the tab as closed unless it is private or on the New Tab page, removes the row, fixes the current index (the next tab, or the previous one for the last tab, `-1` when empty) and calls `deleteLater()` on the tab. `closeOtherTabs` keeps the given tab and the pinned ones, closing from the end; `closeTabsToTheRight` closes the unpinned tabs after the index, from the end.
- **Reopening:** `reopenClosedTab(index = 0)` takes the entry counted from the newest, inserts it on the **default** profile at its old row clamped to `pinnedCount…count`, restores a non-empty title, and emits `canReopenClosedTabChanged` when the list became empty and `recentlyClosedChanged` always. Remembering emits `canReopenClosedTabChanged` when the list was empty, and `recentlyClosedChanged`.

### 8. `SessionManager`

- **Instance:** `SessionManager.instance()`; the constructor makes a single-shot `QTimer` of 2,000 ms whose `timeout` calls `save_now`, and connects `QCoreApplication.instance().aboutToQuit` to `save_now` when an application exists.
- **`watch(model)`:** ignores `None` and a model already watched; prunes dead models; connects `countChanged`, `currentIndexChanged` and `rowsRemoved` to `schedule_save`, `rowsInserted` to "track the new rows' tabs, then schedule", `destroyed` to "prune, then schedule"; tracks every existing tab (its `urlChanged` schedules a save). Dead models are found with `shiboken6.isValid(model)`, the twin of `QPointer` (a destroyed model's wrapper must never be called).
- **`save(model)`:** watches it when not `None`, then `save_now()`.
- **`save_now()`:** stops the timer, prunes, and writes only when a watched model has `privateTabs` off. Each window keeps its non-private tabs (a tab on the New Tab page saved with an empty URL), its current index counted among those tabs, and windows with no tab left are skipped. The bytes are `sessionformat.to_json(windows)`, written to `AppDataLocation/session.json` (folder created) through `QSaveFile`; open and commit failures warn as in C++.
- **`saved_windows()`:** `sessionformat.from_json` of the file, or `[]` when it cannot be opened.

### 9. `PasswordBridge` and `PasswordPageApi`

- **`PasswordPageApi(bridge)`** (parent: the bridge): `formSubmitted` (`Slot(str, str, str)`) and `credentialsFor` (`Slot(str, result="QVariantList")`) forward to the bridge; signals `credentialsChanged` and `fillRequested(str, str, str)`. The web channel publishes its `QMetaObject`, so these names are what `passwords.js` calls.
- **`PasswordBridge(parent=None)`:** creates the API and connects `PasswordStore.instance().changed` to `api.credentialsChanged`. `tab` is writable and notifies `tabChanged` on change; when the tab is destroyed, the bridge forgets it (connect `destroyed`, or check `shiboken6.isValid`), as `QPointer` does.
- **Rules**, as `passwordbridge.cpp`: allowed only with a tab that is not private. `form_submitted`: only with a non-empty password, `can_save_for(origin)`, `offerToSavePasswords` on and the origin not in `passwordNeverSaveSites`; then `ensureOpen()`; when the store is `unavailable`, show the wallet notice once per run (`unavailable_notice_shown` / `set_unavailable_notice_shown`); when open and the login is not already saved with that password, `tab.passwords.offer_save(…)`. `credentials_for`: `[]` when not allowed or for an empty origin, else `ensureOpen()` and `credentials_for(origin)`. `fill(username)`: only when allowed, the tab's origin is not empty and the store is open; emits `api.fillRequested(origin, username, password)`.

### 10. Tests

Each C++ case becomes a test with the same intent (umbrella item 9); data-driven cases become `pytest.mark.parametrize` with the same rows and ids; test functions have at most 20 lines. Harness headers become helper modules or fixture classes next to their tests. Tab strip and address bar tests drive the staged QML with `QTest` mouse and key events on a shown window, with `desktop_style`, as their C++ twins do. **No test reaches the network or a real wallet.**

```
pytests/browser/
  pagecontextmenucases.py
  test_pagecontextmenu.py
  address/
    addressbarharness.py
    test_addressbar.py
  session/
    test_sessionmanager.py
  tabs/
    test_assignandnotify.py
    test_recentlyclosedtabs.py
    test_tabmodel.py
    test_tabnewtabpage.py
    test_tabpasswords.py
    test_tabpinning.py
    test_tabsecurity.py
    features/
      __init__.py
      test_tabextensionitems.py
      test_tabpermissions.py
      test_tabsitereload.py
  tabstrip/
    __init__.py
    tabstripharness.py
    test_tabdrag.py
    test_tabdragrelease.py
    test_tabdragscroll.py
    test_tabstripaccessibility.py
    test_tabstripclosing.py
    test_tabstripscroll.py
    test_tabstripwidths.py
pytests/site/
  sitepermissionsharness.py
  test_sitepermissions.py
  test_sitepermissionsui.py
pytests/passwords/bridge/
  __init__.py
  test_passwordbridge.py
  test_passwordfill.py
pytests/data/AddressBarHost.qml   (copied from tests/data/)
```

- **`pytests/conftest.py`:** `isolated_profile` also sets `KONDOR_NO_KWALLET=1`, as `tests/CMakeLists.txt` does for every C++ test; `pytests/passwords/conftest.py` keeps removing it where it needs the fake wallet. Nothing else changes there.
- **Tab model tests** build `TabModel()` directly (parented to nothing and deleted at the end of the test) and use the real `ProfileManager`, as the C++ tests do.
- **`test_tabpasswords.py`:** the six C++ cases, with `Settings.passwordNeverSaveSites` reset before each test and restored afterwards.
- **`test_assignandnotify.py`** (new): `test_equal_value_does_not_notify`, `test_new_value_is_stored_and_notified`, `test_floats_use_the_fuzzy_rule` (item 5).
- **`test_tabpermissions.py`** (new, on a `QQuickWebEngineProfile` with `StoreInMemory`): `test_pending_is_readable_from_qml` (a small QML object bound to `tab.permissions.pending.permissionType` and `.origin` reads the queued permission), `test_enqueue_from_qml_reaches_the_queue`, `test_invalid_permissions_are_ignored`.
- **`test_tabsitereload.py`** (new): `test_toggle_is_pending_and_names_the_extension`, `test_toggling_back_clears_the_change`, `test_will_run_follows_the_last_toggle`, `test_dismiss_clears_and_notifies_once`.
- **`test_tabextensionitems.py`** (new): `test_set_checked_notifies_only_on_change`, `test_trigger_flips_a_checkable_item`, `test_trigger_of_a_plain_item_is_not_checked`.
- **`test_sessionmanager.py`:** the five C++ cases on `SessionManager.instance()`, with `session.json` removed before each test, plus `test_url_change_schedules_a_save` (after `watch`, a tab's `setUrl` writes the file within 3 s, `qtbot.waitUntil`) and `test_destroyed_model_is_forgotten` (watch a model, delete it, process events, `save_now()` raises nothing and keeps the other window).
- **`test_passwordbridge.py`** (new, with the `FakeWallet` of phase 6 behind a `PasswordStore` patched in as `PasswordStore.instance()`): `test_private_tab_gets_no_credentials_and_no_offer`, `test_form_submission_offers_to_save`, `test_never_save_site_is_not_offered`, `test_already_saved_login_is_not_offered`, `test_unavailable_wallet_shows_the_notice_once`, `test_fill_emits_the_saved_password`, `test_store_change_reaches_the_page`, `test_destroyed_tab_is_forgotten`.
- **`test_passwordfill.py`:** the six C++ cases on a `QWebEnginePage` (from `PySide6.QtWebEngineCore`), with the same fake channel script and the staged `:/scripts/usernamefield.js` and `:/scripts/passwords.js` (`staged_resources`); `runJavaScript` results awaited with `qtbot.waitUntil`.
- **`test_sitepermissionsui.py`** and **`test_pagecontextmenu.py`** load the staged `site/PermissionBar.qml`, `site/SitePermissionsDialog.qml` and `PageContextMenu` (inside the same inline host QML as the C++ test) through `kondor_engine`.

### 11. API check result

After this phase, `python3 scripts/check-qml-api.py` reports **nine more** classes checked than on the PR's base (`Tab`, `TabSecurity`, `TabPermissions`, `TabPasswords`, `TabSiteReload`, `TabExtensionItems`, `TabModel`, `SessionManager`, `PasswordBridge`) and exits 0. `PasswordPageApi` stays counted as "not ported", because it is no QML type; `test_passwordbridge.py` checks its method and signal names instead (`test_page_api_keeps_the_channel_names`).

## Acceptance criteria

- [ ] `kondor/browser/tabs/`, `kondor/browser/session/sessionmanager.py` and `kondor/passwords/bridge/` have the modules of item 1, and the `qmltypes.py` files register the nine types of item 3.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports nine more classes checked than on the base, with no problems.
- [ ] Every C++ case of the test files in "Context" has its pytest twin, and the new tests of item 10 exist and pass with `scripts/run-pytests.sh`. No test reaches the network or KWallet.
- [ ] Privacy (tests): a private tab is never in `recentlyClosed`, never in `session.json`, never gets a password offer, fill or copy; a window with only private tabs writes no session.
- [ ] `session.json` written by Python for the same tabs is byte-identical to the C++ app's (manual test).
- [ ] The `python` and `build` jobs are green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt` or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md) shared by every step. The snippet is a short Python script that creates a `QGuiApplication` after `QtWebEngineQuick.initialize()`, sets organization `KDE` and application `Kondor`, registers the staged resources and calls every `register_types()`.

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && scripts/run-pytests.sh && python3 scripts/check-qml-api.py`: all pass, and the last reports nine more classes than `main`.
2. **Session both ways:** run the C++ app (built from `main`) on the isolated profile, open `https://kde.org`, `https://example.org` and a New Tab page, select the second tab, and quit. In the snippet, `SessionManager.instance().saved_windows()` gives one window with those three tabs and current index 1. Copy `session.json` aside, build a `TabModel` with the same three tabs in the snippet, `SessionManager.instance().save(model)`, and compare: the new file is byte-identical to the C++ one.
3. **Private window:** in the snippet, a `TabModel` with `privateTabs = True` and two tabs, saved with `save(model)` after removing `session.json`: no file is written. A normal window plus a private tab in it: the file lists only the normal tab.
4. **Tab strip:** load the staged `browser/tabstrip/TabStrip.qml` with a `TabModel` of five tabs in a window (as the harness does), pin the second tab from the snippet, drag the fourth tab over the fifth with the mouse, and close one with its close button: the order, the pinned group and the selection behave as in the C++ app.
5. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- `src/app/` (windows, session restore at startup), `kondor/__main__.py`, and calling `register_types()` from an app entry point: phase 11 (#173).
- The extension tests that build a `Tab` and `src/extensions/bridge/`: phases 10 and 10b (#172, #218).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests or the workflows.
- Changes to `kondor/core/`, `kondor/adblock/`, `kondor/downloads/`, `kondor/history/`, `kondor/bookmarks/`, `kondor/passwords/` outside `bridge/` and `qmltypes.py`, `kondor/browser/` outside `tabs/`, `session/sessionmanager.py` and `qmltypes.py`, `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker, unless a phase-8 file shows a bug in them. In that case, ask first (`question`). The `pytests/conftest.py` change of item 10 is allowed.
- New behavior: no change to the closed-tabs limit, the autosave delay, the session format, the security states or the permission queue.
- Translating Python strings, or running `pyside6-lupdate` (phase 12).

## Dependencies

#168 (password store, merged) and #169 (browser profile, address and session). Umbrella #162.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| How do `Tab` and `TabModel` meet the 200-line limit, when C++ splits one class over several `.cpp` files? | A single-inheritance chain of `QObject` subclasses, one module per link, with only the last class registered (item 2). Signals and properties of base links are in the final `QMetaObject`, so QML and `check-qml-api.py` see one class. Mixins without `QObject` were rejected: PySide6 only collects `Signal` and `Property` from `QObject` subclasses. |
| How does Python replace `assignAndNotify`? | A function `assign_and_notify(owner, attribute, value, signal)` with `qFuzzyCompare`'s float rule (item 5), not a descriptor: it reads like the C++ call sites and stays tiny. |
| What replaces `QPointer<TabModel>` and `QPointer<Tab>`? | `shiboken6.isValid(object)` when pruning, plus `destroyed` connections, so a deleted C++ object's wrapper is never called. |
| Where does the bridge go? | `kondor/passwords/bridge/` and `pytests/passwords/bridge/`, as in `src/passwords/bridge/`, since both `passwords/` folders are close to the 10-file limit. |
| `KONDOR_NO_KWALLET` in pytest? | Set by `isolated_profile` for every test, as `tests/CMakeLists.txt` does for every C++ test, so `Tab` tests never open the real wallet. |
| Which tests cover `TabSiteReload`, `TabExtensionItems`, `TabPermissions` from QML and `PasswordBridge`? | New Python unit tests in this phase (item 10); the C++ ones only cover them through the extension and fill tests, which move with their phases. |
