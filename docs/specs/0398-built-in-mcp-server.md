# Built-in MCP server: let AI agents control Kondor without extra tools (#398)

> **Issue:** [#398](https://github.com/lukasborges/kondor/issues/398) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Today an agent reaches Kondor only through a third-party MCP server (`npx chrome-devtools-mcp`),
which needs Node.js and sometimes clicks through JavaScript, so the agent pointer of #385 does not
show. Ship the MCP server **inside Kondor**: any MCP client (Claude Code, Claude Desktop, opencode,
VS Code, Cursor…) adds one command, `<kondor> --mcp`, and controls Kondor's pages with every click
visible. The toolbar indicator shows only while something is connected, with the agent's name.

## Context

- Remote control: `docs/specs/0256-ai-agent-control.md`. Decided at startup in
  `src/kondor/app/remotecontrol/remotecontrolstartup.py` (setting `remoteControlEnabled` /
  `remoteControlPort`, or `--remote-control <port>`); `RemoteControl` (QML singleton) exposes
  `active`, `address`, `port`. Qt WebEngine's DevTools endpoint can only be turned on **before**
  the engine starts (`QTWEBENGINE_REMOTE_DEBUGGING`).
- Indicator: `qml/app/remotecontrol/RemoteControlButton.qml` and `RemoteControlPopup.qml`.
- Settings: `qml/settings/pages/PrivacySettingsPage.qml` (Remote control check box and Port).
- Single instance: `src/kondor/app/instance/` (local socket in the runtime directory, shared inside
  the Flatpak, JSON lines of `SingleInstanceMessage`).
- Command line: `src/kondor/app/commandline/commandline.py`; entry point `src/kondor/__main__.py`.
- Agent pointer: `docs/specs/0385-agent-pointer.md` (shows `Input.dispatchMouseEvent` input only).
- `PySide6.QtWebSockets` is available in the development environment; check the Flatpak and the
  AppImage ship it.

## Design / behavior

### 1. `--mcp`: the server process

- New option `--mcp` (help: "serve the Model Context Protocol on stdin and stdout for AI agents").
  It is handled in `__main__.py` **before** any GUI starts: it runs a `QCoreApplication` (no QML,
  no WebEngine, no window) and never becomes the single instance. `--profile <name>` selects the
  profile as for a normal start; other options are refused with status 2.
- stdout carries only JSON-RPC messages; every log line goes to stderr.
- Transport: MCP stdio, newline-delimited JSON-RPC 2.0, read with a `QSocketNotifier` on stdin
  (no Python thread holding the GIL, see #397). Methods: `initialize` (answer the client's
  `protocolVersion` when it is one Kondor knows, `2025-06-18` otherwise; `serverInfo` name `kondor`
  and Kondor's version; capability `tools`), `notifications/initialized`, `ping`, `tools/list`,
  `tools/call`. Unknown methods → error `-32601`; bad params → `-32602`. End of stdin → exit 0.
- No MCP SDK dependency: the subset above is small, and the official SDK would add pydantic, anyio
  and an HTTP stack to the Flatpak and the AppImage.

### 2. Reaching the browser

On the first `tools/call`:

1. Ask the running instance of the profile, over the single-instance socket, for its remote control
   state (a new request type next to `SingleInstanceMessage`; the answer is `{active, port}`). It
   also registers the session: `{clientName, clientVersion}` from `initialize`. The socket stays
   open for the session's lifetime; closing it ends the session in the browser.
2. **Not running:** start Kondor detached with the same profile, as the desktop launcher would, then
   retry for up to 20 s.
3. **Running with remote control off** (or the setting off when it starts): every tool returns
   `isError: true` with the text "Remote control is off. Turn it on in Kondor's Settings → Privacy,
   then restart Kondor." `--mcp` never turns remote control on by itself: the setting is the
   user's consent (see Decisions).
4. **Active:** connect to `http://127.0.0.1:<port>` over CDP (`QtWebSockets`), one WebSocket per
   page target, opened on demand.

### 3. Tools

`page` is the CDP target id from `list_pages`; when omitted, the current tab of the most recently
active window. Private tabs never exist while remote control is on (#256).

| Tool | Does |
| --- | --- |
| `list_pages` | Open tabs: id, title, URL, which one is current. |
| `new_tab(url)` | Opens a tab through the single-instance socket (CDP cannot open Kondor tabs). |
| `navigate(page, url)` / `go_back(page)` / `go_forward(page)` / `reload(page)` | Main frame navigation; waits for `load` (30 s max). |
| `snapshot(page)` | Visible text and a numbered list of interactive elements (role, name, `uid`), from a script in an isolated world. |
| `click(page, uid)` | Scrolls it into view and sends `mouseMoved`, `mousePressed`, `mouseReleased` at its center (`Input.dispatchMouseEvent`), so the #385 pointer shows. |
| `hover(page, uid)` | `mouseMoved` only. |
| `type_text(page, uid, text, submit?)` | Clicks the element, then `Input.insertText`; `submit` presses Enter. |
| `press_key(page, key)` | `Input.dispatchKeyEvent` for a key name (Enter, Escape, Tab, arrows, Ctrl+… combos). |
| `scroll(page, direction, amount?)` | `mouseWheel` at the viewport center. |
| `screenshot(page)` | `Page.captureScreenshot`, returned as MCP image content (PNG). |
| `evaluate(page, expression)` | `Runtime.evaluate` with `returnByValue`, in the page's main world. |

Each tool has a JSON schema with descriptions in `tools/list`. Never synthesize clicks with
`element.click()`.

### 4. Indicator: only while something is connected (`prototypes/398-mcp-agent-connected.qml`)

This replaces #256's "every window shows the indicator while active".

- `RemoteControl` gets `connections` (a list model): one row per `--mcp` session (name from
  `clientInfo.name`, connected time), plus one row "Automation tool" when other CDP clients are
  connected (established TCP connections to the port on `127.0.0.1`, read from `/proc/net/tcp`
  every 2 s, ignoring those of `--mcp` sessions and any seen in only one poll, so `curl` probes
  do not flash the icon).
- `RemoteControlButton` is visible only when `connections` is not empty. Tooltip and accessible name:
  one row → "%1 is controlling Kondor" (or "An automation tool is controlling Kondor"); more →
  "%n agents are controlling Kondor" (plural forms).
- The popup keeps #256's header and text, then a separator and one row per connection: a
  `dialog-scripts` icon, the name (bold), "Connected since %1" (locale short time) and, for `--mcp`
  sessions only, an icon-only **Disconnect** button (`network-disconnect`, tooltip "Disconnect",
  accessible name "Disconnect %1"). Disconnect closes that session's socket; the `--mcp` process
  then drops its CDP connections and exits with status 0. Generic CDP clients have no Disconnect
  (Kondor cannot close another program's connection).
- When the last connection goes away, the popup closes and the button hides.

### 5. Settings: the command (`prototypes/398b-settings-mcp-command.qml`)

- Privacy page, under Port: **MCP server:** a read-only monospace `TextField` with the command and
  an icon-only Copy button (`CopyFeedbackButton`, tooltip "Copy Command", copied feedback as in the
  #256 popup), then the hint "Add it to an AI agent, such as Claude Code, as an MCP server." in
  `disabledTextColor`. Enabled only while the Remote control check box is checked (like Port).
- The command matches how this Kondor runs (`RemoteControl.mcpCommand`): Flatpak (`FLATPAK_ID`) →
  `flatpak run <FLATPAK_ID> --mcp`; AppImage (`APPIMAGE`) → `"<APPIMAGE>" --mcp` (quoted when it has
  spaces); otherwise `kondor --mcp` when `kondor` on `PATH` is this installation, else
  `<python> -m kondor --mcp`. With a non-default profile, add `--profile <name>`. The field's
  tooltip shows the full command in case it is cut.

### 6. README

- "Remote control" section: turn it on in Settings, then add the command shown there to the agent,
  with the Claude Code example (`claude mcp add kondor -- flatpak run io.github.lukasborges.Kondor --mcp`)
  and one generic JSON example (`"command"`/`"args"`) for other clients. Keep the
  `chrome-devtools-mcp` line as the alternative for any CDP tool.
- Update the "Remote control" feature bullet if needed (at most about ten words).

## Acceptance criteria

- [ ] `kondor --mcp` answers `initialize` and `tools/list` on stdio with nothing but JSON-RPC on
      stdout, and starts no window.
- [ ] With remote control on, Claude Code configured with the Settings command lists the tabs,
      navigates, takes a snapshot, clicks (the #385 pointer and ring show), types and takes a
      screenshot.
- [ ] With Kondor closed, the first tool call starts it and succeeds; with remote control off,
      tools return the "Remote control is off…" error and Kondor's state is unchanged.
- [ ] The toolbar indicator is hidden while nothing is connected, appears with "Claude Code is
      controlling Kondor" while the session is up, and disappears when Claude Code exits.
      `curl /json/version` does not show it; `chrome-devtools-mcp` shows an "Automation tool" row.
- [ ] Disconnect ends the session; the agent's next call fails and the row disappears.
- [ ] The Settings row shows the right command for the Flatpak, the AppImage and a source checkout,
      copies it, and is disabled while the check box is off. Matches `398-mcp-agent-connected.png`
      and `398b-settings-mcp-command.png` in Breeze and Breeze Dark.
- [ ] Tests: JSON-RPC handling (initialize, unknown method, bad params, end of stdin), each tool's
      CDP calls against a fake transport, the command text per install type, the `/proc/net/tcp`
      parser and the two-poll rule, indicator visibility and plural tooltip (QML harness), and one
      offscreen end-to-end run (`--remote-control` instance + `--mcp` client on a local page).
- [ ] Strings in `qsTr()`, translations complete; README updated.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with its own XDG folders under `~/kondor-test` (the maintainer keeps their own
Kondor open); point the MCP client at that instance with the same XDG variables.

1. Turn on remote control in Settings, restart, copy the MCP server command.
2. `claude mcp add kondor-test -e XDG_CONFIG_HOME=… -e XDG_DATA_HOME=… -e XDG_CACHE_HOME=… -- <command>`.
   No icon in the toolbar yet.
3. Ask Claude Code to open kde.org, click "Community" and screenshot it: the icon appears, the
   popup shows "Claude Code", the orange pointer clicks.
4. Disconnect in the popup: the row and the icon go; Claude Code reports the server ended.
5. Quit Kondor, ask Claude Code to open a page: Kondor starts and the call works.

## Out of scope

- Control of Kondor's UI beyond tabs (bookmarks, settings, windows), file uploads, downloads,
  dialogs (`alert`, `confirm`), network inspection, performance traces.
- MCP over HTTP / SSE, resources and prompts; any listener outside `127.0.0.1`.
- Turning remote control on without the setting, or without a restart.
- A per-client snippet picker in Settings (rejected below).

## Dependencies

- #256 AI agent control, #385 Agent pointer (both done).

## Prototype

- [`prototypes/398-mcp-agent-connected.qml`](../../prototypes/398-mcp-agent-connected.qml) →
  [screenshot](../../prototypes/screenshots/398-mcp-agent-connected.png)
- [`prototypes/398b-settings-mcp-command.qml`](../../prototypes/398b-settings-mcp-command.qml) →
  [screenshot](../../prototypes/screenshots/398b-settings-mcp-command.png)
  (`withMcpCommand` in `prototypes/common/SettingsDialogMock.qml`)

## Decisions

| Question | Decision |
| --- | --- |
| A Kondor extension, like Claude in Chrome? | No: Kondor extensions run inside pages and cannot talk to a local agent; Claude in Chrome's bridge is Anthropic's, for Chrome and Edge only. An MCP server is the standard every agent speaks. |
| Only for Claude Code? | No, any MCP client. Settings shows the generic command (maintainer's choice); a picker with per-client snippets was rejected as more UI to keep up to date, and the README carries the examples. |
| Indicator always on while remote control is active (#256)? | No, the maintainer's choice: only while something is connected, with its name; nothing connected means nothing to watch. The address stays in Settings. |
| May `--mcp` turn remote control on by itself? | No. The setting is the user's consent, it would act differently depending on whether Kondor is running, and Qt can only turn the endpoint on at startup. |
| Use the MCP Python SDK? | No: the stdio subset is small, the SDK would add pydantic, anyio and an HTTP stack to every package. |
| QtWebSockets as a dependency? | Yes here (rejected in #385 for a visual aid): it is the CDP transport of a feature, and it ships with PySide6. |
| How are clicks sent? | Always `Input.dispatchMouseEvent`, so the #385 pointer shows every agent click; never `element.click()`. |
