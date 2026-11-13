# Python port 1/12: Toolchain and packaging proof (#163)

> **Issue:** [#163](https://github.com/lukasborges/kondor/issues/163) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) and the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) first. This file details phase 1 (umbrella items 2, 3, 4, 8 and 10) and must follow the umbrella. Only the architect edits it.

## Objective

Prove that a PySide6 Kondor can be built, checked, tested and packaged before any class is ported:

- **Toolchain:** the Python project, the QML staging script and the QML API check.
- **Quality:** `scripts/check-code-quality.py` also checks Python.
- **CI:** the `build` job runs ruff, mypy, the staging script, pytest and the API check.
- **Packaging proof:** a minimal PySide6 app runs from an AppImage and from a Flatpak and prints `PROOF OK`.

This phase is the go/no-go gate of #162. No C++ class is ported here.

## Context

- **No Python app yet:** there is no `kondor/` package, no `pytests/` and no `pyproject.toml`.
- **Quality checker** (`scripts/codequality/`, tests in `scripts/tests/`, run in CI by `python3 -m unittest discover -s scripts/tests`):
  - `files.py`: `ROOTS = ("src", "qml", "tests")`, `SUFFIXES = (".cpp", ".h", ".js", ".qml")`, `tests/data/` skipped.
  - `folders.py`: at most 10 files per folder and 2 levels below a root; `tests/data` skipped.
  - `rules.py`: `check_source()` strips comments (`strip.py`), then finds functions with `cpp.py` or `qml.py` and returns `Violation`s. Tests get a 20-line limit (`path.startswith("tests/")`).
  - `strip.forbidden_comment_lines()` holds the allowed comments (SPDX, `//:` / `//~`, workaround links).
- **Resources** compiled into the C++ binary (`CMakeLists.txt`, `qt_add_resources` and `qt_add_translations`):

  | Resource path | Source |
  | --- | --- |
  | `:/packaging/kondor.png`, `:/packaging/kondor.svg` | `packaging/` |
  | `:/reader/Readability.js`, `:/reader/Readability-readerable.js` | `3rdparty/readability/` |
  | `:/scripts/passwords.js`, `:/scripts/usernamefield.js` | `src/passwords/bridge/` |
  | `:/scripts/channel.js`, `:/scripts/extensionruntime.js` | `src/extensions/bridge/` |
  | `:/scripts/usergm.js` | `src/extensions/scripts/` |
  | `:/LICENSE` | `LICENSE` |
  | `:/i18n/kondor_<lang>.qm` | `i18n/kondor_<lang>.ts` (lrelease) |

  `:/qtwebchannel/qwebchannel.js` comes from Qt WebChannel itself and needs nothing.
- **QML module:** 146 `.qml` files under `qml/`. No file uses `pragma Singleton`, and no two files share a base name. `qml/common/InlineBar.qml` imports only QtQuick, Layouts, Kirigami and `Kondor`. It is the first real Kondor file that can load without any C++ type.
- **Fedora 45 packages** (checked with `dnf repoquery`): `python3-pyside6` 6.11.2 (has QtWebEngineQuick, QtWebEngineCore, QtDBus, QtSql, QtQuickControls2 and QtWebChannel), `pyside6-tools` 6.11.2 (`pyside6-rcc`, `pyside6-lrelease`, `pyside6-lupdate`), `python3-pytest` 9.1, `python3-pytest-qt` 4.5, `python3-mypy` 1.18 and `ruff` 0.17.
- **CI today:**
  - `build.yml` (`fedora:latest` container): dnf install, then the code quality step, CMake configure, build, `ctest` and the translations check.
  - `release.yml` builds the AppImage with linuxdeploy. Its "Prepare AppDir" step lists the Qt and KDE plugins Kondor needs.
  - `flatpak.yml` builds `packaging/flatpak/io.github.lukasborges.Kondor.yml` (`org.kde.Platform` 6.11, base `io.qt.qtwebengine.BaseApp` 6.11) in `ghcr.io/flathub-infra/flatpak-github-actions:kde-6.11`.

## Design / behavior

### 1. Python project

- **`pyproject.toml`** at the repository root:
  - `[project]`: `name = "kondor"`, `version = "0.2.0"` (the CMake `project()` version), `requires-python = ">=3.13"`, no `dependencies` (everything comes from Fedora).
  - `[tool.ruff]`: `target-version = "py313"` and `line-length = 100`. `include` limits ruff to the new Python code: `kondor/**/*.py`, `pytests/**/*.py`, `packaging/python-proof/**/*.py`, `scripts/build.py`, `scripts/staging/**/*.py`, `scripts/check-qml-api.py` and `scripts/qmlapi/**/*.py`. `prototypes/` and the existing `scripts/` code are not linted.
  - `[tool.ruff.lint]`: `select = ["E", "F", "W", "I", "N", "UP", "B", "SIM", "PL"]`, `ignore = ["N802", "N815"]`.
  - `[tool.mypy]`: `strict = true`, `python_version = "3.13"`.
  - `[tool.pytest.ini_options]`: `testpaths = ["pytests"]`, `qt_api = "pyside6"`.
- **`kondor/__init__.py`:** empty.
- **`kondor/core/__init__.py`:** empty.
- **`kondor/core/qmlregistration.py`:** the registration contract that every later phase uses, and that `check-qml-api.py` reads:
  - `class QmlKind(Enum)`: `SINGLETON`, `UNCREATABLE`, `CREATABLE`.
  - `class QmlType(NamedTuple)`: `type_class: type[QObject]`, `name: str` (the QML name), `kind: QmlKind`.
  - `register(types: Sequence[QmlType]) -> None`. For each entry, it calls (URI `"Kondor"`, version 1.0):
    - `SINGLETON`: `qmlRegisterSingletonInstance(type_class, "Kondor", 1, 0, name, type_class.instance())`;
    - `UNCREATABLE`: `qmlRegisterUncreatableType(type_class, "Kondor", 1, 0, name, <reason>)`;
    - `CREATABLE`: `qmlRegisterType(type_class, "Kondor", 1, 0, name)`.
  - Later phases write `kondor/<feature>/qmltypes.py` with a module constant `QML_TYPES: tuple[QmlType, ...]` and `def register_types() -> None: register(QML_TYPES)`. Phase 1 adds no `qmltypes.py`.

### 2. Staging: `scripts/build.py`

`python3 scripts/build.py [--out DIR]` (default `build/python`) clears `DIR`, then writes:

1. **`DIR/qml/Kondor/`**: a copy of every `qml/**/*.qml` and `qml/**/*.js` file, keeping the tree (`qml/common/InlineBar.qml` becomes `DIR/qml/Kondor/common/InlineBar.qml`), plus a generated **`qmldir`**:
   ```
   module Kondor
   <Basename> 1.0 <path relative to DIR/qml/Kondor>
   ```
   There is one line per `.qml` file, sorted by path. If two `.qml` files share a base name, the script fails and names both.
2. **`DIR/i18n/kondor_<lang>.qm`**: `pyside6-lrelease` on each `i18n/kondor_<lang>.ts`.
3. **`DIR/kondor.qrc`** and **`DIR/kondor.rcc`**: a Qt resource collection with the **same resource paths** as the C++ binary (table in "Context"), including `/i18n/kondor_<lang>.qm` from step 2. It is compiled with `pyside6-rcc --binary`. Later phases register it with `QResource.registerResource()`, so the ported code keeps the C++ `:/…` paths unchanged.

Rules:

- **Resource table:** the table lives in one module of `scripts/staging/` and mirrors `CMakeLists.txt`. A unit test parses the `qt_add_resources` blocks of `CMakeLists.txt` (`PREFIX`, `BASE`, `FILES`) and fails when the two differ, so they cannot drift while both builds exist.
- **Missing tool:** if `pyside6-rcc` or `pyside6-lrelease` is missing, the script exits 1 and names the Fedora package (`pyside6-tools`).
- **Layout:** `scripts/build.py` is a thin entry point (as `check-code-quality.py` is). The logic is in `scripts/staging/` (qmldir, resources, translations), with unit tests in `scripts/tests/`. That code follows the AGENTS.md limits and passes ruff.

### 3. QML API check: `scripts/check-qml-api.py`

`python3 scripts/check-qml-api.py` compares each Python class registered for QML with its C++ twin:

- **C++ side:** every class with `Q_OBJECT` in `src/**/*.h`, by class name:
  - **Properties:** each `Q_PROPERTY(<type> <name> …)`, even across lines. It is writable when it has `WRITE`, or `MEMBER` without `CONSTANT`.
  - **Callables:** `Q_INVOKABLE` methods and the methods under `public slots:` / `public Q_SLOTS:`. Each name gets the set of argument counts it accepts: a default argument adds the shorter counts, and overloads add theirs.
  - **Signals:** the methods under `signals:` / `Q_SIGNALS:`, with their argument counts.
- **Python side:** it imports every `kondor/**/qmltypes.py` and reads `QML_TYPES`. Then it reads each `type_class.staticMetaObject` through `QMetaObject`: the properties and methods declared after `QObject`'s, so `objectName` and `destroyed` are skipped. Python slots and C++ invokables both count as callables.
- **Pairing:** a Python class pairs with the C++ class of the same class name (`QMetaObject.className()`). A Python class without a C++ twin is an error.
- **Failure (exit 1)** lists, per class:
  - a missing property, signal or callable name;
  - a C++ argument count that Python does not accept;
  - a writability difference;
  - a property type difference. Types are compared after removing `const`, `&`, `*` and spaces, and `QVariant` on either side matches any type.
- **Success (exit 0)** prints `<n> classes checked, <m> C++ classes not ported yet`. Unported C++ classes are not errors. In phase 1, `n` is 0.
- **Layout:** the parsing and the comparison are in `scripts/qmlapi/`, apart from the collection, so the comparison can be tested without Qt. Unit tests in `scripts/tests/` cover:
  - the header parser: multi-line `Q_PROPERTY`, `MEMBER`/`CONSTANT`, default arguments, overloads, `Q_SIGNALS`;
  - each failure kind, on hand-built descriptions.

  Ruff applies to that code.

### 4. Python in the quality checker

Extend `scripts/codequality/` without changing its C++/QML results:

- **Roots:** `kondor` and `pytests` join `ROOTS`, and `.py` joins `SUFFIXES`.
  - `pytests/data/` is skipped like `tests/data/`, for files and folders.
  - **Folders:** `__pycache__` folders are never in scope. An **empty** `__init__.py` does not count toward the 10-file limit; a non-empty one does.
- **New module `codequality/python.py`**, using `ast` and `tokenize` (no regex parsing):
  - **Functions:** every `def` and `async def`, methods and nested functions included, becomes a `Function`:
    - `key`: the qualified name (`Class.method`);
    - `line`: the line of `def`;
    - `body_lines`: lines from the first body statement through `end_lineno`, without blank lines. A docstring counts too.
    - `parameters`: positional-only, positional and keyword-only parameters, plus `*args` and `**kwargs`. A first parameter named `self` or `cls` is not counted.
    - `nesting`: the deepest stack of `if`, `for`, `while`, `with`, `try` and `match` in the function's own body. An `elif` stays at its `if`'s depth, and a nested `def` is measured on its own.
  - **Comment lines:** each `#` comment token is a comment line, except:
    - `#!` on line 1;
    - SPDX lines;
    - a workaround link accepted by `strip.forbidden_comment_lines` today;
    - `# type: ignore[<code>]` and `# noqa: <code>`, always with an explicit code (a bare `# type: ignore` or `# noqa` counts).
  - **Docstrings:** every module, class or function docstring counts as one comment line (rule `comments`).
- **Limits:**
  - `rules.length_limit()` gives 20 lines to `tests/` and `pytests/`;
  - the other limits are the same numbers as for C++ (10 lines, 3 parameters, depth 2, 200 file lines, no comments).
- **Tests** in `scripts/tests/`:
  - a long function, `self` not counted, `elif` depth, nested `def`, a docstring, each allowed pragma and a bare `# noqa`;
  - the `__pycache__` and empty-`__init__.py` folder rules.
- **Baseline:** `scripts/code-quality-baseline.json` gets no Python entries.

### 5. Test setup: `pytests/`

- **`pytests/conftest.py`:**
  - **`staged_build`** (session): the `Path` of `build/python`. If `build/python/qml/Kondor/qmldir` is missing, it calls `pytest.fail("run python3 scripts/build.py first")`.
  - **`qml_engine`** (function, needs pytest-qt's `qapp`): a `QQmlEngine` with `staged_build / "qml"` added to its import path and `kondor.rcc` registered. The `org.kde.desktop` style is set once per session, before the first engine.
- **`pytests/core/test_qmlregistration.py`** (test classes defined in the test file):
  - a `SINGLETON` entry: `engine.singletonInstance("Kondor", name)` is `Class.instance()`, the #159 check;
  - a `CREATABLE` entry: a QML snippet creates it;
  - an `UNCREATABLE` entry: creating it from QML fails with the reason.
- **`pytests/test_staged_module.py`:**
  - loading `import Kondor; InlineBar {}` from the staged module creates the object with no QML warnings;
  - `QFile(":/scripts/passwords.js").exists()` and `QFile(":/i18n/kondor_pt_BR.qm").exists()` are true.

The real `pytests/core/test_singletons.py` (umbrella item 3) comes in phase 2, with the first singleton.

### 6. CI: `build.yml`

- **Install step:** add `python3-pyside6 pyside6-tools python3-pytest python3-pytest-qt python3-mypy ruff` to the existing dnf list. Keep the retry loop.
- **New steps after "Test",** before "Check translations", each with `timeout-minutes`:

  | Step | Command | Timeout |
  | --- | --- | --- |
  | Ruff | `ruff check` | 5 |
  | Mypy | `mypy --strict kondor` | 10 |
  | Stage Python build | `python3 scripts/build.py` | 10 |
  | Pytest | `QT_QPA_PLATFORM=offscreen pytest pytests` | 20 |
  | QML API | `python3 scripts/check-qml-api.py` | 5 |

- **Checks already in CI:** the code quality step needs no change, because it now also covers `kondor/` and `pytests/`, and `scripts/tests` already runs the new unit tests.

### 7. The proof app: `packaging/python-proof/`

Files (deleted in phase 12):
- `proof.py`, plus modules next to it if the limits need them;
- `qml/Kondor/qmldir` and `qml/Kondor/Proof.qml`;
- `AppRun`;
- `io.github.lukasborges.KondorProof.yml`.

The Python follows the AGENTS.md limits and passes ruff and `mypy --strict`.

`python3 packaging/python-proof/proof.py` checks five things in one run. It prints one line per check, `PASS <check>` or `FAIL <check>: <reason>`:

1. **`webengine`:** `QtWebEngineQuick.initialize()` runs before the `QGuiApplication` is created. A `WebEngineView` in `Proof.qml` loads a `data:text/html,…` URL and reports `LoadSucceededStatus`.
2. **`style`:** `QQuickStyle.setStyle("org.kde.desktop")` is called before the engine. `Proof.qml` has a QQC2 `Button` with `implicitWidth > 0` and reads `Kirigami.Theme.backgroundColor`, which must have a non-zero alpha. The engine logs no warnings while it loads `Proof.qml`. A missing style module is a warning, so it fails this check.
3. **`module`:** the engine's import path gets `packaging/python-proof/qml`, a qmldir module `Kondor` with `Proof 1.0 Proof.qml`. `proof.py` registers a `ProofState` singleton into `Kondor` 1.0 with `qmlRegisterSingletonInstance`. `Proof.qml` (`import Kondor`) calls `ProofState.report(…)`, and `proof.py` prints whether `engine.singletonInstance("Kondor", "ProofState") is ProofState.instance()`.
4. **`interceptor`:** a `QWebEngineUrlRequestInterceptor` subclass written in Python is set on the view's profile. The `data:` page has `<img src="http://proof.invalid/pixel.png">`. The interceptor records that URL and blocks it, so the check needs no network.
5. **`dbus`:** `QDBusConnection.sessionBus()` calls `org.freedesktop.DBus.ListNames`, and the reply contains `org.freedesktop.DBus`.

When all five pass, it prints `PROOF OK` and exits 0. It exits 1 on any `FAIL`, or after **30 seconds** without a result (printing `FAIL timeout`).

### 8. Packaging proof: `.github/workflows/python-proof.yml`

Triggers: `pull_request` with `paths: ['packaging/python-proof/**', '.github/workflows/python-proof.yml']`, and `workflow_dispatch`. Three jobs:

- **`appimage-build`** (`fedora:latest` container, timeout 60):
  - Install `python3 python3-pyside6` and the Qt/KDE runtime packages `release.yml` installs (`kf6-kirigami kf6-qqc2-desktop-style plasma-integration plasma-breeze-qt6 qt6-qtsvg` and the rest), plus `file wget fuse-libs`.
  - Build `AppDir` with:
    - Fedora's `python3` binary and its standard library;
    - `site-packages/PySide6` and `site-packages/shiboken6`, only the PySide6 modules of the Flatpak list below;
    - `proof.py` and `qml/`;
    - the plugins and QML modules `release.yml` copies in "Prepare AppDir".
  - Run linuxdeploy with `--deploy-deps-only` for the PySide6 extension modules, the Qt plugins and the python3 binary, with `--exclude-library "libp11-kit.so*"` as in `release.yml`.
  - **`AppRun`** sets `PYTHONHOME`, `PYTHONPATH`, `QT_PLUGIN_PATH`, `QML_IMPORT_PATH` and `QTWEBENGINEPROCESS_PATH` inside the AppDir, then runs `python3 proof.py`.
  - Upload `Kondor-Proof-x86_64.AppImage` as an artifact.
- **`appimage-run`** (needs `appimage-build`; a fresh `fedora:latest` container):
  - Install only `dbus-daemon`, plus the host libraries that linuxdeploy's excludelist leaves out (for example `mesa-libGL mesa-libEGL fontconfig libxkbcommon nss`; the developer lists the exact set).
  - Assert `! rpm -q python3-pyside6 qt6-qtbase`, so the run proves the bundle is self-contained.
  - Run `APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen dbus-run-session -- ./Kondor-Proof-x86_64.AppImage | tee proof.log`, then `grep -qx "PROOF OK" proof.log`.
- **`flatpak`** (`ghcr.io/flathub-infra/flatpak-github-actions:kde-6.11`, `--privileged`, timeout 180):
  - **Manifest** `packaging/python-proof/io.github.lukasborges.KondorProof.yml`: app id `io.github.lukasborges.KondorProof` on `org.kde.Platform`/`org.kde.Sdk` 6.11 with base `io.qt.qtwebengine.BaseApp` 6.11 (as the Kondor manifest).
  - **PySide6 from source:** modules `shiboken6` and `pyside6` from the official `pyside-setup-everywhere-src-6.11.2` tarball on `download.qt.io`, pinned by `sha256`. They are built with CMake against the runtime's Qt, with `MODULES` limited to `Core;Gui;Qml;Quick;QuickControls2;Network;Sql;DBus;WebEngineCore;WebEngineQuick;WebChannel`.
  - **libclang:** shiboken needs it to build. It comes from the freedesktop LLVM SDK extension that matches the runtime's freedesktop base, listed in `sdk-extensions` and used only at build time.
  - **The proof module** installs `proof.py` and `qml/` under `/app/share/kondor-proof/`, plus a `/app/bin/kondor-proof` launcher (`exec python3 /app/share/kondor-proof/proof.py "$@"`).
  - **`finish-args`:** `--share=ipc`, `--socket=wayland`, `--socket=fallback-x11`, `--device=dri` and `--env=QTWEBENGINEPROCESS_PATH=/app/bin/QtWebEngineProcess`.
  - **Build and run:**
    - Build with `flatpak/flatpak-github-actions/flatpak-builder@v6` (`build-bundle: false`, `cache-key` derived from the manifest's hash so reruns reuse the PySide6 build).
    - Install the result into a user installation, then run `dbus-run-session -- flatpak run --env=QT_QPA_PLATFORM=offscreen io.github.lukasborges.KondorProof | tee proof.log` and `grep -qx "PROOF OK" proof.log`.
    - If Chromium's sandbox cannot start inside the CI container, the run command, never the manifest, may add `--env=QTWEBENGINE_CHROMIUM_FLAGS=--no-sandbox`. The PR then says why.

**pip is not allowed** anywhere: no `pip install`, no wheels, no PyPI sources (umbrella "Decisions").

### 9. Exit gate

If the AppImage or the Flatpak job cannot reach `PROOF OK`, the developer does not work around the umbrella's constraints. They add `question` to #163 with the failing log, and the maintainer decides (umbrella item 10, "Exit").

## Acceptance criteria

- [ ] `pyproject.toml`, `kondor/__init__.py`, `kondor/core/__init__.py`, `kondor/core/qmlregistration.py`, `pytests/conftest.py` and the two pytest files of item 5 exist as described.
- [ ] `ruff check` and `mypy --strict kondor` pass.
- [ ] `python3 scripts/build.py` writes the qmldir module, the `.qm` files and `kondor.rcc` with the C++ resource paths. Its unit test fails if the resource table differs from `CMakeLists.txt`.
- [ ] `QT_QPA_PLATFORM=offscreen pytest pytests` passes, including `InlineBar` loading from the staged module with no warnings and the #159 singleton check.
- [ ] `python3 scripts/check-qml-api.py` exits 0 with `0 classes checked, <m> C++ classes not ported yet`, and its unit tests cover every failure kind of item 3.
- [ ] `scripts/check-code-quality.py` checks `.py` files in `kondor/` and `pytests/` with the item 4 rules. Its C++/QML results on `main` are unchanged (the baseline is untouched), and `python3 -m unittest discover -s scripts/tests` passes with the new tests.
- [ ] The `build` job runs the five new steps with timeouts and is green. CMake, `ctest` and the translations check still pass.
- [ ] `python3 packaging/python-proof/proof.py` prints five `PASS` lines and `PROOF OK` locally on Fedora 45 (offscreen, under `dbus-run-session`).
- [ ] The `appimage-run` job prints `PROOF OK` in a container without `python3-pyside6` or `qt6-qtbase`.
- [ ] The `flatpak` job builds PySide6 6.11.2 from source on `org.kde.Platform` 6.11 and prints `PROOF OK`.
- [ ] No file in `src/`, `qml/` or `tests/` changes. No pip and no wheels.
- [ ] The PR body links the green `python-proof` run and pastes the `PROOF OK` lines of both packages.

## Manual test

On Fedora 45 with the packages of "Context" installed, in a clean checkout of the PR branch:

1. `python3 scripts/build.py && ls build/python/qml/Kondor/qmldir build/python/kondor.rcc build/python/i18n/`.
2. `head -3 build/python/qml/Kondor/qmldir`: `module Kondor`, then `<Basename> 1.0 <path>` lines.
3. `ruff check && mypy --strict kondor && QT_QPA_PLATFORM=offscreen pytest pytests && python3 scripts/check-qml-api.py`: all pass, and the last prints `0 classes checked, …`.
4. `python3 scripts/check-code-quality.py`: no output. Add a temporary `kondor/core/bad.py` with an 11-line function and a `# note` comment: the checker reports `function-length` and `comments`. Delete the file.
5. `QT_QPA_PLATFORM=offscreen dbus-run-session -- python3 packaging/python-proof/proof.py`: five `PASS` lines and `PROOF OK`, exit code 0.
6. Without `QT_QPA_PLATFORM`, in a Plasma session, the proof window shows a Breeze-styled button (the proof needs no visual check beyond this).
7. Open the `python-proof` workflow run of the PR: both `appimage-run` and `flatpak` show `PROOF OK`.

## Out of scope

- Porting any C++ class, test or JS resource logic (phases 2-11). The only class in `kondor/` is the registration helper of item 1.
- `pytests/core/test_singletons.py` for real singletons (phase 2), `scripts/bench-adblock.py` (phase 3).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, `release.yml`, `flatpak.yml` or the Kondor Flatpak manifest.
- Spell-check dictionaries in `scripts/build.py` (phase 12) and `pyside6-lupdate` (phase 12).
- Shipping the proof: the proof AppImage and Flatpak are CI artifacts only, not releases or repository updates.
- Linting or typing the existing `scripts/` code and `prototypes/`.

## Dependencies

#162 (umbrella spec), #156 (layout), #159 (singleton registration rule). Nothing in `src/` is needed.

## Prototype

None: no UI. The proof window is a test fixture, not a Kondor UI.

## Decisions

| Question | Decision |
| --- | --- |
| How does the Python app get the `:/…` resources the C++ binary embeds? | `scripts/build.py` writes a `.qrc` with the same paths and compiles it with `pyside6-rcc --binary`. The app registers it with `QResource.registerResource()`. Ported code keeps the C++ paths (`:/scripts/passwords.js`, `:/i18n`), so phases 2-11 change no resource path. Rejected: loose files on disk (every resource path would change in the port). |
| How does `check-qml-api.py` find the Python classes? | Each feature's `qmltypes.py` exposes `QML_TYPES` (a tuple of `QmlType`), and `register_types()` only passes it to `kondor.core.qmlregistration.register()`. The check reads the same tuple, so it covers exactly what QML sees. Rejected: having `register_types()` return the classes (a command that also returns data). |
| What does the API check do with C++ classes not ported yet? | It reports their count and passes. Python classes pair by class name, and every Python class must have a C++ twin. |
| Do empty `__init__.py` files count toward the 10-files-per-folder limit? | No: they are package markers with no code. A folder with ten C++ classes would otherwise have to split only because of Python packaging. A non-empty `__init__.py` counts. |
| Are `# type: ignore[…]` and `# noqa: …` comments? | They are tool pragmas, allowed only with an explicit code. The reviewer challenges each one. Bare forms count as comments. |
| The proof's `module` check: real `qml/` or a mini module? | A mini qmldir module `Kondor` in `packaging/python-proof/qml/`. Real Kondor QML needs the C++ types, which are not ported yet. Loading a real file from the staged module is covered by `pytests/test_staged_module.py` (`InlineBar`). |
| The proof's `interceptor` check: does the `data:` URL itself reach the interceptor? | Not relied on: the `data:` page requests `http://proof.invalid/pixel.png`, which the Python interceptor records and blocks. This proves a Python interceptor sees page requests, with no network, which is what ad blocking needs. |
| How does the AppImage job prove the bundle is self-contained? | It runs in a second, fresh `fedora:latest` container without `python3-pyside6` or `qt6-qtbase`. The Ubuntu host cannot be used: an AppImage built on Fedora 45 needs a newer glibc than Ubuntu 24.04 has. |
