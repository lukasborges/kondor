# Tabs: mute and unmute a tab, with a sound indicator (#366)

> **Issue:** [#366](https://github.com/lukasborges/kondor/issues/366) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Silence one tab without pausing it or leaving it, and see at a glance which tab makes sound. The
maintainer asked for a "Mute Tab" entry in the tab context menu; a mute command is only useful if
the tab that plays sound can be found, so the tab also shows a sound indicator, as in every
mainstream browser.

## Context

- Python app (C++ removed in #174). QML shared folders: `qml/browser/tabstrip/`,
  `qml/browser/tabitem/` (`TabIcon.qml`, `TabInfo.qml`), `qml/browser/sidebar/`,
  `qml/browser/view/` (`WebViewTab.qml`, `PageView.qml`).
- **Tab feature groups** (#144, AGENTS.md "The Tab bridge pattern"): `tab.sleep`, `tab.media`… in
  `src/kondor/browser/tabs/features/` (9 files now; this adds the 10th), owned by `Tab` and exposed
  as `CONSTANT` properties.
- `WebEngineView` has `recentlyAudible` (read-only, true while the page plays sound and about two
  seconds after) and `audioMuted` (read/write).
- Tab context menu: `qml/browser/tabstrip/TabContextMenu.qml` (also used by the side bar).
- Sleeping tabs (#257): audible pages already refuse to sleep (`recommendedState`).

## Design / behavior

### 1. State: `tab.audio`

- New group `TabAudio` (`src/kondor/browser/tabs/features/tabaudio.py`), `Tab.audio` (`CONSTANT`).
  - State, set by the view: `isAudible` (from `recentlyAudible`) and `isMuted` (from `audioMuted`),
    each with a setter and a `NOTIFY` signal emitted only on change.
  - Command: `toggleMuted()` emits `mutedToggleRequested`; the view answers by flipping
    `audioMuted`, and the state flows back through the setter.
- `PageView.qml` / `WebViewTab.qml` bridge both ways, as `PageSleep.qml` does for `tab.sleep`
  (a small `PageAudio.qml` in `qml/browser/view/` if it keeps the files within the limits).
- A sleeping tab (#257) keeps `isMuted`; when it wakes, the new view starts with `audioMuted` set
  from `tab.audio.isMuted`.
- Not saved in the session: a restored tab starts unmuted (decision below). Nothing is written to
  disk, in normal or private tabs.

### 2. Sound indicator (`prototypes/366-mute-tab.qml`, `366b-mute-tab-vertical.qml`)

- **Tabs with a title** (horizontal styles and the expanded side bar): a flat icon-only
  `ToolButton` between the favicon and the title, 20 × 20 with a 16 px icon, shown only while the
  tab is audible or muted:
  - `audio-volume-high-symbolic` when audible and not muted; tooltip and `Accessible.name`
    "Mute Tab";
  - `audio-volume-muted-symbolic` when muted; tooltip and `Accessible.name` "Unmute Tab";
  - `ToolTip.delay: 600`. A click calls `tab.audio.toggleMuted()` and does **not** select the tab.
- **Icon-only tabs** (pinned tabs, collapsed side bar #242): a 10 px emblem with the same icon at the
  favicon's bottom-right corner, overlapping it by 3 px; not a button (the menu and Ctrl+M mute
  them). The tab's accessible name gets ", playing sound" / ", muted" appended.
- The indicator follows the tab's hover/current/sleeping looks like the favicon does (#266 states).

### 3. Context menu

- After **Pin Tab**: **Mute Tab** (`audio-volume-muted`) or, when the tab is muted, **Unmute Tab**
  (`audio-volume-high`). Always enabled, also on a silent tab, so a tab can be muted before it plays.

### 4. Shortcut

- **Ctrl+M** toggles mute of the current tab (`Shortcut` with the other window shortcuts); add it to
  the README shortcut table.

## Acceptance criteria

- [ ] `tab.audio` follows the Tab bridge pattern; pytest for `TabAudio` (state changes notify once,
      `toggleMuted()` only requests).
- [ ] A page playing sound shows the speaker button; clicking it mutes the page (the sound stops,
      the icon becomes muted) without selecting the tab; clicking again unmutes.
- [ ] Pinned tabs and the collapsed side bar show the emblem; menu and Ctrl+M mute them.
- [ ] The context menu shows Mute Tab / Unmute Tab as in the prototypes, in every tab style.
- [ ] A muted tab put to sleep and woken up is still muted.
- [ ] Ctrl+M works and is in the README shortcut table.
- [ ] Nothing written to disk; private tabs behave the same.
- [ ] Strings in `qsTr()`, translations complete.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Isolated XDG dirs (AGENTS.md); a local page with `<audio src="…" autoplay loop>` (a file in
`tests/data/` or generated) avoids network media.

1. Open the page in a background tab: the speaker appears on that tab. Click it: silence, muted
   icon, the current tab did not change. Click again: sound.
2. Right-click the tab: Mute Tab; right-click again: Unmute Tab.
3. Ctrl+M on the current audio tab mutes and unmutes it.
4. Pin the tab: the emblem shows on its icon; Unmute through the menu.
5. Vertical tabs, expanded and collapsed: same behavior as in `366b-mute-tab-vertical.png`.
6. Mute the tab, put it to sleep from the menu, select it: it wakes up muted.
7. Repeat 1 in a private window; nothing new on disk.

## Out of scope

- Muting a whole site or remembering mute per site.
- A volume slider.
- Pausing media (MPRIS, #259, does that).

## Dependencies

- #257 Sleeping tabs, #242 collapsed side bar, #144 Tab feature groups (all done).

## Prototype

- [`prototypes/366-mute-tab.qml`](../../prototypes/366-mute-tab.qml) →
  [screenshot](../../prototypes/screenshots/366-mute-tab.png)
- [`prototypes/366b-mute-tab-vertical.qml`](../../prototypes/366b-mute-tab-vertical.qml) →
  [screenshot](../../prototypes/screenshots/366b-mute-tab-vertical.png)
- Shared mock: `audio: "playing" | "muted"` in `prototypes/common/TabStyleFrame.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| Only a menu item, as asked? | Menu item plus an indicator on the tab: without the indicator the user cannot tell which tab to mute, and the indicator as a button is the one-click path (kde-ux: the common path is one click and visible). |
| Where is the indicator? | Between favicon and title, so it never moves with the close button and stays visible on narrow tabs. Replacing the favicon on hover was rejected: hidden behind hover. |
| Is the menu item enabled on silent tabs? | Yes, to mute a tab before it starts (autoplaying sites). |
| Remember mute across restarts? | No, like Firefox and Chrome: a restored tab plays again, and nothing is added to the session format. |
| Shortcut? | Ctrl+M, Firefox's, free in Kondor. |
