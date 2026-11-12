# Refactor: shrink C++ in the browser folder (#144)

> **Issue:** [#144](https://github.com/lukasborges/kondor/issues/144) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first, especially "Code quality" and "The Tab bridge pattern". This file is the source of truth for the issue; only the architect edits it.

## Objective

Clear every `src/browser/` entry of `scripts/code-quality-baseline.json` (51 entries over 2 554
lines), so that the folder follows AGENTS.md → "Code quality". Reuse the `Sql` helper from #138.
**Kondor behaves exactly as before.** Session file format, database schema, `Kondor.conf` keys,
User-Agent and page scripts stay the same.

The one deliberate API change: `Tab` cannot fit in 200 lines with 39 flat properties, so four
feature groups move into sub-objects (§1). Their QML and C++ call sites are renamed in this PR.
Every other QML-visible API stays the same.

## Context

- **Baseline entries in scope** (`origin/main` after #138):

  | File | Entries |
  | --- | --- |
  | `tab.{h,cpp}` | **files:** `tab.cpp` 552, `tab.h` 273. **functions:** `setUrl` 17, `updateSecurityState` 22, `answerPermission` 18, `setPendingCertificateError` 12. **comments:** `tab.cpp` 16, `tab.h` 25 |
  | `tabmodel.{h,cpp}` | **file:** `tabmodel.cpp` 293. **functions:** `closeTab` 35, `insertTab` 32 (4 parameters), `setPinned` 21, `moveTab` 18, `reopenClosedTab(int)` 14, `closeOtherTabs` 11. **comments:** `tabmodel.cpp` 15, `tabmodel.h` 5 |
  | `profilemanager.{h,cpp}` | **file:** `profilemanager.cpp` 269. **functions:** `installPageScripts` 44, `setupProfile` 42, `ProfileManager` (constructor) 33, `defaultProfile` 13, `createPrivateProfile` 12. **comments:** `profilemanager.cpp` 22, `profilemanager.h` 14 |
  | `sessionmanager.{h,cpp}` | **file:** `sessionmanager.cpp` 244. **functions:** `saveNow` 63, `savedWindows` 43, `watch` 29. **comments:** `sessionmanager.cpp` 14, `sessionmanager.h` 10 |
  | `faviconstore.{h,cpp}` | **functions:** `store` 42 (nesting 3), `storeImage` 25, `imageForHost` 14. **comments:** `faviconstore.cpp` 1, `faviconstore.h` 11 |
  | `searchsuggestions.{h,cpp}` | **functions:** `request` 40 (nesting 4), `endpointUrl` 15. **comments:** `searchsuggestions.cpp` 4, `searchsuggestions.h` 8 |
  | `addressresolver.{h,cpp}` | **functions:** `isLocalHost` 26, `addressUrl` 23. **comments:** `addressresolver.cpp` 5, `addressresolver.h` 7 |
  | `zoommanager.{h,cpp}` | **functions:** `setZoomFor` 11, `step` 11. **comments:** `zoommanager.cpp` 1, `zoommanager.h` 9 |

- **Tests today:** `tests/browser/tst_tabmodel.cpp` (tab list, recently closed, New Tab page,
  security state, certificate errors), `tst_sessionmanager.cpp` (multi-window save, private-only
  windows), `tst_faviconstore.cpp`, `tst_zoommanager.cpp`, `tst_addressresolver.cpp`,
  `tests/site/tst_sitepermissions.cpp` (permission queue), `tests/extensions/tst_extensions.cpp`
  (extension toolbar items). **Nothing tests** the password prompt state of a tab, tab pinning
  order, reading an old or invalid session file, or the parsing of search suggestions.

## Design / behavior

Limits for every new or changed function: body ≤ 10 lines, ≤ 3 parameters, nesting ≤ 2. Every file
≤ 200 lines. No comments (AGENTS.md → "Names instead of comments"). The **file and class names below
are binding**. How the functions are split inside them is up to you, as long as the limits hold. If a
listed file still goes over 200 lines, split it again in the same folder and say so in the PR. Never
merge two rows into one file.

### 1. `Tab` and its feature groups

`Tab` keeps the navigation and page state: `title`, `url`, `iconUrl`, `progress`, `loading`,
`canGoBack`, `canGoForward`, `profile`, `zoomFactor`, `isPrivate`, `pinned`, `findMatches`,
`findActiveMatch`, `newTabPage`, `isFullScreen`, `devToolsOpen`, `readerAvailable`, `readerActive`,
`crashed`, `crashReason`, `crashExitCode`, with the same setters, commands and `…Requested` signals
as today. That includes the extension commands `closeTab`, `openTab`, `selectNeighborTab` and
`downloadUrl`.

Four groups move into their own `QObject` classes. Each class is `QML_ELEMENT` +
`QML_UNCREATABLE`, owned by its `Tab` (created in the constructor with the tab as parent), and
exposed as a `CONSTANT` pointer property:

| File | Class | `Tab` property |
| --- | --- | --- |
| `tabsecurity.{h,cpp}` | `TabSecurity` | `security` |
| `tabpermissions.{h,cpp}` | `TabPermissions` | `permissions` |
| `tabpasswords.{h,cpp}` | `TabPasswords` | `passwords` |
| `tabextensionitems.{h,cpp}` | `TabExtensionItems` | `extensionItems` |

**Exact renames.** QML and C++ callers (`qml/`, `src/passwords/passwordbridge.cpp`, tests) change
like this, and nothing else changes:

| Today (`tab.…`) | After |
| --- | --- |
| `securityState` / `securityStateChanged` | `security.state` / `stateChanged` |
| `certificateErrorPending`, `certificateErrorUrl`, `certificateErrorDescription`, `certificateErrorOverridable` / `certificateErrorChanged` | `security.` + same names / same signal |
| `setPendingCertificateError(url, description, overridable)`, `acceptCertificateError()`, `rejectCertificateError()` | `security.` + same names |
| `acceptCertificateErrorRequested`, `rejectCertificateErrorRequested` | same signals on `security` (`Connections { target: root.tab.security }`) |
| `pendingPermission` / `pendingPermissionChanged` | `permissions.pending` / `pendingChanged` |
| `enqueuePermission(p)`, `answerPermission(grant)` | `permissions.enqueue(p)`, `permissions.answer(grant)` |
| `passwordPrompt`, `passwordPromptUsername`, `passwordPromptHost` / `passwordPromptChanged` | `passwords.prompt`, `passwords.promptUsername`, `passwords.promptHost` / `promptChanged` |
| `passwordUsernames` / `passwordUsernamesChanged` | `passwords.usernames` / `usernamesChanged` |
| `savePendingPassword()`, `neverSavePendingPassword()`, `dismissPasswordPrompt()`, `fillPassword(u)` / `fillPasswordRequested(u)` | `passwords.savePending()`, `passwords.neverSavePending()`, `passwords.dismissPrompt()`, `passwords.fill(u)` / `fillRequested(u)` |
| `offerPasswordSave(origin, username, password)`, `showPasswordWalletNotice()` (C++ only) | `passwords()->offerSave(…)`, `passwords()->showWalletNotice()` |
| `extensionItemChecked(e, i)`, `setExtensionItemChecked(e, i, c)`, `triggerExtensionItem(e, i, checkable)` | `extensionItems.isChecked(e, i)`, `extensionItems.setChecked(e, i, c)`, `extensionItems.trigger(e, i, checkable)` |
| `extensionItemsChanged`, `extensionItemTriggered(e, i, checked)` | `extensionItems.changed`, `extensionItems.triggered(e, i, checked)` |

**Wiring that stays inside `Tab`**, with the same order and rules as today's `setUrl`,
`navigateTo` and `showNewTabPage`:

- `setUrl(url)`: leaves the New Tab page for any non-empty URL other than `about:blank`; calls
  `permissions->denyAll()` when the origin changes (scheme, host and port compared
  case-insensitively, as `sameOrigin` does today); then, only when the URL really changed, stores it,
  calls `security->updateFor(url)` and `passwords->updateUsernamesFor(url)`, and emits
  `urlChanged`.
- `navigateTo` and `showNewTabPage` call `security->clearPendingCertificateError()` as today.
- `TabSecurity` takes the tab's profile (for `ProfileManager`'s certificate overrides).
  `TabPasswords` takes `isPrivate` and keeps today's rules: no prompt, no usernames, no fill and no
  `PasswordStore` connection for a private tab.

**One change-and-emit helper.** Every simple setter in `Tab` and in the four classes is a one-line
call to a private template helper (as `Settings::store` in #138): compare, assign, emit, with
≤ 3 parameters (member, value, signal).

`tab.cpp` may be split into `tab.cpp` (constructor, state setters, wiring) and `tabcommands.cpp`
(the one-line command emitters) if it is still over 200 lines. Both files implement `Tab`.

**AGENTS.md:** the architect updates "The Tab bridge pattern" with this spec. A feature that adds
several related properties to a tab gets its own `Tab…` group object, exposed as a `CONSTANT`
property of `Tab`.

### 2. `TabModel` (`tabmodel.{h,cpp}`, `closedtabs.{h,cpp}`)

| File | Holds |
| --- | --- |
| `tabmodel.{h,cpp}` | `TabModel` with the same QML API. `insertTab` is no longer `Q_INVOKABLE` (no QML caller). It becomes private and takes a `NewTab { int index; QQuickWebEngineProfile *profile; QUrl url; bool activate; }` struct. The private-window rule (every tab of a `privateTabs` model gets a fresh private profile) stays inside it. `closeTab`, `moveTab`, `setPinned` and `closeOtherTabs` are split into small steps: remember the closed tab, remove the row, fix the current index, compute the pinned target. |
| `closedtabs.{h,cpp}` | `ClosedTabs`, a value class for today's `m_closed` list: `remember(url, title, index)` (keeps at most `kMaxClosedTabs`, oldest dropped first), `take(indexFromNewest)`, `isEmpty()`, `toVariantList()` (newest first, `{url, title}` maps as `recentlyClosed` returns today). It does not know about `Tab` or private tabs: `TabModel` decides what to remember. |

### 3. `ProfileManager` (`src/browser/`)

| File | Holds |
| --- | --- |
| `profilemanager.{h,cpp}` | `ProfileManager` with the same QML API and the same `profileCreated` signal. Creating the persistent and the private profiles; forwarding `Settings` changes (download directory, spell check) to every live profile through one `forEachProfile`-style helper; `clearDataOnExit` on quit; `clearCookiesAndCacheNow`; the address helpers. |
| `pagescripts.{h,cpp}` | `PageScripts::install(profile)`: the `kondor-channel` script (web channel client + `channel.js`, every profile) and the `kondor-passwords` script (persistent profile only). Same names, injection points, worlds, sub-frame flag and warnings as today. |
| `profilesetup.{h,cpp}` | The rest of today's `setupProfile`: User-Agent (`QtWebEngine/…` → `Kondor/0.1`), `Accept-Language`, download path, spell check, ad blocker, and routing downloads to `DownloadManager` (with the private flag) and notifications to `Notifier`. |
| `certificateoverrides.{h,cpp}` | `CertificateOverrides`: in-memory set of lower-case hosts per profile, `mark(profile, host)`, `isOverridden(profile, host)`, `forget(profile)` (called when the profile is destroyed). `ProfileManager::markCertificateOverridden` / `isCertificateOverridden` forward to it. Never written to disk. |

### 4. `SessionManager` (`src/browser/`)

| File | Holds |
| --- | --- |
| `sessionwindow.h` | `SessionTab` and `SessionWindow`, moved out of `sessionmanager.h`. |
| `sessionformat.{h,cpp}` | `SessionFormat::toJson(const QList<SessionWindow> &)` → `QByteArray` and `SessionFormat::fromJson(const QByteArray &)` → `QList<SessionWindow>`. Same JSON as today: `version` 2, `windows` → `{currentIndex, tabs: [{url, title}]}`, the New Tab page as `about:newtab`. Version 1 (one window at the root) is still read. Invalid JSON, a version outside 1…2, and windows without tabs are ignored, with the same warnings. No file access and no `Tab`. |
| `sessionmanager.{h,cpp}` | `SessionManager` with the same QML API: `watch` (connects one model, tracks its tabs), the save timer, `saveNow` (skips when no window is left or only private windows remain, builds one `SessionWindow` per window from its normal tabs, writes with `QSaveFile`), and `savedWindows` (reads the file and hands it to `SessionFormat`). |

### 5. Smaller files (`src/browser/`)

| File | Holds |
| --- | --- |
| `faviconstore.{h,cpp}` | `store` split into: the icon id from an `image://favicon/` source, requesting the image from the provider, scaling to `kMaxIconSize`, storing. `storeImage` and `imageForHost` use `Sql` from #138, so no `QSqlQuery` boilerplate is left. The same "skip when bytes are unchanged" rule applies. |
| `searchsuggestions.{h,cpp}` | `request` split into building the request (same User-Agent and redirect policy), sending it, and handling the reply. `endpointUrl` becomes a data table: Google (`suggestqueries.google.com`, `client=firefox`) or DuckDuckGo (`duckduckgo.com/ac/`, `type=list`) for every other engine. |
| `suggestionlist.{h,cpp}` | `suggestionsFromJson(const QByteArray &body)` → `QStringList`: the second element of `["query", [...]]`, non-empty strings only, at most 6 (`kMaxSuggestions`), empty for anything else. It has no network access, so it can be tested. |
| `addressresolver.{h,cpp}` | Same three free functions. `isLocalHost` is split into parsing the IPv4 octets (`std::optional<std::array<int, 4>>`) and checking the loopback/private ranges (127/8, 10/8, 192.168/16, 172.16/12). `addressUrl` is split into the explicit-scheme case and the host-pattern case. |
| `zoommanager.{h,cpp}` | `setZoomFor` and `step` split into small steps. Same levels, same `Kondor.conf` keys, still never called for private tabs. |

### 6. Tests first

Before moving code, add these tests and check that they pass on `main`'s behavior. Then keep them
green, renaming the call sites when §1 lands. Each test function body is at most 20 lines, and each
one is registered in `tests/CMakeLists.txt`:

- `tests/browser/tst_tabpasswords.cpp`:
  - `privateTabNeverOffersToSave`;
  - `neverSaveAddsTheOriginOnce`;
  - `walletNoticeReplacesTheSavePrompt`;
  - `dismissClearsThePrompt`.
- `tests/browser/tst_tabmodel.cpp`:
  - `pinningMovesTabToEndOfPinnedGroup`;
  - `unpinningMovesTabToStartOfUnpinnedTabs`;
  - `moveTabKeepsTheCurrentTabSelected`;
  - `recentlyClosedKeepsAtMostTheLimit`.
- `tests/browser/tst_sessionmanager.cpp`:
  - `readsTheVersionOneFormat`;
  - `ignoresInvalidAndFutureFiles`;
  - `savesNewTabPageAsAboutNewTab`.
- `tests/browser/tst_suggestionlist.cpp` (it tests `suggestionsFromJson` directly, so write it once
  the function exists; its cases must also hold for `main`'s reply handling):
  - `keepsAtMostSixSuggestions`;
  - `skipsEmptyAndNonStringEntries`;
  - `returnsNothingForUnexpectedJson`.

All existing tests keep passing, with their call sites renamed as in §1. Tests use the isolated test
locations, as the existing ones do.

### 7. Baseline, CMake, translations

- Remove every `src/browser/` entry from `scripts/code-quality-baseline.json`. New files add no
  entries, and the baseline only shrinks. `python3 scripts/check-code-quality.py` passes. The QML
  files you only rename call sites in must not gain baseline lines.
- Register every new source file in `cmake/KondorSources.cmake` (the groups shared by the app and
  the tests, from #138), and in every test target that compiles the files it now depends on.
- No user-visible string changes. If a `tr()` moves to another class, its context changes: run
  `update_translations` and copy the existing translations into the new context in every
  `i18n/*.ts`, with no `unfinished` messages and no `vanished`/`obsolete` leftovers.
- No README change.

## Acceptance criteria

- [ ] Every file named in §1–§5 exists. Every `.cpp`/`.h` in `src/browser/` is ≤ 200 lines, and
      every function in it is ≤ 10 lines, has ≤ 3 parameters and nests ≤ 2 deep.
- [ ] No comments in `src/browser/` (except `//:` translator notes, SPDX lines and "why" comments
      that link a bug report).
- [ ] The baseline has no `src/browser/` entry; `python3 scripts/check-code-quality.py` passes.
- [ ] `Tab` exposes `security`, `permissions`, `passwords` and `extensionItems` as in §1. No QML or
      C++ file still uses an old name from the rename table (`grep` finds none).
- [ ] `faviconstore.cpp` has no `QSqlQuery` boilerplate (it uses `Sql`).
- [ ] The 14 test functions of §6 exist, and all `ctest` tests pass.
- [ ] Session file format, database schema, `Kondor.conf` keys, User-Agent, page script names, and
      the QML API of `TabModel`, `ProfileManager`, `SessionManager`, `FaviconStore`,
      `SearchSuggestions` and `ZoomManager` are unchanged (except `insertTab`, §2).
- [ ] Private-tab rules hold: no password prompt or usernames, no session entry, no history, no
      per-site zoom, no favicon stored from a private tab.
- [ ] Clean build with no new warnings; the offscreen smoke test shows no QML errors; no
      `unfinished` messages in `i18n/*.ts`.
- [ ] The manual test below behaves as on `main`.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, see AGENTS.md):

1. Open three tabs, pin one, move one by dragging, close one and reopen it with Ctrl+Shift+T.
   Quit and start again: the session comes back with the same tabs, order and current tab.
2. Visit `https://expired.badssl.com/`: the certificate warning shows and the site button shows
   the error state. "Back to Safety" leaves. Visit it again and choose "Advanced…" → "Continue
   Anyway (Unsafe)": the button keeps the error state for that host. `https://example.com` shows the secure state, and an `http://` site the
   insecure state.
3. On a site that asks for the camera or notifications (for example
   `https://permission.site/`), the permissions bar appears. Allow or deny works, and navigating
   to another site denies a pending request.
4. Submit a login form (for example `https://the-internet.herokuapp.com/login` with `tomsmith` /
   `SuperSecretPassword!`). The "save password" bar appears, and "Never for This Site" adds the
   site to the never-save list. In a private window no bar appears.
5. With the Dark Mode or any toolbar-item extension installed, toggling its menu item keeps the
   check mark per tab.
6. Type in the address bar with search suggestions on: suggestions appear (DuckDuckGo, then Google
   after switching the engine). Typing `192.168.0.1` goes to `http://`, `example.com` to `https://`.
7. Zoom in on a site, open another tab on the same host: same zoom. Favicons show in the tabs and
   on the New Tab page after a restart.
8. In a private window: nothing appears in History, the session after a restart has no private
   tab, and zoom is not remembered.

## Out of scope

- Any change in behavior, wording, schema, settings keys or session format. If you find a bug,
  report it as a question on the issue; do not fix it here.
- Any QML change other than renaming the call sites listed in §1 (QML functions and files belong
  to #139).
- Other C++ folders: `app`, `adblock`, `passwords` (#145; only the two call sites in
  `passwordbridge.cpp` change here), `extensions` (#146).
- Baseline entries of test files that already exist (only new or changed test functions must
  follow the 20-line limit).

## Dependencies

- #138 (`Sql` helper, `cmake/KondorSources.cmake`), merged.

## Prototype

None: no visible change.

## Decisions

| Question | Decision |
| --- | --- |
| How does `Tab` fit in 200 lines without changing its QML API? | It cannot: `tab.h` alone declares 39 properties, about 60 invokables and 50 signals. Splitting it by inheritance (base classes that only exist to hold declarations) would hide one class in a chain of fake ones. Four feature groups (security, permissions, passwords, extension items) become `Tab…` sub-objects exposed as `CONSTANT` properties (§1), like QML grouped properties (`font.pixelSize`). The call sites are renamed in the same PR, and "The Tab bridge pattern" in AGENTS.md describes the groups. |
| Why do crash and reader state stay on `Tab`? | They are 3 and 2 properties that `WebViewTab.qml` sets alongside the page state. Moving them would rename call sites without making any file fit the limits. |
| `insertTab` has 4 parameters and is `Q_INVOKABLE`. | Nothing in QML calls it (`addTab` / `addTabWithProfile` do). It becomes private and takes a `NewTab` struct. |
