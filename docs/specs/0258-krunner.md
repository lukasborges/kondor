# KRunner: find open tabs, bookmarks and history from Alt+Space (#258)

> **Issue:** [#258](https://github.com/lukasborges/kondor/issues/258) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

In KRunner (Alt+Space, or the Application Launcher's search), typing a few letters lists Kondor's
**open tabs**, then its **bookmarks**, then its **history**. Choosing an open tab switches to it
and raises its window. Choosing a bookmark or a history entry opens it in a new tab of Kondor.
Private tabs and private windows never show up.

## Context

- **App:** Python + PySide6 since #174 (`src/kondor/`); `qml/` is the UI. There is no C++ twin.
- **KRunner D-Bus runners:** KRunner (KF6, `kf6-krunner`) loads every `*.desktop` file in
  `share/krunner/dbusplugins/` (system, `~/.local/share`, and Flatpak exports). A file with
  `X-Plasma-API=DBus` names a D-Bus service and object path; while that name is on the session bus,
  KRunner calls the interface `org.kde.krunner1` on it:
  - `Match(s query) → a(sssida{sv})`: one struct per result: match id, text, icon name,
    category relevance (`int`, 0–100), relevance (`double`, 0–1), properties (`subtext` `s`,
    `urls` `as`, `actions` `as`, `icon-data` `(iiibiiay)`);
  - `Run(s matchId, s actionId)`: the user chose a result (`actionId` is empty without actions);
  - `Actions() → a(sss)`: the actions a result may offer;
  - `SetActivationToken(s token)`: called right before `Run` (Plasma 6) with an XDG activation token
    so the runner may raise its window;
  - `Teardown()`: the KRunner session ended.
  Examples on the maintainer's machine: `/usr/share/krunner/dbusplugins/org.kde.neochat.desktop`
  and `plasma-runner-browsertabs.desktop`.
- **QtDBus cannot serve `Match` from Python.** PySide6 has no way to marshal an array of structs:
  `QDBusArgument.beginArray()` only takes element types with a registered D-Bus signature, and a
  hand-built `(sssida{sv})` array aborts with "the expected type here is array … signature 'aav'"
  (tried while writing this spec). **`jeepney`** (pure Python, Fedora `python3-jeepney`, already a
  dependency of `python3-keyring`) marshals any signature; a probe with a jeepney blocking connection,
  a non-blocking socket and a `QSocketNotifier` on its file descriptor answered
  `gdbus call … org.kde.krunner1.Match` with the right `a(sssida{sv})` reply inside a Qt event loop.
- **Windows and tabs:** `WindowManager` (`src/kondor/app/windows/windowmanager.py`, 138 lines)
  keeps `self._windows` (the `BrowserWindow` objects); each window has `privateWindow` and
  `tabModel` (QML properties, read with `window.property(...)`). A `TabModel`
  (`src/kondor/browser/tabs/tabmodel.py` → `tabmodelrows.py`) has `rowCount()`, `data()` (role
  `tab`), `indexOfTab(tab)` and `setCurrentIndex(index)`. A `Tab` has `title`, `url`, `isPrivate`
  and `newTabPage`.
- **Opening URLs from outside:** `windowlaunch.handle_single_instance_message(manager, message)`
  (`src/kondor/app/windows/windowlaunch.py`) opens `message.urls` in new tabs of the active normal
  window (or a new normal window) and raises it with `message.activation_token` through
  `raise_window()` (`src/kondor/app/instance/windowactivation.py`).
- **Matching code used by the address bar:** `BookmarkManager.search(text, limit)` →
  `bookmarkqueries.search` (`url`, `title`; title matches first) and `historysearch.suggest(text,
  limit)` (`url`, `title`; most visited first). History holds normal-tab visits only.
- **Favicons:** `FaviconStore.instance().image_for_host(host) → QImage` (null when unknown), filled
  only from normal tabs (#45, #267).
- **Startup:** `open_windows()` in `src/kondor/app/startup/appstartup.py` sets up favicons and the
  `WindowManager`, then opens the startup windows; `shut_down()` releases the windows.
- **Packaging:** `scripts/staging/install.py` (`PACKAGING_FILES`) installs `packaging/*` files under
  the prefix; the Flatpak manifest is `packaging/flatpak/io.github.lukasborges.Kondor.yml` (KDE
  runtime 6.11 + PySide BaseApp, `rename-icon: kondor`); the AppImage is built by
  `packaging/appimage/prepare-appdir.sh`. Flatpak 1.18 exports `share/krunner/dbusplugins` files
  whose name starts with the app id. A Flatpak app may own its app id and every name below it on the
  session bus without `--own-name`.

## Design / behavior

### 1. The runner file (packaging)

New file `packaging/io.github.lukasborges.Kondor.krunner.desktop` (the app id prefix lets Flatpak
export it):

```ini
[Desktop Entry]
Type=Service
Name=Kondor Browser
Comment=Find open tabs, bookmarks and history in Kondor Browser
Icon=kondor
X-KDE-ServiceTypes=Plasma/Runner
X-KDE-PluginInfo-EnabledByDefault=true
X-Plasma-API=DBus
X-Plasma-DBusRunner-Service=io.github.lukasborges.Kondor.KRunner
X-Plasma-DBusRunner-Path=/KRunner
X-Plasma-Request-Actions-Once=true
X-Plasma-Runner-Min-Letter-Count=3
```

- `Name[xx]` copies every translated `Name[xx]` of `packaging/kondor.desktop`; `Comment[xx]` is
  translated into the same languages (KDE terminology: "tabs", "bookmarks", "history" as in the
  app's `.ts` files).
- `scripts/staging/install.py`: add `("io.github.lukasborges.Kondor.krunner.desktop",
  "share/krunner/dbusplugins")` to `PACKAGING_FILES`.
- Flatpak manifest: after `scripts/build.py --install /app`, rewrite the installed file's
  `Icon=kondor` to `Icon=io.github.lukasborges.Kondor` (the renamed icon) with a `sed -i` build
  command. No new `finish-args`: the app already owns names below its app id.
- No D-Bus activation file: when Kondor is not running, KRunner simply gets no Kondor results
  (see "Decisions").

### 2. Dependency: `jeepney`

- Python import `jeepney` (≥ 0.8), used **only** in `runnerbus.py` (3).
- `README.md`: add `python3-jeepney` to the Fedora `dnf install` line and `jeepney` to the
  dependency list.
- `.github/workflows/build.yml` and `.github/workflows/release.yml`: add `python3-jeepney` to the
  `dnf` lists.
- AppImage (`prepare-appdir.sh`): copy `/usr/lib/python$python_version/site-packages/jeepney` into
  the AppDir's `site-packages` (it is pure Python).
- Flatpak manifest: a module before `kondor` that installs the jeepney wheel from PyPI
  (`type: file` source with its `sha256`, `pip3 install --no-index --no-deps --prefix=/app`).
- `pyproject.toml`: a `[[tool.mypy.overrides]]` with `module = ["jeepney", "jeepney.*"]` and
  `ignore_missing_imports = true` (jeepney ships no type hints); `runnerbus.py` turns jeepney
  values into typed Python values at its boundary so `mypy --strict` stays clean elsewhere.

### 3. The code: `src/kondor/app/krunner/`

New sub-feature folder `src/kondor/app/krunner/` (with `__init__.py`), tests in
`tests/app/krunner/`. Suggested split (each file ≤ 200 lines, functions ≤ 10 lines):

| File | Holds |
| --- | --- |
| `runnerbus.py` | `RunnerBus(QObject)`: the jeepney connection, the bus name, the `QSocketNotifier`, replies |
| `opentabs.py` | `OpenTab` (window, tab model, tab) and `open_tabs(windows) → list[OpenTab]` |
| `runnermatches.py` | `RunnerMatch` and `find_matches(query, tabs) → list[RunnerMatch]` |
| `runnericons.py` | `icon_data(url) → tuple \| None` from the favicon store |
| `krunnerservice.py` | `KRunnerService(QObject)`: `Match`, `Run`, `Actions`, `SetActivationToken`, `Teardown` |

**3.1 `RunnerBus`**

- Constants `SERVICE_NAME = "io.github.lukasborges.Kondor.KRunner"`, `OBJECT_PATH = "/KRunner"`,
  `INTERFACE = "org.kde.krunner1"`.
- `start() → bool`: open a blocking jeepney connection to the session bus
  (`open_dbus_connection(bus="SESSION")`), call `RequestName(SERVICE_NAME, 4)`
  (`DBUS_NAME_FLAG_DO_NOT_QUEUE`); if the reply is not `1` (primary owner), close the connection,
  log one `qInfo("Kondor: another instance answers KRunner")` and return `False`. On success, set
  the socket non-blocking and watch its file descriptor with a `QSocketNotifier` (`Read`).
  A missing session bus (no `DBUS_SESSION_BUS_ADDRESS`, connection refused) returns `False` with
  one `qWarning`; Kondor runs on without KRunner.
- On `activated`: read every complete message (`connection.receive(timeout=0)` until
  `TimeoutError`; jeepney keeps a partial message buffered). Ignore everything that is not a
  method call to `OBJECT_PATH` on `INTERFACE`; hand each such call (member + body) to a handler
  callable given to the constructor, and send what it returns:
  - a reply `(signature, body)` → `new_method_return(call, signature, body)`;
  - `None` for an unknown member → `new_error(call, "org.freedesktop.DBus.Error.UnknownMethod")`.
- `stop()`: disable the notifier and close the connection (the name is released with it).
- A disconnected bus (end of file on the socket) stops the runner quietly.

**3.2 Open tabs (`opentabs.py`)**

- `WindowManager` gets a public query `windows() → list[QObject]` (alive windows, in opening
  order).
- `open_tabs(windows)` returns one `OpenTab(window, tab_model, tab)` per tab, **skipping windows
  whose `privateWindow` is true and tabs whose `isPrivate` is true**, and tabs on the New Tab page
  or with an empty URL.

**3.3 Matching (`runnermatches.py`)**

- `RunnerMatch` (frozen dataclass): `match_id`, `kind` (`"tab"`, `"bookmark"`, `"history"`),
  `title`, `url` (`QUrl`), and for tabs the `OpenTab`.
- `find_matches(query, tabs)`:
  1. `query.strip()`; fewer than 3 characters → `[]`.
  2. **Open tabs:** a tab matches when every whitespace-separated word of the query appears,
     ignoring case (`casefold()`), in its title or its URL string. At most **8**, in window order
     then tab order.
  3. **Bookmarks:** `bookmarkqueries.search(query, 5)` (the same function the address bar uses
     through `BookmarkManager.search`).
  4. **History:** `historysearch.suggest(query, 5)`.
  5. **One result per URL:** a bookmark whose URL is an open tab's, or a history entry whose URL is
     an open tab's or a listed bookmark's, is dropped (compare `QUrl` values).
  6. Match ids: `"tab-<n>"`, `"bookmark-<n>"`, `"history-<n>"` (`n` = position in its group).
- The matching is pure Python over the given tabs and the database; it is tested without a bus.

**3.4 Icons (`runnericons.py`)**

- `icon_data(url)`: `FaviconStore.instance().image_for_host(url.host())`; a null image → `None`.
  Otherwise convert to `QImage.Format.Format_RGBA8888` and return
  `(width, height, bytesPerLine, True, 8, 4, bytes)` (the `icon-data` struct `(iiibiiay)`).
- **Fallback icon names** when there is no favicon: open tab `internet-web-browser`, bookmark
  `bookmarks`, history `view-history`. With a favicon the icon name is `""` and `icon-data` is set.

**3.5 `KRunnerService`**

- Singleton like `WindowManager` (`instance()`); owns a `RunnerBus` built with its `handle_call`.
- `start()` / `stop()`: start and stop the bus.
- **`Match(query)`**: `find_matches(query, open_tabs(WindowManager.instance().windows()))`; keep
  the result as `last_matches: dict[str, RunnerMatch]` (replacing the previous one) and reply
  `a(sssida{sv})` with, per match:
  - id = `match_id`; text = the title, or the URL's display string
    (`toDisplayString(QUrl.UrlFormattingOption.RemoveUserInfo)`) when the title is empty;
  - icon name and `icon-data` as in 3.4;
  - **category relevance:** open tab `100`, bookmark `70`, history `50`;
  - **relevance:** `1.0 - 0.01 * n` (`n` = position in its group), so KRunner keeps this order;
  - properties: `subtext` = the URL's display string, `urls` = `[url string]`, `actions` = `[]`.
- **`Actions()`**: reply `a(sss)` with an empty list.
- **`SetActivationToken(token)`**: keep the token for the next `Run`; reply with no body.
- **`Run(matchId, actionId)`**: look `matchId` up in `last_matches`; unknown id → do nothing.
  - **Open tab:** if the tab still exists (`shiboken6.isValid` on the window and the tab, and
    `tab_model.indexOfTab(tab) >= 0`), call `tab_model.setCurrentIndex(index)` and
    `raise_window(window, token)`; if it was closed meanwhile, open its URL as below.
  - **Bookmark / history:** `WindowManager.instance().handle_single_instance_message(
    SingleInstanceMessage(urls=[url], activation_token=token))` (a new tab in the active normal
    window, or a new normal window, raised).
  - Clear the stored token after use; reply with no body.
- **`Teardown()`**: clear `last_matches` and the token (no references to tabs are kept between
  KRunner sessions); reply with no body.
- The D-Bus calls run on the GUI thread (the socket notifier), so touching windows and tabs is safe.

### 4. Startup

- `appstartup.open_windows()`: after `open_startup_windows()`, call
  `KRunnerService.instance().start()`. `shut_down()` calls `KRunnerService.instance().stop()`
  before releasing the windows.
- A `--new-instance` Kondor (or a second profile) finds the name taken and runs without KRunner;
  the first instance keeps answering.

### 5. Privacy

- Private windows and private tabs are filtered out in `open_tabs()` (3.2); bookmarks and history
  never contain private-tab data; favicons are stored only from normal tabs.
- The runner writes nothing to disk. `last_matches` and the token live in memory and are cleared by
  `Teardown()`.

### 6. Strings, README

- **No new `qsTr()` strings:** KRunner shows page titles and URLs, and the group name comes from the
  runner file's translated `Name`. The runner file's `Comment` is translated in the file itself (1).
- **`README.md`:** in "Made for KDE", add **KRunner search**: find open tabs, bookmarks and history
  with Alt+Space. Add `python3-jeepney` to the Fedora dependencies (2).

### 7. Tests (pytest, through `scripts/run-pytests.sh`)

- `tests/app/krunner/test_opentabs.py`: private windows and private tabs are skipped; New Tab page
  and empty-URL tabs are skipped; window and tab order kept.
- `tests/app/krunner/test_runnermatches.py` (temporary database): short queries give nothing; a tab
  matches by title and by URL, every word must match, case ignored; order is tabs, bookmarks,
  history; limits 8/5/5; a bookmark open in a tab and a history entry that is bookmarked are not
  repeated; match ids per group.
- `tests/app/krunner/test_runnericons.py`: a stored favicon gives an RGBA `icon-data` tuple of the
  right size; an unknown host gives `None`.
- `tests/app/krunner/test_krunnerservice.py` (calls `handle_call` directly, no bus): `Match` reply
  signature `a(sssida{sv})` and fields (category relevance 100/70/50, decreasing relevance,
  `subtext`, `urls`, empty `actions`, fallback icon names); `Run` on a tab id selects that tab and
  raises its window with the token from `SetActivationToken`; `Run` on a closed tab and on a
  bookmark opens the URL through `handle_single_instance_message`; `Run` with an unknown id does
  nothing; `Teardown` forgets the matches; an unknown member returns `None`.
- `tests/app/krunner/test_runnerbus.py` (on the private bus of `run-pytests.sh`): `start()` owns
  `io.github.lukasborges.Kondor.KRunner`; a second `RunnerBus` returns `False`; a
  `gdbus call --session --dest io.github.lukasborges.Kondor.KRunner --object-path /KRunner
  --method org.kde.krunner1.Match kon` run with `QProcess` (wait with `qtbot.waitUntil`, never
  block the event loop) gets the handler's reply; an unknown method gets
  `org.freedesktop.DBus.Error.UnknownMethod`; `stop()` releases the name.
- Staging tests (next to `tests/test_staged_module.py`): `install.py` puts the runner file in
  `share/krunner/dbusplugins/`.

## Acceptance criteria

- [ ] With Kondor running (installed with `scripts/build.py --install ~/.local` or as a Flatpak),
      typing three or more letters of an open tab's title or URL in KRunner lists it with its
      favicon and URL; Enter switches to that tab and raises its window, also when it is in another
      Kondor window.
- [ ] Bookmarks and history entries that match are listed after the open tabs (tabs, then
      bookmarks, then history), each URL once; Enter opens it in a new tab of the active normal
      Kondor window and raises it.
- [ ] A private tab, or any tab of a private window, never shows up, whatever its title.
- [ ] With Kondor not running, KRunner shows no Kondor results and does not start Kondor.
- [ ] `packaging/io.github.lukasborges.Kondor.krunner.desktop` exists with translated `Name` and
      `Comment`, is installed to `share/krunner/dbusplugins/`, and the Flatpak build installs it
      with the app-id icon.
- [ ] `jeepney` is added to README, both workflows' `dnf` lists, the AppImage and the Flatpak
      manifest; `mypy --strict` passes.
- [ ] A second instance (`--new-instance`) starts normally and leaves KRunner to the first.
- [ ] README "Made for KDE" has the **KRunner search** bullet.
- [ ] The tests of "Design → Tests" exist and pass, with all Python checks of AGENTS.md
      (`ruff`, `mypy --strict`, `scripts/build.py`, `scripts/run-pytests.sh`,
      `scripts/check-qml-api.py`); the smoke test prints no QML errors;
      `scripts/check-code-quality.py --changed origin/main` is clean.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, as in `AGENTS.md`). For steps 5 and 6 only, copy the runner file to
`~/.local/share/krunner/dbusplugins/` so the desktop's KRunner finds it, and remove it afterwards:

1. Start Kondor, open `https://kde.org` and `https://example.com` in two windows, bookmark
   `https://www.qt.io`, visit `https://planet.kde.org` once and close that tab.
2. Without KRunner (works headless): `gdbus call --session --dest
   io.github.lukasborges.Kondor.KRunner --object-path /KRunner --method org.kde.krunner1.Match kde`
   → the `kde.org` tab first (category relevance 100), then `planet.kde.org` from history (50).
3. `gdbus call … --method org.kde.krunner1.Run tab-0 ""` → that tab becomes current and its window
   comes to the front.
4. Open a private window with a page titled "kde"; `Match kde` again → it is not listed.
5. On the desktop: `kquitapp6 krunner` (KRunner reloads its plugins on its next start), then
   Alt+Space, type `exam` → "Example Domain" under "Kondor Browser"; Enter switches to it.
6. Quit Kondor; `Match` now fails with "name has no owner", and Alt+Space `exam` shows no Kondor
   result and does not start Kondor.
7. Start `kondor --new-instance` next to a running Kondor: it starts, logs once that another
   instance answers KRunner, and KRunner keeps the first instance's tabs.

## Out of scope

- Starting Kondor through D-Bus activation from KRunner.
- KRunner actions on results (close tab, open in a new window, copy URL, open privately) and the
  `Actions` list beyond an empty reply.
- Search engine queries, "open URL", or a trigger word / prefix syntax (`X-Plasma-Runner-Syntaxes`).
- A Kondor setting to turn the runner off (KRunner's own settings in System Settings → Search →
  Plasma Search already do it).
- Matching passwords, downloads or extensions.
- KRunner support in the AppImage (it cannot install files on the host).
- Python-side translation infrastructure (no new translatable strings come from Python).

## Dependencies

- None open. Builds on #2 (bookmarks), #1 (history), #45/#267 (favicons), #14 (multiple windows),
  #15 (single instance and window raising) and #174 (Python app), all closed.

## Prototype

None: Kondor shows no new UI. KRunner draws the results itself (title, URL as subtext, favicon,
grouped under the runner's name "Kondor Browser").

## Decisions

| Question | Decision |
| --- | --- |
| Start Kondor from KRunner when it is not running (D-Bus activation)? | No. KRunner calls `Match` on every keystroke, so activation would launch a whole browser while the user types something unrelated. Without Kondor running there are no open tabs to find; bookmarks and history wait until it runs. |
| QtDBus or a new Python library? | `jeepney`. PySide6's `QDBusArgument` cannot marshal `a(sssida{sv})` (it aborts with a signature mismatch), and `QDBusAbstractAdaptor` cannot declare that type from Python. jeepney is pure Python, small, packaged by Fedora and already on most Plasma systems; dbus-python and PyGObject need a GLib main loop and are not in the KDE Flatpak runtime. |
| How are the three kinds told apart in KRunner? | By order and category relevance (tabs 100, bookmarks 70, history 50) and the fallback icons; no "Open tab" / "Bookmark" labels (show, don't tell). Every URL appears once, and when it is open its tab is the result, so choosing it never makes a duplicate tab. |
| Which bus name, and what if two instances run? | One well-known name below the app id, `io.github.lukasborges.Kondor.KRunner`, requested with `DO_NOT_QUEUE`. Flatpak allows it without `--own-name`. A second instance (`--new-instance`, another profile) runs without KRunner; a wildcard name per instance was rejected because KRunner would then mix results of throwaway test profiles into the user's search. |
| Minimum query length? | 3 characters (`X-Plasma-Runner-Min-Letter-Count=3`, checked again in Python): one or two letters match almost every page title. |
| How many results? | 8 open tabs, 5 bookmarks, 5 history entries, like the address bar's suggestion sizes; KRunner shows only the top ones anyway. |
| Where do bookmarks and history open? | In a new tab of the active normal window, through the same path as a link opened from another app (`handle_single_instance_message`), so the window is raised with the activation token. |
| Private windows? | Never listed, and `Run` never opens anything in a private window: everything goes to normal windows. |
