# AI agent control: let automation tools drive Kondor's pages (#256)

> **Issue:** [#256](https://github.com/lukasborges/kondor/issues/256) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Let an AI agent such as Claude Code drive Kondor the way "Claude in Chrome" drives Chrome: open
pages, click, type, read the page and take screenshots. Kondor opens the Chrome DevTools Protocol
(CDP) port of Qt WebEngine on `127.0.0.1` when the user turns **remote control** on, so existing
MCP servers (chrome-devtools-mcp, Playwright MCP) can connect. It is off by default, a toolbar
indicator shows it while it is on, and private browsing is unavailable meanwhile, because the
endpoint would expose private pages.

This issue is the **page control** half of #256. Control of Kondor's own UI (tabs, windows,
address bar, bookmarks) over D-Bus or a built-in MCP server is out of scope here (see "Out of
scope"); the issue body allows the split.

## Context

- **When:** after the switch to Python (#174, #248). Everything is in `src/kondor/` (Python) and
  `qml/`; there is no C++ twin.
- **Startup:** `src/kondor/__main__.py` → `prepare_environment()` (`app/startup/environment.py`,
  calls `QtWebEngineQuick.initialize()`), `QApplication`, `parse_command_line()`
  (`app/commandline/commandline.py`), `forwards_to_running_instance()` and `start_browser()`
  (`app/startup/appstartup.py`), then `open_windows()`.
- **Settings:** `core/settings/settingsoptions.py` (`STORED_OPTIONS`), `settingsdefaults.py`;
  the Settings dialog edits a draft (`qml/settings/SettingsDraft.qml`) applied with OK/Apply; the
  Privacy page is `qml/settings/pages/PrivacySettingsPage.qml`, and its option list is in
  `qml/settings/SettingsPages.qml`.
- **Private browsing entry points** (all of them must be covered by item 5):
  `qml/app/BrowserActions.qml` (`newPrivateTabAction`, `newPrivateWindowAction`),
  `qml/browser/contextmenu/PageMenuEntries.qml` / `PageMenuActions.qml` ("Open Link in New Private
  Tab"), `qml/browser/pages/NewTabPage.qml`, `qml/app/window/WindowTabController.qml`,
  `qml/bookmarks/BookmarkSelection.qml`, `qml/bookmarks/bar/BookmarksBarActions.qml`,
  `src/kondor/browser/tabs/tabmodel.py`, `tabmodelrows.py`, `WindowManager.create_window()`
  (`app/windows/windowmanager.py`), `--private` on the command line and the `private_mode` of
  `SingleInstanceMessage` (`app/windows/windowlaunch.py`).
- **Toolbar:** `qml/app/NavigationToolBar.qml` (buttons before the main menu button).

### What Qt WebEngine 6.11.2 does (checked by the architect)

- `QTWEBENGINE_REMOTE_DEBUGGING=127.0.0.1:<port>` opens a CDP endpoint with `/json/version`
  (browser `webSocketDebuggerUrl`), `/json/list` and the `Target`, `Page`, `Runtime`, `Input`
  domains.
- **It lists the pages of off-the-record (private) profiles too.** There is no way to hide a
  profile from it. Hence item 5.
- `Target.createTarget` answers `"Not supported"`: agents cannot open new tabs through CDP; they
  navigate existing tabs (`Page.navigate`). `Target.getBrowserContexts` returns an empty list.
- Unless `--remote-allow-origins` is given, Qt adds `--remote-allow-origins=*` (it prints
  "Added {--remote-allow-origins=*} …"), and then a WebSocket with any `Origin` header (for
  example a web page in another browser) is accepted. With
  `--remote-allow-origins=http://127.0.0.1:<port>` in `QTWEBENGINE_CHROMIUM_FLAGS`, Qt adds
  nothing, connections **without** an `Origin` header (MCP servers, Node clients) still work, and
  `Origin: https://evil.example` is refused.
- Requests with a foreign `Host` header get HTTP 500 (DNS rebinding protection is built in).

## Design / behavior

### 1. Turning it on

- New settings (in `STORED_OPTIONS` and `settingsdefaults.py`):
  - `remoteControlEnabled`: bool, default `false`, key `RemoteControl/Enabled`;
  - `remoteControlPort`: int, default `9222`, key `RemoteControl/Port`.
- New command-line option `--remote-control <port>` (help: "turn on remote control for this run,
  on 127.0.0.1:<port>"): remote control is on for this run with that port, whatever the setting
  says. It does not change the setting. A port outside 1024–65535 is an error: print
  `Kondor: --remote-control needs a port from 1024 to 65535` to stderr and exit with status 2.
- Remote control is decided **once, at startup**, before the first web engine profile is created
  (Qt WebEngine reads the variables when it creates its context): from `--remote-control` if
  given, else from the two settings. Changing the setting takes effect at the next start.
- When it is on for port `P`:
  1. check that `127.0.0.1:P` is free (`QTcpServer.listen(QHostAddress.LocalHost, P)`, then close
     it). If it is not, print `Kondor: port P is in use; remote control is off` to stderr and
     start with remote control **off** (everything below as if it were off);
  2. set `QTWEBENGINE_REMOTE_DEBUGGING=127.0.0.1:P` (never `0.0.0.0`, never a bare port, which
     Qt binds to all interfaces);
  3. append `--remote-allow-origins=http://127.0.0.1:P` to `QTWEBENGINE_CHROMIUM_FLAGS`, keeping
     what the variable already holds.
- When it is off, Kondor **removes** `QTWEBENGINE_REMOTE_DEBUGGING` from its environment before
  the engine starts, so no port opens because of a variable left in the shell.
- **Single instance:** `--remote-control` cannot be forwarded to a running Kondor. If another
  instance is running (and `--new-instance` is not given), print
  `Kondor: already running; quit it before starting with --remote-control` to stderr and exit
  with status 1, without forwarding the URLs.

### 2. `RemoteControl` (Python, QML singleton)

New folder `src/kondor/app/remotecontrol/` (same singleton pattern as the other Python
singletons, registered in the app's `qmltypes.py`):

- `RemoteControl.active` (bool, constant): remote control is on in this run;
- `RemoteControl.address` (str, constant): `http://127.0.0.1:P` when active, else `""`;
- `RemoteControl.copyAddress()` (slot): puts `address` on the clipboard (plain text; it is not a
  secret, so no `PasswordClipboard` tricks).

Split the startup decision (pure function: command line + settings → port or none), the port
check and the environment setup into separate small functions so each is unit-tested.

### 3. Toolbar indicator (every window while active)

Prototype: `prototypes/256-remote-control-indicator.qml`.

- An icon-only `ToolButton` in `NavigationToolBar.qml`, right before the main menu button,
  visible only when `RemoteControl.active`:
  - `icon.name: "automated-tasks"`, `icon.color: Kirigami.Theme.neutralTextColor` (an attention
    state, like a warning, not an error);
  - tooltip and `Accessible.name`: `qsTr("Remote control is on")`, `ToolTip.delay: 600`;
  - `checked` while its popup is open.
- Clicking it opens a `Popup` below it, built like the site security and ad blocking popups:
  - a row: `Kirigami.Icon` `automated-tasks` (`iconSizes.medium`, neutral color); a heading
    `qsTr("Remote Control Is On")` (`Kirigami.Heading` level 4) with `RemoteControl.address`
    under it in `disabledTextColor`; at the end, an icon-only `edit-copy` button, tooltip and
    `Accessible.name` `qsTr("Copy Address")`. After a click it shows `dialog-ok-apply` tinted
    `positiveTextColor` for 2 s, tooltip `qsTr("Copied")`, and calls `Accessible.announce()`
    (the #176 pattern);
  - a wrapped `Label`: `qsTr("Automation tools on this computer can read and control the pages
    of normal windows. Private browsing is unavailable.")`;
  - a separator, then a flat `qsTr("Configure…")` button (`configure` icon), aligned right, that
    opens Settings on the Privacy page (`browserWindow.openSettingsPage("privacy")`, using the
    Privacy page's existing id) and closes the popup.
- Esc closes the popup; Tab reaches the copy and Configure buttons.

### 4. Settings → Privacy

Prototype: `prototypes/256b-settings-remote-control.qml` (shown after Apply, restart pending).

At the end of the Privacy page's `Kirigami.FormLayout`, after a section spacer:

- `CheckBox`, `Kirigami.FormData.label: qsTr("Remote control:")`, text
  `qsTr("Allow automation tools to control pages")` → `draft.remoteControlEnabled`;
- under it, a `Label` in `disabledTextColor`:
  `qsTr("Private browsing is unavailable while it is on.")`;
- `SpinBox`, `Kirigami.FormData.label: qsTr("Port:")`, 1024–65535, no thousands separator
  (`textFromValue` returns `String(value)`), enabled only while the check box is checked →
  `draft.remoteControlPort`;
- a `Kirigami.InlineMessage` (Information) right above the check box, visible when the **saved**
  settings (not the draft) differ from what this run uses: saved `remoteControlEnabled` differs
  from `RemoteControl.active`, or both are on and the saved port differs from the active one.
  Text: `qsTr("Restart Kondor to apply the remote control change.")`. It is not shown when remote
  control came from `--remote-control` and the setting is off (the run was asked for explicitly);
  in that case it compares nothing and stays hidden.
- Add both options to the draft (`SettingsDraft.qml`), to the Privacy entry of
  `SettingsPages.qml` (so Defaults and the sidebar search cover them) and to OK/Apply.

### 5. Private browsing is unavailable while active

While `RemoteControl.active`, no private profile is ever created:

- `ProfileManager` gets `privateBrowsingAvailable` (bool, constant) = `not RemoteControl.active`.
- UI entry points are **disabled** (not hidden, so the menus keep their shape):
  `newPrivateTabAction`, `newPrivateWindowAction`, "Open Link in New Private Tab" (and any other
  private entry in the page context menu or bookmark menus), and the private entries of the
  New Tab page if it has any. Their shortcuts do nothing.
- Code paths refuse: `WindowManager.create_window()` with `is_private` returns `None`; adding a
  private tab (`tabmodel.py`, `tabmodelrows.py`, and the QML paths listed in "Context") opens
  nothing. Put the check in **one** place per layer (one Python helper, one QML function on the
  window or the tab model) instead of copying it at every caller.
- `--private` together with active remote control at startup: print
  `Kondor: private browsing is unavailable while remote control is on` to stderr and exit with
  status 2, before any window opens.
- A forwarded `SingleInstanceMessage` with `private_mode` reaching an instance with remote
  control on: activate the current normal window (as for an empty request), open none of the
  URLs, and log the same message with `qWarning`.

### 6. README

- "For developers" group: one bullet, e.g.
  **Remote control** for AI agents and automation tools (off by default).
- A short "Remote control" section (after "Extensions") showing how to use it with Claude Code:
  turn it on in Settings → Privacy (or start `kondor --remote-control 9222`), then
  `claude mcp add kondor -- npx chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9222`.
  Say that agents navigate the open tab (Kondor cannot open new tabs over the protocol), that
  private browsing is off meanwhile, and that only programs on this computer can connect. If the
  developer finds that chrome-devtools-mcp cannot connect but Playwright MCP
  (`--cdp-endpoint http://127.0.0.1:9222`) can, document the one that works and say so in the PR.

### 7. Tests

- Startup decision: setting off → none; setting on → its port; `--remote-control 9333` wins over
  both; invalid port → error.
- Environment: active → `QTWEBENGINE_REMOTE_DEBUGGING == "127.0.0.1:P"` and the allow-origins
  flag appended to existing flags; inactive → the variable is removed.
- Busy port → inactive.
- Privacy: with `RemoteControl` active, `WindowManager.create_window()` for a private window
  returns `None`, the Python tab model paths add no private tab and never call
  `ProfileManager.createPrivateProfile()`, and the private actions are disabled (QML harness).
- Single instance: `--remote-control` with a running instance exits 1 without sending a message.

## Acceptance criteria

- [ ] With remote control off (default), no TCP port is listening for Kondor
      (`ss -ltnp | grep python3` shows nothing new), even with `QTWEBENGINE_REMOTE_DEBUGGING` set
      in the shell.
- [ ] With the setting on, after a restart, `curl http://127.0.0.1:9222/json/version` answers,
      and it is bound to `127.0.0.1` only (`ss -ltn`).
- [ ] `--remote-control 9333` turns it on for that run on port 9333 without changing the setting.
- [ ] Qt does not print "Added {--remote-allow-origins=*}"; a WebSocket with
      `Origin: https://evil.example` is refused, one without `Origin` connects.
- [ ] Every window shows the indicator while active, and its popup matches the prototype; Copy
      Address copies the address and turns into a check mark.
- [ ] Settings → Privacy matches `256b`; the restart message appears after applying a change and
      disappears when the change is undone.
- [ ] While active, every private entry point is disabled or refused (item 5), `--private` exits
      with status 2, and `/json/list` never lists a private page.
- [ ] Claude Code, through the MCP server documented in README, opens a page in Kondor, clicks a
      link and reads the result.
- [ ] New strings translated in every `i18n/*.ts` file; README updated; Python checks pass.

## Manual test

On an isolated profile (`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_RUNTIME_DIR`
in a temporary directory):

1. Start Kondor with no option: `curl -s 127.0.0.1:9222/json/version` fails; no indicator.
2. `QTWEBENGINE_REMOTE_DEBUGGING=9222` in the shell, start again: still no port.
3. Settings → Privacy → check "Allow automation tools to control pages", Apply: the restart
   message appears. Quit and start: the indicator is there, `/json/version` answers, `ss -ltn`
   shows `127.0.0.1:9222` only. The main menu's New Private Tab / Window are disabled, and so is
   "Open Link in New Private Tab" on a link.
4. `/json/list` lists the open tabs; navigate one with an MCP server or a small CDP script
   (`Page.navigate`), click a link (`Input.dispatchMouseEvent`) and read `document.title`
   (`Runtime.evaluate`).
5. While it runs, `kondor --private https://kde.org` from another terminal: no private window
   opens; the running window comes to the front.
6. Quit; start `kondor --remote-control 9333 --private`: exits with status 2 and the message.
7. Occupy port 9222 (`python3 -m http.server 9222 --bind 127.0.0.1`), start Kondor with the
   setting on: the "port 9222 is in use" message, no indicator, private browsing available.

## Out of scope

- Control of Kondor's UI (tabs, windows, address bar, bookmarks) over D-Bus or a built-in MCP
  server. The architect files it as a follow-up issue.
- Opening new tabs over CDP (`Target.createTarget` is not supported by Qt WebEngine), a bundled
  MCP server, or any network listener other than `127.0.0.1`.
- Turning remote control on or off without a restart, a "Restart Now" button, a per-window or
  per-tab opt-in, authentication tokens on the port.
- Hiding private pages from the endpoint by other means (not possible in Qt WebEngine 6.11).

## Dependencies

None (`Depends on: -`). Reuses **Settings**, the Settings dialog (#57), the popup pattern of the
site security / ad blocking buttons and the copy feedback of #176.

## Prototype

- `prototypes/256-remote-control-indicator.qml` → `prototypes/screenshots/256-remote-control-indicator.png`
- `prototypes/256b-settings-remote-control.qml` → `prototypes/screenshots/256b-settings-remote-control.png`
  (`common/SettingsDialogMock.qml`, `withRemoteControl`)

## Decisions

| Question | Decision |
| --- | --- |
| One issue or two? | Two: page control over CDP here; Kondor UI automation in a follow-up. The issue allows the split, and CDP alone already meets its first acceptance criterion. |
| How to keep private pages out of the endpoint? | Qt WebEngine lists every profile's pages, private ones included, and cannot hide them. So private browsing is unavailable while remote control is on; entry points are disabled, not hidden. Rejected: listing private pages, or opening a "private" request as a normal tab (the user would think it is private). |
| Command-line option, setting or both? | Both. The setting is how a desktop user turns it on (Kondor is usually started from the launcher); `--remote-control <port>` is a one-off for a terminal session and does not change the setting. |
| Why a restart? | Qt WebEngine reads the debugging address once, when its context is created. The Settings page says so with an InlineMessage after Apply. Rejected: a "Restart Now" button (more code than this issue needs). |
| Origin check | Pass `--remote-allow-origins=http://127.0.0.1:<port>` so Qt does not add `*`; MCP servers send no `Origin` and still connect, while web pages are refused. |
| What if the variable is already set in the shell? | Removed when remote control is off, so "off" always means no port. |
| Indicator | An `automated-tasks` toolbar button in the neutral (warning) color with a popup, like the ad blocking button. Rejected: a permanent `InlineBar` in every window (takes page height for hours, and InlineBars are for things to act on now); an icon with no popup (the address an MCP server needs would have no place). |
| Where does the setting go? | Settings → Privacy: it decides who can read the pages and turns off private browsing. Rejected: General (it is not a daily preference). |
| Popup action | "Configure…" opens the Privacy page, where it is turned off. Rejected: "Turn Off" in the popup, because it would only take effect after a restart and would read as immediate. |
