# Python port 12/12: Switch to Python (#174)

> **Issue:** [#174](https://github.com/lukasborges/kondor/issues/174) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 1, 2, 8, 10 and 11, "Acceptance criteria" and "Manual test"), the toolchain spec [`0163-python-toolchain-proof.md`](0163-python-toolchain-proof.md) (the AppImage and Flatpak proof this phase turns into the real packages) and the app startup spec [`0173-python-app-startup.md`](0173-python-app-startup.md) (`stagedbuild.py`, `prepare_environment()`, `set_up_language_and_style()`). This file details phase 12 and must follow the umbrella. Only the architect edits it.

## Objective

Make the Python app **the** Kondor Browser and delete the C++, closing #162:

- **Ship Python:** the release AppImage, the Flatpak and the maintainer's local AppImage run `python3 -m kondor` from an installed staged build, through a `kondor` launcher. They start offscreen with no QML errors, and they open a profile written by the last C++ build with nothing lost.
- **CI is Python only:** the `build` job runs the code-quality checks, `ruff`, `mypy`, the staging, the tests and the translation check. CMake, `ctest` and the C++/Python API comparison are gone.
- **No C++ left:** `src/`, the C++ `tests/`, `CMakeLists.txt`, `cmake/`, the proof app and every C++-only script are deleted, and `pytests/` becomes `tests/`.
- **Translations come from Python and QML:** `pyside6-lupdate` scans `kondor/` and `qml/`. Every message the `.ts` files hold today is kept with its translation.
- **Docs say Python:** README, the agent role files, the loop prompts and the PR template describe the Python build, checks and layout.

## Context

- **After phase 11** (#173), `python3 scripts/build.py && python3 -m kondor` runs the whole browser from the checkout. Every C++ QML type and every C++ test has a Python twin. This phase does not wait for QA (#217): the maintainer chose to finish the port first, and QA tests the Python app after the switch.
- **Where the app finds its files** (`kondor/app/startup/stagedbuild.py`, phase 11): `staged_build_directory()` is `<checkout>/build/python`. `load_staged_resources()` registers `kondor.rcc` and needs `qml/Kondor/qmldir`. `PROJECT_VERSION = "0.2.0"` is checked by a test against `CMakeLists.txt` and `pyproject.toml`. `prepare_environment()` looks for spell-check dictionaries in `<staged>/../share/kondor/qtwebengine_dictionaries`, then `<staged>/qtwebengine_dictionaries`.
- **Staging** (`scripts/build.py`, `scripts/staging/`):
  - `stage()` writes `build/python/qml/Kondor/` with its `qmldir`, plus `i18n/*.qm` (from `pyside6-lrelease`) and `kondor.rcc` (from `pyside6-rcc --binary`).
  - `resources.py` `RESOURCE_GROUPS` lists the resource files. Five JS files still live in `src/`: `src/passwords/bridge/passwords.js`, `src/passwords/bridge/usernamefield.js`, `src/extensions/bridge/channel.js`, `src/extensions/bridge/extensionruntime.js` and `src/extensions/scripts/usergm.js`.
  - `cmakeresources.py` and `scripts/tests/test_staging.py::test_matches_the_cmake_resource_blocks` check that list against the `qt_add_resources` blocks of `CMakeLists.txt`.
- **What CMake still does that Python does not:**
  - `qt_add_translations(… LUPDATE_OPTIONS -no-obsolete)` and the `update_translations` target.
  - Spell-check dictionaries: `qwebengine_convert_dict` (Fedora: `/usr/lib64/qt6/libexec/qwebengine_convert_dict`, package `qt6-qtwebengine`) converts `/usr/share/hunspell/<lang>.dic` for `KONDOR_SPELLCHECK_LANGS` = `en_US;pt_BR` into `<lang with "-">.bdic`. Each missing tool or dictionary gives a warning and is skipped, and the result is installed to `share/kondor/qtwebengine_dictionaries`.
  - `install()`: the binary to `bin/`, `packaging/kondor.desktop` to `share/applications`, the metainfo to `share/metainfo`, `kondor-extension.xml` to `share/mime/packages`, and `kondor.png` / `kondor.svg` to `share/icons/hicolor/{256x256,scalable}/apps`.
- **Translations today:** 542 messages per `.ts` file. Most come from `qml/`, and about 43 from `src/` (`appidentity`, `bookmarkmanager`, `defaultbookmarks`, `downloadmanager`, `historymodel` and many `extensions/` files). The Python twins use `self.tr()` in classes with the C++ class names, or `QCoreApplication.translate("<C++ class>", …)` (umbrella item 8), so the contexts match. There are two translator notes, both `//:` in C++: `appidentity.cpp` and `permissiondescription.cpp`.
- **CI** (`.github/workflows/`):
  - `build.yml` has three jobs. `changes` runs `scripts/needs-cpp-checks.sh`. `build` holds the C++ steps, the code-quality step and the translation check. `python` holds ruff, mypy, staging, pytest and the QML API check. The architect merges once the `build` check is green.
  - `release.yml` builds the C++ AppImage with linuxdeploy, then the Flatpak, the Pages site and the bundle upload.
  - `flatpak.yml` (`workflow_dispatch`) builds `packaging/flatpak/io.github.lukasborges.Kondor.yml`, which uses base `io.qt.qtwebengine.BaseApp` and `buildsystem: cmake-ninja`.
  - `python-proof.yml` builds and runs the proof AppImage on a bare Fedora host, and the proof Flatpak on base `io.qt.PySide.BaseApp` 6.11 with `PYTHONPATH=/app/lib/python3.13/site-packages`. Both print `PROOF OK` (#163).
- **Maintainer tools:**
  - `scripts/local-appimage.sh` builds an AppImage of `origin/main` with CMake every time a PR is merged, and installs it.
  - `scripts/bin/cmake` is the job-capping, ccache and build-lock wrapper the loops put first in `PATH` (the systemd units in `dev-loop.sh` and `architect-loop.sh`).
- **Code quality** (`scripts/codequality/`):
  - `files.py` sets `ROOTS = ("src", "qml", "tests", "kondor", "pytests")` and `SUFFIXES` with `.cpp` and `.h`.
  - `folders.py` ignores `tests/data` and `pytests/data`, and `rules.py` sets `TEST_ROOTS = ("tests/", "pytests/")`.
  - `cpp.py` (`find_cpp_functions`) finds brace-delimited functions and is used for both `.cpp`/`.h` and `.js`.
  - `strip.ALLOWED_COMMENT` allows `//:` and `//~`. The Python rules reuse it.
  - The baseline `scripts/code-quality-baseline.json` is empty.
- **`AGENTS.md` is not in git:** the maintainer keeps it in `~/.config/kondor-agents/`, so a PR cannot change it (see "Decisions").

## Design / behavior

Nothing here changes what the app does. Every step either moves a job from CMake to Python or deletes what only the C++ needed.

### 1. Installed layout and launcher

One layout for every package (AppImage `AppDir/usr`, Flatpak `/app`, a plain `/usr` install):

```
<prefix>/bin/kondor                       the launcher (packaging/kondor, 0755)
<prefix>/share/kondor/kondor/             the Python package (*.py only, byte-compiled)
<prefix>/share/kondor/qml/Kondor/         the staged QML module
<prefix>/share/kondor/kondor.rcc
<prefix>/share/kondor/qtwebengine_dictionaries/*.bdic   when converted
<prefix>/share/applications/kondor.desktop
<prefix>/share/metainfo/io.github.lukasborges.Kondor.metainfo.xml
<prefix>/share/mime/packages/kondor-extension.xml
<prefix>/share/icons/hicolor/256x256/apps/kondor.png
<prefix>/share/icons/hicolor/scalable/apps/kondor.svg
```

- **`packaging/kondor`** is a POSIX shell launcher:
  1. It resolves its own directory with `readlink -f`.
  2. It prepends `<that>/../share/kondor` to `PYTHONPATH`.
  3. It runs `exec python3 -P -m kondor "$@"`. With `-P`, a `kondor/` folder in the current directory is never imported instead of the installed package.
  4. The `.desktop` file keeps `Exec=kondor %U`.
- **`staged_build_directory()`** (`kondor/app/startup/stagedbuild.py`) chooses between two places:
  - the package's parent folder (`Path(__file__).resolve().parents[3]`), when it holds `kondor.rcc` (installed);
  - else `<that folder>/build/python`, as today (checkout).

  Nothing else in `kondor/` changes for the layout. The dictionaries are then found through phase 11's second candidate, `<staged>/qtwebengine_dictionaries`, in both layouts.
- **`PROJECT_VERSION`** stays in `stagedbuild.py`. Its test now compares it with `pyproject.toml` only.

### 2. Staging and install (`scripts/build.py`, `scripts/staging/`)

- **Dictionaries** (`staging/dictionaries.py`):
  - `stage()` converts each language of `--spellcheck-languages` (default `en_US,pt_BR`) with `qwebengine_convert_dict <dic> <out>/qtwebengine_dictionaries/<lang with "-">.bdic`, run with `QT_QPA_PLATFORM=offscreen`.
  - It looks for the tool on `PATH`, then in `/usr/lib64/qt6/libexec`, `/usr/lib/qt6/libexec` and `/app/libexec`, and for the dictionary in `/usr/share/hunspell` and `/app/share/hunspell`.
  - A missing tool or dictionary prints the CMake warnings (`qwebengine_convert_dict not found: spell checking dictionaries are not built`, `Hunspell dictionary <path> not found: no <lang> spell checking`) and the build goes on.
- **Tools:** `find_tool` tries `pyside6-rcc` / `pyside6-lrelease` first, then Qt's own `rcc` / `lrelease` on `PATH` and in the same libexec folders. The `--binary` and `-qm` outputs are the same, and the Flatpak SDK may have only Qt's tools. The error still names the Fedora package `pyside6-tools`.
- **`--install <prefix>`** (`staging/install.py`) stages as usual into `--out`, then writes the layout of item 1 under `<prefix>`:
  - the staged folder without `kondor.qrc` and `i18n/`, since the `.qm` files are inside `kondor.rcc`;
  - every `kondor/**/*.py` (no `__pycache__`), byte-compiled with `compileall -q`;
  - the launcher with mode 0755;
  - the five `packaging/` files of the C++ `install()`.

  It does not run tools that need a display, apart from the offscreen dictionary conversion.
- **JS resources move out of `src/`** with `git mv`, so that their history follows:

  | From | To |
  | --- | --- |
  | `src/passwords/bridge/{passwords,usernamefield}.js` | `kondor/passwords/bridge/` |
  | `src/extensions/bridge/{channel,extensionruntime}.js` | `kondor/extensions/bridge/` |
  | `src/extensions/scripts/usergm.js` | `kondor/extensions/scripts/` |

  `RESOURCE_GROUPS` points to the new places, and the resource paths (`:/scripts/*.js`) stay the same. If a folder then holds more than 10 files, split it by responsibility as AGENTS.md says, and keep the resource paths. `--install` does not copy the `.js` files next to the package, since they are already in `kondor.rcc`.
- **Delete** `staging/cmakeresources.py` and its test. A new test in `scripts/tests/test_staging.py` checks that every `RESOURCE_GROUPS` file exists.

### 3. Translations

- **`scripts/update-translations.py`** replaces the `update_translations` target. It runs `pyside6-lupdate -no-obsolete -locations relative <files> -ts i18n/kondor_*.ts` on a sorted list of every `kondor/**/*.py`, `qml/**/*.qml` and `qml/**/*.js`, with the same `.ts` files `TS_FILES` lists. A new language is added by creating `i18n/kondor_<lang>.ts`; the script takes every `i18n/kondor_*.ts`.
- **No message is lost:**
  - After the first run, every `.ts` file still has the same set of `(context, source, comment)` messages with the same `<translation>` text. Only `<location>` lines change.
  - A message that disappears means pyside6-lupdate does not recognize its Python call. Fix the call in `kondor/` (use `self.tr()` in the class with the C++ name, or `QCoreApplication.translate("<context>", "<text>", None, n)`) and keep the context and text. Do not edit the `.ts` by hand.
  - The PR body has the before/after message counts per file.
- **Translator notes:** the two C++ `//:` notes become `#:` comments on the line above the Python call. The quality checker allows `#:` and `#~` in Python, as it allows `//:` and `//~`. If pyside6-lupdate does not carry `#:` into the `.ts` `<extracomment>`, ask (`question`).
- **CI** runs the script and `git diff --exit-code -- i18n/`, then the existing completeness check (moved unchanged from the inline YAML into `scripts/check-translations.py`).

### 4. Packaging

- **AppImage:**
  - **Shared AppDir script:** `packaging/appimage/prepare-appdir.sh <AppDir>` is used by `release.yml` and `scripts/local-appimage.sh`, so they cannot drift apart. It builds the AppDir the way `python-proof.yml` did:
    - the bundled interpreter and standard library;
    - `shiboken6` and the PySide6 modules listed in `packaging/appimage/pyside-modules.txt`;
    - `QtWebEngineProcess`, its resources and translations;
    - the QML modules `QtQuick`, `QtQml`, `QtWebEngine`, `QtWebChannel` and `QtCore`, and `org/kde/{kirigami,desktop,qqc2desktopstyle}`;
    - the plugins the C++ release copied: platforms `xcb`, `wayland` and `offscreen`, `wayland-*`, `sqldrivers/libqsqlite.so`, `KDEPlasmaPlatformTheme6`, `breeze6`, the Kirigami desktop platform and `libqsvgicon`;
    - then `python3 scripts/build.py --install AppDir/usr`, `packaging/appimage/AppRun`, the desktop file and the icon.

    After it, both callers run linuxdeploy with the proof's `--deploy-deps-only` set and the `libp11-kit` exclusion.
  - **Module list:** `pyside-modules.txt` has one module per line. A `scripts/tests` test checks that it holds every `PySide6.Qt*` module imported anywhere in `kondor/`, so a new import cannot break only the AppImage.
  - **`packaging/appimage/AppRun`:** the proof's environment (`PYTHONHOME`, `PYTHONPATH` for the standard library and `site-packages`, `LD_LIBRARY_PATH`, `QT_PLUGIN_PATH`, `QML_IMPORT_PATH`, `QTWEBENGINEPROCESS_PATH`, `QTWEBENGINE_RESOURCES_PATH`, `QTWEBENGINE_LOCALES_PATH`), with `$HERE/usr/bin` first in `PATH`. It then runs `exec "$HERE/usr/bin/kondor" "$@"`.
- **`release.yml`:**
  - It installs Python and the runtime packages instead of the C++ toolchain: `git python3 python3-pyside6 pyside6-tools file wget gh fuse-libs qt6-qtbase qt6-qtdeclarative qt6-qtwebengine qt6-qtwebchannel qt6-qtsvg qt6-qtwayland kf6-kirigami kf6-qqc2-desktop-style plasma-integration plasma-breeze-qt6 hunspell-en-US hunspell-pt-BR`.
  - It runs `prepare-appdir.sh` and keeps the two `test -f …/qtwebengine_dictionaries/*.bdic` checks.
  - It uploads the AppImage as an artifact.
  - A new `appimage-run` job, copied from the proof's, runs the AppImage on a bare `fedora:latest` with only host libraries. It uses `QT_QPA_PLATFORM=offscreen`, `QTWEBENGINE_DISABLE_SANDBOX=1` and an isolated XDG home, under `dbus-run-session -- timeout 15`. Exit code 124 counts as success. It fails on any line matching `ReferenceError|TypeError|Cannot assign|is not a type` or `cannot find the staged build`.
  - "Publish release" needs `appimage-run`.
  - The workflow gets `workflow_dispatch`. On a dispatch it builds and runs the AppImage only: the publish, Flatpak, Pages and upload jobs have `if: github.event_name == 'push'`.
- **Flatpak** (`packaging/flatpak/io.github.lukasborges.Kondor.yml`):
  - Base `io.qt.PySide.BaseApp` 6.11, plus `--env=PYTHONPATH=/app/lib/python3.13/site-packages` as in the proof. Keep every other `finish-args` line.
  - The module `kondor` is `buildsystem: simple`, with `build-commands: [python3 scripts/build.py --out build/python --install /app]`, on the same `dir` source.
  - `command: kondor`, `rename-desktop-file`, `rename-icon` and `copy-icon` stay.
  - If the SDK lacks a tool `build.py` needs, ask (`question`) with the log before adding a module.
- **`scripts/local-appimage.sh`:**
  - `build_appimage` calls `prepare-appdir.sh` and the linuxdeploy steps instead of `cmake`.
  - `check_deps` lists the release's Fedora packages instead of `qt6-qttools-devel` and `qt6-qtwebengine-devel`.
  - The offscreen smoke test, the install and the notifications are unchanged.

### 5. CI: `build.yml`

One job, still named **`build`** (the merge rule waits for it), on `fedora:latest`:

1. Install `git python3 python3-pyside6 pyside6-tools python3-pytest python3-pytest-qt python3-mypy ruff kf6-kirigami kf6-qqc2-desktop-style qt6-qtdeclarative dbus-daemon procps-ng` with the existing retry loop.
2. Checkout.
3. `python3 -m unittest discover -s scripts/tests` and `python3 scripts/check-code-quality.py`.
4. `ruff check`, `mypy --strict kondor`, `python3 scripts/build.py`, `scripts/run-pytests.sh`.
5. The translation check of item 3.

Keep the per-step timeouts of today's `python` job. Delete the `changes` and `python` jobs, the ccache steps and the binary upload.

### 6. Deletions and the rename

- **Delete:**
  - code and build: `src/` (after the JS moves), `tests/` (C++, with `tests/data/`), `CMakeLists.txt`, `cmake/`;
  - scripts and their tests: `scripts/check-qml-api.py`, `scripts/qmlapi/`, `scripts/tests/test_qmlapi.py`, `scripts/needs-cpp-checks.sh`, `scripts/bin/`;
  - the proof: `packaging/python-proof/` and `.github/workflows/python-proof.yml`.
- **Rename** `pytests/` to `tests/` with `git mv`:
  - change every `from pytests.` / `import pytests` to `tests`;
  - change `testpaths` in `pyproject.toml`;
  - change the default path in `scripts/run-pytests.sh`.
- **`pyproject.toml`:** ruff's `include` drops the proof, `check-qml-api.py` and `qmlapi`, and adds `tests/**/*.py`, `scripts/update-translations.py` and `scripts/check-translations.py`.
- **Quality checker:**
  - `ROOTS = ("qml", "tests", "kondor")`, `SUFFIXES = (".js", ".qml", ".py")`, `TEST_ROOTS = ("tests/",)` and `IGNORED_FOLDERS = ("tests/data",)`.
  - `cpp.py` becomes `braces.py` (`find_brace_functions`), since `.js` still uses it. Its C++-only cases (for example constructors and initializer lists) go, if nothing in `.js` needs them, with their tests.
  - The Python comment rule allows `^#[:~]`.
  - `scripts/tests` keeps passing, adjusted to the new roots.
- **Loops:** the systemd units in `dev-loop.sh` and `architect-loop.sh` drop `$control/scripts/bin:` from `PATH`. Their prompts lose the CMake sentence ("Build with cmake --build … --parallel 4 …") and keep the `run-pytests.sh` one.
- **`.gitignore`:** drop the CMake block (`CMakeCache.txt`, `CMakeFiles/`, `cmake_install.cmake`, `Makefile`, `cmake-build-*/`) and the C object lines. Keep `build/`, `build-*/` and the rest.

### 7. Docs in the repository

- **README.md:**
  - "Built with": Python 3.13+, PySide6 6.8+ (tested with 6.11.2) and the same Qt modules.
  - "Requirements": `sudo dnf install python3 python3-pyside6 pyside6-tools kf6-kirigami kf6-qqc2-desktop-style qt6-qtwebengine hunspell-en-US hunspell-pt-BR`, plus the development tools `python3-pytest python3-pytest-qt python3-mypy ruff dbus-daemon`.
  - "Build and run": `python3 scripts/build.py && python3 -m kondor`, and `--install <prefix>`.
  - "Tests": `scripts/run-pytests.sh`.
  - "Translations": `python3 scripts/update-translations.py`; a new language is a new `i18n/kondor_<lang>.ts`.
  - "Code quality" names `kondor/`, `qml/` and `tests/`.

  Features and shortcuts do not change.
- **`docs/agents/developer.md`:**
  - the role line says Python + PySide6;
  - the checks list (step 2) is `ruff check`, `mypy --strict kondor`, `python3 scripts/build.py`, `scripts/run-pytests.sh`, the offscreen smoke test `QT_QPA_PLATFORM=offscreen timeout 15 python3 -m kondor` with the isolated XDG folders, and the spec's manual test;
  - the build-wrapper and `--parallel` text goes.
- **`docs/agents/architect.md`:** the role line and review checklist item 2 say the same checks, with no C++ build or `ctest`.
- **`.github/pull_request_template.md`:** "How it was tested" lists the Python checks and the offscreen smoke test. "New dependencies added to …" names README, `build.yml`, `release.yml`, `prepare-appdir.sh` / `pyside-modules.txt` and the Flatpak manifest.
- **Old specs** in `docs/specs/` are history and are not rewritten.

### 8. What the architect does after the merge (not in the PR)

`AGENTS.md` lives outside git, so after merging, the architect rewrites it in `~/.config/kondor-agents/AGENTS.md`:

- **What Kondor is:** Python 3.13 + PySide6, minimum Qt 6.8.
- **Build and run:** `scripts/build.py`, `python3 -m kondor`, the smoke test.
- **Which checks a change needs:** every change runs the Python checks; the `needs-cpp-checks.sh` text goes.
- **Architecture:** `kondor/` instead of `src/`, and `tests/` is Python.
- **The Tab bridge pattern:** Python `Property` / `Signal` / `Slot`.
- **Shared building blocks:** the Python module paths.
- **Conventions:** the umbrella's Python rules from item 3, translations with `scripts/update-translations.py`, and new modules in `pyside-modules.txt`.
- **Dependencies, the delivery checklist and the freeze rule:** the C++ freeze sentence goes.

The architect also updates the specs of open issues that name C++ files (for example #211, #212 and #227), and records it on #174.

## Acceptance criteria

- [ ] No `.cpp`, `.h`, `CMakeLists.txt`, `cmake/`, `src/`, `pytests/`, `packaging/python-proof/`, `scripts/qmlapi/`, `scripts/check-qml-api.py`, `scripts/needs-cpp-checks.sh` or `scripts/bin/` is left. `tests/` holds the Python tests, and `scripts/run-pytests.sh` runs them all and passes.
- [ ] `python3 scripts/build.py --install <tmp>/usr` writes the item 1 layout. `<tmp>/usr/bin/kondor` started from another directory with `QT_QPA_PLATFORM=offscreen timeout 15` and an isolated XDG home prints no QML errors. With `hunspell-en-US` and `hunspell-pt-BR` installed, `en-US.bdic` and `pt-BR.bdic` are there.
- [ ] Tests cover `staged_build_directory()` for both layouts, `PROJECT_VERSION` against `pyproject.toml`, the `RESOURCE_GROUPS` files existing, `pyside-modules.txt` against the imports, and the dictionary step skipping a missing tool or dictionary with the warning.
- [ ] `python3 scripts/update-translations.py` leaves every `.ts` file with the same messages and translations as before the PR (only `<location>` lines differ, counts in the PR body). A second run changes nothing. `scripts/check-translations.py` passes, and both translator notes are in the `.ts` files.
- [ ] `build.yml` has one `build` job with the item 5 steps, and it is green on the PR.
- [ ] A `release.yml` dispatch on the PR branch builds the AppImage, and `appimage-run` passes on a bare host. A `flatpak.yml` dispatch builds the Flatpak and checks its repository. Both run links are in the PR body.
- [ ] `scripts/local-appimage.sh --now` builds, smoke-tests and installs the Python AppImage (manual test).
- [ ] `ruff check`, `mypy --strict kondor`, `python3 -m unittest discover -s scripts/tests` and `python3 scripts/check-code-quality.py` pass, and the baseline stays empty.
- [ ] README, `docs/agents/developer.md`, `docs/agents/architect.md`, the loop scripts and the PR template follow item 7. A search for `cmake`, `ctest`, `CMakeLists` and `needs-cpp-checks` outside `docs/specs/` finds nothing.
- [ ] `qml/` is unchanged. `kondor/` changes only in `stagedbuild.py` (item 1), translation calls (item 3), the moved JS files and the import renames.
- [ ] Privacy: the ported privacy tests pass, and the umbrella's manual-test private-tab step finds nothing new on disk.

## Manual test

On Fedora 45, in a clean checkout of the PR branch. Every app run uses one isolated profile: `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` and `XDG_STATE_HOME` under one temp folder (AGENTS.md), with downloads in it too.

1. **Checks:** `ruff check && mypy --strict kondor && python3 -m unittest discover -s scripts/tests && python3 scripts/check-code-quality.py && python3 scripts/build.py && scripts/run-pytests.sh`. All pass.
2. **Install:** run `python3 scripts/build.py --install "$T/usr"`, then `cd /tmp && "$T/usr/bin/kondor"` on the real display. The browser opens with the Breeze style. Close it: exit code 0, nothing on stderr.
3. **Profile migration:** build the C++ app from the PR's base (`git worktree add <tmp> <base>`, then `cmake -S <tmp> -B <tmp>/build && cmake --build <tmp>/build --parallel 4`).
   1. Run the umbrella manual test's step 1 with `<tmp>/build/kondor`.
   2. Run steps 2-4 with the AppImage from the PR's `release.yml` dispatch (`APPIMAGE_EXTRACT_AND_RUN=1` if FUSE is missing).
   3. Everything the umbrella lists is there: tabs, history, bookmark, KWallet password, extension, settings and cookies. Private browsing leaves nothing on disk, and the rest works: ad blocking, the download notification, find in page, Get New Extensions, a second window, and a second instance forwarding its URL.
4. **Flatpak:** install the bundle from the `flatpak.yml` run and start `flatpak run io.github.lukasborges.Kondor` on the same kind of throwaway profile (`--env=XDG_…`). The window opens and a page loads. Settings → Passwords reaches KWallet. Spell checking underlines a misspelled word in a text field.
5. **Translations:** `LANG=pt_BR.UTF-8 "$T/usr/bin/kondor"` shows the Portuguese UI and the "Navegador Kondor" title.
6. **Local AppImage:** `KONDOR_APPIMAGE_CONTROL=<checkout of the PR> KONDOR_APPIMAGE_DEST="$T/kondor.appimage" scripts/local-appimage.sh --now` builds, smoke-tests and installs it, and the installed AppImage starts.
7. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- Any behavior, UI or QML change, and new features. Bugs found in `kondor/` are reported with `question` first, and fixed in this PR with a test only if the architect agrees.
- Editing `AGENTS.md` (item 8: the architect does it after the merge) and rewriting old specs.
- pip, wheels, PyPI, `setup.py` or a Python package install (`pip install .`). The app is installed by `build.py --install`, not as a Python distribution.
- A Flathub submission, new distribution packages (RPM, Debian), signing or release-process changes beyond the AppImage and Flatpak build steps.
- Changing the number or names of the CI jobs other than merging `python` and `changes` into `build`.
- Renaming the app, the app id, the desktop file, the socket name or any on-disk path.

## Dependencies

- #173 (phase 11: the Python app runs).

Phase 12 closes the umbrella #162 (`Closes #174`, and the PR body also says `Closes #162`).

## Prototype

None: no UI changes.

## Decisions

| Question | Decision |
| --- | --- |
| Who updates `AGENTS.md`? | The architect, after the merge (item 8). It lives in `~/.config/kondor-agents/` and is never committed, so the PR cannot change it. This replaces the umbrella item 11 "AGENTS.md" bullet, which now points here. |
| Where does the installed app find its QML and resources? | Next to the package, in `<prefix>/share/kondor/`. `staged_build_directory()` picks that folder when it holds `kondor.rcc`, else the checkout's `build/python`. There is no environment variable, as in phase 11. |
| How is the app started? | The `packaging/kondor` launcher sets `PYTHONPATH` relative to itself and runs `python3 -P -m kondor`. `-P` keeps a `kondor/` folder in the current directory from shadowing the installed package. The AppImage's `AppRun` and the Flatpak's `command` both go through it. |
| Where do the five JS resources go when `src/` is deleted? | Next to the Python twins of the C++ code that loaded them (`kondor/passwords/bridge/`, `kondor/extensions/bridge/`, `kondor/extensions/scripts/`). The resource paths stay the same, so the QML and the page scripts do not change. |
| One AppImage script or two? | One, `packaging/appimage/prepare-appdir.sh`, shared by `release.yml` and `local-appimage.sh`. The C++ setup had two copies that had to be kept in sync by hand. |
| Why `rcc` / `lrelease` as a fallback? | The Flatpak SDK may ship Qt's tools without `pyside6-*`. The formats are the same, and Fedora still prefers the PySide6 tools. |
| Why keep a single `build` job? | The architect loop merges when the `build` check is green. Merging `python` and `changes` into it keeps that rule. Without C++, every change runs every check in a few minutes. |
| How is a release AppImage tested before tagging? | `release.yml` gets `workflow_dispatch`, which builds it and runs it on a bare host without publishing. The C++ release was never smoke-tested in CI. |
| Wait for the QA parity run (#217) before switching? | No, chosen by the maintainer: #174 is the last step of the port and goes first. QA runs after the switch, on the Python app. |
