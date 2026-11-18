# Agent pointer driven by kondor --mcp: show exactly the clicks it dispatches, mark the agent's tabs and keep it in them (#417)

> **Issue:** [#417](https://github.com/lukasborges/kondor/issues/417) · **Priority:** P1 (high) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Show the agent's pointer and clicks on the page again (#385's look), but driven by an **exact
signal**: `kondor --mcp` announces every pointer action it dispatches. Kondor never infers the
agent's input from page events, so the user's own mouse can never show the pointer. This
replaces #385's detection, which #416 removed after it kept firing on the user's clicks (#405).

Like Claude in Chrome, the agent also works **only in tabs it opened itself**, and those tabs are
**marked** so the user sees at a glance where it works (maintainer's requests).

## Context

- `kondor --mcp` (#398): `src/kondor/app/mcp/`. Pointer actions go through
  `src/kondor/app/mcp/tools/pointer.py` (`move_to`, `click_at`, `wheel`), on a `PageSession` of a
  CDP page target (`src/kondor/app/mcp/cdp/`).
- The `--mcp` process keeps a local socket to the running Kondor: `BrowserLink`
  (`src/kondor/app/mcp/session/browserlink.py`), line protocol in
  `src/kondor/app/instance/sessionprotocol.py` (`hello_line`, `ports_line`), received by
  `src/kondor/app/remotecontrol/connections/sessionregistry.py`.
- `WebEngineView.devToolsId` (Qt 6.6+) is the CDP target id of the view's page.
- The overlay of #385 (`AgentPointerOverlay`, `AgentPointerShape`, `AgentClickRing` in
  `qml/browser/view/pointer/`) was deleted by #416; restore those three components from git
  history (the commit before #416's merge), not the detection pieces (`agentpointer.js`,
  `AgentPointerBridge`, `RealInputWatch`, `RealInputClock`, `RealHoverWatch`, `RealPointWatch`).

## Design / behavior

### 1. Announcing (in `--mcp`)

- Right **before** each `Input.dispatchMouseEvent` it sends, the `--mcp` process writes one line
  on the `BrowserLink` socket: `pointer <targetId> <kind> <x> <y>`, `kind` being `move` (for
  `mouseMoved`) or `press` (for `mousePressed`); releases and wheels are not announced. `x`, `y`
  are the CSS-pixel viewport coordinates it sends to CDP.
- `sessionprotocol` gets `pointer_line(target_id, kind, point)` and its parser; unknown lines are
  ignored as today.

### 2. Showing (in Kondor)

- The session registry turns a valid `pointer` line from a registered `--mcp` session into a
  signal; a new `AgentPointer` QML singleton re-emits it as `moved(targetId, x, y)` /
  `pressed(targetId, x, y)`.
- `PageView.qml` hosts the overlay (as #385: a `Loader`, `z: 1`, `enabled: false`) while
  `RemoteControl.active`; the overlay listens to `AgentPointer` and reacts only when `targetId ===
  webView.devToolsId`. Coordinates are mapped with the zoom factor as before.
- Look, motion, click ring, 3 s fade-out, hide on main-frame navigation, `Accessible.ignored`: as
  in #385 and `prototypes/385-agent-pointer.qml`.
- Other CDP clients (Playwright, chrome-devtools-mcp) show no pointer: they do not announce.

### 3. Agent tabs: the agent works only in them

- **Kondor** (not the `--mcp` process) keeps which tabs are **agent tabs**. A tab becomes one when:
  - an `--mcp` session opens it with `new_tab` (the session sends `own <targetId>` right after
    creating the target; Kondor records the session's client name, e.g. "Claude Code");
  - an agent tab opens it (`newWindowRequested`: the pop-up or new tab inherits agent access and the
    name);
  - the user chooses **Allow Agent Access** in its tab context menu (`prototypes/417c-allow-agent-access.qml`;
    no name).
- It stops being one only when the user chooses **Remove Agent Access**
  (`prototypes/417b-agent-tab-menu.qml`) or closes it. Ending an `--mcp` session changes nothing:
  the tabs stay agent tabs, so a later session can keep working in them (maintainer's choice).
- `Tab` gets read-only `agentAccess` (bool) and `agentName` (string, empty when the user granted
  access), with setters used by Kondor's own logic; they are saved with the session of normal
  windows as optional keys (older readers ignore them, no version bump) and restored at startup.
- The two menu items exist only while `RemoteControl.active`, after Mute Tab; never in private
  windows (unavailable while remote control is on anyway).
- **What sessions can use:** on connecting, an `--mcp` session asks for the agent tabs
  (`agent-tabs?`, answered with their `devToolsId`s); Kondor then pushes `agent-tab <id>` /
  `no-agent-tab <id>` lines to every connected session whenever the set changes. Every tool
  (`list_pages`, `navigate`, `go_back`, `go_forward`, `reload`, `snapshot`, `click`, `hover`,
  `type_text`, `press_key`, `scroll`, `screenshot`, `evaluate`) sees and acts only on agent tabs.
  `list_pages` lists only them; any other page id fails with "This tab is not open to agents. Open
  one with new_tab, or ask the user to choose Allow Agent Access on it." With no agent tab, a tool
  without a page id fails with the same hint; the default page is the session's most recently used
  agent tab. The tool descriptions say so, so agents call `new_tab` first.
- Out of reach on purpose: the raw CDP port of remote control (#256) stays unrestricted; it is the
  endpoint for other automation tools, already flagged by the toolbar indicator.

### 4. Marking agent tabs (`prototypes/417-agent-tab.qml`)

- Horizontal tab styles: an agent tab has a 2 px border in `Kirigami.Theme.neutralTextColor` (the
  remote control color) and the `automated-tasks` icon in that color before the title, after the
  favicon. Side bar: the same icon in the row. Icon-only tabs (pinned, collapsed side bar): a
  12 px emblem in that color with the white `automated-tasks` mask on the favicon's lower right.
- Tooltip and `Accessible.description`: "%1 is working in this tab" while a connected session
  acted on it in the last 10 s; else "Opened by %1"; for a tab the user handed over, "Agents can
  use this tab".
- Marks show only while `RemoteControl.active`; with remote control off they are hidden but kept.

## Acceptance criteria

- [ ] An MCP `click` and `hover` from `kondor --mcp` on a test instance show the pointer at the
      target point (and the ring for the click) in the right tab only.
- [ ] With remote control on and an MCP session connected but idle, clicking checkboxes, fields
      and empty areas with the real mouse never shows the pointer (the #405 cases, including a
      page whose click inserts content above the cursor).
- [ ] No script is injected into pages for the pointer; `grep -r "pointermove" src qml` finds
      nothing for it.
- [ ] pytest: a `pointer` line for target T moves only the overlay whose `devToolsId` is T;
      lines from an unregistered connection and malformed lines are ignored.
- [ ] Zoom 150 %: the pointer lands where the agent clicked.
- [ ] An MCP session lists only agent tabs; acting on another tab id fails with the hint; with no
      agent tab, `click` without a page id fails with the hint.
- [ ] Tabs opened by a session, and their pop-ups, become agent tabs; after the `--mcp` process
      exits they stay marked, and a new session lists and uses them.
- [ ] Allow Agent Access hands a user's tab to agents (a connected session sees it at once);
      Remove Agent Access takes it back (a connected session loses it at once); both only while
      remote control is on.
- [ ] Agent tabs survive a restart (session restore) with their mark and name.
- [ ] Marks in every tab style (floating, below, classic, vertical expanded and collapsed,
      pinned), with the three tooltip texts.
- [ ] Matches `417-agent-tab.png`, Breeze and Breeze Dark.
- [ ] Strings in `qsTr()`, translations complete; README "Remote control" bullet mentions the
      agent pointer and that agents work in their own tabs.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`, remote control
on; an MCP client running that instance's `kondor --mcp`.

1. Ask the agent to click a link and a checkbox on a page: the pointer glides there and rings.
2. With the agent idle, click checkboxes and fields yourself: no pointer.
3. Two tabs: the agent acts in the background tab: the pointer shows there, not in the current
   one.
4. Ask the agent to read a tab you opened yourself: it cannot; it opens its own tab instead, which
   gets the orange border. Quit the MCP client and start it again: the border stays and the new
   session works in that tab.
5. Allow Agent Access on one of your tabs: the agent can now read it. Remove Agent Access: it
   cannot anymore, and the border goes.

## Out of scope

- A pointer for other CDP clients, keyboard or typing indicators, pointers inside iframes.

## Dependencies

- #416 (removes the detection first).

## Prototype

- Pointer, unchanged: [`prototypes/385-agent-pointer.qml`](../../prototypes/385-agent-pointer.qml) →
  [screenshot](../../prototypes/screenshots/385-agent-pointer.png)
- Marked tabs: [`prototypes/417-agent-tab.qml`](../../prototypes/417-agent-tab.qml) →
  [screenshot](../../prototypes/screenshots/417-agent-tab.png) (`agent` in
  `prototypes/common/TabStyleFrame.qml`)
- Remove Agent Access: [`prototypes/417b-agent-tab-menu.qml`](../../prototypes/417b-agent-tab-menu.qml) →
  [screenshot](../../prototypes/screenshots/417b-agent-tab-menu.png)
- Allow Agent Access: [`prototypes/417c-allow-agent-access.qml`](../../prototypes/417c-allow-agent-access.qml) →
  [screenshot](../../prototypes/screenshots/417c-allow-agent-access.png)

## Decisions

| Question | Decision |
| --- | --- |
| Why not detect the agent from page events again? | Two fixes (#405) could not tell CDP input from the user's own reliably (delayed reports, synthetic hover moves). The maintainer asked for an exact signal: only the process that dispatches the click knows it is the agent's. |
| Pointer for Playwright or other CDP clients? | No: they cannot announce their actions, and guessing is what failed. `kondor --mcp` is the supported way to connect agents (#398). |
| How to find the tab? | `WebEngineView.devToolsId` equals the CDP target id the `--mcp` process uses: an exact match, no URL or title heuristics. |
| Which tabs may the agent use? | Only agent tabs: those agents opened, their pop-ups, and tabs the user handed over with Allow Agent Access (maintainer's requests, like Claude in Chrome); the user's other tabs, accounts and data stay out of reach. |
| Unmark when the session ends? | No, the maintainer's choice: the agent may continue in the same tab in a new session. The user takes a tab back with Remove Agent Access; agent tabs are restored with the session. |
| How are its tabs marked? | A 2 px border and the `automated-tasks` icon in the remote control color, an emblem when icon-only. An icon alone was too faint next to the favicon; approved on the prototype. |
