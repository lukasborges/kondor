# Agent pointer driven by kondor --mcp: show exactly the clicks it dispatches (#417)

> **Issue:** [#417](https://github.com/lukasborges/kondor/issues/417) · **Priority:** P1 (high) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Show the agent's pointer and clicks on the page again (#385's look), but driven by an **exact
signal**: `kondor --mcp` announces every pointer action it dispatches. Kondor never infers the
agent's input from page events, so the user's own mouse can never show the pointer. This
replaces #385's detection, which #416 removed after it kept firing on the user's clicks (#405).

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
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`, remote control
on; an MCP client running that instance's `kondor --mcp`.

1. Ask the agent to click a link and a checkbox on a page: the pointer glides there and rings.
2. With the agent idle, click checkboxes and fields yourself: no pointer.
3. Two tabs: the agent acts in the background tab: the pointer shows there, not in the current
   one.

## Out of scope

- A pointer for other CDP clients, keyboard or typing indicators, pointers inside iframes.

## Dependencies

- #416 (removes the detection first).

## Prototype

- Unchanged: [`prototypes/385-agent-pointer.qml`](../../prototypes/385-agent-pointer.qml) →
  [screenshot](../../prototypes/screenshots/385-agent-pointer.png)

## Decisions

| Question | Decision |
| --- | --- |
| Why not detect the agent from page events again? | Two fixes (#405) could not tell CDP input from the user's own reliably (delayed reports, synthetic hover moves). The maintainer asked for an exact signal: only the process that dispatches the click knows it is the agent's. |
| Pointer for Playwright or other CDP clients? | No: they cannot announce their actions, and guessing is what failed. `kondor --mcp` is the supported way to connect agents (#398). |
| How to find the tab? | `WebEngineView.devToolsId` equals the CDP target id the `--mcp` process uses: an exact match, no URL or title heuristics. |
