# Tab styles: floating tabs by default, with a setting (#211)

> **Issue:** [#211](https://github.com/lukasborges/kondor/issues/211) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Give the tab strip a modern look that still follows Breeze, and let the user pick the style:

- **Floating** (new default): the tab strip and the toolbar form one header, and the active tab is a
  rounded card in the toolbar color.
- **Below Address Bar:** the tabs sit under the navigation toolbar, and the active tab uses the
  Breeze selection colors.
- **Classic:** today's Breeze `TabBar`, unchanged.

The choice lives in **Settings → General → Appearance** as a picker with one thumbnail per style.
#212 adds a fourth style, **Side Bar**, on top of this issue.

Today's strip is the stock Breeze `TabBar`: every tab has a border, inactive tabs are grey blocks
next to each other, and only a thin blue line marks the active tab. It reads like a KDE 4 dialog,
not like a browser.

## Context

- **When:** during the Python port. **Port twin rule** (umbrella #162, "The freeze"): this issue runs during the port. Every `src/` change goes into the C++ class and its Python twin in `kondor/` in the same PR, with a C++ test and a pytest test, and `check-qml-api.py` must pass. QML is shared by both apps. Here that means
  `Settings.tabStyle` in `src/core/settings/` and in the Python `Settings` (#164). The QML files
  below are the same in both apps.
- **Tab strip:** `qml/browser/tabstrip/TabStrip.qml`, a `Rectangle` in the `Header` color set with a
  `RowLayout`: the private window icon, the left scroll button, a `TabBar` (`background: null`),
  the right scroll button and the new tab button. The other files of the folder add the behavior:
  - `TabButtonDelegate.qml` (icon or `BusyIndicator`, title, close button);
  - `TabDragHandler.qml` and `TabSlideAnimation.qml` (reordering by drag);
  - `TabWidthFreeze.qml` (widths stay frozen while closing with the mouse);
  - `TabStripScroller.qml`, `TabStripScrollButton.qml`, `TabStripWheel.qml` (overflow);
  - `TabStripTaps.qml` (double-click on empty space), `TabContextMenu.qml`.
- **Widths:** `standardTabWidth` 240, `minimumTabWidth` 120, `pinnedTabWidth` 36, unchanged.
- **Header:** `qml/app/BrowserWindow.qml` → `header: ColumnLayout { TabStrip; NavigationToolBar;
  BookmarksBar }`.
- **Settings:** the `Settings` singleton (one property per option, `defaultValue(name)`), and
  `qml/settings/SettingsDraft.qml` (`optionNames`, `values`, Apply / OK / Defaults).
  `qml/settings/pages/GeneralSettingsPage.qml` is a `StackLayout` with the tabs **Startup** and
  **New Tabs**.
- **Folder limits:** `qml/browser/tabstrip/` already holds 10 files. New files go in a
  sub-feature folder (`qml/browser/tabstrip/style/`), as AGENTS.md "Code quality" requires.

## Design / behavior

### 1. The setting

- `Settings.tabStyle`: a string, `"floating"` (default), `"below"` or `"classic"`. Any other stored
  value reads as `"floating"`. Written to `Kondor.conf` like the other options.
- It is added to `SettingsDraft` (`optionNames`, `values`), so Apply, OK, Cancel and **Defaults**
  work as for every other option. Defaults restores `"floating"`.
- Applying it restyles **every open window at once**, private windows too, without a restart and
  without reloading any page. Reading the setting in a private window writes nothing.

### 2. Settings → General → Appearance

- A third tab, **Appearance**, after **New Tabs** on the General page.
- One row in a `Kirigami.FormLayout`: the label **Tabs:** (top-aligned,
  `Kirigami.FormData.labelAlignment: Qt.AlignTop`) and a picker in a two-column grid.
- One `ItemDelegate` per style, checkable, `highlighted` when selected. It holds a thumbnail
  (8 × 5 `gridUnit`s, drawn with `Rectangle`s in `Kirigami.Theme` colors only) and the name under it:
  **Floating**, **Below Address Bar**, **Classic**.
- Keyboard: Tab enters the picker on the selected style, the arrow keys move between styles, and
  Space or Enter selects. A visible focus frame shows the focused style.
- Screen readers: `Accessible.role: Accessible.RadioButton`, `Accessible.name` = the style name,
  `Accessible.checked` = selected.
- Copy the thumbnails from `prototypes/common/TabStylePicker.qml`. Put the picker in its own file.

### 3. Floating (default)

- The strip keeps the `Header` color set. The navigation toolbar is unchanged.
- Tabs are `gridUnit * 2` tall with 2 px between them, and `smallSpacing` around the row.
- **Active tab:** a rounded rectangle (`Kirigami.Units.cornerRadius`) filled with the `Window`
  color set's background (the toolbar color), with a 1 px border in `textColor` at 20 % opacity.
- **Hovered inactive tab:** `textColor` at 5 % opacity, same radius. Other inactive tabs have no
  background and no border.
- **Close button:** shown on the active tab and on the hovered tab only. It keeps its space on the
  other tabs (`opacity: 0`, not `visible: false`), so titles do not move on hover. Middle click,
  Ctrl+W and the context menu still close any tab.
- **Keyboard focus** on a tab draws the Breeze focus color as its border.
- **Pinned tabs:** 36 px, icon only, the same card when active.
- The private window icon, the scroll buttons, the new tab button (`tab-new`), the widths, the
  overflow, dragging, the wheel and the context menu behave as today.

### 4. Below Address Bar

- The tab strip moves under the navigation toolbar, above the bookmarks bar, in the `Window` color
  set.
- **Active tab:** `highlightColor` at 20 % opacity with a 1 px `highlightColor` border, radius
  `cornerRadius`, like a selected item in Dolphin or System Settings.
- Hover, the close button, focus, pinned tabs and every behavior are the same as in Floating.

### 5. Classic

- Exactly today's strip: the Breeze `TabButton` background, the close button on every tab.

### 6. Code layout

- One `TabStrip` with a `tabStyle` property. Classic keeps today's `TabButton` background; Floating
  and Below set `background:` on the same delegate. The behavior files do not fork per style.
- `BrowserWindow` orders the header by style: strip then toolbar (Floating, Classic), or toolbar
  then strip (Below).

## Acceptance criteria

- [ ] `Settings.tabStyle` exists with the default `"floating"`; unknown values read as
      `"floating"`; it is part of `SettingsDraft`, and Defaults restores it.
- [ ] Settings → General has an **Appearance** tab with the **Tabs:** picker, matching
      `prototypes/211e-settings-tab-style.qml`.
- [ ] The picker works with the keyboard only, and a screen reader reads each style as a radio
      button with its name and state.
- [ ] Floating matches `prototypes/211-tab-style-floating.qml`, and with 16 tabs in a private window
      matches `prototypes/211b-tab-style-floating-many.qml`.
- [ ] Below Address Bar matches `prototypes/211c-tab-style-below.qml`.
- [ ] Classic looks exactly as before this issue (`prototypes/211d-tab-style-classic.qml`).
- [ ] Changing the style applies to every open window at once, without a restart or a page reload.
- [ ] In all three styles: drag to reorder, pinned tabs, overflow scrolling, middle click,
      double-click on empty space, the context menu and the loading spinner work as before.
- [ ] Only `Kirigami.Theme` colors and `Kirigami.Units` sizes: no hex colors. All three styles
      render correctly with Breeze Dark.
- [ ] New strings are in `qsTr()`, and `i18n/*.ts` are updated (the CI translations check passes).
- [ ] README "Features" mentions the tab styles.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Start Kondor with a new profile: the tabs are Floating. Open five tabs, pin one, and hover an
   inactive tab: only it and the active tab show a close button.
2. Open 16 tabs: they shrink to 120 px and the scroll arrows appear. Drag a tab to a new position.
3. Open Settings → General → Appearance. Using only the keyboard, select **Below Address Bar** and
   press Apply: the tabs move under the address bar in every open window, and no page reloads.
4. Select **Classic** and click OK: the old Breeze tabs come back.
5. Click **Defaults** on the Appearance tab, then OK: the style is Floating again.
6. Switch the system color scheme to Breeze Dark and check all three styles.
7. Open a private window and change the style: it follows, and nothing is written about it.

## Out of scope

- The **Side Bar** style (#212).
- A different style per window, custom colors, tab height or width settings.
- New animations; the existing slide animation stays.
- Any change to the navigation toolbar or the bookmarks bar, apart from their order in Below.

## Dependencies

- #164 (the Python `Settings`, for the twin rule).
- #3 Settings page, #12 tab management, #83 tab widths and overflow.
- #212 builds on this issue.

## Prototype

- Floating, six tabs, one pinned, one loading, one hovered:
  [`prototypes/211-tab-style-floating.qml`](../../prototypes/211-tab-style-floating.qml),
  [screenshot](../../prototypes/screenshots/211-tab-style-floating.png).
- Floating, 16 tabs, private window, overflow:
  [`prototypes/211b-tab-style-floating-many.qml`](../../prototypes/211b-tab-style-floating-many.qml),
  [screenshot](../../prototypes/screenshots/211b-tab-style-floating-many.png).
- Below Address Bar:
  [`prototypes/211c-tab-style-below.qml`](../../prototypes/211c-tab-style-below.qml),
  [screenshot](../../prototypes/screenshots/211c-tab-style-below.png).
- Classic (today):
  [`prototypes/211d-tab-style-classic.qml`](../../prototypes/211d-tab-style-classic.qml),
  [screenshot](../../prototypes/screenshots/211d-tab-style-classic.png).
- Settings → General → Appearance:
  [`prototypes/211e-settings-tab-style.qml`](../../prototypes/211e-settings-tab-style.qml),
  [screenshot](../../prototypes/screenshots/211e-settings-tab-style.png).
- Shared mocks: `prototypes/common/TabStyleFrame.qml`, `TabStyleTabs.qml`, `TabStylePicker.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| Which style is the default? | Floating, chosen by the maintainer. The others stay available in Settings, Classic included. |
| A list of radio buttons with the style names? | Rejected. "Floating" or "Classic" mean nothing without seeing them. A thumbnail picker, like the System Settings appearance pages, shows the difference. |
| Active tab color in Floating: the page color (`View`) or the toolbar color (`Window`)? | The toolbar color. The active tab then reads as part of the toolbar below it, as in current browsers. A white card looked detached from the page, with the toolbar in between. |
| Close button on every tab in Floating and Below? | No: only on the active and the hovered tab, to keep the strip calm. Its space stays reserved, so nothing moves on hover. Middle click, Ctrl+W and the context menu close any tab, also on touch. Classic keeps a close button on every tab. |
| Hover as strong as the active tab? | Rejected after the first render: with 8 % opacity the hovered tab competed with the active one. 5 % for hover. |
| Style per window? | No. One global setting; per-window styles add state for no clear use. |
