# Refactor: shrink long QML functions and large QML files (#139)

> **Issue:** [#139](https://github.com/lukasborges/kondor/issues/139) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first, especially "Code quality". This file is the source of truth for the issue; only the architect edits it.

## Objective

Clear every entry of `qml/**` and `src/**/*.js` in `scripts/code-quality-baseline.json`, so that all
QML and JavaScript follows AGENTS.md → "Code quality". **Kondor behaves and looks exactly as
before.** Every user-visible string, icon name, layout, shortcut, `objectName` and every property or
function that tests or other files use stays the same.

The baseline entries of test files (`tests/**`) are **not** part of this issue (see "Decisions"): they
move to #151.

## Context

- **Baseline entries in scope** (`origin/main` after #146): 36 `comments` entries (every `qml/` and
  `src/**/*.js` file listed there), 13 `file-length` entries and 33 `function-length` / 6 `nesting`
  entries:

  | File | Entries |
  | --- | --- |
  | `qml/browser/WebViewTab.qml` | 616 lines; `enterReader` 29, `onLoadingChanged` 41, `onCertificateError` 11, `onRejectCertificateErrorRequested` 11, `pdfFinished` 12; 62 comments |
  | `qml/passwords/PasswordsPage.qml` | 409 lines; `onActiveChanged` 11, `rebuild` 14; 17 comments |
  | `qml/browser/TabStrip.qml` | 359 lines; `emptyAt` 14, `ensureCurrentVisible` 13, `onCompleted` 13; 39 comments |
  | `qml/browser/PageContextMenu.qml` | 355 lines; `perform` 81, `rebuild` 47 (nesting 4), `editingBlock` 33, `mediaBlock` 22, `addEntry` 19, `selectionBlock` 11; 16 comments |
  | `qml/app/AboutWindow.qml` | 337 lines; 13 comments |
  | `qml/extensions/ExtensionSettingsDialog.qml` | 297 lines; 7 comments |
  | `qml/browser/NewTabPage.qml` | 267 lines; 10 comments |
  | `qml/history/HistoryWindow.qml` | 261 lines; `onClicked` 13; 8 comments |
  | `qml/browser/TabButtonDelegate.qml` | 251 lines; `update` 28, `onActiveChanged` 15, `onTriggered` 13; 17 comments |
  | `qml/extensions/ExtensionsPage.qml` | 224 lines; 7 comments |
  | `qml/app/MainMenu.qml` | 211 lines; `rebuild` 40 (nesting 3); 8 comments |
  | `qml/downloads/DownloadsPopup.qml` | 207 lines; `statusText` 26; 3 comments |
  | `qml/site/SiteInfoPopup.qml` | 205 lines; `reload` 22; 4 comments |
  | `qml/browser/AddressSuggestions.qml` | `buildRows` 84; 16 comments |
  | `qml/bookmarks/BookmarkMenu.qml` | `appendFolder` 36 (nesting 3); 16 comments |
  | `qml/bookmarks/BookmarksBar.qml` | `openBookmark` 11; 7 comments |
  | `qml/extensions/ExtensionsMenu.qml` | `rebuild` 24; 5 comments |
  | `qml/site/PermissionTypeInfo.qml` | `iconFor`, `labelFor`, `sentenceFor` 23 each; 3 comments |
  | `qml/site/SitePermissionsDialog.qml` | `reload` 31; 4 comments |
  | `src/passwords/passwords.js` | the wrapping IIFE 149 (nesting 4); 14 comments |
  | `src/extensions/extensionruntime.js` | `__kondorCreateRuntime` 88 (nesting 5); 7 comments |
  | `src/extensions/channel.js` | the wrapping IIFE 25 (nesting 3); 7 comments |
  | Comments only | `AdBlockPopup`, `BookmarksBar`, `CertificateErrorPage`, `CrashedPage`, `FindBar`, `FullScreenHint`, `ReaderControls`, `TabContextMenu`, `InlineBar`, `SiteIcon`, `SiteMenuItem`, `ExtensionCatalogDialog`, `ExtensionIcon`, `InstallExtensionDialog`, `AddPasswordDialog`, `ImportPasswordsDialog`, `PasswordBar`, `PermissionBar` |

- **How the checker reads JavaScript:** only the *outermost* function of a nested group is measured
  (`scripts/codequality/qml.py`, `outermost`). A file wrapped in one IIFE is therefore one function
  as long as the file. The wrapper itself has to go (§3).
- **Who reads these files from tests:** `tst_tabstrip` (`tabWidth`, `tabsAreaWidth`, `overflowing`,
  `maxScroll`, `contentX`, `dragShift`, `tabDragActive`, `scrolled`, `tabBar`, `clip`…),
  `tst_addresssuggestions` / `tst_suggestionlist` (`rows`, `activate`, `selectedText`, `text`),
  `tst_sitepermissions` (`revoke`, `showWindow`), `tst_mainmenu`, `tst_extensions` (QML pages and
  dialogs), `tst_contentscriptbuilder` (the recorded content script, which contains
  `extensionruntime.js`).
- **Translations:** `qsTr()` uses the QML file name as its context. A message that moves to another
  file gets a new context in `i18n/*.ts`.

## Design / behavior

Limits for every new or changed function and handler: body ≤ 10 lines, ≤ 3 parameters, nesting ≤ 2.
Every file ≤ 200 lines. No comments (AGENTS.md → "Names instead of comments"): every "why" comment of
today becomes a name (for example `keepWidthsUntilPointerLeaves()`, `endReaderOnNavigation()`,
`reapplySavedZoomAfterCommit()`). Workarounds keep a comment only if it links a bug report.

The **file names and the responsibilities below are binding**. How the functions are split inside a
file is up to you, as long as the limits hold. If a listed file still goes over 200 lines, split it
again in the same folder and say so in the PR. Never merge two rows into one file. Components get
what they need through `required property`; they never reach into ids of other files. Each new file
goes into `QML_FILES` in `CMakeLists.txt`.

**Rules that hold everywhere:**

- Public API unchanged: every property, function, signal and `objectName` used by another QML file or
  a test stays on the same object with the same name. Where a property moves into a child component,
  the old object keeps an alias.
- `switch` statements that map a value to a value become data tables (`readonly property var …: ({…})`
  or a JS object), with the fallback of today.
- Private tabs: every `isPrivate` check stays, in the same place in the flow (history, favicons,
  zoom writing, top sites, passwords).

### 1. Large files

| File | Becomes |
| --- | --- |
| `browser/WebViewTab.qml` | `WebViewTab.qml`: the root `Item` (`tab`, `tabModel`, `contextMenuPosition`), the `SplitView` with the page and DevTools views, the overlays (`NewTabPage`, `CertificateErrorPage`, `ReaderControls`, `CrashedPage`), `PageContextMenu` and its `Shortcut`, `onVisibleChanged`, and the composition of the components below. |
| | `PageView.qml`: the page `WebEngineView` and its signal handlers, each one line or a call to a named function. `onLoadingChanged` becomes named steps in today's order: clear the crash, update reader state, update the tab (`loading`, `canGoBack`, `canGoForward`), then for a finished non-reader load: detect reader mode, add the history visit (normal tabs), re-apply the saved zoom (normal tabs). |
| | `PageZoom.qml`: `zoomHost`, `applyingZoom`, `setViewZoom`, `applySavedZoom`, the `ZoomManager` connection and the "save the zoom of a normal tab" step of `onZoomFactorChanged`. |
| | `ReaderMode.qml`: `readerOriginalUrl`, `readerLoadPending`, `detectReader`, `enterReader` (split into: run Readability, check the article, build the page from `template.html`, load it), `exitReader`, `escapeHtml`. |
| | `ReaderStyle.qml`: the View color set, `readerVars()`, `applyReaderStyle()` and the `Settings` / color connections. |
| | `PageOutput.qml`: `printPath`, `pdfFinished` (the three notifications as named steps), print, print to PDF and save page. |
| | `CertificateErrorHandler.qml`: the pending error holder, `onCertificateError`, accept, reject (Back answers the pending request too, as today). |
| | `PageScriptBridges.qml`: `PasswordBridge`, `ExtensionBridge`, the `WebChannel`, the extension settings and toolbar action connections, the password fill connection. |
| | `TabCommands.qml`: the `Connections { target: tab }` for the navigation, zoom, find, tab and download commands. Commands owned by a component above (reader, print, DevTools, certificate) are handled there. |
| `passwords/PasswordsPage.qml` | `PasswordsPage.qml` (the `StackLayout`, its API, `onActiveChanged` as named steps, the dialogs); `SavedPasswordsTab.qml` (messages, "Offer to save" check box, filter and buttons, the list frame); `SavedPasswordDelegate.qml` (one row: site, username, password with Show/Copy/Delete); `NeverSavedTab.qml`; `RevealedPasswords.qml` (`keyOf`, `isRevealed`, `toggleReveal`, clearing). `rebuild` is split into reading the list and keeping the selection. |
| `browser/TabStrip.qml` | `TabStrip.qml` (the `Rectangle`, the width properties and `computeTabWidth`, the layout); `TabStripScroller.qml` (`tabX`, `scrollTo`, `scrollTarget`, `scrollBy`, `ensureCurrentVisible`, the animation and the delayed check); `TabWidthFreeze.qml` (`closeWithMouse`, `unfreeze`, the timer and hover handling); `TabStripTaps.qml` (`emptyAt` and the two `TapHandler`s). `tst_tabstrip` keeps finding every property it reads on the strip. |
| `browser/PageContextMenu.qml` | `PageContextMenu.qml` (`request`, `webView`, `tab`, `tabModel`, `popupAt`, `rebuild` = clear, collect blocks, add them with single separators); `PageMenuEntries.qml` (a `QtObject`: `linkBlock`, `imageBlock`, `mediaBlock`, `selectionBlock`, `editingBlock`, `pageBlock`, `shortText`, `blocksFor(request)`; the edit entries as a data table of text, icon, action and edit flag); `PageMenuActions.qml` (`perform(action, data)`: a data table action → `WebEngineView` web action, and a table of the other actions → small functions); `SpellCheckLanguagesMenu.qml` (the submenu and `toggleSpellCheckLanguage`). |
| `app/AboutWindow.qml` | `AboutWindow.qml` (window, API, header, tab bar, buttons); `AboutTab.qml`, `ComponentsTab.qml`, `AuthorsTab.qml` (one per tab, today's content); `LicenseWindow.qml`. |
| `extensions/ExtensionSettingsDialog.qml` | `ExtensionSettingsDialog.qml` (dialog, `openFor`, `setValue`, `restoreDefaults`, `accept`, buttons, the three sections); `ExtensionSettingControls.qml` (the six control `Component`s and the `ColorDialog`); `ExtensionSitesSection.qml` (the disabled-sites list). |
| `browser/NewTabPage.qml` | `NewTabPage.qml` (page, API, top-site refresh, heading, search field, the labels); `TopSitesGrid.qml` (the grid and its tiles); `TopSiteMenu.qml` (the tile menu). |
| `history/HistoryWindow.qml` | `HistoryWindow.qml` (window, API, toolbar, timer); `HistoryList.qml` (the list and its delegate; `onClicked` split into select, open, context menu); `HistoryEntryMenu.qml`; `ClearHistoryDialog.qml`. |
| `browser/TabButtonDelegate.qml` | `TabButtonDelegate.qml` (the button, its content and taps); `TabDragHandler.qml` (the `DragHandler`, `contentX`, `update` split into pointer position, auto-scroll and reorder, and `onActiveChanged` split into start and finish); `TabSlideAnimation.qml` (`settle`, `slideAnimation`, `onXChanged`). The menu `onTriggered` becomes named steps. `dragShift` stays readable on the delegate. |
| `extensions/ExtensionsPage.qml` | `ExtensionsPage.qml` and `ExtensionDelegate.qml` (one row of the list). |
| `app/MainMenu.qml` | `MainMenu.qml`; `HistoryMenu.qml` (the History submenu: `rebuild` = clear, then "Recently Closed Tabs" and "Today" through one shared "add a section" function); `ZoomMenuRow.qml` (the zoom row item). |
| `downloads/DownloadsPopup.qml` | `DownloadsPopup.qml`; `DownloadDelegate.qml` (one row); `DownloadStatus.qml` (a `QtObject` with `text(download)`, where `download` has `state`, `isPaused`, `receivedBytes`, `totalBytes`, `speedText`, `interruptReasonString`; one small function per state, chosen from a data table). |
| `site/SiteInfoPopup.qml` | `SiteInfoPopup.qml`; `SiteSecurityState.qml` (`stateIcon`, `stateText`, `stateColor` as data tables, `siteName`, `originUrl`). `reload` is split into reading the permissions and building the rows. |

### 2. Long functions in the other QML files

| File | Change |
| --- | --- |
| `browser/AddressSuggestions.qml` | `buildRows` = the rows of five small functions in today's order (visit, search, bookmarks, history, network suggestions), one shared `appendUnique(rows, seen, row)` for bookmarks and history, then `slice(0, maxRows)`. The row objects keep their keys. |
| `bookmarks/BookmarkMenu.qml` | `appendFolder(menu, id, depth)` split into adding a folder submenu, adding a bookmark item and the empty placeholder. |
| `bookmarks/BookmarksBar.qml` | `openBookmark` as named steps. |
| `extensions/ExtensionsMenu.qml` | `rebuild` split into "no tab", collecting the action extensions and building one entry. |
| `site/PermissionTypeInfo.qml` | `iconFor`, `labelFor`, `sentenceFor` read one data table `type → { icon, label, sentence }`, with today's fallbacks. |
| `site/SitePermissionsDialog.qml` | `reload` split into reading the decisions, grouping them by site and building the model. |

### 3. Page scripts (`src/**/*.js`)

The wrapping IIFE goes. Each file keeps its behavior and its world:

- **`passwords.js`** and **`channel.js`** run at the top level of the `ApplicationWorld`, which is
  shared by every Kondor page script and every extension content script. Their code becomes one
  top-level block `{ … }` holding `const` arrow functions (`const visible = (field) => { … }`) and
  `let`/`const` state, ending with one call that starts the script (`startAutofill()`,
  `connectChannel()`). `const`/`let` in a block never leak into the world's global scope, unlike
  `function` declarations in a non-strict block. Early `return`s of today move into that start
  function. `window.__kondorChannel` stays the only global they set.
- **`extensionruntime.js`** is pasted inside the content script's function (see
  `contentscriptbuilder.cpp`), next to the extension's own code. `__kondorCreateRuntime(cfg)` stays
  the entry point (the builder does not change) and becomes ≤ 10 lines; its helpers become sibling
  functions whose names all start with `__kondor` (for example `__kondorCall(cfg, method, args)`,
  `__kondorSettingsApi(state)`, `__kondorStorageApi(cfg)`, `__kondorTabsApi(cfg)`), so they cannot
  clash with names in an extension's code. The `kondor` object keeps exactly its keys, the frozen
  objects, `window.__kondorExtensions[id]` and `window.__kondorExtensionActions[id]`.
- `tests/data/extensions/sample-content-script.js` contains the runtime: re-record it from the new
  code. Its diff must touch only the runtime part.

### 4. Tests first

Before moving code, add these tests and check that they pass on `main`'s behavior (where the
component under test is new, write the test once it exists; its cases must also hold for `main`).
Each test function body is at most 20 lines, each file is registered in `tests/CMakeLists.txt`, and
tests use isolated locations as the existing ones do:

- `tests/browser/tst_pagecontextmenu.cpp` (loads `PageContextMenu` with a JS request object):
  - `showsTheBlocksOfTheRequest` (data-driven: link, image, video with controls, selection,
    editable field with a misspelling, nothing → page block; the item texts in today's order);
  - `neverDoublesOrEndsWithASeparator`.
- `tests/site/tst_permissiontypeinfo.cpp`: `everyTypeHasIconLabelAndSentence` (data-driven over every
  type and one unknown type, today's values).
- `tests/downloads/tst_downloadstatus.cpp`: `describesEveryState` (data-driven: requested, in
  progress with and without total and speed, paused with and without total, completed, canceled,
  failed with and without a reason).
- `tests/browser/tst_tabstripscroll.cpp`: `newCurrentTabIsScrolledIntoView` and
  `emptyAreaIsOnlyOutsideTabsAndButtons`.

`tst_tabstrip.cpp`, `tst_addresssuggestions.cpp`, `tst_mainmenu.cpp` and the other test files in the
baseline get no new test functions (they would grow past their baseline); only call sites may change,
and no test function there may grow. All existing tests keep passing.

### 5. Baseline, translations, README

- Remove every `qml/**` and `src/**/*.js` entry from `scripts/code-quality-baseline.json`. New files
  add no entries. `python3 scripts/check-code-quality.py` passes.
- Run `cmake --build build --target update_translations`. Copy the existing translation of every
  moved message into its new context in **every** `i18n/*.ts` file, keep the `//:` notes, and drop
  the `vanished`/`obsolete` entries the move leaves behind. No source string changes; no message is
  `unfinished`.
- No README change.

## Acceptance criteria

- [ ] Every file named in §1 exists; every `.qml` and `.js` file is ≤ 200 lines and every function and
      handler in it is ≤ 10 lines, has ≤ 3 parameters and nests ≤ 2 deep.
- [ ] No comments in `qml/**` and `src/**/*.js` (except `//:` translator notes, SPDX lines and "why"
      comments that link a bug report).
- [ ] The baseline has no `qml/**` or `src/**/*.js` entry; `python3 scripts/check-code-quality.py`
      passes.
- [ ] No `switch` that maps a value to a value is left in `PageContextMenu`/`PageMenuActions`,
      `PermissionTypeInfo`, `DownloadStatus` or `SiteSecurityState`.
- [ ] `passwords.js` and `channel.js` define no global other than `window.__kondorChannel`; every
      top-level name of `extensionruntime.js` starts with `__kondor`.
- [ ] The tests of §4 exist; `sample-content-script.js` was re-recorded with a diff limited to the
      runtime; all `ctest` tests pass.
- [ ] No string changes; every `i18n/*.ts` file has no `unfinished` message.
- [ ] Private-tab rules hold: no history, favicon, zoom, top-site or password write from a private tab.
- [ ] Clean build with no new warnings; the offscreen smoke test shows no QML errors.
- [ ] The manual test below behaves and looks as on `main`.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, see AGENTS.md):

1. Open several pages in tabs; open enough tabs to overflow the strip: the arrows, wheel scrolling and
   "current tab scrolled into view" work; close tabs with the mouse (the widths stay until the
   pointer leaves); drag a tab to reorder it; double-click the empty strip for a new tab.
2. Right-click a link, an image, a video, selected text, a text field with a misspelled word and the
   empty page: the same menus as on `main`; every entry works (open in new tab, copy, save, search,
   spelling replacement, Inspect Element).
3. Type in the address bar: visit, search, bookmark, history and suggestion rows as on `main`.
4. Zoom a page, reload: the zoom is kept; a private tab does not save it. Open a long article and use
   reader mode; change the reader font size; leave reader mode with Back.
5. Print to PDF and Save Page; open a page with a certificate error (for example
   `https://expired.badssl.com`) and use Back to Safety and the override. Kill the renderer
   (`chrome://kill`): the crashed page shows.
6. New Tab page: top sites, remove one, open one in a new tab. History window: search, open, copy,
   clear. Downloads popup: start, pause, resume, cancel a download (to the temporary directory).
   Site info popup and Site Permissions dialog: revoke a permission. Main menu: History submenu
   (Recently Closed Tabs, Today) and the zoom row. About window: every tab and the license.
7. Settings → Passwords: save a login on a test form, show, copy, delete it; Never Saved tab. Fill a
   login form with autofill. Settings → Extensions: install the sample (see #146's manual test),
   configure it (every control type and the disabled sites), use its toolbar menu; its page script
   and storage work as on `main`.

## Out of scope

- Any change in behavior, wording, layout, icons or shortcuts. If you find a bug, report it as a
  question on the issue; do not fix it here.
- The baseline entries of test files (#151) and any C++ change, except a call site that a moved QML
  property or function forces.
- The extensions repository (`lukasborges/kondor-extensions`).

## Dependencies

- #135 (checker and baseline), #136 and #137 (window splits), #138, #144, #145, #146 (C++), merged.

## Prototype

None: no visible change.

## Decisions

| Question | Decision |
| --- | --- |
| Why does the IIFE in `passwords.js` and `channel.js` become a block? | The checker measures the outermost function, so an IIFE is always as long as the file. A top-level block with `const` functions keeps every name private to the script in the shared `ApplicationWorld`, which an IIFE was used for. |
| Why prefix the runtime helpers with `__kondor`? | `extensionruntime.js` is pasted inside the content script's function, where the extension's own code also lives. A prefix keeps the helpers from shadowing or being shadowed by an extension's names, and `contentscriptbuilder.cpp` stays unchanged. |
| Why are the test files not here? | The issue lists QML/JS only, and the C++ issues (#138, #144–#146) excluded existing test files. Their 82 entries are a separate job with their own review, filed as #151 and placed right after this issue in the roadmap. |
| Why no new tests in `tst_tabstrip.cpp` and similar files? | They are over the file limit and in the baseline, which can only shrink. New tests get their own files. |
