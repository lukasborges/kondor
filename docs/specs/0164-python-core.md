# Python port 2/12: Core (#164)

> **Issue:** [#164](https://github.com/lukasborges/kondor/issues/164) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 8 and 9, "Rules for every phase") and the phase 1 spec [`0163-python-toolchain-proof.md`](0163-python-toolchain-proof.md) first. This file details phase 2 and must follow the umbrella. Only the architect edits it.

## Objective

Port `src/core/` to Python in `kondor/core/`, and port `tests/core/` to `pytests/core/`:

- **Same QML API:** `Settings`, `Notifier` and `FileHelper` are QML singletons in `Kondor` 1.0. `check-qml-api.py` pairs all three with their C++ twins.
- **Same data:** the Python `Settings` reads and writes the same `~/.config/KDE/Kondor.conf` as the C++ app. The Python `Database` opens, migrates and uses the same `kondor.sqlite`.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Phase 1 (#163, merged in 8f52e6d)** added:
  - `pyproject.toml`;
  - `kondor/core/qmlregistration.py` (`QmlKind`, `QmlType`, `register()`);
  - `pytests/conftest.py` (`staged_build`, `staged_resources`, `qml_engine`) and `pytests/qmlsupport.py` (`captured_messages`, `create_object`);
  - `scripts/build.py`, `scripts/check-qml-api.py`, the Python rules of `scripts/check-code-quality.py`;
  - the `python` job in `build.yml`.

  `check-qml-api.py` prints `0 classes checked, 44 C++ classes not ported yet` today.
- **`src/core/`** (976 lines). Nothing in it depends on another feature folder:

  | C++ file | What it does |
  | --- | --- |
  | `filehelper.{h,cpp}` | QML singleton `FileHelper`: `sanitizeFileName`, `suggestedFileUrl`, `tempPdfPath` (one `QTemporaryDir` `kondor-print-XXXXXX` and a counter), `readerResource` (only `Readability.js`, `Readability-readerable.js` and `template.html` from `:/reader/`), `openFile` (`QDesktopServices`) |
  | `notifier.{h,cpp}` | QML singleton `Notifier`: `notify(title, body, iconName)` calls `Notify` on `org.freedesktop.Notifications`, blocking. The arguments are the app display name, `0u`, the icon (`$FLATPAK_ID`, or `kondor`, when `iconName` is empty or `kondor`), title, body, an empty `QStringList`, an empty `QVariantMap` and `5000` |
  | `database/database.{h,cpp}` | plain class `Database` (not a `QObject`): `instance()` opens `AppDataLocation/kondor.sqlite` (connection `kondor`, driver `QSQLITE`), probes it with `PRAGMA user_version`, and migrates it in one transaction to version 5 |
  | `database/databasemigrations.{h,cpp}` | the steps: 1 history, 2 bookmarks table + root folders, 3 favicons, 4 default bookmarks, 5 extension storage |
  | `database/defaultbookmarks.{h,cpp}` | the default bookmark tree. Folder titles are `QT_TRANSLATE_NOOP("DefaultBookmarks", …)` |
  | `database/sql.{h,cpp}` | namespace `Sql`: `run`, `ids`, `inTransaction`, `idOrNull` |
  | `settings/settings.{h,cpp}` | QML singleton `Settings`: 23 stored options (one `Option{key, name, changed}` each), `downloadDirectoryValid`, invokables `defaultValue`, `availableSpellCheckLanguages`, `searchUrlTemplate`, `searchEngineName`, `refreshDownloadDirectory` |
  | `settings/settingsdefaults.{h,cpp}` | the default of every option, by name |
  | `settings/searchengines.{h,cpp}` | built-in engines and the custom-URL rule |
  | `settings/spellcheckdictionaries.{h,cpp}` | `*.bdic` files in `$QTWEBENGINE_DICTIONARIES_PATH` → `{code, name}` entries sorted by name |

- **`tests/core/`:**

  | C++ test | Cases |
  | --- | --- |
  | `tst_filehelper.cpp` | `keepsHashAndPercent`, `keepsSpaces` |
  | `tst_database.cpp` | `upgradesVersionOneFileKeepingHistory` |
  | `tst_settings.cpp` + `settingsharness.h` | `defaultValue` (data-driven), `freshSettingsUseDefaults`, `storageKeysStayTheSame` (data-driven over `kStorageRows`), `readerFontSizeIsClamped` |
  | `tst_singletons.cpp` | compile-time check that no singleton is default-constructible (#159) |

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior and edge cases as the C++, with the Python conventions of umbrella item 3. A C++ helper namespace becomes a module of functions.

### 1. Layout

```
kondor/core/
  __init__.py                (empty, from phase 1)
  qmlregistration.py         (phase 1, unchanged)
  qmltypes.py
  filehelper.py
  notifier.py
  database/
    __init__.py              (empty)
    database.py
    databasemigrations.py
    defaultbookmarks.py
    sql.py
  settings/
    __init__.py              (empty)
    settings.py
    settingsoptions.py
    settingsdefaults.py
    searchengines.py
    spellcheckdictionaries.py
```

`settingsoptions.py` is the only new module name. It holds the option table that `settings.cpp` keeps in its anonymous namespace, so `settings.py` stays under 200 lines. Further splits for the limits are allowed if they keep the C++ base names for the existing modules.

### 2. `qmltypes.py`

```python
QML_TYPES: tuple[QmlType, ...] = (
    QmlType(FileHelper, "FileHelper", QmlKind.SINGLETON),
    QmlType(Notifier, "Notifier", QmlKind.SINGLETON),
    QmlType(Settings, "Settings", QmlKind.SINGLETON),
)

def register_types() -> None:
    register(QML_TYPES)
```

Importing `qmltypes.py` must not create any instance: `check-qml-api.py` imports it without a `QCoreApplication`.

### 3. Singletons

- `FileHelper`, `Notifier` and `Settings` each have `instance()`. It returns one module-level object and creates it on the first call (umbrella item 3).
- **`Database.instance()`** works as in C++. It stores the new object as the instance **before** it opens and migrates the file, because the migrations call `sql.run()`, and `sql.run()` calls `Database.instance()`.
- **`Database.reset_instance()`** closes the connection, calls `QSqlDatabase.removeDatabase("kondor")` and forgets the instance. The next `instance()` then opens the file from the current paths again. Tests use it (pytest runs all tests in one process, while each C++ test is its own process). The app does not call it in this phase.

### 4. `Settings`

- **Storage:**
  - `QSettings("KDE", "Kondor")`, with the same keys, types and defaults as `settings.cpp` and `settingsdefaults.cpp`.
  - Each value is read once, in the constructor: `value(key, default, type=…)` with the option's type.
  - A setter returns early when the value does not change. Otherwise it stores the value, writes it with `setValue` + `sync()`, and emits the option's signal.
- **Option table** (`settingsoptions.py`): one row per C++ `Option`, with its key, its QML name, its Python value type and the name of its `…Changed` signal. `settings.py` builds the 23 stored properties from it, instead of 23 hand-written getter/setter pairs.
- **Property types** must match the C++ types for `check-qml-api.py`:
  - use `"QStringList"` for the string lists (a Python `list` becomes `QVariantList`, which does not match);
  - use `QDateTime` for `adBlockLastUpdate`.
- **Special cases, as in C++:**
  - `readerFontSize` is clamped to 12…32 on read and on write.
  - `downloadDirectory` returns the stored value only when it is an existing folder, and otherwise `QStandardPaths.writableLocation(DownloadLocation)`. `downloadDirectoryValid` (read-only, notify `downloadDirectoryChanged`) tells which.
  - `refreshDownloadDirectory()` only emits `downloadDirectoryChanged`.
  - `spellCheckLanguages` defaults to the system locale (`_` replaced by `-`) when a dictionary with that code exists, and otherwise to `["en-US"]`.
- **Invokables:** `defaultValue(name)` (result `QVariant`, an invalid/`None` value for an unknown name), `availableSpellCheckLanguages()` (result `QVariantList` of `{"code", "name"}` maps), `searchUrlTemplate()`, `searchEngineName()` and `refreshDownloadDirectory()`.
- **Spell-check language names:**
  - Build them as `spellcheckdictionaries.cpp` does: `QLocale.nativeLanguageName()` with its first letter upper-cased, then ` (<nativeTerritoryName>)` when there is one, or the bare code when the language name is empty.
  - Sort with `QCollator()` on the default locale, the Python counterpart of `localeAwareCompare`.
- **Compatibility with the C++ file** is the point of this phase. See the test fixtures in item 8.

### 5. `Database` and `sql`

- **Driver:** QtSql (`QSqlDatabase`, driver `QSQLITE`, connection name `kondor`), not Python's `sqlite3`. Later phases port C++ code that uses `QSqlQuery` (`lastInsertId`, `value(n)`), so the port stays 1:1.
- **Opening:**
  - Create the folder, then open `QStandardPaths.writableLocation(AppDataLocation) + "/kondor.sqlite"`.
  - Probe the file with `PRAGMA user_version`. On failure, warn with `qWarning` (same texts as C++), close the file and stay invalid.
  - Migrate in one transaction: run each step whose version is above the file's `user_version`, then set `PRAGMA user_version = 5`.
- **Migration steps:** the same statements as `databasemigrations.cpp`, character for character, so a file migrated by Python matches one migrated by C++.
  - Root folders and default bookmarks get `created_at` = the current time in ms since the epoch.
  - Default folder titles go through `QCoreApplication.translate("DefaultBookmarks", title)`. Bookmark titles are not translated.
- **`defaultbookmarks.py`:**
  - Use the same tree, order, titles and URLs. Each node is a `NamedTuple` (`title`, `url: str | None`, `children`), and a node is a folder when `url is None`.
  - Mark the folder titles with `QT_TRANSLATE_NOOP("DefaultBookmarks", …)`, so `pyside6-lupdate` keeps the `DefaultBookmarks` context in phase 12.
- **`sql.py`** (snake_case, nothing here is seen by QML):
  - `run(statement: str, values: Sequence[object] = ()) -> QSqlQuery | None`: `None` when the database is invalid, or when prepare or exec fails;
  - `ids(statement, values=()) -> list[int]`;
  - `in_transaction(work: Callable[[], bool]) -> bool`: commit when `work()` is true and the commit succeeds, and otherwise roll back and return false;
  - `id_or_null(id: int) -> int | None`.

### 6. `Notifier`

- **The call:** the same blocking `Notify` call on the session bus as `notifier.cpp`, with the same eight arguments. If the interface is not valid, it returns silently.
- **D-Bus types:** the call must reach the server with the exact `Notify` signature, `susssasa{sv}i`.
  - Python `int`s default to 64-bit, so `replaces_id` must be sent as `uint32` and `expire_timeout` as `int32`.
  - An empty Python list or dict must arrive as `as` and `a{sv}`.
  - How to type them in PySide6 (`QDBusArgument`, typed `QDBusMessage` arguments, …) is the developer's choice.

### 7. `FileHelper`

- **`sanitizeFileName`:**
  - Trim the title. Replace each of `/\:*?"<>|` and each character below U+0020 with `_`.
  - Keep the first **100 UTF-16 code units** (`QString::left`), then trim again. A character that the cut would split in half (a surrogate pair) is dropped.
  - An empty result becomes `page`.
- **`suggestedFileUrl`:** `QUrl.fromLocalFile(QDir(directory).filePath(sanitized + extension))`, so `#` and `%` stay in the path.
- **`tempPdfPath`:** one `QTemporaryDir(QDir.tempPath() + "/kondor-print-XXXXXX")`, kept for the object's lifetime, and `print-<n>.pdf` with an increasing counter. It returns an empty string when the folder is not valid.
- **`readerResource`:** only the three allowed names, read as UTF-8 from `:/reader/`. Any other name, or a file that cannot be opened, gives an empty string.
- **`openFile`:** `QDesktopServices.openUrl(QUrl.fromLocalFile(path))`.

### 8. Tests: `pytests/core/`

Each C++ case becomes a test with the same intent (umbrella item 9). Test functions have at most 20 lines.

- **`pytests/conftest.py` additions:**
  - **`isolated_profile`** (session, `autouse`): before the first test, it points `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` at folders under `tmp_path_factory`. It also unsets `QTWEBENGINE_DICTIONARIES_PATH`. pytest then never reads or writes the maintainer's real profile (AGENTS.md).
  - **`kondor_types`** (session): calls `register_types()` of every `kondor/**/qmltypes.py` once. It finds them with `pkgutil.walk_packages` over `kondor`, so later phases need no change here.
- **`test_filehelper.py`:**
  - `test_keeps_hash_and_percent` and `test_keeps_spaces` (ported);
  - `test_cuts_long_titles_at_100_code_units`: a title of 99 `a` plus `😀` gives 99 `a`;
  - `test_reader_resource_reads_allowed_names_only`: `Readability.js` is non-empty from the staged `kondor.rcc`, and `../LICENSE` is empty.
- **`test_database.py`** (each test calls `Database.reset_instance()` and deletes the file first):
  - `test_upgrades_version_one_file_keeping_history` (ported). It writes a version-1 file with one history row through a separate connection, then checks: the history row is kept, `user_version` is 5, `favicons` and `extension_storage` exist and are empty, and both root folders exist.
  - `test_fresh_file_gets_the_default_bookmarks`: a new file has the `defaultbookmarks.py` tree under the `toolbar` folder, with the same titles, URLs and positions.
  - `test_unusable_file_leaves_the_database_invalid`: a file with non-SQLite bytes gives `is_valid()` false, and `sql.run()` gives `None`.
- **`test_settings.py`** + **`settingsrows.py`** (the twin of `settingsharness.h`):
  - A fixture clears the isolated `Kondor.conf` and returns a new `Settings()`. That object is not registered with QML; the singleton check is in `test_singletons.py`.
  - `test_default_value` (parametrized over the same rows as `defaultValue_data`), `test_fresh_settings_use_defaults`, `test_storage_keys_stay_the_same` (parametrized over the rows of `settingsharness.h`) and `test_reader_font_size_is_clamped` (all ported).
  - **The `adBlockLastUpdate` row** uses `QDateTime.fromSecsSinceEpoch(1000000, QTimeZone.UTC)`. A local time would make the fixture below depend on the time zone of the machine that wrote it.
  - `test_reads_the_file_written_by_cpp`: copy `pytests/data/core/Kondor.conf` into the isolated config folder, create `Settings()`, and check every property against its row. The exception is `downloadDirectory`: its row value `changed` is not a folder, so it falls back to the download location, and `downloadDirectoryValid` is false.
  - `test_writes_the_same_file_as_cpp`: set every row on a cleared `Settings()`. The written `Kondor.conf` has the same lines as the fixture (QSettings sorts groups and keys).
  - `test_reads_empty_lists_written_by_cpp`: with `pytests/data/core/Kondor-empty-lists.conf`, every string-list property is `[]`, including `spellCheckLanguages`, whose default is not empty.
  - `test_lists_spell_check_languages_by_name`: point `QTWEBENGINE_DICTIONARIES_PATH` at a temp folder with empty `en-US.bdic` and `pt-BR.bdic`. The result is two `{"code", "name"}` entries in the order `en-US`, `pt-BR`, and the `pt-BR` name is `Português (Brasil)`.
  - `test_search_url_template_uses_custom_url_only_with_placeholder`: `custom` + `https://x/?q=%1` gives that URL and an empty engine name; `custom` + `https://x/` gives DuckDuckGo's.
- **The two fixtures** come from the **C++** `Settings`, not from Python:
  - `pytests/data/core/Kondor.conf`: every option of `settingsharness.h` set to its row value, with the UTC `adBlockLastUpdate` above.
  - `pytests/data/core/Kondor-empty-lists.conf`: every string-list option set to an empty `QStringList`.

  The developer writes them with a throw-away local change to `tests/core/tst_settings.cpp` (set the values, copy the `.conf`), runs it on an isolated profile, then discards the change. Nothing in `tests/` is committed. The PR body says how the files were made.
- **`test_notifier.py`:**
  - **`test_notify_sends_the_freedesktop_signature`:** a helper script `pytests/core/fakenotifications.py`, started with `subprocess` (`python3 -I`), owns `org.freedesktop.Notifications` on the session bus. It exports `Notify` and prints the received message signature and arguments as one JSON line, then exits.
  - The test calls `Notifier.instance().notify("Title", "Body", "")`. It expects the signature `susssasa{sv}i` and the arguments `[<display name>, 0, "kondor", "Title", "Body", [], {}, 5000]`.
  - The helper is a separate process because the call blocks the test's thread.
  - The test is **skipped** when the helper cannot own the name, as on a Plasma desktop where `plasmashell` owns it. So it never sends a real notification on the maintainer's desktop. CI runs it on a private bus (item 9).
  - `test_icon_name_kondor_uses_flatpak_id`: with `FLATPAK_ID=io.github.lukasborges.Kondor`, an icon of `kondor` is sent as the Flatpak id, and `dialog-information` is sent unchanged. Test the icon function directly, with no D-Bus.
- **`test_singletons.py`** (umbrella item 3, the Python twin of `tst_singletons.cpp`): it uses `kondor_types`, and for **every** `SINGLETON` entry of every `QML_TYPES`, `qml_engine.singletonInstance("Kondor", name) is type_class.instance()`. It is parametrized over the entries, so phases 3-11 add their singletons without editing it.
- **`test_core_qml.py`:** `import Kondor; QtObject { property string engine: Settings.searchEngine; property string name: FileHelper.sanitizeFileName("a/b") }` loads from the staged module with no warnings, and reads `duckduckgo` and `a_b`.

### 9. CI: the `python` job in `build.yml`

- Add `dbus-daemon` to its dnf list.
- Change the Pytest step to `QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests`, so `test_notifier.py` gets a private session bus. The timeout stays the same.
- Nothing else in `build.yml` changes. The `build` job is untouched.

### 10. API check result

After this phase, `python3 scripts/check-qml-api.py` prints `3 classes checked, 41 C++ classes not ported yet` and exits 0.

## Acceptance criteria

- [ ] `kondor/core/` has the modules of item 1, and `kondor/core/qmltypes.py` registers `FileHelper`, `Notifier` and `Settings` as singletons.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` prints `3 classes checked, 41 C++ classes not ported yet`.
- [ ] Every C++ case of `tests/core/` has its pytest twin, and the extra tests of item 8 exist and pass: `QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests`.
- [ ] The Python `Settings` reads `Kondor.conf` and `Kondor-empty-lists.conf`, both written by the C++ app, and writes a file with the same lines as the first.
- [ ] A version-1 `kondor.sqlite` is migrated to version 5 with its history kept. A fresh one gets the default bookmarks, and an unusable one leaves the database invalid.
- [ ] `test_notifier.py` passes in CI with the `susssasa{sv}i` signature, and is skipped, not failed, on a desktop that owns `org.freedesktop.Notifications`.
- [ ] `test_singletons.py` checks every registered singleton through `engine.singletonInstance`.
- [ ] The `python` job runs pytest under `dbus-run-session` and is green. The `build` job is green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt`, `release.yml`, `flatpak.yml` or the Kondor manifest. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md):

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests && python3 scripts/check-qml-api.py`: all pass, and the last prints `3 classes checked, 41 C++ classes not ported yet`.
2. `QT_QPA_PLATFORM=offscreen pytest pytests/core/test_notifier.py -rs` in the Plasma session: the signature test is skipped with a reason saying the name is taken. No notification appears.
3. **Profile written by C++:** build `main` with CMake and start `./build/kondor` on the temporary profile. Change the search engine and the home page in Settings, visit a page, then quit. With the same `XDG_*` variables, a short Python snippet run from the PR checkout (`QCoreApplication` with organization `KDE` and application `Kondor`) must show:
   - `Settings.instance()` returns the changed search engine and home page;
   - `Database.instance().is_valid()` is true;
   - `sql.ids("SELECT id FROM history")` is not empty.
4. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- Any class outside `src/core/`: `ProfileManager`, `FaviconStore`, the history, bookmark and download managers and the rest wait for their phases. So do `ExtensionStorage` and the other users of `sql`, beyond the migrations.
- Calling `register_types()` from an app entry point. `kondor/__main__.py` comes in phase 11.
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests or the `build` job.
- Changes to `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker, unless a phase-2 file shows a bug in them. In that case, ask first (`question`).
- Translating Python strings, or running `pyside6-lupdate` (phase 12).

## Dependencies

#163 (toolchain, merged). Umbrella #162.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| QtSql or Python's `sqlite3` for `Database`? | QtSql (`QSQLITE`, connection `kondor`). Later phases port code that uses `QSqlQuery` (`lastInsertId`, `value(n)`), and one driver keeps the port 1:1. Rejected: `sqlite3`, which would rewrite every query of phases 4-9. |
| How do tests get a fresh `Database` in one pytest process? | `Database.reset_instance()` closes the connection, removes it and forgets the instance. Rejected: a public constructor with a path, because `sql.run()` must reach the same object through `instance()`, as in C++. |
| How do tests get a fresh `Settings`? | They build a new `Settings()`, which is never registered with QML. The #159 check is `test_singletons.py`, on the registered instance. |
| How is "same settings file" proven? | With two `.conf` fixtures written by the **C++** `Settings`: Python must read both, and must write the same lines as the first. The timestamp row is in UTC, so the fixtures do not depend on a time zone. A Python round trip alone would not prove compatibility. |
| Why a D-Bus test for `Notifier`, when C++ has none? | Python ints default to 64-bit on D-Bus, so a careless port sends `x` instead of `u`/`i` and the server rejects `Notify`. That risk exists only in Python. The fake server runs in a subprocess (the call blocks), and the test is skipped when the real notification server owns the name, so it never notifies the maintainer's desktop. |
| `sanitizeFileName` cuts at 100 characters: code points or UTF-16 units? | UTF-16 units, as `QString::left(100)`. A surrogate pair the cut would split is dropped, so the result is never invalid text. |
| `scripts/qmlapi/pythonside.py` calls `staticMetaObject()`, but on PySide6 classes it is an attribute, so the first real `qmltypes.py` raises `TypeError`. Fix it in this PR? | Yes: drop the `()` in the #164 PR. It is the "phase-2 file shows a bug" case of "Out of scope"; the script must then print `3 classes checked, 41 C++ classes not ported yet`. |
| PySide6 cannot put a `uint32` in a plain `QDBusMessage`; typed `Q_ARG`s through `QMetaObject.invokeMethod` on the introspected `QDBusInterface` only reach servers whose introspection carries Qt's `QtTypeName` annotation for `a{sv}`. Accept the gap, or add a D-Bus library? | Accept it (option a). Kondor targets Plasma, whose `plasmashell` has the annotation; the architect confirmed a non-Qt server (dbus-python, same `susssasa{sv}i` signature, no annotation) receives no call. `notify()` stays silent there, never raises or warns. The PR lists it under "Differences". Rejected: `python3-gobject` (`Gio` + `GLib.Variant`), a new runtime dependency in the AppImage and the Flatpak for desktops Kondor does not target; a fallback that skips the call, which is option a under another name. |
