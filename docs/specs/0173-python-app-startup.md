# Python port 11/12: App startup (#173)

> **Issue:** [#173](https://github.com/lukasborges/kondor/issues/173) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 1-4, 8, 9 and "Acceptance criteria", phase 11) and the specs of the phases this one wires together first: [`0169`](0169-python-browser-profile-address-session.md) (`ProfileManager`, `pagescripts`, `resolve_address`), [`0170`](0170-python-tabs.md) (`Tab`, `TabModel`, `SessionManager.saved_windows()`), [`0171`](0171-python-extensions-core.md) (`ExtensionManager`, `ExtensionLoader`, `has_package_suffix`), [`0172`](0172-python-extensions-catalog.md) (`ExtensionCatalog.start_auto_update()`) and [`0218`](0218-python-extensions-bridge.md) (`ExtensionBridge`). This file details phase 11 and must follow the umbrella. Only the architect edits it.

## Objective

Port `src/app/` to Python and add `kondor/__main__.py`, so that **`python3 -m kondor` starts the whole browser** from the staged build, and port `tests/app/` and `tests/settings/`:

- **Same app:** the same window, menus, dialogs and shortcuts as the C++ app, from the unchanged `qml/`. `QT_QPA_PLATFORM=offscreen timeout 15 python3 -m kondor` prints no QML errors.
- **Same QML API:** `AboutInfo`, `StartupArgs` and `WindowManager` are QML singletons in `Kondor` 1.0. `check-qml-api.py` pairs them with their C++ twins. After this phase every C++ QML type has a Python twin.
- **Same command line and single instance:** the same options, the same socket name and the same message bytes, so a C++ instance and a Python instance of one profile never both run, and either one forwards its URLs to the other.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/`, `CMakeLists.txt` or the workflows changes. The C++ app stays the product until phase 12.

## Context

- **Earlier phases** ported every other folder of `src/`. Each feature has `kondor/<feature>/qmltypes.py` with `QML_TYPES` and `register_types()` (`kondor/core/qmlregistration.py`: `QmlType`, `QmlKind`, `register`). The tests register all of them through `pytests/kondortypes.py` (`qmltypes_modules()`, which walks the package) in the `kondor_types` session fixture.
- **The staged build:** `python3 scripts/build.py` writes `build/python/qml/Kondor/` (the QML module with its `qmldir`), `build/python/i18n/*.qm` and `build/python/kondor.rcc`, which holds `:/LICENSE`, `:/packaging/kondor.png`, `:/packaging/kondor.svg`, `:/i18n/kondor_<lang>.qm`, `:/reader/*` and `:/scripts/*.js` (`scripts/staging/resources.py`, `bundle.py`). The C++ app compiles the same files into its binary.
- **Version:** `CMakeLists.txt` has `project(Kondor VERSION 0.2.0 …)` and passes it as `PROJECT_VERSION`; `pyproject.toml` has `version = "0.2.0"`.
- **The scope** (about 1,050 lines):

  | C++ file | What it does |
  | --- | --- |
  | `main.cpp` | `installMessageHandler()`, `prepareEnvironment()`, `QApplication`, `setUpIdentity()`, `parseCommandLine(app)`, `SingleInstance`; return 0 when `forwardsToRunningInstance`; `startBrowser(app, commandLine)`; a `QQmlApplicationEngine`; `openWindows(engine, singleInstance) ? app.exec() : 1` |
  | `aboutinfo.{h,cpp}` | QML singleton `AboutInfo`: `CONSTANT` properties `version`, `qtRuntimeVersion`, `qtBuildVersion`, `webEngineVersion`, `chromiumVersion`, `windowingSystem` (`Wayland` for `wayland*`, `X11` for `xcb`, else the platform name), `operatingSystem` (`QSysInfo::prettyProductName()`), `licenseText` (`:/LICENSE`, trimmed) |
  | `commandline/commandline.{h,cpp}` | `CommandLine` (`urls`, `isPrivate`, `newWindow`, `newInstance`, `extensionDirectories`); `parseCommandLine(app)` with `QCommandLineParser`: description `Kondor web browser`, `--help`, `--version`, `--private`, `--new-window`, `--new-instance`, repeatable `--load-extension <dir>`, positional `urls` (`[urls...]`) |
  | `commandline/extensionpackages.{h,cpp}` | `takeExtensionPackages(urls)`: moves local `.kondorext` files (case-insensitive) out of the list, keeping the order of both parts, and returns their paths |
  | `commandline/startupargs.{h,cpp}` | QML singleton `StartupArgs`: `CONSTANT` `startupUrls` (`QList<QUrl>`) and `startupPrivate`; C++-only setters |
  | `commandline/startupurl.{h,cpp}` | `StartupContext` (`workingDirectory`, `homePage`, `searchTemplate`); `startupUrlForArgument` (trimmed; empty → empty URL; an existing file relative to the working directory → `QUrl::fromUserInput(input, dir, AssumeLocalFile)`; else `resolveAddress`); `startupUrlsForArguments` (context from `QDir::currentPath()` and `Settings`, empty results dropped) |
  | `instance/singleinstance.{h,cpp}` | `SingleInstance(serverName = "")`: `serverName()` = `runtimeDirectory() + "/kondor-" + first 16 hex chars of SHA-1(AppDataLocation) + ".socket"` (inside Flatpak `RuntimeLocation/app/<FLATPAK_ID>`, created); `sendMessage` (500 ms timeouts); `start` → `Listening` / `Forwarded` / `Failed` (send, else remove the stale server and listen, else send again); `UserAccessOption`; reads newline-separated messages, at most 1 MiB buffered (`Kondor: single-instance message too large, ignored`, then disconnects); signal `messageReceived` |
  | `instance/singleinstancemessage.{h,cpp}` | `SingleInstanceMessage` (`urls`, `privateMode`, `newWindow`, `activationToken`); `toJsonLine()` = compact JSON `{"activationToken":…,"newWindow":…,"private":…,"urls":[…]}` + `\n` (URLs as `toEncoded()`); `fromJsonLine` (not an object → empty message; invalid or empty URLs dropped) |
  | `instance/windowactivation.{h,cpp}` | `raiseWindow(window, token)`: for a `QQuickWindow`, set `XDG_ACTIVATION_TOKEN` when the token is not empty, then `raise()` and `requestActivate()` |
  | `startup/appidentity.{h,cpp}` | `setUpIdentity()`: organization `KDE`, application `Kondor`, version, desktop file name (`FLATPAK_ID` or `kondor`), window icon `:/packaging/kondor.png`. `setUpLanguageAndStyle(app)`: translators `kondor` from `:/i18n` and `qt` from `QLibraryInfo::TranslationsPath`, display name `translate("Kondor", "Kondor Browser")`, style `org.kde.desktop` (else `Fusion`) |
  | `startup/appstartup.{h,cpp}` | `forwardsToRunningInstance` (skipped with `--new-instance`; `Failed` warns `Kondor: cannot listen for later launches on <name>; running as a separate instance`); `startBrowser` (publish `StartupArgs`, language and style, `AdBlockManager::start()`, connect `profileCreated` to `ExtensionManager::registerProfile` and register the existing profiles, `ExtensionLoader` for `--load-extension`); `openWindows` (image provider `kondor-favicon`, `WindowManager` engine, `messageReceived` → `handleSingleInstanceMessage`, `openStartupWindows()`, `ExtensionCatalog::startAutoUpdate()`, true when a window exists) |
  | `startup/environment.{h,cpp}` | `prepareEnvironment()`: `AA_ShareOpenGLContexts`; `QTWEBENGINE_DICTIONARIES_PATH` from the first existing candidate next to the executable unless already set; `QtWebEngineQuick::initialize()`; `PLASMA_INTEGRATION_USE_PORTAL=1` inside an AppImage unless set |
  | `startup/messagehandler.{h,cpp}` | prints every message to stderr, except debug and info messages outside the `kondor.extensions` category |
  | `windows/windowmanager.{h,cpp}`, `windows/windowlaunch.cpp` | QML singleton `WindowManager`: property `windowCount` (notify `windowCountChanged`), invokables `newWindow(privateWindow = false, urls = [])` and `closeWindow(window)`; creates `Kondor.BrowserWindow` with the initial properties `privateWindow`, `initialUrls`, `initialTitles`, `initialCurrentIndex`; tracks the active window; `windowForRequest(private)`; `handleSingleInstanceMessage`; `openStartupWindows` (session restore when `startupBehavior` is `restore`, then the command-line window, else one empty window; then the first extension package) |

- **QML that uses it:** `BrowserActions.qml`, `WindowTabController.qml` and `PageView.qml` call `WindowManager.newWindow(…)`; `WindowCloseGuard.qml` calls `closeWindow` and reads `windowCount`; `qml/app/about/*.qml` read `AboutInfo`. `BrowserWindow.qml` has `openUrlsInNewTabs(urls)` and `openSettingsPage(pageId)`.
- **Tests to port** (every case):

  | C++ test | Cases |
  | --- | --- |
  | `app/tst_aboutinfo` | `versionMatchesProjectVersion`, `licenseTextIsEmbedded`, `runtimeVersionsAreFilled` |
  | `app/tst_extensionpackages` | `takesLocalPackagesOutOfTheUrls`, `keepsRemoteUrlsThatLookLikePackages` |
  | `app/tst_singleinstance` | `socketNameDependsOnProfileDirectory`, `encodesAndDecodesMessage`, `rejectsInvalidData`, `forwardsMessageToRunningInstance`, `forwardsWhenAnotherInstanceStartedFirst` |
  | `app/tst_startupurl` | `convertsArguments` (6 rows), `resolvesRelativeFilesAgainstWorkingDirectory`, `skipsEmptyArguments` |
  | `app/tst_mainmenu` (stub window + `MainMenu`) | `rowsAndOrder`, `historySubmenuListsRecentlyClosedTabs`, `shortcutsWorkWithTheMenuClosed`, `actionsDoNotShareASequenceWithAShortcut` |
  | `app/tst_toolbaraccessibility` (stub window + `NavigationToolBar`) | `everyVisibleToolBarButtonHasAName` |
  | `settings/tst_settingsapply` (`SettingsWindow`) | `pendingChangesAreDiscarded`, `applyWritesAndDisablesApply`, `okAppliesAndCloses`, `everyPageDefaultsResetOnlyItsOptions` (7 rows), `walletUnavailableState` |
  | `settings/tst_settingsnavigation` | `clickingSidebarSwitchesPages`, `arrowKeysMoveBetweenPages`, `searchFiltersPages` |

  With their helpers `app/mainmenuharness.h`, `app/mainmenustub.h`, `settings/settingswindowharness.h`, `settings/settingsnavigationharness.h` and `common/accessibilitywalk.h`. After this phase every C++ test has a pytest twin.

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior, texts and edge cases as the C++, with the Python conventions of umbrella item 3 (a struct becomes a dataclass, a helper namespace a module of functions).

### 1. Layout

```
kondor/__main__.py           main(): the steps of main.cpp; sys.exit(main())
kondor/app/
  __init__.py
  qmltypes.py                AboutInfo, StartupArgs, WindowManager (singletons)
  aboutinfo.py
  commandline/
    __init__.py
    commandline.py           CommandLine, parse_command_line(app), parse_arguments(arguments)
    extensionpackages.py     take_extension_packages(urls)
    startupargs.py           StartupArgs
    startupurl.py            StartupContext, startup_url_for_argument, startup_urls_for_arguments
  instance/
    __init__.py
    singleinstance.py        SingleInstance, StartResult
    singleinstancemessage.py SingleInstanceMessage, to_json_line, from_json_line
    windowactivation.py      raise_window(window, token)
  startup/
    __init__.py
    appidentity.py           set_up_identity(), set_up_language_and_style(app)
    appstartup.py            forwards_to_running_instance, start_browser, open_windows
    environment.py           prepare_environment()
    messagehandler.py        install_message_handler(), is_silenced(type, category)
    stagedbuild.py           staged_build_directory(), load_staged_resources(), PROJECT_VERSION
    qmlregistry.py           FEATURE_TYPES, register_all_types()
  windows/
    __init__.py
    windowmanager.py         WindowManager, WindowContents
    windowlaunch.py          the windowlaunch.cpp half, as functions over the manager
```

No other `kondor/` module changes. If the size limits need it, split a module by responsibility inside the same folder; the names above are fixed.

### 2. Staged build, resources and version (`startup/stagedbuild.py`)

The C++ app carries its QML and resources inside the binary; the Python app reads them from the staged build.

- **`staged_build_directory() -> Path`:** `Path(__file__).resolve().parents[3] / "build" / "python"`, the folder `scripts/build.py` writes in the checkout. Phase 12 adds the installed location.
- **`load_staged_resources(directory) -> bool`:** `QResource.registerResource(str(directory / "kondor.rcc"))`. When `directory / "qml" / "Kondor" / "qmldir"` or `kondor.rcc` is missing, print `Kondor: cannot find the staged build in <directory>; run python3 scripts/build.py` to stderr and return `False`; `main()` then exits with 1.
- **`PROJECT_VERSION = "0.2.0"`:** the Python twin of the CMake `PROJECT_VERSION`. A test checks it equals both the `project(Kondor VERSION …)` of `CMakeLists.txt` and the `version` of `pyproject.toml`, so a version bump that forgets one fails CI.

### 3. `kondor/__main__.py`

`main() -> int` follows `main.cpp` step by step, each step one call:

1. `install_message_handler()`;
2. `prepare_environment()`;
3. `signal.signal(signal.SIGINT, signal.SIG_DFL)`, so Ctrl+C in a terminal ends the app as it ends the C++ one (Python would otherwise swallow it while Qt's loop runs);
4. `app = QApplication(sys.argv)`;
5. `load_staged_resources(staged_build_directory())`, or return 1. It runs before `set_up_identity()` because the window icon and the translations come from `kondor.rcc`;
6. `set_up_identity()`;
7. `command_line = parse_command_line(app)`;
8. `single_instance = SingleInstance()`; return 0 when `forwards_to_running_instance(single_instance, command_line)`;
9. `start_browser(app, command_line)`;
10. `engine = QQmlApplicationEngine()` with `engine.addImportPath(str(staged / "qml"))`;
11. return `app.exec()` when `open_windows(engine, single_instance)`, else 1.

The module ends with `if __name__ == "__main__": sys.exit(main())`. Importing `kondor.__main__` must not start anything.

**Shutdown:** closing the last window ends the process with exit code 0, with no crash and no warning on stderr (for example Qt WebEngine's `Release of profile requested but WebEnginePage still not deleted`). Python may destroy objects in an order C++ never does: after `app.exec()` returns, delete the remaining windows, then the engine, before the `QApplication` goes away (an explicit `del` or a small `shut_down` helper in `appstartup.py`). The manual test checks it.

### 4. Command line (`commandline/`)

- **`CommandLine`** is a dataclass: `urls: list[QUrl]`, `is_private`, `new_window`, `new_instance` (`bool`, default `False`), `extension_directories: list[str]`.
- **`parse_command_line(app) -> CommandLine`** returns `parse_arguments(app.arguments())`. **`parse_arguments(arguments)`** builds the `QCommandLineParser` exactly as `describe()` does: the same description, option names, help texts (untranslated, as in C++), value name `dir` and positional `urls` / `URLs or files to open` / `[urls...]`; then `parser.process(arguments)` and the same `read()`. `--help` and `--version` print and exit as `QCommandLineParser` does (`Kondor 0.2.0` for `--version`).
- **`take_extension_packages(urls: list[QUrl]) -> list[str]`** changes the list in place like the C++ (`std::stable_partition`): the non-package URLs stay in order, and the returned paths keep the packages' order. It uses phase 9's `has_package_suffix`.
- **`StartupContext`** is a frozen dataclass (`working_directory: str`, `home_page: QUrl`, `search_template: str`). `startup_url_for_argument` and `startup_urls_for_arguments` follow the C++ with `QUrl.fromUserInput(input, directory, QUrl.UserInputResolutionOption.AssumeLocalFile)` and phase 7's `resolve_address`; the context reads `Settings.instance()`'s `homePage` and `searchUrlTemplate()`.
- **`StartupArgs`** (`QObject`): `startupUrls` (`Property("QList<QUrl>", …, constant=True)`) and `startupPrivate` (`Property(bool, …, constant=True)`), with the snake_case setters `set_startup_urls` and `set_startup_private`. If PySide6 6.11.2 cannot declare a `QList<QUrl>` property or the API check reports a type difference, ask (`question`) before choosing another type.

### 5. Single instance (`instance/`)

- **`SingleInstanceMessage`** is a dataclass: `urls: list[QUrl]`, `private_mode`, `new_window` (`bool`), `activation_token: bytes`.
- **`to_json_line(message) -> bytes`** and **`from_json_line(line: bytes) -> SingleInstanceMessage`** use `QJsonDocument` / `QJsonObject` in both directions (as phase 7's `sessionformat` does), so the bytes match the C++ app's: sorted keys, compact, URLs as `QUrl.toEncoded()` decoded as UTF-8, a trailing `\n`. `from_json_line` trims, treats a non-object as the empty message, reads `toBool()` / `toString()` semantics and drops invalid or empty URLs.
- **`SingleInstance(server_name="", parent=None)`** (`QObject`) with `QLocalServer` / `QLocalSocket` from `QtNetwork`:
  - `StartResult` is an `Enum` (`LISTENING`, `FORWARDED`, `FAILED`);
  - `server_name()` is a `staticmethod` with the C++ formula: `QStandardPaths.writableLocation(AppDataLocation)` hashed with `QCryptographicHash.hash(…, Sha1)`, the first 16 hex characters, the Flatpak runtime folder rule, the `.socket` suffix;
  - `send_message(message) -> bool` and `start(message) -> StartResult` with the same steps, 500 ms timeouts and `QLocalServer.removeServer`;
  - `messageReceived = Signal(object)` carries a `SingleInstanceMessage`;
  - per-socket buffers in a `dict` keyed by the socket, the 1 MiB limit and its warning (`qWarning` text unchanged), complete lines emitted one by one, sockets dropped and `deleteLater()`ed on `disconnected`.
- **`raise_window(window, token)`:** only for a `QQuickWindow`; a non-empty token goes to `os.environ["XDG_ACTIVATION_TOKEN"]` (PySide6 has no `qputenv`; CPython's `os.environ` calls `putenv`, which Qt reads); then `raise_()` and `requestActivate()`.

### 6. Startup (`startup/`)

- **`install_message_handler()`** installs a `qInstallMessageHandler` function that writes `message + "\n"` to `sys.stderr` and flushes, unless **`is_silenced(message_type, category)`**: `QtDebugMsg` or `QtInfoMsg` with a category other than `kondor.extensions` (`category` is `context.category`, which may be `None`).
- **`prepare_environment()`:** `QCoreApplication.setAttribute(AA_ShareOpenGLContexts)`, find the dictionaries, `QtWebEngineQuick.initialize()`, then the AppImage portal rule, in the C++ order. **Dictionaries:** `/proc/self/exe` is the Python interpreter in this app, so the candidates are taken relative to the staged build directory instead, with the C++ layout: `<staged>/../share/kondor/qtwebengine_dictionaries`, then `<staged>/qtwebengine_dictionaries`, each `QDir.cleanPath`ed. An already set `QTWEBENGINE_DICTIONARIES_PATH` wins. Converting the dictionaries into the staged build is phase 12; until then no candidate exists and the variable stays unset, like a C++ build without dictionaries.
- **`set_up_identity()` and `set_up_language_and_style(app)`:** as the C++, with `PROJECT_VERSION`, `QTranslator.load(QLocale(), name, "_", directory)` (a translator that loads is kept alive by parenting it to `app`), `QCoreApplication.translate("Kondor", "Kondor Browser")` (same context and source text, so the existing translations apply; the translator note stays in the C++ until phase 12, because `lupdate` does not scan Python yet) and `QQuickStyle`.
- **`appstartup.py`:** `forwards_to_running_instance`, `start_browser` and `open_windows` with the C++ steps and warning text. `message_for(command_line)` takes `XDG_ACTIVATION_TOKEN` from `os.environ` as bytes. `open_windows` first calls `register_all_types()`, then adds the image provider `kondor-favicon` (phase 4's `FaviconImageProvider`), gives the engine to `WindowManager.instance().set_engine`, connects `messageReceived` to `handle_single_instance_message`, calls `open_startup_windows()` and `ExtensionCatalog.instance().start_auto_update()`, and returns `windowCount > 0`. The `ExtensionLoader` is parented to the `QApplication`.
- **`qmlregistry.py`:** `FEATURE_TYPES` is an explicit tuple of the feature `qmltypes` modules (core, adblock, downloads, history, bookmarks, passwords, browser, extensions, app); `register_all_types()` calls each `register_types()` once. The app does not walk the package at run time; a test checks the tuple lists every module `pytests/kondortypes.qmltypes_modules()` finds.

### 7. `AboutInfo` (`aboutinfo.py`)

Every property is `Property(str, …, constant=True)`:

| Property | Python source |
| --- | --- |
| `version` | `QCoreApplication.applicationVersion()` |
| `qtRuntimeVersion` | `PySide6.QtCore.qVersion()` |
| `qtBuildVersion` | `PySide6.QtCore.__version__` (the Qt version PySide6 was built against, the twin of `QT_VERSION_STR`) |
| `webEngineVersion`, `chromiumVersion` | `PySide6.QtWebEngineCore.qWebEngineVersion()`, `qWebEngineChromiumVersion()` |
| `windowingSystem` | the C++ mapping of `QGuiApplication.platformName()` |
| `operatingSystem` | `QSysInfo.prettyProductName()` |
| `licenseText` | `:/LICENSE` read with `QFile` as UTF-8 and trimmed, `""` when missing |

**`licenseText` is read on first access and cached**, not in the constructor: the singleton is created when its type is registered, which in the tests can happen before `kondor.rcc` is loaded. The value QML sees is the same.

### 8. `WindowManager` (`windows/`)

- **`WindowContents`** is a dataclass: `is_private = False`, `urls: list[QUrl]`, `titles: list[str]`, `current_index = -1`.
- **QML API:** `windowCount` (`Property(int, notify=windowCountChanged)`); `newWindow` with 0, 1 or 2 arguments (`privateWindow: bool = False`, `urls` a list of `QUrl` or URL strings from a JS array, converted with `QUrl(value)`), returning the window `QObject` or `None`; `closeWindow(window)` → `deleteLater()` when not `None`. The API check must see `newWindow` accept 0, 1 and 2 arguments (stacked `Slot` decorators).
- **Snake case API:** `set_engine(engine)` (only the first non-`None` engine), `create_window(contents)`, `load_component()`, `window_for_request(private)`, `is_private_window(window)` (static), `handle_single_instance_message(message)` and `open_startup_windows()`.
- **Component:** `QQmlComponent(engine, "Kondor", "BrowserWindow")`, kept after the first success; errors give the C++ warnings `Kondor: cannot create a window before the QML engine is set`, `Kondor: cannot load the browser window: <error>` and `Kondor: cannot create the browser window: <error>`. Windows are made with `createWithInitialProperties` and the four C++ property names.
- **Tracking:** the manager keeps the window objects in a list (Python holds them, so an open window is never garbage-collected), follows `activeChanged` of a `QQuickWindow` to remember the active one, and on `destroyed` drops windows that are gone (`shiboken6.isValid` is the twin of `QPointer::isNull`), picks the last remaining one as active when the active one went away, and emits `windowCountChanged`. Track and creation emit `windowCountChanged` as in C++.
- **`windowlaunch.py`:** `handle_single_instance_message`, `open_urls_for_launch`, `add_tabs` (`QMetaObject.invokeMethod(window, "openUrlsInNewTabs", Q_ARG("QVariant", urls))`, warning `Kondor: cannot add tabs to the running window` on failure), `normal_window`, `show_packages`, `show_extension_package` (`ExtensionManager.instance().inspectFile(path)`, then `openSettingsPage("extensions")`, warning `Kondor: cannot open the extensions settings`), `open_startup_windows`, `open_restored_windows` (`Settings` `startupBehavior == "restore"`, phase 8's `SessionManager.instance().saved_windows()`) and `open_command_line_window`, as module functions taking the manager first; `WindowManager`'s two public methods delegate to them.
- **Privacy:** a private message or `--private` only reuses or opens a private window (`window_for_request(True)`); restored windows are never private, as in C++.

### 9. `qmltypes.py`

```python
QML_TYPES = (
    QmlType(AboutInfo, "AboutInfo", QmlKind.SINGLETON),
    QmlType(StartupArgs, "StartupArgs", QmlKind.SINGLETON),
    QmlType(WindowManager, "WindowManager", QmlKind.SINGLETON),
)
```

`pytests/core/test_singletons.py` covers them through `qmltypes_modules()` without changes.

### 10. Tests

Each C++ case becomes a test with the same intent (umbrella item 9). Data-driven cases become `pytest.mark.parametrize` with the same rows and ids. Test functions have at most 20 lines. No test reaches the internet.

```
pytests/app/
  __init__.py
  conftest.py
  test_aboutinfo.py
  test_appmain.py              new: subprocess runs of python3 -m kondor
  test_qmlregistry.py          new
  commandline/   __init__.py, test_extensionpackages.py, test_startupurl.py, test_commandline.py (new)
  instance/      __init__.py, test_singleinstance.py
  menu/          __init__.py, mainmenuharness.py, mainmenustub.py, test_mainmenu.py, test_toolbaraccessibility.py
  startup/       __init__.py, test_environment.py (new), test_messagehandler.py (new)
  windows/       __init__.py, windowstub.py, test_windowmanager.py (new)
pytests/settings/
  __init__.py
  conftest.py
  settingswindowharness.py
  settingsnavigationharness.py
  test_settingsapply.py
  test_settingsnavigation.py
```

- **Folders:** `pytests/app/` mirrors `kondor/app/`; the menu and tool bar tests go to `menu/`, after `qml/app/menu/`, so no folder passes 10 files.
- **Registration:** the tests use the real types through `kondor_types` and `kondor_engine`. The C++ tool bar test registers `tests/data/ExtensionManagerStub.qml` as `ExtensionManager` because its target does not link the extensions; the Python `ExtensionManager` is already registered, so the real one is used and the stub is not copied.
- **Helpers:** `accessibilitywalk.h`'s `unnamedButtons` goes to `pytests/qmlsupport.py` as `unnamed_buttons(item)`; the favicon provider is phase 4's `pytests/browser/fakefaviconprovider.py`; captured warnings use `qmlsupport.captured_messages()`. Do not copy a helper an earlier phase already has.
- **`test_aboutinfo.py`:** `version` equals `PROJECT_VERSION` (the app identity is set by a fixture, as `initTestCase` does); `licenseText` starts with `GNU GENERAL PUBLIC LICENSE` (needs `staged_resources`); the runtime versions are filled. New: `test_project_version_matches_cmake_and_pyproject`; `test_windowing_system_names` (`wayland-egl` → `Wayland`, `xcb` → `X11`, `offscreen` → `offscreen`, with the platform-name lookup patched).
- **`test_singleinstance.py`:** the five cases, with unique server names (`kondor-test-<pid>`) and `qtbot.waitSignal(…, timeout=2000)`. `socketNameDependsOnProfileDirectory` sets `XDG_DATA_HOME` with `monkeypatch`. New: `test_message_bytes_match_the_cpp_format` (a message with one URL, private, token `t` gives exactly `{"activationToken":"t","newWindow":false,"private":true,"urls":["https://kde.org"]}\n`); `test_oversized_message_is_ignored` (more than 1 MiB without a newline: no signal, the warning is logged); `test_two_messages_in_one_write_give_two_signals`.
- **`test_startupurl.py`** and **`test_extensionpackages.py`:** the C++ cases with the same rows. New `test_commandline.py`: `parse_arguments` for `--private --new-window kde.org` (flags and the resolved URL), two `--load-extension` values kept in order, and `--new-instance` alone.
- **`test_mainmenu.py`** and **`test_toolbaraccessibility.py`:** the stub window of `mainmenustub.h` as a Python string in `mainmenustub.py`, built on the staged `kondor_engine` with `TabModel` and the real singletons; `QAccessible.setActive(True)` for the tool bar test; `historySubmenuListsRecentlyClosedTabs` adds and closes tabs on the real `TabModel`; `shortcutsWorkWithTheMenuClosed` uses `qtbot.keyClick` and checks no captured warning contains `Ambiguous`; `actionsDoNotShareASequenceWithAShortcut` reads `qml/app/BrowserActions.qml` and `BrowserShortcuts.qml` with the same regular expressions.
- **`pytests/settings/`:** the harness ports `registerSettingsWindowTypes` (nothing to register: `kondor_types`), `resetSettingsToTestDefaults`, `pendingOf`, the fixture (`SettingsWindow.qml` from the staged module with a `TabModel`) and the navigation helpers. `walletUnavailableState` runs with `KONDOR_NO_KWALLET=1` set by the fixture, as phase 6's `pytests/passwords/conftest.py` does, and waits for `PasswordStore.instance().state` to be `unavailable`.
- **New `test_windowmanager.py`** (C++ has no `WindowManager` test). `windowstub.py` holds a `StubWindowManager(WindowManager)` whose `load_component()` returns a component made from inline QML: a `Window` (not shown) with the four initial properties, `openUrlsInNewTabs(urls)` and `openSettingsPage(pageId)` recording their arguments. Each test builds its own `StubWindowManager()` (not `instance()`). Cases:
  - `test_new_window_passes_initial_properties`;
  - `test_window_count_follows_created_and_closed_windows` (`closeWindow`, `deleteLater` processed, `windowCountChanged` emitted);
  - `test_message_adds_tabs_to_window_of_same_privacy`;
  - `test_private_message_never_reuses_a_normal_window`;
  - `test_new_window_flag_always_creates_a_window`;
  - `test_extension_package_opens_the_extensions_page` (`ExtensionManager.instance().inspectFile` patched with a recorder; the package path is recorded and `openSettingsPage("extensions")` is called on a normal window);
  - `test_startup_restores_saved_windows` (`startupBehavior` `restore`, `saved_windows` patched to two windows: two windows with their URLs, titles and current index);
  - `test_startup_without_urls_opens_one_empty_window`;
  - `test_open_window_survives_garbage_collection` (`gc.collect()`, still valid and counted);
  - `test_raise_window_exports_the_activation_token`.
- **New `test_messagehandler.py`:** `is_silenced` rows (debug and info silenced, debug in `kondor.extensions` shown, warning shown, `None` category).
- **New `test_environment.py`:** the dictionary lookup picks the first existing candidate, keeps an already set variable, and sets nothing when no candidate exists; the AppImage rule sets `PLASMA_INTEGRATION_USE_PORTAL` only with `APPIMAGE` and only when unset (`monkeypatch` on the environment; `QtWebEngineQuick.initialize()` is not called by these tests).
- **New `test_qmlregistry.py`:** `FEATURE_TYPES` lists every module of `qmltypes_modules()`, each once.
- **New `test_appmain.py`** (subprocesses with `sys.executable -m kondor` from the repository root, an isolated XDG home under `tmp_path`, `QT_QPA_PLATFORM=offscreen`, `QTWEBENGINE_DISABLE_SANDBOX=1`, `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`, `KONDOR_NO_KWALLET=1` and the conftest's `NO_DESKTOP_SERVICES`):
  - `test_version_option_prints_the_version`: `--version` exits 0 and prints `Kondor 0.2.0`;
  - `test_help_lists_the_options`: `--help` exits 0 and lists `--private`, `--new-window`, `--new-instance` and `--load-extension <dir>`;
  - `test_app_starts_without_qml_errors`: `--new-instance about:blank` is still running after 10 s; then it is terminated, and its stderr has none of `ReferenceError`, `TypeError`, `Cannot assign`, `is not a type`, `Kondor: cannot`;
  - `test_second_launch_forwards_to_the_first`: a first run without `--new-instance` is started; once its socket exists (`SingleInstance.server_name()` computed for the same isolated home, waited for up to 15 s), a second run with `https://kde.org` exits 0 within 5 s; both are cleaned up.

  These tests are marked `no_qt_log` where needed and must stay under 30 s together.

### 11. API check result

After this phase, `python3 scripts/check-qml-api.py` reports three more classes checked (`AboutInfo`, `StartupArgs`, `WindowManager`) and three fewer not ported than on the PR's base, and exits 0.

## Acceptance criteria

- [ ] `kondor/__main__.py` and `kondor/app/` have the modules of item 1, and `kondor/app/qmltypes.py` registers the three singletons.
- [ ] `python3 scripts/build.py && python3 -m kondor` shows the browser window with the Breeze style; `QT_QPA_PLATFORM=offscreen timeout 15 python3 -m kondor` (isolated XDG home) prints no QML errors (`ReferenceError`, `TypeError`, `Cannot assign…`, `is not a type`).
- [ ] Without a staged build, `python3 -m kondor` prints the `run python3 scripts/build.py` message and exits 1.
- [ ] `--help`, `--version`, `--private`, `--new-window`, `--new-instance` and `--load-extension` behave as in the C++ app.
- [ ] A second launch on the same profile forwards its URLs to the running instance, whether the running one is the C++ or the Python app (tests for Python ↔ Python, manual test for C++ ↔ Python), and the message bytes equal the C++ ones (test).
- [ ] Closing the last window exits with code 0, with no crash and no warning on stderr.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports three more classes checked than on the base, with no problems.
- [ ] Every C++ case of the eight test files in "Context" has its pytest twin, and the new tests of item 10 exist and pass with `scripts/run-pytests.sh`.
- [ ] Privacy: a private launch opens or reuses only a private window, and restored windows are never private (tests).
- [ ] The `build` job is green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt`, `scripts/build.py`, `scripts/check-qml-api.py` or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch. Every app run uses the same isolated profile: `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` and `XDG_STATE_HOME` under one temp folder (AGENTS.md), downloads into it too.

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && scripts/run-pytests.sh && python3 scripts/check-qml-api.py`: all pass, and the last reports three more classes than `main`.
2. **The Python app runs:** `python3 -m kondor` on the real display.
   1. The window has the Breeze style, the system colors, the same tool bar, tab strip and main menu as the C++ build from `main`.
   2. Load two sites in two tabs, open Settings, About Kondor Browser (version `0.2.0`, the Components tab filled, the license window shows the GPL) and the History and Bookmarks windows.
   3. Open a new window (Ctrl+N) and a private window (Ctrl+Shift+P); the private one says "Private Browsing" in its title.
   4. From a terminal, run `python3 -m kondor https://kde.org`: it opens a tab in the running window and exits; `python3 -m kondor --private https://kde.org` opens it in the private window.
   5. Close every window: the process exits with 0 and stderr shows no crash or warning. Ctrl+C in the terminal also ends it.
3. **C++ ↔ Python:** start the C++ app built from `main` on the same profile, then `python3 -m kondor https://example.com`: the C++ window opens the tab and the Python process exits. Swap them (Python running, `./build/kondor https://example.com`): the Python window opens the tab.
4. **Session restore and data from the C++ app:** with the umbrella's manual-test steps 1 and 2 (data made by the C++ app, "When Kondor starts: Restore previous session"), the Python app shows the same tabs, history, bookmark, saved password (KWallet), extension and settings.
5. **Extensions from the command line:** `python3 -m kondor --new-instance --load-extension pytests/data/extension` loads the unpacked extension; `python3 -m kondor <path>/sample.kondorext` (packed from `pytests/data/extensions/sample`) opens Settings → Extensions with the install preview.
6. **Offscreen smoke test:** `QT_QPA_PLATFORM=offscreen timeout 15 python3 -m kondor`: no QML errors.
7. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- Packaging and CI of the real Python app (AppImage, Flatpak, the `kondor` launcher), the installed location of the staged build, converting the spell-check dictionaries, `pyside6-lupdate`, deleting the C++ and docs changes: phase 12 (#174).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, `scripts/build.py`, `scripts/check-qml-api.py`, the quality checker or the workflows. If the app cannot run without such a change (for example a QML file that only works with the C++ types, or a resource `build.py` does not stage), ask first (`question`).
- Changes to `kondor/` outside `kondor/__main__.py` and `kondor/app/`. A bug found in an earlier phase's module while wiring the app is reported with `question` first; if the architect agrees, it is fixed in this PR with a test.
- New command-line options, new environment variables, translated command-line help texts, or a different single-instance protocol.
- The QA parity agent (#217), which compares the two apps after this phase.

## Dependencies

#167 (phase 5: bookmarks), #172 (phase 10: `ExtensionCatalog.start_auto_update()`) and #218 (phase 10b: `ExtensionBridge`, so `PageScriptBridges.qml` loads), which together close every earlier phase. Umbrella #162. The QA agent (#217) and phase 12 (#174) wait for this phase.

## Prototype

None: no UI changes.

## Decisions

| Question | Decision |
| --- | --- |
| Where does the Python app find its QML and resources? | In the staged build `build/python/` next to the package (`stagedbuild.py`), loaded before the app identity because the window icon and translations live in `kondor.rcc`. Phase 12 adds the installed location; no environment variable is added now. |
| How does the Python app know its version? | `PROJECT_VERSION` in `stagedbuild.py`, with a test that it equals the CMake project version and the `pyproject.toml` version. There is no pip install, so `importlib.metadata` has nothing to read. |
| `/proc/self/exe` is the Python interpreter: where are the dictionaries looked for? | Relative to the staged build, with the same two candidate paths as the C++ build. `build.py` creates them in phase 12; until then the variable stays unset, as in a C++ build without dictionaries. |
| Why read `licenseText` lazily? | The singleton is created when its type is registered. In the tests that can precede loading `kondor.rcc`; the QML-visible value is the same. |
| Does the Python tool bar test keep `ExtensionManagerStub.qml`? | No. The stub exists because the C++ test target does not link the extensions; the real Python `ExtensionManager` is registered for every test, and a second registration of the name would conflict. |
| Why `signal.SIGINT` → `SIG_DFL`? | Python's default handler only raises `KeyboardInterrupt` when Python code runs, so Ctrl+C would do nothing while Qt's loop runs. The default action ends the process like the C++ app. |
| How are windows kept alive and tracked? | The manager holds the window objects (Python references keep them from being garbage-collected) and drops them on `destroyed`; `shiboken6.isValid` replaces `QPointer::isNull`. A test checks a window survives `gc.collect()`. |
| How is `WindowManager` tested when C++ has no test for it? | Through a `StubWindowManager` that overrides `load_component()` with an inline `Window` stub, so the launch rules (privacy, reuse, packages, session restore) are tested without the real `BrowserWindow`. `test_appmain.py` covers the real window. |
| Does the app walk the package to register types? | No: an explicit `FEATURE_TYPES` tuple, checked by a test against the module walk the tests use, so a forgotten feature fails CI instead of at run time. |
| PySide6 cannot declare `StartupArgs.startupUrls` as `QList<QUrl>`; which type does the Python twin use? | `Property("QVariantList", …)`, holding `QUrl` values. QML sees both as an array of URLs, and no QML file reads the property. `scripts/check-qml-api.py` now treats any C++ `QList<T>` property as matching a Python `QVariantList` (architect change, with tests in `scripts/tests/test_qmlapi.py`). |
