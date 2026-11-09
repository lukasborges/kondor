<p align="center">
  <img src="packaging/kondor.png" width="128" alt="Kondor Browser logo">
</p>

# Kondor Browser

A native **Qt 6** browser (Qt Quick + Qt WebEngine) with the **KDE/Breeze** look and feel.

> Personal/experimental project. **Not an official KDE project.**

![Kondor Browser screenshot](assets/screenshot.png)

## Status

A working prototype with the core functionality in place: it actually browses, with tabs, a private mode, browsing history, a settings window and keyboard shortcuts. Everyday features such as bookmarks are still missing.

## Features

### Implemented

- **Real tabs** with `Qt WebEngine` (one `WebEngineView` per tab, preserving state when switching)
- **Tab management**: favicons and a loading indicator, drag to reorder, middle-click to close, pinned tabs, a tab context menu (reload, duplicate, pin, close others and tabs to the right), keyboard switching and overflow handling (tabs shrink, then the bar scrolls)
- **Unified address/search bar**: accepts a URL, a host (`example.com`, IP, `localhost`) or free text (searches with the configured engine)
- **Navigation**: back, forward, reload/stop, home
- **Private mode**: off-the-record tabs, isolated from the persistent profile
- **Browsing history**: records visited pages (persistent profile only), with a searchable history window (Ctrl+H) grouped by day and clear options (all or a time range)
- **Settings** (Ctrl+,): home page, search engine (including a custom URL), download folder and privacy options (third-party cookies, clear data on exit), applied immediately and stored in `~/.config/KDE/Kondor.conf`
- **Find in page** (Ctrl+F): incremental search with match counter, previous/next and match case
- **Download manager**: downloads show live progress, speed and size in a toolbar popup; pause, resume, cancel, open the file or show it in its folder, desktop notification on completion/failure, optional "ask where to save", and a confirmation before quitting with active downloads
- **Menu** and **keyboard shortcuts**
- **KDE look** via the `org.kde.desktop` (QQC2) style, with a `Fusion` fallback
- **Semantic colors** (`Kirigami.Theme`/`palette`): follows the system color scheme
- **Translations**: English source strings with a Brazilian Portuguese translation, selected by the system locale

## Stack

- **Qt 6.5+** (tested with **6.11.2**): `Core`, `DBus`, `Gui`, `LinguistTools`, `Qml`, `Quick`, `QuickControls2`, `Sql`, `WebEngineQuick`
- **Qt Quick Controls 2** with the **`org.kde.desktop`** (Breeze) style
- **Kirigami** for theming (`Kirigami.Theme`)
- **C++17** + **CMake 3.21+**
- C++ backend exposed to QML (`QML_ELEMENT` / `QML_SINGLETON`)

## Requirements

- Qt 6.5+ with the modules above (**including Qt WebEngine**)
- The **`org.kde.desktop`** (QQC2 Desktop Style) and **Kirigami** packages available at runtime
- A C++17-capable compiler and CMake 3.21+

On **Fedora** (the original development environment):

```bash
sudo dnf install cmake gcc-c++ \
    qt6-qtbase-devel qt6-qtdeclarative-devel qt6-qtwebengine-devel qt6-qttools-devel \
    kf6-qqc2-desktop-style kf6-kirigami
```

> Package names vary across distributions. What matters is having Qt 6 with
> WebEngine plus KDE's `qqc2-desktop-style`/Kirigami.

## Build and run

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
./build/kondor
```

## Project structure

```
CMakeLists.txt
src/
  main.cpp            startup (WebEngine, KDE style, QML engine)
  profilemanager.*    persistent/private profiles, address/search resolution
  settings.*          QML singleton: user settings persisted with QSettings
  tab.*               per-tab state (title, URL, icon, loading, history)
  tabmodel.*          tab model (QAbstractListModel)
  database.*          SQLite storage (schema + migrations)
  historymanager.*    QML singleton: write/query/clear browsing history
  historymodel.*      history list model (QAbstractListModel)
  downloadmanager.*   QML singleton: downloads list model, actions and notifications
  notifier.*          QML singleton: desktop notifications over D-Bus
qml/
  Main.qml            window, tab bar, navigation bar, menu, shortcuts
  WebViewTab.qml      WebEngineView + bridge to the Tab object
  TabButtonDelegate.qml  one tab button (favicon, title, close, drag, pinned)
  TabContextMenu.qml  context menu for a tab in the tab bar
  InlineBar.qml       shared strip between the header and the page content
  FindBar.qml         find bar (Ctrl+F)
  DownloadsPopup.qml  download list popup with progress and actions
  HistoryWindow.qml   browsing history window (search, grouped by day, clear)
  SettingsWindow.qml  settings window (home page, search, downloads, privacy)
```

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+T` | New tab |
| `Ctrl+Shift+N` | New private tab |
| `Ctrl+W` | Close tab (quits the app if it is the last one) |
| `Ctrl+Tab` / `Ctrl+PgDown` | Next tab |
| `Ctrl+Shift+Tab` / `Ctrl+PgUp` | Previous tab |
| `Ctrl+1` … `Ctrl+8` | Go to tab N |
| `Ctrl+9` | Go to the last tab |
| `Ctrl+Shift+PgUp` / `Ctrl+Shift+PgDown` | Move the current tab left / right |
| `Ctrl+H` | Browsing history |
| `Ctrl+,` / `Ctrl+Shift+,` | Configure Kondor Browser (settings) |
| `Ctrl+L` | Focus the address bar |
| `Ctrl+F` | Find in page |
| `F3` / `Shift+F3` | Next / previous match (find bar open) |
| `Esc` | Close the find bar |
| `Ctrl+R` / `F5` | Reload |
| `Alt+←` / `Alt+→` | Back / forward |
| `Ctrl++` / `Ctrl+-` | Zoom in / out |
| `Ctrl+0` | Reset zoom |

## Translations

English is the source language; every user-visible string is wrapped in `qsTr()`.
Brazilian Portuguese ships in `i18n/kondor_pt_BR.ts`, and the compiled `.qm` files are
embedded in the binary under `:/i18n`. Kondor Browser loads the translation that matches the
system locale at startup (and Qt's own translations for dialogs and context menus).

- **Update the `.ts` files** after changing strings: `cmake --build build --target update_translations`.
  This runs `lupdate` with `-no-obsolete` and writes the result to `i18n/`.
- **Add a language**: create `i18n/kondor_<lang>.ts` (the `update_translations` target creates it
  if it is listed in `TS_FILES`), add it to `TS_FILES` in `CMakeLists.txt`, and translate the
  messages with Qt Linguist (`linguist-qt6 i18n/kondor_<lang>.ts`).

## Notes

- The `org.kde.desktop` style is applied in `main.cpp`; if it cannot be found, it falls back to `Fusion`.
- Colors come from the theme, so changing the KDE color scheme will not break the layout.

## License

Licensed under the **GNU General Public License v3.0 or later** (GPL-3.0-or-later). See [LICENSE](LICENSE).
