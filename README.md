<p align="center">
  <img src="packaging/kondor.png" width="128" alt="Kondor Browser logo">
</p>

<h1 align="center">Kondor Browser</h1>

<p align="center"><b>A fast, private web browser that feels at home on the KDE Plasma desktop.</b></p>

Kondor Browser opens modern websites with the same engine as Chrome, but it looks and behaves like any other Plasma app: Breeze controls, your icons and your color scheme, KDE dialogs and notifications, and the keyboard shortcuts you already know. Ads and trackers are blocked from the start, and private tabs leave nothing behind when you close them.

![Kondor Browser screenshot](assets/screenshot.png)

## Highlights

- **Native on Plasma.** It follows your light or dark color scheme and uses Breeze icons and the KDE Configure, About and file dialogs. It can be your default browser.
- **Private by default.** Ads and trackers are blocked. Private tabs and windows never write anything to disk, and every site asks before it uses your camera, microphone or location.
- **Everything at hand.** Tabs, bookmarks, history, downloads, reader mode, find in page, zoom and developer tools, without add-ons.
- **Speaks your language.** Kondor Browser comes in 19 languages, picked from your system settings.

## Download

Get the latest AppImage from the [Releases page](https://github.com/lukasborges/kondor/releases/latest). Make it executable and run it; no installation needed. To build it yourself, see [Build and run](#build-and-run).

New features and fixes land every week. See what's coming next on the [Kondor Roadmap](https://github.com/users/lukasborges/projects/1).

## Features

### Tabs and windows

- Open as many tabs as you like. They share the tab bar evenly, and arrows appear when there are too many to fit.
- Drag tabs to reorder them, pin the ones you always keep open, and middle-click to close.
- Right-click a tab to reload, duplicate, pin it, close the others, or move it to a new window.
- Closed a tab by mistake? **Ctrl+Shift+T** brings it back, up to the last 20.
- Work in several windows at once. When you start Kondor again, it can reopen every window and tab from last time.
- Launching Kondor while it is already running opens the link in the window you used last, instead of starting a second copy.

### Search and the address bar

- Type an address or anything you want to search for in the same bar.
- Suggestions appear as you type: your bookmarks, the sites you visit most, and, if you turn them on, the search engine's suggestions. Known sites are completed for you (`kd` becomes `kde.org`).
- Choose your search engine in the settings, or enter any search URL.
- New tabs show a search box and the sites you visit most, one click away.

### Privacy and security

- **Ad and tracker blocking** using the EasyList and EasyPrivacy lists, which update by themselves. A shield shows how many requests were blocked on the current page, and you can switch blocking off for a site.
- **Private tabs and windows** keep no history, cookies, downloads list or site settings, and each private tab is isolated from the others.
- **Site permissions:** camera, microphone, screen sharing, location, notifications and clipboard access are always requested in a bar above the page. Your answer is remembered per site, and you can review it or take it back at any time.
- **Connection security** at a glance: a padlock for secure sites, a "Not Secure" label for the rest, and a clear warning page before you visit a site with an invalid certificate.
- Optionally block third-party cookies and clear your browsing data when you quit.

### Reading and using pages

- **Reader mode** turns cluttered articles into clean, readable text in your color scheme, with adjustable font and size.
- **Find in page** highlights every match as you type.
- **Zoom** is remembered for each site.
- **Spell checking** in text fields, with suggestions in the right-click menu and a choice of languages.
- A **right-click menu** for links, images, videos, selected text and text fields.
- **Print**, **save as PDF**, or **save the page** to read it offline.
- **Full screen** for videos, or for the whole window with F11.
- A page that crashes only affects its own tab, and one click reloads it.

### Bookmarks, history and downloads

- Bookmark a page with the star (**Ctrl+D**) and organize bookmarks in folders on the bookmarks toolbar.
- The bookmark manager supports drag and drop between folders and imports bookmarks from Firefox and Chrome. New profiles start with a set of KDE and Linux bookmarks.
- **History** is grouped by day and searchable, and you can clear all of it or just a time range.
- **Downloads** show their progress in the toolbar and can be paused, resumed or opened. You get a desktop notification when one finishes, and Kondor asks before quitting while downloads are still running.

### Made for KDE

- Breeze style, Breeze icons and your system color scheme.
- A **Configure Kondor Browser** window in the familiar KDE layout, with a searchable sidebar and Defaults, OK, Apply and Cancel buttons.
- Desktop notifications, KDE file dialogs, and a **New Private Window** action in the launcher.
- Familiar keyboard shortcuts, listed [below](#keyboard-shortcuts).

### For web developers

- Chromium **developer tools** (F12), docked below the page, and **Inspect Element** in the right-click menu.
- **View page source** from the right-click menu.

## Stack

- **Qt 6.8+** (tested with **6.11.2**): `Core`, `DBus`, `Gui`, `LinguistTools`, `Qml`, `Quick`, `QuickControls2`, `Sql`, `WebEngineCore`, `WebEngineQuick`, `Widgets`
- **Qt Quick Controls 2** with the **`org.kde.desktop`** (Breeze) style
- **Kirigami** for theming (`Kirigami.Theme`)
- **C++17** + **CMake 3.21+**
- C++ backend exposed to QML (`QML_ELEMENT` / `QML_SINGLETON`)

## Requirements

- Qt 6.8+ with the modules above (**including Qt WebEngine**)
- The **`org.kde.desktop`** (QQC2 Desktop Style) and **Kirigami** packages available at runtime
- A C++17-capable compiler and CMake 3.21+

On **Fedora** (the original development environment):

```bash
sudo dnf install cmake gcc-c++ \
    qt6-qtbase-devel qt6-qtdeclarative-devel qt6-qtwebengine-devel qt6-qttools-devel \
    kf6-qqc2-desktop-style kf6-kirigami hunspell-en-US hunspell-pt-BR
```

The Hunspell dictionaries (`/usr/share/hunspell`) are converted to Qt WebEngine's
`.bdic` format at build time for spell checking; choose the languages with
`-DKONDOR_SPELLCHECK_LANGS="en_US;pt_BR"`.

> Package names vary across distributions. What matters is having Qt 6 with
> WebEngine plus KDE's `qqc2-desktop-style`/Kirigami.

## Build and run

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
./build/kondor
```

### Tests

The non-UI logic has Qt Test suites (`tst_addressresolver`, `tst_tabmodel`):

```bash
cmake --build build
ctest --test-dir build --output-on-failure
```

Pass `-DBUILD_TESTING=OFF` to configure without building them.

## Set as default browser

Install Kondor (or use the AppImage), then open **System Settings → Default Applications → Web
browser** and choose **Kondor Browser**. From a terminal the same is done with:

```bash
xdg-settings set default-web-browser kondor.desktop
```

Kondor then opens links clicked in other applications. The desktop entry also provides a
**New Private Window** action (`kondor --private`).

## Project structure

```
CMakeLists.txt
src/
  main.cpp            startup (command line, WebEngine, KDE style, QML engine)
  profilemanager.*    persistent/private profiles, address/search resolution
  addressresolver.*   pure address/search resolution (unit tested)
  startupargs.*       QML singleton: command-line URLs and private mode
  startupurl.*        command-line argument to URL conversion (unit tested)
  settings.*          QML singleton: user settings persisted with QSettings
  sessionmanager.*    QML singleton: save/restore the normal tabs of every window
  windowmanager.*     QML singleton: create the browser windows (normal and private)
  singleinstance.*    one process per profile: later launches forward their URLs over a local socket in the runtime directory
  tab.*               per-tab state (title, URL, icon, loading, history, pending permissions)
  tabmodel.*          tab model (QAbstractListModel)
  database.*          SQLite storage (schema + migrations)
  historymanager.*    QML singleton: write/query/clear browsing history
  historymodel.*      history list model (QAbstractListModel)
  bookmarkmanager.*   QML singleton: bookmark tree, folders, HTML import
  searchsuggestions.* QML singleton: search-engine autocomplete for the address bar
  bookmarkmodel.*     one folder's items as a list model (QAbstractListModel)
  faviconstore.*      QML singleton: one favicon per host (table `favicons`), filled by normal tabs only
  downloadmanager.*   QML singleton: downloads list model, actions and notifications
  notifier.*          QML singleton: desktop notifications over D-Bus
  filehelper.*        QML singleton: file names, temporary PDFs and opening files for print / save
  aboutinfo.*         QML singleton: read-only version and license data for the About window
qml/
  BrowserWindow.qml   one browser window: tab bar, navigation bar, menu, shortcuts
  AddressSuggestions.qml  address bar dropdown (visit/search, bookmarks, history, suggestions)
  WebViewTab.qml      WebEngineView + bridge to the Tab object
  NewTabPage.qml      New Tab page (logo, search field, top sites)
  TabButtonDelegate.qml  one tab button (favicon, title, close, drag, pinned)
  TabContextMenu.qml  context menu for a tab in the tab bar
  InlineBar.qml       shared strip between the header and the page content
  FindBar.qml         find bar (Ctrl+F)
  PermissionBar.qml   inline site permission request with Allow and Block
  PermissionTypeInfo.qml  wording and Breeze icons for each permission type
  SitePermissionsDialog.qml  remembered site decisions, filter and Revoke
  DownloadsPopup.qml  download list popup with progress and actions
  HistoryWindow.qml   browsing history window (search, grouped by day, clear)
  SettingsWindow.qml  settings window (home page, new tabs, search, downloads, privacy)
  AboutWindow.qml     About Kondor Browser window with components, authors and license
  BookmarksBar.qml    bookmarks toolbar under the navigation bar
  BookmarkMenu.qml    folder menu (bar folders and the main menu submenu)
  BookmarksWindow.qml bookmark manager window (folders, reorder, drag and drop, import)
  SiteIcon.qml        favicon with a fallback icon (toolbar, manager, New Tab page)
```

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+T` | New tab |
| `Ctrl+Shift+N` | New private tab |
| `Ctrl+N` | New window |
| `Ctrl+Shift+P` | New private window |
| `Ctrl+W` | Close tab (closes the window if it is the last one; the app quits when the last window closes) |
| `Ctrl+Shift+W` | Close window |
| `Ctrl+Shift+T` | Reopen closed tab |
| `Ctrl+Tab` / `Ctrl+PgDown` | Next tab |
| `Ctrl+Shift+Tab` / `Ctrl+PgUp` | Previous tab |
| `Ctrl+1` … `Ctrl+8` | Go to tab N |
| `Ctrl+9` | Go to the last tab |
| `Ctrl+Shift+PgUp` / `Ctrl+Shift+PgDown` | Move the current tab left / right |
| `Ctrl+H` | Browsing history |
| `Ctrl+D` | Bookmark this page (edit name and folder) |
| `Ctrl+Shift+B` | Show or hide the bookmarks toolbar |
| `Ctrl+Shift+O` | Manage bookmarks |
| `Ctrl+,` / `Ctrl+Shift+,` | Configure Kondor Browser (settings) |
| `Ctrl+L` | Focus the address bar |
| `Ctrl+F` | Find in page |
| `Ctrl+P` | Print (opens a PDF in the viewer) |
| `Ctrl+S` | Save page as… |
| `F12` / `Ctrl+Shift+I` | Toggle developer tools |
| `Ctrl+Alt+R` | Toggle reader mode (article pages) |
| `Ctrl+F` (Configure window) | Filter the settings pages |
| `F3` / `Shift+F3` | Next / previous match (find bar open) |
| `Esc` | Close the find bar; leave page full screen |
| `Shift+F10` / `Menu` | Open the page context menu |
| `F11` | Toggle window full screen |
| `Ctrl+R` / `F5` | Reload |
| `Alt+←` / `Alt+→` | Back / forward |
| `Ctrl++` / `Ctrl+-` | Zoom in / out |
| `Ctrl+0` | Reset zoom (also by clicking the zoom level in the address bar) |

## Translations

English is the source language; every user-visible string is wrapped in `qsTr()`.
Kondor Browser ships translations for Catalan, Czech, Dutch, French, German, Italian,
Japanese, Korean, Polish, Portuguese (Brazil and Portugal), Russian, Spanish, Swedish,
Turkish, Ukrainian, and Chinese (Simplified and Traditional), in `i18n/kondor_<lang>.ts`.
The compiled `.qm` files are embedded in the binary under `:/i18n`. Kondor Browser loads
the translation that matches the system locale at startup (and Qt's own translations for
dialogs and context menus).

- **Update the `.ts` files** after changing strings: `cmake --build build --target update_translations`.
  This runs `lupdate` with `-no-obsolete` and writes the result to `i18n/`.
- **Add a language**: create `i18n/kondor_<lang>.ts` (the `update_translations` target creates it
  if it is listed in `TS_FILES`), add it to `TS_FILES` in `CMakeLists.txt`, and translate the
  messages with Qt Linguist (`linguist-qt6 i18n/kondor_<lang>.ts`).
- **Keep them complete**: a PR that adds or changes a user-visible string updates every
  `i18n/*.ts` file. The "Check translations" CI step runs `update_translations`, fails when the
  result differs from the committed files, and reports any `unfinished`, empty, or
  placeholder-mismatched message.

## Notes

- The `org.kde.desktop` style is applied in `main.cpp`; if it cannot be found, it falls back to `Fusion`.
- Colors come from the theme, so changing the KDE color scheme will not break the layout.

## Third-party code

- [Mozilla Readability](https://github.com/mozilla/readability) (Apache-2.0), vendored in `3rdparty/readability/` with its license, powers reader mode.

## License

Licensed under the **GNU General Public License v3.0 or later** (GPL-3.0-or-later). See [LICENSE](LICENSE).
