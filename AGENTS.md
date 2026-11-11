# AGENTS.md — guide for AI coding agents (and humans)

Read this file before working on any issue of the **Kondor Roadmap**
(<https://github.com/users/lukasborges/projects/1>). Every issue assumes the rules below.

Two agents work on the roadmap: the **architect** (`docs/agents/architect.md` — specs,
prototypes, answers, reviews, merges) and the **developer** (`docs/agents/developer.md` —
implementation; Claude Sonnet via Claude Code by default, or DeepSeek via opencode — see
`scripts/dev-loop.sh`). They talk
only through GitHub (labels, issue/PR comments, PR reviews); see "Agent workflow" at the end.

## What Kondor Browser is

Kondor Browser is a small web browser written in **C++17 + Qt 6 (Qt Quick / QML + Qt WebEngine)** that must look and
behave like a native **KDE Plasma** app (Breeze style, Breeze icons, system color scheme).

- Minimum Qt: **6.8** (`find_package(Qt6 6.8 …)`; site permissions, #7, need the 6.8 `WebEnginePermission` API), developed and tested on **Qt 6.11.2 / Fedora**.
- QML style: `org.kde.desktop` (qqc2-desktop-style), set in `src/main.cpp`.
- Kirigami is used **only for theming** (`Kirigami.Theme.*`) and, where useful, `Kirigami.FormLayout`
  / `Kirigami.InlineMessage` / `Kirigami.Icon`. The main window is a QQC2 `ApplicationWindow`, not a
  `Kirigami.ApplicationWindow`. Do not convert it.

## Build and run

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --parallel 4
./build/kondor
```

Always give `--parallel` a job count (4 on the maintainer's machine). With the Makefile generator
a bare `--parallel` means `make -j` with **no limit**. Every test target recompiles the sources, so
a full build then starts dozens of compilers at once and runs the machine out of memory. The agent
loops enforce it: their systemd units put `scripts/bin` first in `PATH`, where a `cmake` wrapper
caps every build at 4 jobs, and they run under a memory cap (`MemoryMax=16G`).

Smoke test without a display (useful in CI or for agents):

```bash
export KONDOR_TEST_HOME="$(mktemp -d)"
XDG_CONFIG_HOME="$KONDOR_TEST_HOME/config" XDG_DATA_HOME="$KONDOR_TEST_HOME/data" \
XDG_CACHE_HOME="$KONDOR_TEST_HOME/cache" QT_QPA_PLATFORM=offscreen timeout 15 ./build/kondor
```

**Never run the app you are testing on the maintainer's real profile.** Every agent run (smoke
test, manual test, review) sets `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` to a
temporary directory as above, so settings (`~/.config/KDE/Kondor.conf`), history, downloads and
the web profile of the person using Kondor are never touched. Point test downloads to that
temporary directory too.

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
| **Settings** | `src/settings.{h,cpp}` | QML singleton `Settings` (`QML_ELEMENT` + `QML_SINGLETON`, same `instance()`/`create()` pattern as `ProfileManager`) wrapping `QSettings` (organization `KDE`, application `Kondor` → `~/.config/KDE/Kondor.conf`). One `Q_PROPERTY` (READ/WRITE/NOTIFY) per option, written immediately on set, with its default in `Settings::defaultValue()`. Defined in issue #3. **UI**: `qml/SettingsWindow.qml` is a KDE Configure dialog (#57): new options go into an existing sidebar page/tab or a new data-driven page entry, and are applied with OK/Apply. |
| **Database** | `src/database.{h,cpp}` | `Database::instance()` opens one SQLite file at `QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/kondor.sqlite"` with `QSqlDatabase` (driver `QSQLITE`, connection name `kondor`). Schema versioning with `PRAGMA user_version` and a `migrate()` step per version. Add `Sql` to `find_package(Qt6 …)` and `Qt6::Sql` to `target_link_libraries`. Defined in issue #1. |
| **Notifications** | `src/notifier.{h,cpp}` | QML singleton `Notifier` with `Q_INVOKABLE void notify(const QString &title, const QString &body, const QString &iconName)`, implemented with `QDBusInterface` on `org.freedesktop.Notifications` (`Notify` method, app name `Kondor`, `app_icon` = `kondor`). Add `DBus` to Qt components and `Qt6::DBus`. Defined in issue #4. |
| **Inline page bar** | `qml/InlineBar.qml` | A bar shown between the toolbar and the page (for find, permission prompts, crash notices): `Kirigami.InlineMessage`-like look, uses `Kirigami.Theme` colors. Defined in issue #5. |
| **Favicons** | `src/faviconstore.{h,cpp}`, `qml/SiteIcon.qml` | QML singleton `FaviconStore` keeps one favicon per host in the `favicons` table of **Database** (filled only from normal tabs); `image://kondor-favicon/<page URL>` serves it and `SiteIcon` shows it with a fallback icon. Qt's `image://favicon/` only resolves icon URLs of open views, never page URLs. Defined in bug #45. |

## UI prototypes (visual target)

`prototypes/` holds a static QML mockup for every issue with UI, rendered with the real Breeze
style into `prototypes/screenshots/*.png` (see `prototypes/README.md` for the issue → file table).
When an issue has a prototype (linked from its spec), **the implementation must match it**: same controls, Kirigami
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
  translations live only in the `i18n/kondor_<lang>.ts` files (issues #19 and #34), never as another
  language in the source.
- **Translations stay complete**: a PR that adds or changes a user-visible string runs
  `cmake --build build --target update_translations` and translates the new messages in **every**
  `i18n/*.ts` file, with no `unfinished` messages and every plural form filled. Use KDE's usual
  terminology for each language. CI fails otherwise (from #34 on).
- **Shortcuts**: `Shortcut { sequence(s): …; onActivated: … }` in `Main.qml`; use standard
  `StandardKey` where one exists (e.g. `StandardKey.Find`). Update the shortcut table in `README.md`.
- **Dependencies**: prefer Qt modules already used. A new Qt module or KDE library must also be added
  to: `CMakeLists.txt`, the Fedora package list in `README.md`, `.github/workflows/build.yml` and
  `.github/workflows/release.yml` (dnf list), and — if it needs a runtime plugin — copied in the
  "Prepare AppDir" step of `release.yml`.
- **No placeholders**: do not leave `TODO` stubs for things the issue asks for.

## Agent workflow

- **Specs** live in `docs/specs/<NNNN>-<slug>.md` (one per issue, source of truth, edited only by
  the architect); a `bug` issue is specified by its own body instead (see "Defects"). The issue
  body is a summary with a link; decisions go in the spec's "Decisions" table.
- **State** lives in one label per issue: `to-spec` (architect writes the spec) → `to-dev`
  (developer implements or addresses review) → `in-review` (architect reviews the PR) → closed
  when the architect merges the PR (`Closes #N`). `question` is added on top of the state when the
  developer needs an answer; the architect removes it after answering. `approved` is added on top
  of `in-review` when the architect approves a PR; the architect squash-merges it once its build
  check passes (both
  agents use the same GitHub account, so approvals are comment reviews starting with
  "Verdict: APPROVE").
- **Board**: every issue is on the "Kondor Roadmap" project board; `scripts/board.sh <N> [status]`
  adds it and sets Todo / In Progress (closing sets Done).
- **Queue**: `scripts/update-queue.sh` writes `docs/QUEUE.md` (git-ignored) from that state; each
  agent regenerates it and takes the topmost row for its role. The "Update queue" workflow shows
  the same table in its run summary.
- **One issue at a time**: only one issue is in `to-dev`/`in-review`; the architect promotes the
  next one following the roadmap order below.
- **Conversation** happens only on GitHub: questions and answers as issue/PR comments, reviews as
  PR reviews with inline comments. Never use files in the repository to talk.
- **Working copies**: each agent uses its own git worktree; the developer works on
  `feature/<issue-number>-<short-slug>` branches cut from current `origin/main`, the architect on
  `main`.

### Developer delivery checklist

1. Implement exactly the spec ("Out of scope" is binding) and match the prototype.
2. Build without new warnings in your files; run the offscreen smoke test; do the spec's
   "Manual test".
3. Update `README.md` when user-visible behavior changes: add or adjust one user-facing bullet in the matching "Features" group: a bold name plus at most about ten words on what the user can do (no implementation details, settings paths or edge cases), and the shortcut table.
4. Commit messages **in English**, Conventional Commits style (`feat: add find in page`,
   `fix: …`, `chore: …`, `docs: …`), **without `Co-Authored-By` or any other attribution trailer**.
5. Open a PR using `.github/pull_request_template.md` (body says `Closes #<issue-number>`), then
   switch the issue label to `in-review`.

### Defects

Defects found in delivered features go into the backlog as their own issues, labeled `bug` (one
defect per issue). A bug issue has no file in `docs/specs/`: **its body is the spec**, with the
sections *Steps to reproduce*, *Expected*, *Actual*, *Acceptance criteria* and, when known,
*Cause*. Decisions about a bug are recorded as issue comments. The developer works on a
`fix/<issue-number>-<short-slug>` branch and commits with `fix: …`. Bugs follow the same labels
and one-at-a-time rule as features, but **open bugs are promoted before the next roadmap issue**
(by `priority:` label — high, medium, low, none — and oldest first among equals), since they
break features that are already delivered.

### Roadmap order

Promoted to `to-dev` one at a time by the architect, after any open `bug` issue (dependencies
first: shared blocks, then privacy fixes, then features):

1. #1 Browsing history (creates **Database**) · 2. #3 Settings page (creates **Settings**) ·
3. #5 Find in page (creates **InlineBar**) · 4. #4 Download manager (creates **Notifier**) ·
5. #12 Tab management (fixes the private-tab link bug) · 6. #19 Translations (English source +
pt_BR) · 7. #36 Rename to Kondor Browser · 8. #34 Translations for the main KDE languages ·
9. #26 Automated tests ·
10. #10 Default browser · 11. #6 Session restore · 12. #2 Bookmarks · 13. #43 New Tab page ·
14. #44 Address bar: visit or search · 15. #47 Default bookmarks · 16. #7 Site permissions ·
17. #9 Security indicator · 18. #8 Fullscreen · 19. #18 Crashed page · 20. #13 Page context menu ·
21. #11 Address bar suggestions · 22. #14 Multiple windows · 23. #15 Single instance ·
24. #16 Developer tools · 25. #17 Print and save as PDF · 26. #24 Per-site zoom ·
27. #23 Spell checking · 28. #22 Reader mode · 29. #20 Ad and tracker blocking ·
30. #21 Passwords · 31. #25 Flatpak · 32. #98 Self-hosted Flatpak repository ·
33. #88 Browser extensions spike · 34. #106 Import passwords
