# Replace the C++ backend with Python (PySide6) (#162)

> **Issue:** [#162](https://github.com/lukasborges/kondor/issues/162) · **Priority:** P3 (low) · **State:** umbrella issue; the work is done by the phase issues listed below, one at a time, and the last one closes #162.
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the migration and for every phase issue; only the architect edits it. A phase may get its own spec at promotion (`docs/specs/<NNNN>-<slug>.md`), which details its classes and tests and must follow this file.

## Objective

Rewrite all the C++ in `src/` in **Python with PySide6**, keep the UI in `qml/` as it is, and ship the Python app instead of the C++ one:

- **Same app:** same features, same QML, same look, same keyboard shortcuts.
- **Same data:** an existing profile (database, settings, session, extensions, passwords in KWallet, web storage) keeps working after the switch, with nothing to migrate by hand.
- **No C++ left:** after the last phase, `src/`, the C++ tests and the CMake build are gone.

## Context

- **Today** (`main` at 4480716, non-blank lines):

  | Part | Lines |
  | --- | --- |
  | C++ in `src/` (9 feature folders, 231 files) | 12,594 |
  | C++ tests in `tests/` | 8,719 |
  | QML in `qml/` (with inline JS) | 9,170 |
  | JS resources (`3rdparty/readability/`, `src/passwords/passwords.js`, `src/extensions/*.js`) | 477 |

- **Folder dependencies** (C++ `#include`s between feature folders):

  | Folder | Lines | Uses |
  | --- | --- | --- |
  | `core` | 976 | nothing |
  | `adblock` | 1,076 | core |
  | `downloads` | 633 | core |
  | `bookmarks` | 1,024 | core |
  | `history` | 601 | core, `browser/faviconstore` |
  | `passwords` | 1,207 | core; `passwordbridge` uses `browser/tab*` |
  | `browser` | 2,341 | core, adblock, downloads, history (`profilemanager`), passwords (`tabpasswords`) |
  | `extensions` | 3,682 | core, browser (`tab`, `tabextensionitems`) |
  | `app` | 1,054 | everything; holds `main.cpp` |

- **C++-only libraries in use:**
  - `KF6Wallet` in `src/passwords/`: `openWallet(NetworkWallet(), …, Asynchronous)`, `hasFolder`, `createFolder`, `setFolder`, `entryList`, `readMap`, `writeMap` and `removeEntry`, all in the folder `Kondor`.
  - `KF6Archive` in `src/extensions/packagearchive.cpp`, to unpack `.kondorext` (zip) packages.
- **The QML module:** `CMakeLists.txt` compiles `qml/**` into the module `Kondor` 1.0 with `qt_add_qml_module`. The C++ types are registered into the same module with `QML_ELEMENT` / `QML_SINGLETON`. #159 shows how that registration can silently create a second instance.
- **Packaging:**
  - `release.yml` builds an AppImage with linuxdeploy from a Fedora container.
  - `flatpak.yml` builds the Flatpak on `org.kde.Platform` 6.11 with base `io.qt.qtwebengine.BaseApp`.
- **Available on Fedora 45 (all 6.11.2-compatible):** `python3-pyside6` 6.11.2 (built against the system Qt), `pyside6-tools`, `python3-pytest`, `python3-pytest-qt`, `python3-mypy` and `ruff`. There is **no** Fedora package of Brave's `adblock` engine.

## Design

### 1. Strategy: a parallel port, then one switch

- **Two apps side by side:** the Python app is written in a **new package next to the C++ app**, phase by phase. The C++ app stays the product, keeps building and ships releases until the last phase.
- **Why not a mixed app:** C++ code cannot call Python. Porting bottom-up inside one process would need throw-away bridges in every phase.
- **Bottom-up order:** each phase ports one area together with its tests. Python code only imports Python modules that are already ported, so phases follow the dependency table above, bottom-up.
- **The switch:** the second-to-last phase makes the Python app start and run the whole UI. The last phase switches CI, packaging and docs to Python and deletes the C++.
- **The freeze:** while the port runs, the only `src/` changes allowed are fixes for `bug` issues. When a bug fix touches a C++ class that is already ported, the same PR fixes the Python port too.
- **`qml/` does not change in phases 1-11.** If a phase cannot keep a QML file unchanged, the developer asks (`question`) before touching it.

### 2. Layout

| Today | Python port |
| --- | --- |
| `src/<feature>/<sub>/name.cpp` + `name.h` | `kondor/<feature>/<sub>/name.py`, the same base name, one module per C++ class |
| `tests/<feature>/<sub>/tst_name.cpp` | `pytests/<feature>/<sub>/test_name.py` |
| `tests/data/` | `pytests/data/`, the same files (copied, then the C++ copy goes in phase 12) |
| `main.cpp` | `kondor/__main__.py`, so the app runs as `python3 -m kondor` |

- **Layout source:** the package mirrors `src/` **after #156** (sub-feature folders).
- **Same limits:** the AGENTS.md "Code quality" limits apply to `kondor/` and `pytests/` exactly as to `src/` and `tests/`:
  - 10-line functions (20 in tests);
  - at most 3 parameters, not counting `self` or `cls`;
  - nesting depth at most 2;
  - files of at most 200 lines;
  - at most 10 files per folder, at most 2 levels deep;
  - no comments and no docstrings.

  Small C++ helpers may be merged into the module of the class that uses them when that keeps the file under 200 lines.
- **`pytests/`** is renamed to `tests/` in phase 12, once the C++ tests are deleted.

### 3. Python conventions

- **Python version:** whatever Fedora ships (3.13 or newer). `pyproject.toml` holds the project metadata and the configuration of `ruff`, `mypy` and `pytest`. There is no `setup.py`, and nothing comes from pip.
- **Type checking:** type hints everywhere, and `mypy --strict kondor` must pass. `ruff check` must pass with the rule set from `pyproject.toml`. That set is `E`, `F`, `W`, `I`, `N`, `UP`, `B`, `SIM` and `PL`, without `N802` and `N815`.
- **Naming:**
  - Names QML sees keep their C++ names exactly: properties, slots and `Q_INVOKABLE`s, signals, model roles and enum values, all in camelCase.
  - Overrides of Qt virtual methods keep Qt's names (`rowCount`, `interceptRequest`, …).
  - Everything else is snake_case.
  - Do not use `from __feature__ import snake_case, true_property`.
- **Qt objects:**
  - Use `Property(type, getter, setter, notify=signal)` and `Signal`.
  - Use `Slot(…, result=…)` for every `Q_INVOKABLE`.
  - Emit a change signal only when the value really changes, as in C++.
- **Singletons**, to avoid the #159 trap: each singleton class has `instance()`, which returns one module-level object. Its QML registration is `qmlRegisterSingletonInstance(Class, "Kondor", 1, 0, "Name", Class.instance())`.
  - Do not use the `@QmlSingleton` decorator.
  - `QML_UNCREATABLE` types (for example `Tab`) use `qmlRegisterUncreatableType`.
  - Creatable types use `qmlRegisterType`.
- **Registration per feature:** each feature folder has `kondor/<feature>/qmltypes.py` with `register_types()`, which registers that feature's QML types.
  - The app calls every `register_types()` before loading QML.
  - A test calls only the ones it needs.
  - `pytests/core/test_singletons.py` checks that `engine.singletonInstance("Kondor", name)` is `Class.instance()` for every registered singleton (the Python twin of #159's check).
- **Privacy:** the AGENTS.md privacy rule is unchanged. Every place where C++ checks `isPrivate()` has the same check in Python, and the ported tests keep those cases.

### 4. Same QML API, same data

- **QML API parity:** every class that QML sees exposes at least the C++ class's:
  - properties, with the same names, types and writability;
  - invokables and slots, with the same names and argument counts;
  - signals;
  - model roles.

  `scripts/check-qml-api.py` (added in phase 1) checks the first three automatically:
  - From C++, it reads `Q_PROPERTY`, `Q_INVOKABLE`, `public slots:` and `signals:` in `src/**/*.h`.
  - From Python, it reads every class passed to a `register_types()`, through `QMetaObject`.
  - It fails when a name is missing in Python.
  - The ported tests and the review cover the roles.
- **On-disk compatibility** with a profile written by the C++ app:
  - **SQLite** `kondor.sqlite`: same path and same schema. The `PRAGMA user_version` migrations keep the C++ numbering, and Python runs only the steps above the file's `user_version`.
  - **Settings** `~/.config/KDE/Kondor.conf`: same keys, types and defaults (`QSettings`, organization `KDE`, application `Kondor`).
  - **Session, closed tabs, certificate overrides, zoom, site permissions:** same file names and formats as the C++ code writes today.
  - **Extensions:** same folder layout under `AppDataLocation/extensions/`, same state file and same staging names.
  - **Ad blocking:** same filter-list cache files and allowlist.
  - **Web engine:** same persistent profile storage name `kondor`, so cookies, logins and web storage carry over.
  - **Passwords:** see item 6.
- **Same command line:** the same arguments as `commandline.cpp`. Single instance uses the same socket name (`runtimeDirectory()/kondor-<profileHash>.socket`) and message format, so a C++ instance and a Python instance of the same profile never both run.

### 5. Ad blocking

- **The engine:** port `src/adblock/` 1:1 (filter rules, options, patterns, engine, allowlist), with the same matching results. Brave's `adblock` engine is not used: it has no Fedora package and would change behavior.
- **Performance:**
  - In Qt 6, `QWebEngineUrlRequestInterceptor.interceptRequest` runs on the UI thread, so a slow match blocks the UI.
  - Phase 3 adds `scripts/bench-adblock.py`. It loads the filter lists Kondor enables by default (snapshots in `pytests/data/adblock/`) and times `match` over the request URLs in `pytests/data/adblock/requests.txt`.
  - **Budget** on the developer's machine: median at most **50 µs** and p99 at most **500 µs** per request. The PR body reports the numbers.
  - If the budget cannot be met with the same data structures, ask (`question`) before changing the algorithm.

### 6. Passwords: KWallet over D-Bus

There are no Python bindings for KF6Wallet. Talk to `kwalletd6` directly with `QtDBus`:

- **Interface:** service `org.kde.kwalletd6`, path `/modules/kwalletd6`, interface `org.kde.KWallet` (see `/usr/share/dbus-1/interfaces/kf6_org.kde.KWallet.xml`).
- **Opening:**
  1. Get the wallet name with `networkWallet()`.
  2. Open it with `openAsync(wallet, 0, "Kondor", false)`, then wait for `walletAsyncOpened(tId, handle)`.
  3. Follow `walletClosed(handle)` to forget the handle, as `PasswordStore::forgetClosedWallet` does.
- **Folder `Kondor`:** use `hasFolder`, `createFolder`, `entryList`, `readMap`, `writeMap` and `removeEntry`, with `appid` `"Kondor"`.
- **Map bytes** must be byte-compatible with `KWallet::Wallet::readMap/writeMap`: a `QDataStream`-serialized `QMap<QString, QString>`. That is a big-endian `quint32` count, then each key and value as a `QString`, written and read with `QDataStream`. The reader accepts any pair order.
- **Tests:**
  - Unit tests cover the serializer against fixed bytes, and the store against a fake D-Bus interface object.
  - Real KWallet is only in the manual test.

### 7. Extension packages

- **Unpacking:** `.kondorext` packages are unpacked with Python's `zipfile`, replacing KArchive.
- **Path safety:** keep every check `packagearchive.cpp` makes: entries with absolute paths or `..` are rejected, and the same limits apply.

### 8. Loading the QML

- **Staging:** `scripts/build.py` (phase 1) stages everything the Python app needs into `build/python/`:
  - `qml/Kondor/`: a copy of `qml/**` that keeps the tree, plus a generated `qmldir` (`module Kondor`, one `<Basename> 1.0 <relative path>` line per `.qml` file);
  - the JS resources and assets the C++ build puts in its resources;
  - the compiled translations (`lrelease` on `i18n/*.ts`).
- **Who uses it:**
  - The app adds `build/python/qml` (or the installed equivalent) to the engine's import path.
  - Tests use the same staged tree through a session fixture.
- **Translations:**
  - QML keeps `qsTr()`.
  - Python strings use `self.tr()` or `QCoreApplication.translate("<C++ class name>", …)`, so the `.ts` contexts stay the same.
  - From phase 12, `pyside6-lupdate` scans `kondor/` and `qml/`.

### 9. Phases

One issue per phase, promoted one at a time in this order (AGENTS.md "Roadmap order"):

| # | Issue | Scope | Tests to port |
| --- | --- | --- | --- |
| 1 | #163 Toolchain and packaging proof | see item 10 | — |
| 2 | #164 Core | `src/core/` | `tests/core/` |
| 3 | #165 Ad blocking | `src/adblock/` + `scripts/bench-adblock.py` | `tests/adblock/` |
| 4 | #166 Downloads and history | `src/downloads/`, `src/history/`, `browser/faviconstore` | `tests/downloads/`, `tests/history/` |
| 5 | #167 Bookmarks | `src/bookmarks/` | `tests/bookmarks/` |
| 6 | #168 Password store | `src/passwords/` except `passwordbridge` | `tests/passwords/` except the bridge |
| 7 | #169 Browser profile, address and session | `src/browser/` except `tab*`, `tabmodel*` and `faviconstore` | `tests/browser/` for those classes, `tests/site/` |
| 8 | #170 Tabs | `src/browser/` `tab*` and `tabmodel*`, `passwords/passwordbridge` | the rest of `tests/browser/`, the bridge tests |
| 9 | #171 Extensions: state, catalog and install | `src/extensions/` state, catalog, package, install, manifest | their tests in `tests/extensions/` |
| 10 | #172 Extensions: scripts and bridge | the rest of `src/extensions/` and its JS resources | the rest of `tests/extensions/` |
| 11 | #173 App startup: the Python app runs | `src/app/`, `kondor/__main__.py` | `tests/app/`, `tests/settings/` |
| 12 | #174 Switch to Python | item 11; closes #162 | — |

**Rules for every phase from 2 to 11:**

- **Port, don't redesign:** same classes, same behavior and same edge cases as the C++. A class may be split to meet the size limits.
- **Every C++ test case becomes a pytest test** with the same intent (`tst_x.cpp::someCase` becomes `test_x.py::test_some_case`).
- **UI tests:** C++ UI tests that load QML become `pytest-qt` tests that load the staged QML. If a UI test needs a type that is not ported yet, it moves to the phase that ports that type.
- **The phase is done when:**
  - the `build` CI job is green, with ruff, mypy, pytest, `check-qml-api.py` and `check-code-quality.py` all passing;
  - the C++ build and tests are untouched and still green.

### 10. Phase 1: toolchain and packaging proof

This is the go/no-go gate: no code is ported until the Python app is proven to build, run and package.

- **Toolchain:**
  - `pyproject.toml` (see item 3).
  - An empty `kondor/__init__.py` and `pytests/conftest.py` with the staged-QML session fixture.
  - `scripts/build.py` (item 8) and `scripts/check-qml-api.py` (item 4).
- **Quality checker:** `scripts/check-code-quality.py` also checks `.py` files with `ast`, using the item 2 limits (function body lines, parameters, nesting depth, file lines, no comments or docstrings). The folder rules are extended to `kondor/` and `pytests/`.
- **CI:**
  - The `build` job in `build.yml` also installs `python3-pyside6 pyside6-tools python3-pytest python3-pytest-qt python3-mypy ruff`.
  - After the C++ test step, it runs `ruff check`, `mypy --strict kondor`, `python3 scripts/build.py`, `QT_QPA_PLATFORM=offscreen pytest pytests` and `python3 scripts/check-qml-api.py`.
  - The new steps get timeouts like the existing ones.
- **The proof app** (`packaging/python-proof/`, deleted in phase 12) is a minimal `proof.py` plus `Proof.qml`. It shows, in one run:
  1. `QtWebEngineQuick.initialize()` before the app object, and a `WebEngineView` that loads a `data:` URL;
  2. the `org.kde.desktop` style on a QQC2 `Button`, and a `Kirigami.Theme` color read from QML;
  3. a QML file loaded from a staged `qmldir` module `Kondor`, which reads a Python singleton registered into `Kondor` with `qmlRegisterSingletonInstance`, and gets the **same** object (`is` check printed);
  4. a `QWebEngineUrlRequestInterceptor` subclass in Python that sees the `data:` request;
  5. a `QtDBus` call to `org.freedesktop.DBus.ListNames`.

  It prints `PROOF OK` and exits 0 when all five hold.
- **Packaging proof:** two workflow jobs on pull requests that touch `packaging/python-proof/`, plus `workflow_dispatch`:
  - **AppImage:** bundle Fedora's `python3` and `python3-pyside6` with the Qt libraries and plugins `release.yml` already copies, then run the AppImage with `QT_QPA_PLATFORM=offscreen` and expect `PROOF OK`.
  - **Flatpak:** on the existing runtime and base (`org.kde.Platform` 6.11, `io.qt.qtwebengine.BaseApp` 6.11), build `shiboken6` and `PySide6` 6.11 from source as manifest modules. Only the modules Kondor needs: Core, Gui, Qml, Quick, QuickControls2, Network, Sql, DBus, WebEngineCore, WebEngineQuick and WebChannel. Then run `flatpak run … --offscreen` and expect `PROOF OK`.
  - **Constraint:** PySide6 must use the same Qt as the `org.kde.desktop` style, so pip wheels, which bundle their own Qt, are not allowed in either package.
- **Exit:** if either package cannot pass, the developer adds `question` with the failing log. The maintainer then decides whether the port stops (close the phase issues as `wontfix`) or changes course.

### 11. Phase 12: switch to Python

- **Packaging and CI:**
  - `release.yml` builds the AppImage of the real app the way the proof did.
  - `packaging/flatpak/io.github.lukasborges.Kondor.yml` uses the proof's PySide6 modules and installs the app.
  - `build.yml` drops CMake and the C++ steps.
  - The `kondor` command runs `python3 -m kondor`, through a small launcher script installed to `bin/`.
- **Spell-check dictionaries:** `scripts/build.py` also converts them with `qwebengine_convert_dict`, as CMake does today.
- **Delete:** `src/`, `tests/` (C++), `CMakeLists.txt`, `cmake/`, `scripts/check-qml-api.py`, `packaging/python-proof/` and the C++ parts of `check-code-quality.py` (and their baseline entries). Then rename `pytests/` to `tests/`.
- **Docs:**
  - AGENTS.md: Python instead of C++ in "What Kondor is", "Build and run", "Architecture", "Shared building blocks", "Conventions", "Dependencies" and the delivery checklist (`ruff`, `mypy`, `pytest`).
  - README.md: build instructions and Fedora packages.
  - `docs/agents/developer.md` and `docs/agents/architect.md`.
  - `scripts/dev-loop.sh` and `scripts/architect-loop.sh` prompts (build and test commands).
  - The AppImage timer script, if it builds with CMake.
- **Profile migration check:** the manual test runs the last C++ AppImage and then the Python AppImage on the same isolated profile.

## Acceptance criteria

- [ ] Phases 1-12 are merged in order, each with its own PR, and each meets its row in item 9 and the "Rules for every phase".
- [ ] Phase 1: the proof prints `PROOF OK` in both the AppImage and the Flatpak CI jobs, and the CI runs ruff, mypy, pytest and the API check.
- [ ] Phase 3: the adblock benchmark is within budget (item 5), and the numbers are in the PR.
- [ ] Phase 11: `python3 -m kondor` with the staged build shows the browser window, and `QT_QPA_PLATFORM=offscreen timeout 15 python3 -m kondor` prints no QML errors (`ReferenceError`, `TypeError`, `Cannot assign…`, `is not a type`).
- [ ] Phase 12: no `.cpp`, `.h` or `CMakeLists.txt` is left in the repository. The release AppImage and the Flatpak start, and the manual test passes.
- [ ] No QML file changed in phases 1-11 without a recorded decision.
- [ ] No private-tab data is written to disk by the Python app (ported privacy tests pass).

## Manual test

Run after phase 11, and again after phase 12 with the AppImage and the Flatpak. Use an isolated profile: `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` and `XDG_STATE_HOME` under a temp folder.

1. **Make data with the C++ app:** start the last C++ build on the profile.
   - Visit three sites and bookmark one.
   - Save a password, which needs KWallet.
   - Install an extension from the catalog.
   - Change two settings.
   - Leave three tabs open and quit.
2. **Open it with the Python app:** start the Python app on the same profile and check that it shows:
   - the same three tabs (session restore);
   - the history and the bookmark;
   - the saved password, which fills on the login page;
   - the extension, enabled;
   - the two settings;
   - a site still logged in (cookies).
3. **Exercise the Python app:**
   - Open a private tab, browse, close it, and check that nothing new is in history or the session.
   - Block an ad on a test page and allow it per site.
   - Download a file and see the notification.
   - Find in page.
   - Open Settings → Extensions → Get New Extensions and install one.
   - Open a second window, and start a second instance with a URL: it opens in the running one.
4. **Look and feel:** the window looks the same as the C++ build, with the Breeze style, the colors from the system scheme, and the same icons and wording.

## Out of scope

- **New features or behavior changes:** the port must reproduce today's app.
- **QML changes**, except recorded decisions; no UI redesign.
- **Switching UI toolkit** (Widgets, Kirigami `ApplicationWindow`), or moving logic from Python into QML/JS.
- **pip, wheels and PyPI dependencies;** Brave's `adblock` engine.
- **Porting `prototypes/`** (already Python-rendered QML) and the extensions repository (#108-#118).
- **Translating Python strings** beyond keeping the existing contexts.

## Dependencies

- #156 (sub-feature folders): the Python layout mirrors it.
- #159 (singleton instances): the Python registration rule (item 3) follows from it.
- The extensions roadmap (#108-#118) lives in another repository and does not block, nor is blocked by, the port.

## Prototype

None: no UI changes.

## Decisions

| Question | Decision |
| --- | --- |
| Which language replaces C++? | Python with PySide6: the only binding that covers QML, WebEngine (including the request interceptor), QtDBus, image providers and models, built against the system Qt on Fedora. Rust (cxx-qt) has no WebEngine bindings; QML/JS alone cannot write files, use D-Bus or intercept requests. |
| Logic in Python or in QML/JS? | Python. QML/JS stays the UI only, as today with C++. |
| Port in place (mixed C++/Python app) or in parallel? | In parallel, then one switch (item 1): C++ cannot call Python, so a mixed app needs throw-away bridges. |
| Ad blocking engine? | Port Kondor's engine 1:1 with a performance budget (item 5). Brave's `adblock` has no Fedora package and would change behavior. |
| KWallet without KF6Wallet? | `org.kde.KWallet` over QtDBus, byte-compatible maps (item 6), so passwords saved by the C++ app are read by the Python app. |
| Singleton registration? | `qmlRegisterSingletonInstance` with `instance()`, never `@QmlSingleton` (#159). |
| pip / wheels? | Not allowed: PySide6 must share the Qt of the KDE style plugin. Fedora packages for development and the AppImage; PySide6 built from source in the Flatpak. |
