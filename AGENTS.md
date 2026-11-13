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

## Architecture

Code is organized by **feature folder**, with the same folder names in `src/` (C++), `qml/` (QML)
and `tests/` (from #135). Crowded features are split into **sub-feature folders** such as
`src/bookmarks/import/`, `src/extensions/catalog/` or `qml/browser/tabstrip/` (from #156; the
mapping is in `docs/specs/0156-sub-feature-folders.md`):

| Folder | Holds |
| --- | --- |
| `app` | startup (`main.cpp`, arguments, single instance), windows (`WindowManager`, `BrowserWindow.qml`), main menu, About |
| `core` | shared blocks: `Database`, `Settings`, `Notifier`, file helpers |
| `browser` | `Tab`, `TabModel`, `ProfileManager`, zoom, address resolving and suggestions, sessions, favicons; `WebViewTab.qml`, tab strip, find bar, page menus, new tab and error pages |
| `site` | site info, permissions bar and dialog |
| `bookmarks`, `history`, `downloads`, `passwords`, `adblock`, `extensions`, `settings` | one feature each |
| `common` | small reusable QML components (`InlineBar`, `SiteIcon`, `SiteMenuItem`, `ConfirmDialog`) |

Key pieces:

- `ProfileManager`: the persistent profile "kondor" and the private profiles.
- `Tab` (QML_UNCREATABLE): per-tab state and command signals.
- `TabModel` (role "tab"): add, close and current tab.
- `WebViewTab.qml`: one WebEngineView per tab, bridging WebEngineView and `Tab`.

### The Tab bridge pattern (follow it)

- **State** flows *WebEngineView → Tab*: `WebViewTab.qml` calls `tab.setTitle()`, `tab.setUrl()`,
  `tab.setLoading()`… and `Tab` exposes read-only `Q_PROPERTY`s with `NOTIFY` signals.
- **Commands** flow *UI → Tab → WebEngineView*: the UI calls `tab.reload()`, `tab.zoomIn()`… which
  only `emit reloadRequested()` etc.; `WebViewTab.qml` listens with `Connections { target: root.tab }`
  and acts on the `WebEngineView`.
- New per-tab features must use the same pattern: add a property + setter for state, or an
  `Q_INVOKABLE` command + `…Requested` signal, and handle it in `WebViewTab.qml`.
- A feature with several related per-tab properties gets its own `Tab…` group object (from #144:
  `tab.security`, `tab.permissions`, `tab.passwords`, `tab.extensionItems`), owned by the `Tab`
  and exposed as a `CONSTANT` property. It follows the same state/command rules.
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
| **Settings** | `src/settings.{h,cpp}` | QML singleton `Settings` (`QML_ELEMENT` + `QML_SINGLETON`, same singleton pattern as `ProfileManager`, see Conventions → C++) wrapping `QSettings` (organization `KDE`, application `Kondor` → `~/.config/KDE/Kondor.conf`). One `Q_PROPERTY` (READ/WRITE/NOTIFY) per option, written immediately on set, with its default in `Settings::defaultValue()`. Defined in issue #3. **UI**: `qml/SettingsWindow.qml` is a KDE Configure dialog (#57): new options go into an existing sidebar page/tab or a new data-driven page entry, and are applied with OK/Apply. |
| **Database** | `src/database.{h,cpp}` | `Database::instance()` opens one SQLite file at `QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/kondor.sqlite"` with `QSqlDatabase` (driver `QSQLITE`, connection name `kondor`). Schema versioning with `PRAGMA user_version` and a `migrate()` step per version. Add `Sql` to `find_package(Qt6 …)` and `Qt6::Sql` to `target_link_libraries`. Defined in issue #1. |
| **Notifications** | `src/notifier.{h,cpp}` | QML singleton `Notifier` with `Q_INVOKABLE void notify(const QString &title, const QString &body, const QString &iconName)`, implemented with `QDBusInterface` on `org.freedesktop.Notifications` (`Notify` method, app name `Kondor`, `app_icon` = `kondor`). Add `DBus` to Qt components and `Qt6::DBus`. Defined in issue #4. |
| **Inline page bar** | `qml/InlineBar.qml` | A bar shown between the toolbar and the page (for find, permission prompts, crash notices): `Kirigami.InlineMessage`-like look, uses `Kirigami.Theme` colors. Defined in issue #5. |
| **Favicons** | `src/faviconstore.{h,cpp}`, `qml/SiteIcon.qml` | QML singleton `FaviconStore` keeps one favicon per host in the `favicons` table of **Database** (filled only from normal tabs); `image://kondor-favicon/<page URL>` serves it and `SiteIcon` shows it with a fallback icon. Qt's `image://favicon/` only resolves icon URLs of open views, never page URLs. Defined in bug #45. |
| **SQL helper** | `src/core/sql.{h,cpp}` | Namespace `Sql` over **Database**: `run(statement, values)` → `std::optional<QSqlQuery>` (prepared, bound, executed; `nullopt` on an invalid database or failure), `ids(statement, values)` → `QList<qint64>`, `inTransaction(work)` (commit when `work` returns true, else roll back), `idOrNull(id)`. All C++ SQL goes through it instead of `QSqlQuery` boilerplate. Defined in issue #138. |

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
- **QML singletons** use `static X *instance()` plus `static X *create(QQmlEngine *, QJSEngine *)`
  returning `instance()`, and the constructor is **private**. If the class can be built with its
  default constructor, Qt builds a second, QML-only instance and never calls `create()` (#159).
- **QML**: new components go in their own file under `qml/<feature>/`, with `import Kondor`, and
  must be added to `QML_FILES` in `CMakeLists.txt`.
- **Look & feel**: only QQC2 controls with the `org.kde.desktop` style; colors from
  `Kirigami.Theme`/`palette` (never hardcoded colors); icons via `icon.name` with **Breeze icon
  names** (`bookmark-new`, `edit-find`, `document-save`, `security-high`, …); tooltips with
  `ToolTip.delay: 600` like the existing buttons; follow KDE HIG wording (Title Case for menu items). UI work is designed and reviewed with the
  `kde-ux` skill (`.claude/skills/kde-ux/`).
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

## Code quality

Clean Code, taken to the extreme: this is how the maintainer wants the code written, always.
`scripts/check-code-quality.py` enforces the limits in CI (from #135). Existing offenders are listed
in `scripts/code-quality-baseline.json`, which can only shrink: new and changed code always follows
the limits.

- **Tiny functions.**
  - **Length:** every function, method, QML `function` and signal handler block has at most
    **10 lines** in its body, and 5 is better. Tests may use 20.
  - **One thing:** a function does one thing at one level of abstraction. Extract until a further
    extraction would only restate the code.
- **Few parameters:** at most **3**. Group related values in a struct or object.
- **Shallow:** nesting depth inside a function is at most **2**. Prefer early returns and extracted
  helpers over nested `if`s and loops.
- **Small files:** at most **200 lines** per `.cpp`, `.h`, `.js` or `.qml` file. Split a class by
  responsibility. Split a QML file into components in the same feature folder.
- **Small folders:** at most **10 files** per folder in `src/`, `qml/` and `tests/` (not
  `tests/data/`), and at most two folder levels below them (`src/browser/tabs/features/`). When a
  folder would get an 11th file, split it into sub-feature folders (`import/`, `catalog/`,
  `tabstrip/`; never `utils/` or `helpers/`). Files keep their class names when they move
  (from #156).
- **Names instead of comments:**
  - Write no comments. Rename, or extract a well-named function, until the code explains itself.
  - The only allowed comments are a "why" for a workaround that links its bug report
    (`bugreports.qt.io`, `bugs.kde.org`, `invent.kde.org/…/issues`, `github.com/…/issues`),
    `//:` / `//~` notes for translators, and SPDX license lines.
  - When touching code, delete the comments it already has.
- **Intention-revealing names:**
  - functions are verbs (`saveSession`, `isPrivateOrigin`);
  - booleans read as questions (`isLoading`, `hasSelection`);
  - no abbreviations beyond the Qt ones;
  - one word per concept across the codebase.
- **No side effects hidden behind a name.** A query does not change state; a command does not
  return data it computes as a side job.
- **No duplication:** reuse the shared building blocks and `qml/common/`; extract on the second
  copy.
- **Boy Scout rule:** every PR leaves the functions and files it touches within the limits, or
  closer to them. Do not refactor unrelated code in a feature PR.
- **Tests stay readable:** one behavior per test function, named after it
  (`removesFolderAndChildren`).

Agents on the maintainer's machine also have the `clean-code` skill
([wondelai/skills](https://github.com/wondelai/skills/tree/main/clean-code), in `~/.claude/skills/`
and `~/.config/opencode/skills/`). **Load it every time before writing, changing, reviewing or
refactoring code** (the maintainer's rule). Where it
differs from this section, **this section wins**:
- the limits here are stricter (10 lines, not 20);
- no TODO comments;
- Qt code does not throw exceptions: report failures with return values, `std::optional` or error
  signals.

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
- **Specs written at promotion**: an issue in "Roadmap order" may have no spec yet. When the
  architect promotes it, it writes the spec (and the prototype, if it has UI) first, as for a
  `to-spec` issue, then adds `to-dev`.

### Extensions repository

Kondor extensions (#107) live in a second repository,
[`lukasborges/kondor-extensions`](https://github.com/lukasborges/kondor-extensions), where the
community proposes extensions by pull request and CI publishes the catalog (#108). Issues about it
are still tracked here, on the same roadmap, and their spec has the line
`**Repository:** lukasborges/kondor-extensions`. For those issues:

- the developer clones that repository once next to this one (`git clone
  https://github.com/lukasborges/kondor-extensions ../kondor-extensions`) and works in a worktree of
  it (`git -C ../kondor-extensions worktree add ../kondor-extensions-<N> -b feature/<N>-<slug>
  origin/main`);
- the PR is opened **in that repository**, and its body says `Closes lukasborges/kondor#<N>` (a
  plain `#<N>` would point to the wrong repository);
- the architect reviews it there and merges it with
  `gh pr merge <PR> --repo lukasborges/kondor-extensions --squash --body "Closes lukasborges/kondor#<N>"`;
- that repository has no C++ build: the checks are its own (`build` job of #108). An extension is
  tested by packing it (`python3 tools/pack.py extensions/<id>`) and installing it in a Kondor
  build from `main` with "Install from File…", on an isolated profile.

### Developer delivery checklist

1. Implement exactly the spec ("Out of scope" is binding) and match the prototype.
2. Build without new warnings in your files; run the offscreen smoke test; do the spec's
   "Manual test". Follow "Code quality", and from #135 on run
   `python3 scripts/check-code-quality.py --changed origin/main`.
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
33. #88 Browser extensions spike · 34. #106 Import passwords · 35. #107 Kondor extensions ·
36. #135 Feature folders and Clean Code limits · 37. #136 Split BrowserWindow.qml ·
38. #137 Split SettingsWindow.qml and BookmarksWindow.qml · 39. #138 Shrink C++: core, bookmarks,
history, downloads · 40. #144 Shrink C++: browser · 41. #145 Shrink C++: app, adblock, passwords ·
42. #146 Shrink C++: extensions · 43. #139 Shrink QML functions and files ·
44. #151 Shrink the test files · 45. #156 Sub-feature folders ·
46. #176 Copy saved user name and password ·
47. #183 Extensions panel ·
48. #182 Extension menu item icons and shortcuts ·
49. #108 Extensions repository · 50. #109 Dark Mode extension ·
51. #110 Video Speed Controller extension · 52. #111 User Scripts extension ·
53. #112 Cookie Banner Blocker extension · 54. #113 Skip Sponsors extension ·
55. #114 YouTube Dislike Counts extension · 56. #115 JSON Viewer extension ·
57. #116 User Styles extension · 58. #117 Clean Links extension · 59. #118 Mouse Gestures extension ·
60. #163 Python port 1/12: Toolchain and packaging proof · 61. #164 Python port 2/12: Core ·
62. #165 Python port 3/12: Ad blocking · 63. #166 Python port 4/12: Downloads and history ·
64. #167 Python port 5/12: Bookmarks · 65. #168 Python port 6/12: Password store ·
66. #169 Python port 7/12: Browser profile, address and session · 67. #170 Python port 8/12: Tabs ·
68. #171 Python port 9/12: Extensions: state, catalog and install ·
69. #172 Python port 10/12: Extensions: scripts and bridge ·
70. #173 Python port 11/12: App startup · 71. #174 Python port 12/12: Switch to Python

The Python port (#163-#174) follows its umbrella spec,
[`docs/specs/0162-python-backend.md`](docs/specs/0162-python-backend.md). While it runs, `src/` only changes to fix `bug` issues, and a fix to a
class that is already ported also fixes its Python twin.
