# Automated tests (#26)

> **Issue:** [#26](https://github.com/lukasborges/kondor/issues/26) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Add automated tests (Qt Test) for the non-UI logic and run them in CI.

## Context

No tests; `.github/workflows/build.yml` only builds. `ProfileManager::resolveAddress()` mixes logic with the singleton; `TabModel` depends on `ProfileManager` profiles.

## Design / behavior

1. **Refactor for testability**: move the body of `ProfileManager::resolveAddress()` into a pure function in `src/addressresolver.{h,cpp}`:
   ```cpp
   QUrl resolveAddress(const QString &text, const QUrl &homePage, const QString &searchTemplate);
   ```
   `ProfileManager::resolveAddress()` just calls it. Add the new files to the `qt_add_qml_module(... SOURCES ...)` list.
2. **Small behavior fix found by the tests**: `localhost`, `127.0.0.1` and private-network IPs (`10.*`, `192.168.*`, `172.16–31.*`) should resolve to `http://`, not `https://` (dev servers rarely have TLS). Public hosts keep `https://`.
3. **CMake**:
   ```cmake
   option(BUILD_TESTING "Build tests" ON)
   if(BUILD_TESTING)
       enable_testing()
       find_package(Qt6 REQUIRED COMPONENTS Test)
       add_subdirectory(tests)
   endif()
   ```
   `tests/CMakeLists.txt` with `qt_add_executable(tst_addressresolver tst_addressresolver.cpp ../src/addressresolver.cpp)` linked to `Qt6::Test Qt6::Core`, `add_test(NAME tst_addressresolver COMMAND tst_addressresolver)`; and `tst_tabmodel` linked with the app sources it needs (`tabmodel.cpp`, `tab.cpp`, `profilemanager.cpp`, `addressresolver.cpp`) + `Qt6::WebEngineQuick Qt6::Qml Qt6::Test`, environment `QT_QPA_PLATFORM=offscreen;QTWEBENGINE_DISABLE_SANDBOX=1` via `set_tests_properties(... ENVIRONMENT ...)`; call `QtWebEngineQuick::initialize()` before `QGuiApplication` in a custom `main` (use `QTEST_MAIN` alternative: write `int main()` that initializes then runs `QTest::qExec`).
4. **`tests/tst_addressresolver.cpp`** — data-driven (`_data()` + `QFETCH`) cases:
   | input | expected |
   | --- | --- |
   | `""` / `"   "` | home page |
   | `"kde.org"` | `https://kde.org` |
   | `"kde.org/applications"` | `https://kde.org/applications` |
   | `"http://example.com"` | unchanged |
   | `"localhost:8080"` | `http://localhost:8080` |
   | `"192.168.0.1"` | `http://192.168.0.1` |
   | `"8.8.8.8"` | `https://8.8.8.8` |
   | `"about:blank"`, `"file:///etc/hosts"`, `"data:text/plain,hi"` | unchanged |
   | `"kde"` | search URL with `q=kde` |
   | `"hello world"` | search with `hello%20world` |
   | `"c++ tutorial"` | search with `c%2B%2B%20tutorial` |
   | `"what is kde.org?"` | search (contains spaces) |
5. **`tests/tst_tabmodel.cpp`**: add tab → count/current; add 3, close current middle → current index rules from `TabModel::closeTab()`; close before current → index shifts; `setCurrentIndex` out of range ignored; private tab `isPrivate` true and uses a different profile from normal tabs.
6. **CI**: in `build.yml` add `qt6-qtbase-devel` already there; run `ctest --test-dir build --output-on-failure` after the build step.

## Acceptance criteria

- [ ] `ctest --test-dir build` runs both suites locally and they pass.
- [ ] The Build workflow runs the tests and fails on test failures.
- [ ] `localhost`/LAN addresses resolve to `http://`.
- [ ] No behavior change for the app other than the fix above.

## Manual test

`cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure`; type `localhost:8000` in the address bar with `python3 -m http.server` running.

## Out of scope

QML/UI tests (Squish, `qmltestrunner`), coverage reports.

## Dependencies

None. Should be updated whenever later issues add logic worth testing.

## Prototype

No UI for this issue, so there is no prototype.

## Decisions

_None yet._ Answers to developer questions (`question` label) are recorded here as `| Question | Decision |` rows.
