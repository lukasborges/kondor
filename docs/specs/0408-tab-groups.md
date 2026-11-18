# Tab groups: named, colored, collapsible groups of tabs (#408)

> **Issue:** [#408](https://github.com/lukasborges/kondor/issues/408) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Keep related tabs together under a name and a color, and collapse a group to its label to save
room, in every tab style.

## Context

- Tabs: `src/kondor/browser/tabs/` (`Tab`, `TabModel`, `tabmodelrows.py`), group objects follow
  the `Tab…` feature pattern (`src/kondor/browser/tabs/features/`).
- Strip: `qml/browser/tabstrip/` (`TabStrip`, `TabButtonDelegate`, `TabContextMenu`, drag in
  `TabDragHandler`); side bar: `qml/browser/sidebar/`.
- Session: `src/kondor/browser/session/` (`SESSION_VERSION = 2`).

## Design / behavior

### 1. Model

- A `TabGroup` (QObject): `name` (may be empty), `color` (one of `blue`, `green`, `orange`, `red`,
  `purple`, `gray`), `collapsed`. `TabModel` owns its groups; `Tab.group` is the group or null.
- A group's tabs are always **contiguous** in the strip. Pinned tabs are never grouped (pinning a
  grouped tab takes it out of its group). A group left with no tab is deleted.
- Colors map to the color scheme so they follow light and dark themes: blue `highlightColor`,
  green `positiveTextColor`, orange `neutralTextColor`, red `negativeTextColor`, purple
  `visitedLinkColor`, gray `disabledTextColor`. Color names are translatable ("Blue"…) and are
  the tooltips and `Accessible.name` of the swatches.

### 2. Horizontal styles (`prototypes/408-tab-groups.qml`)

- Before the group's first tab: the **label**, a rounded rectangle filled with the color at 25 %
  and a 1 px border in the color, holding the bold name (an unnamed group shows a 12 px circle in
  the color instead). Each tab of the group has a 3 px bar of the color along its bottom edge.
- **Left click** on the label collapses / expands the group; **right click** (or Menu key when
  the label has focus) opens the group editor. A collapsed group shows only its label plus the tab
  count in the disabled color. Collapsing the group of the current tab makes the next tab outside
  the group (else the previous one) current; if there is none, the group does not collapse.
- Tab context menu: **Add Tab to Group** submenu with **New Group** (`group-new`), a separator
  and the existing groups (a `color-fill` icon tinted with the group's color, then its name;
  "Unnamed group" when empty). For a grouped tab, the item becomes **Remove Tab from Group**
  (`object-ungroup`) and the submenu lists the other groups as **Move Tab to Group**.
- Adding moves the tab to the end of the group. New Group creates a group with the first color
  not yet used in the window and opens the editor with the name field focused.
- Drag never changes a tab's group (maintainer's decision, #426): a grouped tab is reordered only
  among its group's tabs, after the label; an ungrouped tab drops before or after a group, never
  inside it. Dragging the label moves the whole group. Joining, moving and leaving happen only in
  the tab context menu.

### 3. Group editor (`prototypes/408b-tab-group-edit.qml`)

- A popup under the label: name field (placeholder "Group name", applied as typed), six color
  swatches (the current one checked), separator, then **New Tab in Group**, **Collapse Group** /
  **Expand Group**, **Move Group to New Window**, **Ungroup Tabs** (`object-ungroup`, keeps the
  tabs), **Close Group** (closes its tabs; each can be reopened with Reopen Closed Tab).
- Enter or Esc closes the editor.

### 4. Side bar (`prototypes/408c-tab-groups-vertical.qml`)

- A header row per group: a 10 px dot in the color, the bold name, the count when collapsed and an
  `arrow-down` / `arrow-right`. Its tabs are indented with a 3 px bar of the color at the left.
  Click on the header toggles collapse; right click opens the editor.
- Collapsed side bar (#242): the header is the dot alone (tooltip: the name); collapsing works
  the same.

### 5. Session and privacy

- Groups are saved in the session: `SESSION_VERSION = 3`, each window gets `groups`
  (`name`, `color`, `collapsed`) and each tab an optional `group` index. Version 2 sessions still
  load (no groups).
- Private windows can use groups, but they are never saved (no session for private windows).

## Acceptance criteria

- [ ] New Group, Add / Move / Remove Tab from Group, drag within a group (never across), collapse / expand by click,
      the editor actions, in every tab style.
- [ ] Collapsing the current tab's group switches to the next tab outside it.
- [ ] Groups survive a restart (normal windows); private windows' groups are never written.
- [ ] Version 2 session files still restore.
- [ ] Colors follow Breeze and Breeze Dark; matches `408-tab-groups.png`,
      `408b-tab-group-edit.png`, `408c-tab-groups-vertical.png`.
- [ ] Strings in `qsTr()`, translations complete; README "Tidy tabs" bullet updated.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`.

1. Six tabs; make a group "Work" of two, another unnamed of two; rename it, recolor it; collapse
   "Work" while on one of its tabs.
2. Drag a tab into and out of a group; drag a group by its label.
3. Restart: groups and collapsed state are back. Switch to vertical tabs: same groups in the side
   bar.

## Out of scope

- Saving a group to reopen later, syncing, group-level tab search (#407), more colors or custom
  colors, nested groups.

## Dependencies

- None (uses #211, #212, #242, done).

## Prototype

- [`prototypes/408-tab-groups.qml`](../../prototypes/408-tab-groups.qml) →
  [screenshot](../../prototypes/screenshots/408-tab-groups.png)
- [`prototypes/408b-tab-group-edit.qml`](../../prototypes/408b-tab-group-edit.qml) →
  [screenshot](../../prototypes/screenshots/408b-tab-group-edit.png)
- [`prototypes/408c-tab-groups-vertical.qml`](../../prototypes/408c-tab-groups-vertical.qml) →
  [screenshot](../../prototypes/screenshots/408c-tab-groups-vertical.png)
  (groups in `prototypes/common/TabStyleFrame.qml`)

## Decisions

| Question | Decision |
| --- | --- |
| Fixed hex colors like Chrome? | No: AGENTS.md forbids hardcoded colors; six color-scheme roles give distinct hues that follow light and dark themes. |
| What does a click on the label do? | Collapse / expand, the frequent action (one click, KDE HIG); the editor is on right click, like every other context action in the strip. |
| "Ungroup Tabs" icon | `object-ungroup`, not the red `group-delete` trash: the tabs stay open. |
| Approved | Prototypes approved by the maintainer. |
| May dragging change a tab's group? | No (maintainer, #426): dragging joined groups by accident and could split a group around its label; only the context menu changes groups. Replaces the first rule "dropping between two tabs of a group joins it". |
| Draw the label inside the first tab's delegate? | No (#435, maintainer's request to simplify): that made every close, move and drag re-place the label and bar and produced #433, #434 and stray bars. Labels are rows of a `TabStripModel` that the strip and the side bar share; the rules for moves live only in the Python model and QML only renders. |
