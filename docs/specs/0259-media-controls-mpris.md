# Media controls: show page playback in Plasma (MPRIS) (#259)

> **Issue:** [#259](https://github.com/lukasborges/kondor/issues/259) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Video and music playing in a Kondor tab show up in Plasma's media controls: the Media Player
applet, the lock screen, the media keys and KDE Connect. From there the user can play, pause, go to
the next or previous track (when the page offers it), seek, and see the title, artist and artwork.
"Raise" switches to the playing tab. Kondor publishes one MPRIS2 player, for the tab that started
playing last; it disappears when no tab has media any more.

## Context

- **App:** Python + PySide6 since #174 (`src/kondor/`); `qml/` is the UI. There is no C++ twin.
- **MPRIS2** (<https://specifications.freedesktop.org/mpris-spec/latest/>): a player owns a bus
  name `org.mpris.MediaPlayer2.<name>` and serves the object `/org/mpris/MediaPlayer2` with the
  interfaces `org.mpris.MediaPlayer2` (root) and `org.mpris.MediaPlayer2.Player`, their properties
  through `org.freedesktop.DBus.Properties` (`Get`, `GetAll`, `Set`, signal `PropertiesChanged`),
  and the signal `Player.Seeked(x)`. Plasma's Media Player applet, the lock screen, the media-key
  shortcuts (Plasma's "Media Controller" global shortcuts) and KDE Connect all read players from
  the session bus. Qt WebEngine does **not** include Chromium's MPRIS support.
- **D-Bus from Python:** #258 (KRunner) adds `jeepney` and a `RunnerBus` (a jeepney connection
  watched by a `QSocketNotifier`, method calls handed to a handler) because PySide6's `QtDBus`
  cannot marshal nested types such as `a{sv}` with `o` and `x` values inside variants. MPRIS needs
  the same plus **signals**. This issue therefore depends on #258 and turns `RunnerBus` into a
  shared block (1).
- **Page scripts:** `src/kondor/browser/profile/pagescripts.py` installs the web channel script
  (`:/scripts/channel.js`, `window.__kondorChannel` → `objects`) in every profile, and the
  password script in normal profiles only; resources are listed in `scripts/staging/resources.py`.
  `qml/browser/view/PageScriptBridges.qml` registers page APIs on the tab's `WebChannel`
  (`kondorExtensions`, `kondorPasswords`); `PasswordBridge` (`src/kondor/passwords/bridge/`) is the
  pattern for a bridge with a `tab` property and a `pageApi()` object. The channel lives in
  `WebEngineScript.ApplicationWorld`; `qt.webChannelTransport` exists only in the main frame.
- **Probed while writing this spec** (Qt 6.11.2, offscreen `QWebEnginePage`):
  `navigator.mediaSession` exists; a script in the ApplicationWorld reads the
  `navigator.mediaSession.metadata` (title, artwork) and `playbackState` the page set in its main
  world. Action handlers are JavaScript functions of the main world and cannot be called from the
  ApplicationWorld; a small **main-world** script that wraps `setActionHandler` and talks to the
  ApplicationWorld through DOM `CustomEvent`s with **string** `detail`s worked both ways (the
  ApplicationWorld saw `["nexttrack","play"]` and calling `nexttrack` ran the page's handler).
- **Tabs and windows:** `Tab` (`src/kondor/browser/tabs/tab.py`) owns its feature groups in
  `_create_feature_groups()` (`security`, `permissions`, `passwords`, `siteReload`,
  `extensionItems`); they are registered in `src/kondor/browser/qmltypes.py`. `WindowManager`
  (`src/kondor/app/windows/windowmanager.py`) gets `windows()` in #258; each window has
  `tabModel` (`indexOfTab(tab)`, `setCurrentIndex(index)`); `raise_window(window, token)` is in
  `src/kondor/app/instance/windowactivation.py`.
- **Identity:** `QGuiApplication.applicationDisplayName()` is the translated "Kondor Browser";
  `appidentity.desktop_file_name()` is `kondor`, or the Flatpak id inside the Flatpak.
- **Startup:** `open_windows()` / `shut_down()` in `src/kondor/app/startup/appstartup.py` (#258
  starts and stops `KRunnerService` there).

## Design / behavior

### 1. Shared block: `SessionBusService` (`src/kondor/core/dbus/`)

Extract #258's `RunnerBus` into a shared block, the second user being MPRIS ("extract on the second
copy"). New folder `src/kondor/core/dbus/` (`__init__.py`, `sessionbusservice.py`, and
`buscall.py` if the file would pass 200 lines):

- `BusCall` (frozen dataclass): `path`, `interface`, `member`, `body` (tuple).
- `BusReply(signature: str, body: tuple)` and `BusError(name: str)` (frozen dataclasses).
- `SessionBusService(QObject)`, built with a handler `Callable[[BusCall], BusReply | BusError |
  None]`:
  - `start(name: str) → bool`: open the jeepney connection, `RequestName(name, 4)`
    (`DO_NOT_QUEUE`), watch the socket with a `QSocketNotifier`. Same failure handling as
    #258 ("name taken" → `False` with one `qInfo`; no session bus → `False` with one `qWarning`).
  - `unique_name → str`: the connection's unique name (`":1.234"`), empty when stopped.
  - On readable socket: every complete method call is handed to the handler; `BusReply` →
    method return, `BusError` → error reply, `None` →
    `org.freedesktop.DBus.Error.UnknownMethod`. Calls to `org.freedesktop.DBus.Peer` (`Ping`) are
    answered by the service itself.
  - `emit_signal(path, interface, member, signature, body)`: send a D-Bus signal (jeepney
    `new_signal`); does nothing when stopped.
  - `stop()`: disable the notifier, close the connection (the name goes with it).
  - `is_running → bool`.
- `KRunnerService` (#258) switches to it: `RunnerBus` and its test file are deleted, the KRunner
  handler filters on `call.path == "/KRunner"` and `call.interface == "org.kde.krunner1"`, and its
  `start()` calls `SessionBusService.start(SERVICE_NAME)`. KRunner behavior does not change; its
  tests keep passing.
- Tests move to `tests/core/dbus/test_sessionbusservice.py` (see 9).

### 2. Page side: two scripts

Both are resources under `/scripts` (`scripts/staging/resources.py`, new `ResourceGroup` for
`src/kondor/browser/media`), installed by `pagescripts.install()` in **every** profile, private
ones included (controls work in private tabs, 7), **main frame only** (`setRunsOnSubFrames(False)`;
give `ScriptSpec` a `runs_on_sub_frames` field, default `True`), at `DocumentCreation`, after the
channel script.

**2.1 `mediasession.js`, main world** (`ScriptWorldId.MainWorld`, script name
`kondor-media-session`). It only relays action handlers; it reads nothing and sends nothing else.

- Wrap `navigator.mediaSession.setActionHandler` (if `navigator.mediaSession` exists): keep the
  handlers in a `Map` inside a closure, call the original, then dispatch on `document`
  `new CustomEvent("kondor-media-actions", { detail: JSON.stringify([...actions]) })`.
- Listen on `document` for `"kondor-media-action"`; its `detail` is a JSON string
  `{"action": "<name>", "seekTime": <number>}`; call the stored handler with
  `{ action, seekTime }` (`seekTime` only for `seekto`) inside `try/catch` (a throwing page handler
  must not break the shim).
- No globals: everything stays in the closure, `window` gets no new property.

**2.2 `mediawatch.js`, ApplicationWorld** (script name `kondor-media-watch`). Waits for
`window.__kondorChannel`, takes `objects.kondorMedia` (missing → does nothing), then:

- **Active element:** listens in the **capture** phase on `document` for `playing`, `pause`,
  `ended`, `emptied`, `durationchange`, `ratechange`, `seeked`, `loadedmetadata` (media events do
  not bubble). On `playing`, an element becomes the active one when it is **eligible**: not
  `muted`, `volume > 0`, and `duration >= 5` or `duration === Infinity` (live). Silent background
  videos and short UI sounds therefore never create a player. Other events matter only for the
  active element.
- **Report** (`kondorMedia.report(state)`), sent on each of those events of the active element,
  on a `"kondor-media-actions"` event, and when the 1-second poll (below) sees a change:
  ```js
  { hasMedia: true, playing: !el.paused, title, artist, album, artworkUrl,
    duration,   // seconds; 0 when NaN or Infinity
    position,   // el.currentTime
    rate,       // el.playbackRate
    actions,    // the action names last seen from mediasession.js
    seeked }    // true only for the report sent on "seeked"
  ```
  - `title`: `navigator.mediaSession.metadata?.title`, else `document.title`, else
    `location.hostname`. `artist`: metadata `artist`, else `location.hostname`. `album`: metadata
    `album` or `""`.
  - `artworkUrl`: from `metadata.artwork`, the entry with the largest `sizes` (`"WxH"`, largest
    area; `"any"` wins); `""` when none.
- **Poll:** while the active element plays, every second compare a snapshot (title, artist, album,
  artwork, actions) with the last report and report on change (pages change `metadata` without
  events); stop the timer on pause. If the active element is no longer in the document
  (`!el.isConnected`), report `{ hasMedia: false }` and forget it.
- **Commands:** connect to `kondorMedia.actionRequested(action, seconds)`:
  - `play` / `pause` / `stop` / `nexttrack` / `previoustrack` / `seekto`: when the page has a handler
    for the action (from the last `"kondor-media-actions"` list), dispatch
    `"kondor-media-action"` with `{action, seekTime: seconds}`;
  - otherwise the default on the active element: `play` → `el.play()`, `pause` → `el.pause()`,
    `stop` → `el.pause()` and `el.currentTime = 0`, `seekto` → `el.currentTime = seconds`
    (clamped to `[0, duration]`), `nexttrack` / `previoustrack` → nothing (they are only offered
    when the page has the handler, 4.2).
- `pagehide` → report `{ hasMedia: false }`.
- Expose nothing on `window` except what tests need through a single `window.__kondorMediaWatch`
  object in the ApplicationWorld (invisible to the page).

### 3. Bridge and tab state

**3.1 `src/kondor/browser/media/`** (new feature folder; tests in `tests/browser/media/`):

| File | Holds |
| --- | --- |
| `mediastate.py` | `MediaState` (frozen dataclass) and `parse_report(report: dict) → MediaState` |
| `mediapageapi.py` | `MediaPageApi(QObject)`: `@Slot("QVariantMap") report(state)`, signal `actionRequested(str, float)` |
| `mediabridge.py` | `MediaBridge(QObject)`, QML type `MediaBridge` (creatable): `tab` property and `pageApi()`, like `PasswordBridge`; `perform(action, seconds)` emits the page API's `actionRequested` |
| `mediatabs.py` | `MediaTabs` registry singleton (5) |
| `mediasession.js`, `mediawatch.js` | 2 |

- `MediaState` fields: `has_media`, `is_playing`, `title`, `artist`, `album`, `artwork_url`
  (`QUrl`), `duration` (seconds, float), `position`, `rate`, `actions` (`frozenset[str]`),
  `was_seeked`. The empty state is `MediaState()` with `has_media=False`.
- `parse_report()` treats the report as **untrusted page data**: wrong types become defaults;
  strings are trimmed and cut to 512 characters; numbers must be finite and `>= 0` (`rate` must be
  `> 0`, else `1.0`); `artwork_url` is kept only for `http`/`https` URLs; `actions` keeps only
  `play`, `pause`, `stop`, `nexttrack`, `previoustrack`, `seekto`.

**3.2 `TabMedia`** (`src/kondor/browser/tabs/features/tabmedia.py`), the `tab.media` group
(`CONSTANT` property, created in `Tab._create_feature_groups()`, registered `UNCREATABLE` in
`browser/qmltypes.py`). State (Tab bridge pattern):

- `apply(state: MediaState)`: stores it with the monotonic time of the report; emits `changed`
  when anything but `position` differs, `playingChanged` when `is_playing` flips, and `seeked`
  when `state.was_seeked`.
- `clear()`: back to the empty state (emits as above).
- Read-only properties for QML/tests: `hasMedia`, `isPlaying`; Python accessors `state` and
  `current_position() → float` = reported position + `rate × elapsed` while playing (clamped to
  `duration` when known), the reported position otherwise.
- Commands (`@Slot`s that only emit `actionRequested(str, float)`): `play()`, `pause()`,
  `togglePlayback()` (pause when playing, else play), `stop()`, `next()`, `previous()`,
  `seekTo(seconds)`.
- Each `TabMedia` registers itself with `MediaTabs.instance().watch(self)` in its constructor.

**3.3 QML** (`qml/browser/view/PageScriptBridges.qml`): add `MediaBridge { id: mediaBridge; tab:
root.tab }`; register `kondorMedia` → `mediaBridge.pageApi()` for **every** tab (outside the
`isPrivate` check); `Connections { target: root.tab.media; function onActionRequested(action,
seconds) { mediaBridge.perform(action, seconds) } }`; and clear the media when the page goes away
without `pagehide`: `Connections { target: root.webView }` with `onRenderProcessTerminated` and
`onLifecycleStateChanged` (state `WebEngineView.LifecycleState.Discarded`) → `root.tab.media.clear()`.
`MediaBridge`'s page API `report` calls `parse_report` and `tab.media.apply(...)`.

### 4. MPRIS player (`src/kondor/app/mpris/`)

New sub-feature folder (with `__init__.py`), tests in `tests/app/mpris/`:

| File | Holds |
| --- | --- |
| `mprisservice.py` | `MprisService(QObject)` singleton: bus name lifetime, call dispatch, signals |
| `mprisproperties.py` | pure functions: root and player property dicts from a `TabMedia` snapshot |
| `mprisplayercalls.py` | `Player` method calls → `TabMedia` commands |
| `mprisintrospection.xml` | the introspection XML of the three interfaces (resource or read with `importlib.resources`) |

**4.1 Bus name and lifetime**

- `MprisService.instance().start()` from `open_windows()` (after #258's KRunner start) connects to
  `MediaTabs.instance().currentChanged`; `shut_down()` calls `stop()`.
- When `MediaTabs.current` becomes a tab and the bus is not running: start a `SessionBusService`
  and own `org.mpris.MediaPlayer2.kondor.instance_<unique>` where `<unique>` is the connection's
  unique name without `:` and with `.` → `_` (`:1.234` → `instance_1_234`; unique per bus, also
  across Flatpak sandboxes whose PIDs repeat). jeepney gives the unique name right after
  `Hello`, before `RequestName`: `SessionBusService.start()` takes the name as a callable of the
  unique name, or the service builds it after an `open()` step — the developer picks one, the
  name format is binding.
- When `current` becomes `None`: `stop()` the bus, so the player disappears from Plasma.
- A switch from one tab to another keeps the name and announces the new values (4.4).

**4.2 Properties** (`mprisproperties.py`), all values as jeepney `(signature, value)` variants.

Root (`org.mpris.MediaPlayer2`): `CanQuit` `false`, `CanRaise` `true`, `HasTrackList` `false`,
`Identity` = `applicationDisplayName()`, `DesktopEntry` = `desktop_file_name()`,
`SupportedUriSchemes` `[]`, `SupportedMimeTypes` `[]` (signature `as`).

Player (`org.mpris.MediaPlayer2.Player`), from the current `TabMedia` and its tab:

| Property | Value |
| --- | --- |
| `PlaybackStatus` (`s`) | `"Playing"` / `"Paused"` |
| `Rate` (`d`) | the reported rate; `MinimumRate` / `MaximumRate` `1.0` / the rate if higher |
| `Volume` (`d`) | `1.0` |
| `Metadata` (`a{sv}`) | see below |
| `Position` (`x`) | `current_position()` in microseconds (`int(seconds * 1_000_000)`) |
| `CanGoNext` / `CanGoPrevious` (`b`) | `nexttrack` / `previoustrack` in `actions` |
| `CanPlay`, `CanPause`, `CanControl` (`b`) | `true` |
| `CanSeek` (`b`) | `duration > 0` |

`Metadata`:
- `mpris:trackid` (`o`): `/io/github/lukasborges/Kondor/track/<n>`; `n` is a counter of the
  service that grows whenever the current tab changes or its title changes.
- `mpris:length` (`x`): duration in microseconds, omitted when `duration == 0` (unknown or live).
- `xesam:title` (`s`), `xesam:artist` (`as`, one entry), `xesam:album` (`s`, omitted when empty),
  `mpris:artUrl` (`s`, omitted when empty), `xesam:url` (`s`, the tab's URL).
- **Private tab:** only `mpris:trackid`, `mpris:length` and `xesam:title` = `Identity`; no artist,
  album, artwork or URL (7).

**4.3 Calls** (`handle_call(call) → BusReply | BusError | None`), path `/org/mpris/MediaPlayer2`
only (other paths → `None`):

- `org.freedesktop.DBus.Properties.Get(ss)` → `v`; `GetAll(s)` → `a{sv}`; unknown interface or
  property → `BusError("org.freedesktop.DBus.Error.UnknownProperty")`.
  `Set(ssv)` → `BusError("org.freedesktop.DBus.Error.PropertyReadOnly")` for every property (rate,
  volume, loop and shuffle are not controllable).
- `org.freedesktop.DBus.Introspectable.Introspect` → the XML of 4 (`s`).
- Root: `Raise()` → `WindowManager.instance().show_tab(tab)` (new command: find the window whose
  `tabModel.indexOfTab(tab) >= 0`, among **all** windows including private ones, select the tab and
  `raise_window(window, b"")`; #258's `KRunnerService.Run` uses it too instead of its own copy);
  `Quit()` → empty reply, does nothing.
- Player: `Play`, `Pause`, `PlayPause`, `Stop`, `Next`, `Previous` → `play()`, `pause()`,
  `togglePlayback()`, `stop()`, `next()`, `previous()` of the current `TabMedia` (`Next` /
  `Previous` do nothing when the page offers no handler, per MPRIS);
  `Seek(x offset)` → `seekTo(max(0, current_position + offset / 1e6))`, and when that passes the
  duration, `next()` if possible, else nothing; `SetPosition(o trackId, x position)` → ignored
  unless `trackId` is the current track id and `0 <= position <= length`, then
  `seekTo(position / 1e6)`; `OpenUri(s)` → `BusError("org.freedesktop.DBus.Error.NotSupported")`.
  Every accepted call replies with an empty body.
- With no current tab every Player call replies with an empty body and does nothing.

**4.4 Signals**

- After every `changed` / `playingChanged` of the current `TabMedia`, and when `current` switches:
  build the Player properties, compare with the last values sent (not `Position`), and emit
  `org.freedesktop.DBus.Properties.PropertiesChanged("org.mpris.MediaPlayer2.Player",
  {changed…}, [])` with only the ones that changed.
- On `seeked` of the current `TabMedia`: `Player.Seeked(x position)`.
- Signals are coalesced: changes within one event-loop turn emit once (`QTimer.singleShot(0)`).

### 5. Which tab is the player (`MediaTabs`)

`MediaTabs` (QObject singleton, `src/kondor/browser/media/mediatabs.py`) keeps the watched
`TabMedia` objects in **most-recently-started order**:

- A `TabMedia` enters the list (at the front) when it starts playing (`playingChanged` to
  playing); a tab whose media was never played never becomes the player.
- When the current tab pauses it stays current, unless another tab starts playing, which moves
  to the front.
- A `TabMedia` leaves the list when its state loses `has_media` (page left, element gone, crash,
  sleeping) or it is destroyed (tab closed); the next one in the list becomes current, whether
  it plays or not.
- `current → TabMedia | None` and signal `currentChanged`. Tracking by object identity must not
  touch destroyed objects (remove on `destroyed` using a key captured at `watch()` time, not the
  dying wrapper).

### 6. Packaging

- Flatpak manifest: add the finish-arg `--own-name=org.mpris.MediaPlayer2.kondor.*` (MPRIS names
  are not below the app id).
- No new Python or Qt dependency beyond #258's `jeepney`; no D-Bus service or activation file.

### 7. Privacy

- Private tabs are controllable (play, pause, next, previous, seek, raise): commands write nothing
  anywhere.
- The bus never gets data of a private tab's page: no title, artist, album, artwork or URL; the
  title is the app name ("Kondor Browser"), so the lock screen and KDE Connect show only that
  Kondor is playing something. `TabMedia` keeps the state in memory only.
- Nothing about media is written to disk, for any tab.

### 8. Strings, README

- **No new `qsTr()` strings** (the private title is the existing translated display name).
- **`README.md`** "Made for KDE": add **Media controls**: play, pause and skip from Plasma, the lock
  screen and the media keys.

### 9. Tests (pytest, through `scripts/run-pytests.sh`)

- `tests/core/dbus/test_sessionbusservice.py`: #258's `RunnerBus` tests, moved (owns the name,
  second owner gets `False`, `gdbus call` gets the handler's reply through `QProcess` with
  `qtbot.waitUntil`, unknown method → `UnknownMethod`, `stop()` releases the name); plus
  `emit_signal` received by a second jeepney connection with a match rule; `Peer.Ping` answered.
- `tests/browser/media/test_mediastate.py`: `parse_report` defaults for wrong types, 512-character
  cut, negative / infinite numbers, non-http artwork dropped, unknown actions dropped.
- `tests/browser/media/test_mediascripts.py` (real `QWebEnginePage`, as
  `tests/passwords/bridge/test_passwordfill.py` does; `mediasession.js` in the main world): the
  shim announces `setActionHandler` actions to the ApplicationWorld; a `"kondor-media-action"`
  event calls the page's handler with `seekTime`; a throwing handler does not break later calls;
  the page sees no new `window` property; `mediawatch.js` builds the report's title, artist,
  album and largest artwork from `navigator.mediaSession.metadata` and falls back to
  `document.title` / host (through `window.__kondorMediaWatch` with a fake element; no real
  playback is needed).
- `tests/browser/tabs/test_tabmedia.py`: `apply` signals (`changed` only on real changes,
  `playingChanged`, `seeked`), `clear`, `current_position()` extrapolation and clamping, each
  command emits `actionRequested` with the right name and seconds.
- `tests/browser/media/test_mediatabs.py`: started tab becomes current; a newer start takes over;
  pausing keeps current; losing media or destroying the tab falls back to the next; never-played
  media is never current; `currentChanged` emitted once per change.
- `tests/app/mpris/test_mprisproperties.py`: root values; Player values for playing / paused;
  microseconds; `CanSeek`, `CanGoNext`, `CanGoPrevious`; `mpris:length` omitted for 0; track id
  changes with tab and title; private tab metadata has only track id, length and the app-name
  title.
- `tests/app/mpris/test_mprisservice.py` (calls `handle_call` directly, fake bus recording
  signals): `Get` / `GetAll` / `Set` replies and errors; each Player method maps to the right
  `TabMedia` command; `Seek` past the end and `SetPosition` with a stale track id; `OpenUri` →
  `NotSupported`; `Raise` calls `show_tab`; `PropertiesChanged` carries only changed properties and
  never `Position`; `Seeked` emitted; the bus starts when a tab becomes current and stops when none
  is left; the bus name format.
- `tests/app/windows/`: `show_tab` selects the tab in its window (also a private window) and
  returns without effect for a tab in no window.

## Acceptance criteria

- [ ] A YouTube video playing in Kondor appears in Plasma's Media Player applet with its title,
      channel name and thumbnail; pause and play from the applet work, and so does the applet's
      position slider.
- [ ] The keyboard's media keys (Play/Pause, Next, Previous) control it; Next goes to the next
      video on a YouTube playlist.
- [ ] Clicking the applet's player icon / "Raise" switches to the playing tab and brings its
      window forward.
- [ ] With two tabs playing, the player follows the one that started last; when that tab is closed
      the other one takes over; when no tab has media, the Kondor player disappears.
- [ ] A muted or silent background video (e.g. an autoplaying muted hero video) creates no player.
- [ ] In a private tab, the controls work but Plasma shows only "Kondor Browser" as title, with no
      artwork, artist or URL.
- [ ] Two Kondor instances (`--new-instance`) each get their own player name; neither fails.
- [ ] `RunnerBus` is gone: KRunner (#258) uses `SessionBusService`, and its tests still pass.
- [ ] The Flatpak manifest has `--own-name=org.mpris.MediaPlayer2.kondor.*`; README "Made for KDE"
      has the **Media controls** bullet.
- [ ] The tests of "Design → Tests" exist and pass, with all Python checks of AGENTS.md
      (`ruff`, `mypy --strict`, `scripts/build.py`, `scripts/run-pytests.sh`,
      `scripts/check-qml-api.py`); the smoke test prints no QML errors;
      `scripts/check-code-quality.py --changed origin/main` is clean.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` in a temporary
directory, as in `AGENTS.md`), on the Plasma desktop session (the player must be on the real
session bus):

1. Open a YouTube playlist and play a video. `busctl --user list | grep mpris` shows
   `org.mpris.MediaPlayer2.kondor.instance_…`; `playerctl -p kondor metadata` (or
   `qdbus6 org.mpris.MediaPlayer2.kondor.instance_… /org/mpris/MediaPlayer2
   org.freedesktop.DBus.Properties.GetAll org.mpris.MediaPlayer2.Player`) shows the title,
   artist (channel), `mpris:artUrl`, `mpris:length` and `xesam:url`.
2. The Media Player applet in the system tray shows the video with its thumbnail; Pause and Play
   there, then the Play/Pause media key; Next skips to the next playlist video; drag the slider
   and the video seeks.
3. Switch to another tab, click "Raise" / the player's app icon in the applet → Kondor switches
   back to the YouTube tab. (Without an activation token KWin may only highlight the taskbar
   entry when another app has focus; that is expected.)
4. Open a second tab with an audio stream (e.g. a podcast page with `<audio>`) and play it → the
   applet follows it. Close it → the YouTube tab is the player again. Close the YouTube tab → the
   Kondor player is gone.
5. Open a page with a muted autoplaying background video → no Kondor player.
6. In a private window, play a YouTube video → the applet and the lock screen (Meta+L) show
   "Kondor Browser" only, no thumbnail; Play/Pause works.
7. Start `kondor --new-instance` with another isolated profile and play something in both → two
   Kondor players are listed.
8. Run Kondor with `QT_QPA_PLATFORM=offscreen` and no `DBUS_SESSION_BUS_ADDRESS` → it starts, logs
   one warning when media plays, and plays normally.

## Out of scope

- A playing / muted indicator or a mute button on tabs, and muting from the tab strip.
- MPRIS `TrackList` and `Playlists` interfaces, `LoopStatus`, `Shuffle`, and setting `Rate` or
  `Volume` from D-Bus.
- Media in sub-frames (an embedded YouTube player inside another site's iframe), Web Audio players
  without an `<audio>`/`<video>` element, and Picture-in-Picture.
- One MPRIS player per tab (Chromium/Firefox style "several players"); there is exactly one.
- A Kondor setting to turn media controls off.
- Downloading the artwork to a local file (Plasma loads `http(s)` artwork itself).
- An activation token for `Raise` (MPRIS does not pass one).
- The AppImage and the Windows/macOS media APIs.

## Dependencies

- **#258** (KRunner): adds `jeepney` and the `RunnerBus` this issue turns into `SessionBusService`,
  and `WindowManager.windows()`.
- Builds on #14 (multiple windows), #15 (window raising), #107 (web channel page scripts) and #174
  (Python app), all closed.

## Prototype

None: Kondor shows no new UI. Plasma's Media Player applet, the lock screen and KDE Connect draw
the player from the MPRIS data.

## Decisions

| Question | Decision |
| --- | --- |
| How does Kondor learn what a page plays? | A page script in the ApplicationWorld watches media element events and reads `navigator.mediaSession.metadata` (readable across worlds, probed), and reports through the web channel. `WebEngineView.recentlyAudible` (suggested in the issue) was rejected: it says that a tab made sound, not which element, its title, position or duration, and it lags by seconds. |
| How are the page's next / previous / seek handlers called? | A tiny main-world script wraps `navigator.mediaSession.setActionHandler` and talks to the ApplicationWorld only through `CustomEvent`s with string details (probed). Handlers live in a closure; the page gets no new global. When the page has no handler, play / pause / stop / seek act on the element itself, like Chromium's default actions; next / previous are then not offered. |
| Which element counts as media? | One that starts playing unmuted, with volume > 0 and lasting at least 5 seconds (or live), like Chromium's media session eligibility. Muted background videos and notification sounds never create a player. |
| Several playing tabs? | One player, following the tab that **started** playing last; pausing keeps it; when it loses its media or closes, the previous one takes over. One player per tab was rejected: Plasma's applet then shows a list of Kondor entries to switch between, and media keys act on whichever Plasma picks. |
| When does the player exist? | Only while some tab has played media and still has it. A permanent empty "Kondor Browser" player in the applet would sit there for a browser that is not playing anything. |
| Bus name? | `org.mpris.MediaPlayer2.kondor.instance_<unique connection name>`: unique per bus even for two Flatpak sandboxes (whose PIDs repeat) and for `--new-instance`; `playerctl -p kondor` still matches it. Flatpak needs `--own-name=org.mpris.MediaPlayer2.kondor.*`. |
| Private tabs? | Controls work (they write nothing), but no page data reaches the bus: the title is "Kondor Browser" and there is no artist, album, artwork or URL, because the lock screen and KDE Connect show it to anyone near the screen or the phone (Firefox does the same in private windows). |
| QtDBus or jeepney? | jeepney, through #258's connection turned into the shared `SessionBusService`: `Metadata` is `a{sv}` with `o`, `x` and `as` inside variants, which PySide6's `QDBusArgument` cannot build, and MPRIS also needs signals (`PropertiesChanged`, `Seeked`). |
| Position updates? | The page reports the position only on events; `TabMedia.current_position()` extrapolates with the rate while playing. MPRIS clients poll `Position` and listen to `Seeked`, so no periodic reports are needed. |
| Artwork from the page's URL? | Yes for normal tabs: Plasma loads `http(s)` artwork itself. Saving it to a temporary file (Chromium's way) is out of scope. |
