# Remote control: show the agent's pointer and clicks on the page (#385)

> **Issue:** [#385](https://github.com/lukasborges/kondor/issues/385) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

While remote control (#256) is on, an AI agent moves and clicks in Kondor's pages through the
Chrome DevTools Protocol, but nothing on screen shows it: the real mouse pointer does not move.
Show the agent's pointer and clicks on the page, like Claude in Chrome does, drawn so the user
never confuses it with their own pointer (maintainer's requirement).

## Context

- Remote control: `docs/specs/0256-ai-agent-control.md`. `RemoteControl.active` (QML singleton)
  is decided at startup; the CDP endpoint is Qt WebEngine's own (`QTWEBENGINE_REMOTE_DEBUGGING`).
- Agents send `Input.dispatchMouseEvent` (Playwright, chrome-devtools-mcp): Chromium delivers
  the events straight to the renderer. **Qt never sees them**, so `WebEngineView` gets no
  `QMouseEvent`, while the page receives normal, trusted `mousemove` / `mousedown` / `click` events.
- Page scripts and their channel: `qml/browser/view/PageScriptBridges.qml` (`WebChannel`,
  bridges for passwords, media, extensions).
- The toolbar indicator of #256 uses `automated-tasks` in `Kirigami.Theme.neutralTextColor`.

## Design / behavior

Everything here exists only while `RemoteControl.active`; otherwise no script is injected and no
item is created.

### 1. Detecting the agent's input

- A document-creation script in the **application world** (invisible to the page's scripts) of the
  top-level document listens, in the capture phase, to `pointermove`, `pointerdown`, `pointerup`
  and `click`, and reports `{type, x, y}` (CSS pixels, viewport coordinates) through the page
  channel, throttling moves to one per animation frame.
- On the Qt side, a passive `HoverHandler` and `PointHandler` on the view (they never accept or
  grab) keep the time of the last **real** pointer event in the view.
- A reported event counts as the **agent's** only if no real pointer event reached the view in the
  last 100 ms. The user's own mouse therefore never moves the agent pointer. If the developer finds
  a more direct sign of CDP-dispatched input (checked on Qt WebEngine 6.11), it may replace the
  timing rule; say so in the PR.
- Coordinates are mapped to the view with the page's zoom factor and scroll-free viewport
  coordinates.
- Accepted limit: events that land inside an iframe are not seen by the top-level document, so
  the pointer is not updated for them.

### 2. The pointer (`prototypes/385-agent-pointer.qml`)

- An overlay item above the page in `WebViewTab.qml`/`PageView.qml` (a new small component in
  `qml/browser/view/`), never accepting input (`enabled: false`, no handlers), so clicks always go to
  the page.
- **Arrow:** a `Shape`, 22 × 30, fill `Kirigami.Theme.neutralTextColor`, 2 px white outline,
  antialiased; the tip is the agent's point.
- **Badge:** a 22 px circle in the same color with a 2 px white border at the arrow's lower right,
  holding the `automated-tasks` icon in white (mask) at 14 px. This badge is what tells it apart
  from the user's pointer at a glance.
- **Motion:** it glides to each new point in `Kirigami.Units.shortDuration` (`InOutQuad`); the
  first point after it was hidden appears without gliding.
- **Click:** on `pointerdown` a 40 px ring (3 px border, same color, opacity 0.7) appears centered on
  the point, grows to 64 px and fades out in `Kirigami.Units.longDuration`.
- It fades out 3 s after the agent's last event and on navigation of the main frame; it is shown
  only in the tab the agent acts on (the overlay belongs to that tab's view).
- `Accessible.ignored: true` on the overlay; it adds nothing to the accessibility tree.

## Acceptance criteria

- [ ] With remote control on, an agent click through CDP (`Input.dispatchMouseEvent`, e.g. from a
      pytest using the CDP port of a test instance) shows the pointer at the click point and the
      ring; moving the real mouse over the page never moves or shows it.
- [ ] The look matches `385-agent-pointer.png` (Breeze and Breeze Dark), and the pointer fades out
      3 s after the last agent event.
- [ ] Clicks of the user always reach the page while the overlay is visible.
- [ ] With remote control off, no script is injected and no overlay exists.
- [ ] Zoomed pages (e.g. 150 %) place the pointer where the agent clicked.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with its own XDG folders under `~/kondor-test`, started with
`--remote-control 9333 --new-instance` (the maintainer keeps their own Kondor open).

1. Connect an MCP client (chrome-devtools-mcp or Playwright) to `http://127.0.0.1:9333` and ask
   it to click a link and a button on `https://kde.org/`: the orange pointer with the badge glides
   to each target, a ring shows each click, and it fades out after 3 s.
2. Move the real mouse over the page: only the system pointer moves.
3. Zoom to 150 % and repeat 1.

## Out of scope

- Showing the agent's keyboard input or text selection, a "being controlled" border around the
  page, pointers inside iframes.
- Any change to how remote control is turned on or to the CDP endpoint.

## Dependencies

- #256 AI agent control (done).

## Prototype

- [`prototypes/385-agent-pointer.qml`](../../prototypes/385-agent-pointer.qml) →
  [screenshot](../../prototypes/screenshots/385-agent-pointer.png)

## Decisions

| Question | Decision |
| --- | --- |
| Draw it like a normal pointer? | No, the maintainer asked to tell it apart from their own: neutral (orange) fill, white outline and the `automated-tasks` badge, the same color as the remote control indicator. Approved on the prototype. |
| Draw it in the page (DOM) or in Kondor? | In Kondor's QML overlay: a DOM element would change the page the agent reads, and pages could hide or restyle it. The page only reports positions, from the application world. |
| How is the agent told apart from the user? | Qt sees the user's real pointer events and never sees CDP-dispatched ones; a page event without a real Qt event in the last 100 ms is the agent's. A CDP proxy in front of Qt's port was rejected: a new network component and the QtWebSockets dependency for a visual aid. |
| Keep it? | No: removed by #416 at the maintainer's request. Guessing the agent's input from page events and Qt's real input timing kept showing the pointer on the user's own clicks after two fixes (#405 rounds 1 and 2: delayed reports on busy pages, Chromium's synthetic hover moves after layout changes). If it returns, it must be driven by an exact signal (for example `kondor --mcp` announcing each action it dispatches), never by a guess. |
