# Refactor: split BrowserWindow.qml into small components (#136)

> **Issue:** [#136](https://github.com/lukasborges/kondor/issues/136) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first, especially "Code quality". This file is the source of truth for the issue; only the architect edits it.

## Objective

`qml/app/BrowserWindow.qml` has 1 488 lines, 106 comments and 12 functions or handlers over the
10-line limit. Split it into small components that each do one thing, so that every file follows
AGENTS.md → "Code quality". **The browser behaves exactly as before.**

## Context

- **The file today** (`origin/main` after #135):

  | Lines | Part |
  | --- | --- |
  | 12–100 | Window properties, title, `TabModel`, full screen state, close confirmation |
  | 101–211 | `ConfirmDialog` for quitting with downloads; tab functions (`closeTabAt`, `closeTabFor`, `activateTabAt`, `stepTab`, `openNewTab`, `moveTabToNewWindow`, `moveCurrentTab`, `openTabContextMenu`) and `TabContextMenu` |
  | 212–367 | Print / save functions, `open…` functions for the other windows, `openUrl`, `openUrlsInNewTabs`, bookmark editor functions, `pageBookmarked` |
  | 368–386 | `Component.onCompleted`: initial or restored tabs |
  | 388–972 | `header`: `TabStrip`, the navigation `ToolBar` (back, forward, reload, home, address bar, downloads, extensions, main menu) and `BookmarksBar` |
  | 475–896 | The address bar alone: `TextField` with inline completion and key handling, security button, the right-hand buttons (ad blocking, extension badges, zoom, passwords, reader, bookmark) and the popups `AddressSuggestions`, `AdBlockPopup`, `SiteInfoPopup` |
  | 973–1019 | Page area: `PermissionBar`, `PasswordBar`, `FindBar`, the `WebViewTab` repeater, `FullScreenHint` |
  | 1020–1068 | On-demand windows (history, settings, about, bookmarks, site permissions) |
  | 1069–1180 | Bookmark editor `Popup`; PDF, page and download `FileDialog`s |
  | 1181–1209 | `Connections` to `DownloadManager` |
  | 1210–1306 | `tabModel` alias and the 15 `…Action` properties used by the main menu |
  | 1307–1467 | 31 `Shortcut`s |
  | 1468–1488 | `Connections` to `tabs` and `tabs.currentTab` (address bar sync) |

- **Baseline entries** in `scripts/code-quality-baseline.json`: `comments` 106, `file-length`
  1 488, and `function-length` for `moveCurrentTab`, `onAccepted#2`, `onClosing#1`,
  `onCompleted#1`, `onDownPressed#1`, `onEscapePressed#1`, `onTextEdited#1`, `onUpPressed#1`,
  `openBookmarkEditor`, `openUrl`, `saveBookmark` and `updateSuggestions`.
- **Who uses the window from outside:**
  - `src/app/windowmanager.cpp` creates `BrowserWindow`, sets `privateWindow`, `initialUrls`,
    `initialTitles` and `initialCurrentIndex`, reads `privateWindow`, and calls
    `openUrlsInNewTabs(urls)` and `openExtensionsSettings()` with `QMetaObject::invokeMethod`.
  - `MainMenu.qml` (`browserWindow.`): the 15 `…Action` properties, `tabModel`,
    `windowFullScreen` (read and written, for the full screen button), `openUrl(url, background)`,
    `openBookmarks()`, `openBookmarkEditor()`.
  - `TabStrip.qml` and `TabButtonDelegate.qml` (`targetWindow.`): `closeTabFor(tab)`,
    `openTabContextMenu(tab, position)`; `TabContextMenu.qml`: `closeTabAt(index)`.
- **Tests that touch it:** `tests/app/tst_mainmenu.cpp`. Its stand-in window has the same Action
  names, and `actionsDoNotShareASequenceWithAShortcut` reads the source of
  `qml/app/BrowserWindow.qml` to compare the Actions' `shortcut:` with the `Shortcut { sequence… }`
  items. No test loads the address bar.
- **Translations:** `qsTr()` uses the QML file name as its context. A message that moves to another
  file gets a new context in `i18n/*.ts`.

## Design / behavior

### 1. Components

Create these files. Each one is at most 200 lines. Every function and handler has at most 10 lines
of body, at most 3 parameters and nesting depth 2. No comments. The names are binding; the split of
the functions inside a component is up to you, as long as the limits hold.

| File | Holds |
| --- | --- |
| `qml/app/BrowserWindow.qml` | The `ApplicationWindow`: the public properties and functions in §2, `title`, the `TabModel`, and the composition of the components below. No logic beyond one-line forwarding functions. |
| `qml/app/WindowTabController.qml` | Tab logic: open the initial or restored tabs (today's `Component.onCompleted`), `closeTabAt`, `closeTabFor`, `activateTabAt`, `stepTab`, `openNewTab`, `moveTabToNewWindow`, `moveCurrentTab`, `openUrl`, `openUrlsInNewTabs`, and the `TabContextMenu`. |
| `qml/app/FullScreenController.qml` | `pageFullScreen`, `windowFullScreen`, `visibilityBeforeFullScreen` and `updateFullScreen()`. |
| `qml/app/WindowCloseGuard.qml` | Today's `onClosing`: save the session, ask for confirmation when the last window closes with running downloads (`quitConfirmed`, its `ConfirmDialog`), then `WindowManager.closeWindow`. The root's `onClosing` only forwards to it. |
| `qml/app/WindowDialogs.qml` | The on-demand windows (history, settings, about, bookmarks, site permissions) and their `open…()` functions, including `openExtensionsSettings()`. |
| `qml/app/PageFileDialogs.qml` | Print, Save Page As and Save as PDF: `localPath`, `suggestedFile`, `printPage`, `savePageAs`, `saveAsPdf`, `canPrintOrSave`, and the PDF and page `FileDialog`s. |
| `qml/app/BrowserActions.qml` | A `QtObject` with the 15 `Action`s (same names, texts, icons, `shortcut:` values). |
| `qml/app/BrowserShortcuts.qml` | All `Shortcut` items. |
| `qml/app/NavigationToolBar.qml` | The `ToolBar` row: back, forward, reload/stop and home buttons, the `AddressBar`, and the downloads, extensions and main menu buttons with their popups. |
| `qml/app/PageArea.qml` | The page column: `PermissionBar`, `PasswordBar`, `FindBar` and the `WebViewTab` repeater. |
| `qml/browser/AddressBar.qml` | The `TextField`, its key handlers, its sync with the current tab (today's `Connections` at 1468–1488 and `syncFromTab`), the suggestions `Timer` and `AddressSuggestions`. The handlers only call functions of `AddressCompleter`. |
| `qml/browser/AddressCompleter.qml` | The typing state (`typedText`, `previousText`, `previousTypedLength`, `lastEditDeleted`), `completeHost()`, `updateSuggestions()`, moving the selection up or down, and restoring the typed text on Escape. |
| `qml/browser/AddressBarButtons.qml` | The right-hand `Row` of the address bar, made of the buttons below and the extension action badges. |
| `qml/site/SiteSecurityButton.qml` | The security button (with `securityIconForState`) and its `SiteInfoPopup`. |
| `qml/adblock/AdBlockButton.qml` | The ad blocking button, its badge and its `AdBlockPopup`. |
| `qml/browser/ZoomButton.qml` | The zoom level button. |
| `qml/passwords/PasswordButton.qml` | The passwords button and its menu. |
| `qml/browser/ReaderButton.qml` | The reader mode button. |
| `qml/bookmarks/BookmarkButton.qml` | The star button in the address bar. |
| `qml/bookmarks/BookmarkEditorPopup.qml` | The bookmark editor `Popup` with `open()` (today's `openBookmarkEditor`), `save()`, `remove()` and `pageBookmarked`. |
| `qml/downloads/DownloadSaveDialog.qml` | The download location `FileDialog` and the `Connections` to `DownloadManager` and `DownloadManager.model`. |

If a file still goes over 200 lines, split it again inside the same feature folder and say so in
the PR. Do not merge two rows of the table into one file.

### 2. Public API of `BrowserWindow`

These stay on the root object with the same names, types and behavior, so `WindowManager`,
`TabStrip`, `TabButtonDelegate` and `TabContextMenu` do not change:
`privateWindow`, `initialUrls`, `initialTitles`, `initialCurrentIndex`, `tabModel`,
`windowFullScreen` (writable), `openUrl(url, background)`, `openUrlsInNewTabs(urls)`,
`openExtensionsSettings()`, `openBookmarks()`, `openBookmarkEditor()`, `closeTabAt(index)`,
`closeTabFor(tab)`, `openTabContextMenu(tab, position)`.

The Actions move to `BrowserActions`. The root exposes them as
`readonly property BrowserActions actions`. `MainMenu.qml` reads `browserWindow.actions.newTabAction`
and so on, and the stand-in window of `tst_mainmenu.cpp` gets the same `actions` object.

### 3. Wiring

- Components receive what they need through `required property` (for example
  `required property TabModel tabs`, `required property var browserWindow`), the way `TabStrip`
  receives `tabModel` and `targetWindow`. They do not reach into ids of other files.
- The Tab bridge pattern stays: the UI talks only to `tabs.currentTab`.
- Private windows: every component that writes something (bookmark editor, downloads, session)
  keeps the existing `isPrivate` / `privateWindow` checks exactly as they are.

### 4. Tests

- Add `tests/browser/tst_addressbar.cpp`. It loads `qml/browser/AddressBar.qml` with a stand-in
  `TabModel`, the way `tst_addresssuggestions.cpp` does, and checks:
  - typing the start of a known host completes it inline, with the completed part selected;
  - Backspace after a completion does not complete again;
  - Down and Up move through the suggestions and put the selected text in the field;
  - Escape with the suggestions open restores the typed text and closes them;
  - Enter navigates the current tab to the resolved address;
  - switching the current tab shows that tab's URL.
- Update `actionsDoNotShareASequenceWithAShortcut` to read `qml/app/BrowserActions.qml` for the
  Actions and `qml/app/BrowserShortcuts.qml` for the Shortcuts.
- All existing tests keep passing.

### 5. Baseline, translations, README

- Remove every `qml/app/BrowserWindow.qml` entry from `scripts/code-quality-baseline.json`. The new
  files add no entries. `python3 scripts/check-code-quality.py` passes.
- Register every new file in `QML_FILES` in `CMakeLists.txt`.
- Run `cmake --build build --target update_translations`. Moved messages get new contexts: copy the
  existing translation of every moved message into its new context in **every** `i18n/*.ts` file,
  so no message is `unfinished`. Drop the `vanished`/`obsolete` entries the move leaves behind. No
  source string changes.
- No README change: nothing visible to the user changes.

## Acceptance criteria

- [ ] The 21 files of §1 exist, each at most 200 lines; `BrowserWindow.qml` keeps only the root
      window, its public API (§2) and the composition.
- [ ] `python3 scripts/check-code-quality.py` passes and the baseline has no
      `qml/app/BrowserWindow.qml` entry and no entry for any file of §1.
- [ ] No comments in the new or changed QML files.
- [ ] `tst_addressbar` exists with the six checks of §4; `tst_mainmenu` reads the new files; all
      `ctest` tests pass.
- [ ] No string changes; every `i18n/*.ts` file has no `unfinished` message.
- [ ] Clean build, no new warnings; the offscreen smoke test shows no QML errors.
- [ ] The manual test below behaves as on `main`.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, see AGENTS.md):

1. Start Kondor. Open a site, go back and forward, reload, and stop a reload. Press Home.
2. Visit `https://kde.org`, open a new tab and type `kd` in the address bar: the host completes inline. Use Down, Up and Escape in the
   suggestions, then press Enter on a suggestion.
3. Open the site information, ad blocking, zoom, reader and bookmark buttons. Add a bookmark,
   edit it, then remove it from the popup.
4. Try every shortcut in the README table, and every main menu item (new tab, new private tab, new
   window, new private window, history, find, print, save page, save as PDF, developer tools, site
   permissions, settings, about).
5. Move a tab with Ctrl+Shift+PgUp/PgDown and to a new window from the tab context menu. Close a tab
   and reopen it.
6. Start a download: the save dialog opens when the setting asks, and the downloads button shows
   progress. Close the window during the download: the confirmation appears.
7. Toggle full screen with F11, and play a video in page full screen.
8. Open a private window and repeat steps 2 and 3: nothing is written to history or bookmarks
   suggestions.

## Out of scope

- Any change in behavior, wording, icons or layout. If you find a bug, report it as a question on
  the issue; do not fix it here.
- Other files over the limits (`SettingsWindow.qml`, `BookmarksWindow.qml`: #137; C++: #138; the
  rest of the QML, including `WebViewTab.qml`, `TabStrip.qml` and `PageContextMenu.qml`: #139).
- Changing `MainMenu.qml` beyond reading the Actions from `browserWindow.actions`.

## Dependencies

- #135 (feature folders, checker and baseline), merged.

## Prototype

None: no visible change. The running app must look the same as on `main`.

## Decisions

| Question | Decision |
| --- | --- |
| Keep the 15 Actions on the root window? | No. They move to `BrowserActions`, exposed as `actions`; `MainMenu` and the `tst_mainmenu` stand-in read `browserWindow.actions.…`. Every other public member stays on the root (§2). |
| Where do the address bar buttons go? | Each one in its feature folder (`site`, `adblock`, `passwords`, `bookmarks`, `browser`), so a later change to a feature stays inside its folder. |
