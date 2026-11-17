# Hide the toolbars: in full screen (F11) and with a Hide Toolbars toggle (#384)

> **Issue:** [#384](https://github.com/lukasborges/kondor/issues/384) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

The maintainer wants the page to fill the window:

1. **F11 full screen hides the tab strip and the toolbar** (today it keeps them: #8 decided "keep
   it visible in F11 window mode", and that decision is replaced here).
2. A **Hide Toolbars** toggle hides them in a normal window too, leaving only the window decoration
   (title bar) and the page.

In both cases the toolbars come back on demand: pointer at the top edge, or a shortcut that needs
them (Ctrl+L).

## Context

- Window: `qml/app/window/` (`BrowserWindow.qml`, `FullScreenController.qml`: `windowFullScreen`
  toggled by F11 in `qml/app/BrowserShortcuts.qml`, `pageFullScreen` for videos, which already
  hides the header). The header holds the tab strip (horizontal tab styles) and the navigation
  toolbar; the bookmarks bar sits under it when on; vertical tab styles use the side bar
  (`qml/browser/sidebar/`).
- Main menu: `qml/app/menu/MainMenu.qml`, zoom and full screen row `ZoomMenuRow.qml`.
- Free shortcut: **Ctrl+Shift+F** (not used in `BrowserShortcuts.qml`).
- `FullScreenHint` exists for page full screen ("press Esc").

## Design / behavior

### 1. State

- New setting `hideToolbars` (bool, default `false`), remembered, global: changing it applies to every
  open window at once. It is a UI preference, so private windows may change it too.
- A window **hides its toolbars** when `windowFullScreen || Settings.hideToolbars`. Page full
  screen (videos) is unchanged: everything hidden, no reveal.
- "Toolbars" means: the tab strip, the navigation toolbar, the bookmarks bar and, in the vertical
  tab styles, the side bar. **Not** hidden: InlineBars (permission prompts, crash notice, reload
  offers) and the find bar, which stay at the top of the page area because they need an answer.

### 2. Hidden (`prototypes/384-toolbars-hidden.qml`)

- The page fills the window's content area. No strip, line or handle is left at the top.

### 3. Reveal (`prototypes/384b-toolbars-revealed.qml`)

- **Pointer:** resting within 4 px of the content area's top edge for 300 ms (in the vertical tab
  styles also the left edge, for the side bar) slides the toolbars in **over** the page, so the
  page does not reflow, with a drop shadow (theme colors) and a `Kirigami.Units.shortDuration`
  animation.
- **Keyboard:** Ctrl+L, Ctrl+T, Alt+D and any shortcut that focuses the address bar reveal them
  and focus the field; the tab shortcuts (Ctrl+Tab, Ctrl+1…9) do not.
- They hide again 500 ms after the pointer has left them, as long as nothing inside has focus and
  none of their menus or popups (main menu, bookmarks panel, extensions panel, site information,
  suggestions) is open. Esc in the address bar hides them after restoring the URL as today.
- Hiding never moves the focus out of the page.

### 4. Turning it on and off (`prototypes/384c-hide-toolbars-menu.qml`)

- Main menu: a checkable **Hide Toolbars** (Ctrl+Shift+F) right under the zoom row, unchecked by
  default and checked while the setting is on. In F11 full screen it stays enabled and still shows the setting (the toolbars
  are hidden by full screen either way).
- **Ctrl+Shift+F** toggles the setting from anywhere in the window; add it to the README shortcut
  table.
- Entering F11 full screen shows the existing hint, with "Press F11 to exit full screen", for 3 s;
  page full screen keeps its Esc hint.
- When the setting is turned on, `Accessible.announce("Toolbars hidden. Move the pointer to the top
  edge or press Ctrl+L to show them.")` once, so screen reader users know how to get back.

## Acceptance criteria

- [ ] F11 hides tab strip, toolbar, bookmarks bar and side bar; F11 again restores them and the
      previous window state (maximized stays maximized).
- [ ] Hide Toolbars on: same in a normal window, with the title bar kept; off: back as before.
      The setting survives a restart and applies to every window.
- [ ] Pointer at the top edge reveals them over the page without resizing it; they hide 500 ms
      after the pointer leaves, but not while the address bar has focus or one of their popups is
      open. Ctrl+L reveals them and focuses the address bar.
- [ ] Vertical tab styles: the side bar is hidden and comes back at the left edge.
- [ ] Find bar and InlineBars still show while the toolbars are hidden.
- [ ] Page full screen (YouTube) behaves as before.
- [ ] Matches `384-toolbars-hidden.png`, `384b-toolbars-revealed.png`, `384c-hide-toolbars-menu.png`;
      Breeze and Breeze Dark.
- [ ] Strings in `qsTr()`, translations complete; README shortcut table and the "Full screen"
      feature bullet updated.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with its own XDG folders under `~/kondor-test` (the maintainer keeps their own
Kondor open).

1. F11: only the page is on screen; move the pointer to the top: toolbars slide in over the page;
   move away: they slide out. F11: back to normal.
2. Ctrl+Shift+F: title bar and page only. Ctrl+L: toolbars and focused address bar; type a URL,
   Enter: page loads and the toolbars hide. Open the main menu from the revealed toolbar: they stay
   while it is open; uncheck Hide Toolbars there.
3. Restart: the setting is kept. Open a second window: same state.
4. Vertical tabs: the side bar returns at the left edge.
5. Ctrl+F with toolbars hidden: the find bar shows.

## Out of scope

- Hiding the window decoration (that is F11).
- Per-window or per-site toolbar settings, a separate "hide only the tab strip" option.
- Touch gestures to reveal the toolbars.

## Dependencies

- #8 Fullscreen (replaces its "keep the toolbar in F11" decision), #211 Tab styles, #212 Vertical
  tabs, #93 main menu.

## Prototype

- [`prototypes/384-toolbars-hidden.qml`](../../prototypes/384-toolbars-hidden.qml) →
  [screenshot](../../prototypes/screenshots/384-toolbars-hidden.png)
- [`prototypes/384b-toolbars-revealed.qml`](../../prototypes/384b-toolbars-revealed.qml) →
  [screenshot](../../prototypes/screenshots/384b-toolbars-revealed.png)
- [`prototypes/384c-hide-toolbars-menu.qml`](../../prototypes/384c-hide-toolbars-menu.qml) →
  [screenshot](../../prototypes/screenshots/384c-hide-toolbars-menu.png)
  (`withHideToolbars` in `prototypes/common/MainMenuMock.qml`)

## Decisions

| Question | Decision |
| --- | --- |
| Keep the toolbar in F11, as #8 decided? | No, the maintainer's choice: F11 shows only the page, like Firefox and Chrome. Replaces #8's decision. |
| Reveal by pushing the page down or over it? | Over it: pushing would reflow the page every time the pointer touches the top. |
| Reveal right away at the top edge? | After 300 ms resting there, so moving to a tab of another window or to the title bar does not flash the toolbars. |
| Hide the InlineBars and find bar too? | No: they ask for an answer or show what the user is doing; hiding them would hide a question. |
| Name and place? | A checkable "Hide Toolbars" in the main menu under the zoom row, unchecked by default: the maintainer's choice over KDE's usual "Show Toolbar" wording (first proposal), because the action is the exception and reads as what it does. Ctrl+Shift+F because Ctrl+M (KDE's "Show Menubar") is Mute Tab in Kondor. |
| Remember it? | Yes, globally: it is how the maintainer wants to browse; the top-edge reveal and Ctrl+L keep it discoverable. |
