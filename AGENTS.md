# AGENTS.md — guide for AI coding agents (and humans)

Read this file before working on any issue of the **Kondor Roadmap**
(<https://github.com/users/lukasborges/projects/1>). Every issue assumes the rules below.

## What Kondor is

A small web browser written in **C++17 + Qt 6 (Qt Quick / QML + Qt WebEngine)** that must look and
behave like a native **KDE Plasma** app (Breeze style, Breeze icons, system color scheme).

- Minimum Qt: **6.5** (`find_package(Qt6 6.5 …)`), developed and tested on **Qt 6.11.2 / Fedora**.
- QML style: `org.kde.desktop` (qqc2-desktop-style), set in `src/main.cpp`.
- Kirigami is used **only for theming** (`Kirigami.Theme.*`) and, where useful, `Kirigami.FormLayout`
  / `Kirigami.InlineMessage` / `Kirigami.Icon`. The main window is a QQC2 `ApplicationWindow`, not a
  `Kirigami.ApplicationWindow`. Do not convert it.

## Build and run

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --parallel
./build/kondor
```

Smoke test without a display (useful in CI or for agents):

```bash
QT_QPA_PLATFORM=offscreen timeout 15 ./build/kondor
```

It must not print QML errors (`ReferenceError`, `TypeError`, `Cannot assign…`, `is not a type`).
Fedora build dependencies are listed in `README.md` and in `.github/workflows/build.yml`.

## Architecture (current)

```
src/main.cpp            app setup: QtWebEngineQuick::initialize, org.kde.desktop style, QML engine
src/profilemanager.*    QML singleton `ProfileManager`: persistent profile "kondor", private profiles,
                        resolveAddress() (URL vs. search), downloads (auto-accepted to ~/Downloads)
src/tab.*               `Tab` (QML_UNCREATABLE): per-tab state + command signals
src/tabmodel.*          `TabModel` (QAbstractListModel, role "tab"): add/close/current tab
qml/Main.qml            window, tab bar, navigation toolbar, address bar, menu, shortcuts
qml/WebViewTab.qml      one WebEngineView per tab, bridges WebEngineView <-> Tab
```

### The Tab bridge pattern (follow it)

- **State** flows *WebEngineView → Tab*: `WebViewTab.qml` calls `tab.setTitle()`, `tab.setUrl()`,
  `tab.setLoading()`… and `Tab` exposes read-only `Q_PROPERTY`s with `NOTIFY` signals.
- **Commands** flow *UI → Tab → WebEngineView*: the UI calls `tab.reload()`, `tab.zoomIn()`… which
  only `emit reloadRequested()` etc.; `WebViewTab.qml` listens with `Connections { target: root.tab }`
  and acts on the `WebEngineView`.
- New per-tab features must use the same pattern: add a property + setter for state, or an
  `Q_INVOKABLE` command + `…Requested` signal, and handle it in `WebViewTab.qml`.
- The UI must only talk to `tabs.currentTab` (a `Tab`), never directly to a `WebEngineView`.

### Profiles and privacy (hard rule)

- Normal tabs share `ProfileManager.defaultProfile()` (storage name `kondor`, persistent).
- **Every private tab gets its own off-the-record profile** (`createPrivateProfile()`).
- **Nothing from a private tab may ever be written to disk**: no history, no session restore, no
  per-site zoom, no remembered permissions, no download list persistence, no bookmarks suggestions
  based on it. Always check `tab.isPrivate` (QML) / `Tab::isPrivate()` (C++).

## Shared building blocks (create them once, reuse them)

Several issues need the same infrastructure. Whoever implements an issue first creates the block
exactly as described here; later issues reuse it. Do not create parallel alternatives.

| Block | Files | Contract |
| --- | --- | --- |
| **Settings** | `src/settings.{h,cpp}` | QML singleton `Settings` (`QML_ELEMENT` + `QML_SINGLETON`, same `instance()`/`create()` pattern as `ProfileManager`) wrapping `QSettings` (organization `KDE`, application `Kondor` → `~/.config/KDE/Kondor.conf`). One `Q_PROPERTY` (READ/WRITE/NOTIFY) per option, written immediately on set. Defined in issue #3. |
| **Database** | `src/database.{h,cpp}` | `Database::instance()` opens one SQLite file at `QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/kondor.sqlite"` with `QSqlDatabase` (driver `QSQLITE`, connection name `kondor`). Schema versioning with `PRAGMA user_version` and a `migrate()` step per version. Add `Sql` to `find_package(Qt6 …)` and `Qt6::Sql` to `target_link_libraries`. Defined in issue #1. |
| **Notifications** | `src/notifier.{h,cpp}` | QML singleton `Notifier` with `Q_INVOKABLE void notify(const QString &title, const QString &body, const QString &iconName)`, implemented with `QDBusInterface` on `org.freedesktop.Notifications` (`Notify` method, app name `Kondor`, `app_icon` = `kondor`). Add `DBus` to Qt components and `Qt6::DBus`. Defined in issue #4. |
| **Inline page bar** | `qml/InlineBar.qml` | A bar shown between the toolbar and the page (for find, permission prompts, crash notices): `Kirigami.InlineMessage`-like look, uses `Kirigami.Theme` colors. Defined in issue #5. |

## UI prototypes (visual target)

`prototypes/` holds a static QML mockup for every issue with UI, rendered with the real Breeze
style into `prototypes/screenshots/*.png` (see `prototypes/README.md` for the issue → file table).
When an issue has a prototype, **the implementation must match it**: same controls, Kirigami
components, icon names, wording and placement. Copy structure from the prototype's QML, but never
import files from `prototypes/` in the app. If the spec and the prototype disagree, the spec wins;
mention the difference in the PR.

## Conventions

- **C++**: C++17, Qt types and containers, `QStringLiteral`/`QLatin1String`, signals emitted only
  when a value really changes (see `Tab::setTitle`). Expose classes to QML with `QML_ELEMENT`
  (and `QML_SINGLETON` for singletons); register every new source file in `CMakeLists.txt`
  (`qt_add_qml_module(... SOURCES ...)`).
- **QML**: new components go in their own file under `qml/` and must be added to `QML_FILES` in
  `CMakeLists.txt`. Keep `Main.qml` readable: extract big blocks (bars, popups, panels) into files.
- **Look & feel**: only QQC2 controls with the `org.kde.desktop` style; colors from
  `Kirigami.Theme`/`palette` (never hardcoded colors); icons via `icon.name` with **Breeze icon
  names** (`bookmark-new`, `edit-find`, `document-save`, `security-high`, …); tooltips with
  `ToolTip.delay: 600` like the existing buttons; follow KDE HIG wording (Title Case for menu items).
- **Language: English everywhere.** UI source strings, code comments, docs, commit messages, PR
  descriptions and test names are written in English. Every user-visible string goes in `qsTr()`;
  translations (pt_BR first) are added through `.ts` files (issue #19), never by writing another
  language in the source. Some existing code still has Portuguese strings/comments: do not copy that
  style — #19 converts them; when you touch such a line anyway, convert it to English.
- **Shortcuts**: `Shortcut { sequence(s): …; onActivated: … }` in `Main.qml`; use standard
  `StandardKey` where one exists (e.g. `StandardKey.Find`). Update the shortcut table in `README.md`.
- **Dependencies**: prefer Qt modules already used. A new Qt module or KDE library must also be added
  to: `CMakeLists.txt`, the Fedora package list in `README.md`, `.github/workflows/build.yml` and
  `.github/workflows/release.yml` (dnf list), and — if it needs a runtime plugin — copied in the
  "Prepare AppDir" step of `release.yml`.
- **No placeholders**: do not leave `TODO` stubs for things the issue asks for.

## Workflow for each issue

1. Branch from `main`: `feature/<issue-number>-<short-slug>` (e.g. `feature/5-find-in-page`).
2. Implement exactly the issue's scope ("Out of scope" sections are binding).
3. Build without new warnings in your files; run the offscreen smoke test; do the issue's
   "Manual test" checklist.
4. Update `README.md` (Features → Implemented, shortcut table) when user-visible behavior changes.
5. Commit messages **in English**, Conventional Commits style (`feat: add find in page`,
   `fix: …`, `chore: …`, `docs: …`), **without `Co-Authored-By` or any other attribution trailer**.
6. Open a PR whose description says `Closes #<issue-number>` and lists how it was tested.
