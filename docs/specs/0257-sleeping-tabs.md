# Sleeping tabs: unload idle tabs to free memory (#257)

> **Issue:** [#257](https://github.com/lukasborges/kondor/issues/257) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Tabs that have not been used for a while **go to sleep**: Qt WebEngine discards their page, which
frees its memory, and the page loads again when the user selects the tab. Sleeping tabs keep their
title and favicon and look dimmed in the tab strip and the side bar. The user can also put a tab to
sleep from its context menu, and can turn the feature off or change the idle time in Settings.

## Context

- **App:** Python + PySide6 since #174 (`src/kondor/`); `qml/` is the UI. There is no C++ twin any
  more.
- **One `WebEngineView` per tab:** `qml/app/PageArea.qml` creates a `WebViewTab` for every row of
  the window's `TabModel`, with `visible: root.tabs.currentTab === tab`. Only the current tab of a
  window is visible.
- **Tab bridge:** `src/kondor/browser/tabs/tab.py` (`Tab`, 106 lines) with its state in
  `tabloadstate.py` / `tabviewstate.py`, its commands in `tabcommands.py` (108 lines), and feature
  groups in `src/kondor/browser/tabs/features/` (`tab.security`, `tab.permissions`,
  `tab.passwords`, `tab.siteReload`, `tab.extensionItems`), each a `CONSTANT` property.
- **View side:** `qml/browser/view/WebViewTab.qml` (172 lines) wires the per-tab helpers
  (`PageZoom`, `ReaderMode`, `PageOutput`, `TabCommands`, …) to `PageView.qml` (the
  `WebEngineView`, 136 lines). `qml/browser/view/` has 9 files.
- **Tab model:** `src/kondor/browser/tabs/tabmodel.py` → `tabmodelclosing.py` → `tabmodelrows.py`
  (`currentTab`, `currentTabChanged`, `notify_current_changed()`). One `TabModel` per window.
  `src/kondor/browser/tabs/` has 9 counted files.
- **Tab looks:** `qml/browser/tabitem/TabIcon.qml` (favicon or busy indicator) and `TabInfo.qml`
  (title and icon source) are shared by the tab strip (`qml/browser/tabstrip/TabButtonDelegate.qml`),
  the side bar rows (`qml/browser/sidebar/SideBarTabRow.qml`) and the side bar's pinned buttons
  (`SideBarPinnedButton.qml`).
- **Tab context menu:** `qml/browser/tabstrip/TabContextMenu.qml` (68 lines), opened from the strip
  and the side bar through `WindowTabController.openTabContextMenu`.
- **Settings:** options in `src/kondor/core/settings/settingsoptions.py` (keys) and
  `settingsdefaults.py` (defaults), normalization in `settings.py`; the dialog's draft in
  `qml/settings/SettingsDraft.qml`, the catalog in `qml/settings/SettingsPages.qml`, the General
  page's tab bar in `qml/settings/SettingsPageHeader.qml`, and its tabs in
  `qml/settings/pages/GeneralSettingsPage.qml` (165 lines: Startup, New Tabs, Appearance).
- **Qt WebEngine lifecycle API** (`WebEngineView`, Qt ≥ 6.8):
  - `lifecycleState`: `WebEngineView.Active`, `Frozen` or `Discarded`, writable;
  - `recommendedState`: read-only, `Active` while the view is visible, inspected by DevTools, or
    playing or capturing audio/video;
  - a visible view must stay `Active`; a `Discarded` view keeps its URL and navigation history and
    reloads the current entry when it becomes `Active` again.

## Design / behavior

### 1. Settings (Python)

Two new options, in `settingsoptions.py` / `settingsdefaults.py`:

| Property | Key | Type | Default |
| --- | --- | --- | --- |
| `tabSleepEnabled` | `Tabs/SleepEnabled` | bool | `True` |
| `tabSleepMinutes` | `Tabs/SleepAfterMinutes` | int | `30` |

- `tabSleepMinutes` only takes the values `15, 30, 60, 120, 240`. Any other value (read from the
  file or written) is normalized to `30`, like `tabStyle` in `settings.normalized()`. Name the
  tuple `TAB_SLEEP_MINUTES` and the fallback `DEFAULT_TAB_SLEEP_MINUTES`.

### 2. `tab.sleep`: a new feature group (Python)

New file `src/kondor/browser/tabs/features/tabsleep.py`, class `TabSleep(QObject)`, owned by the
`Tab` and exposed as `sleep = Property(TabSleep, …, constant=True)` (same pattern as
`tab.siteReload`).

- **State** (view → `Tab`):
  - `sleeping` (`bool`, read-only, `NOTIFY sleepingChanged`);
  - `@Slot(bool) setSleeping(sleeping)`, emitting only on a real change (`assign_and_notify`).
- **Commands** (UI/scheduler → view):
  - `@Slot() putToSleep()` → `sleepRequested()`: the user asked from the context menu;
  - `@Slot() requestIdleSleep()` → `idleSleepRequested()`: the scheduler found the tab idle.
- **Idle time** (Python only, not exposed to QML), measured on a monotonic clock in seconds:
  - `mark_active()`: the tab became the current tab; it is not idle;
  - `mark_inactive(now)`: the tab stopped being current (or was created in the background) at `now`;
  - `inactive_seconds(now) -> float`: `0` while active, else `now - inactive since`.
  - A new tab starts inactive at its creation time; it becomes active when it is selected.

### 3. The scheduler (Python)

New file `src/kondor/browser/tabs/tabsleepscheduler.py` (the 10th file of the folder, the limit),
class `TabSleepScheduler(QObject)`. The `TabModel` creates one in its constructor (a child of the
model), so every window has its own.

- **Current tab:** it listens to the model's `currentTabChanged`; the previous current tab (if it is
  still in the model) gets `mark_inactive(now)`, the new one `mark_active()`. A tab added in the
  background starts inactive (2).
- **Timer:** a `QTimer` with a 60 s interval calls `check()`. `check()` reads the clock once and
  calls `tab.sleep.requestIdleSleep()` on every tab that **may sleep**.
- **May sleep** (a pure function, `may_sleep(tab, now, settings)` or similar, tested on its own):
  - `Settings.tabSleepEnabled` is on;
  - the tab is not the model's current tab;
  - the tab is not `pinned` (see "Decisions");
  - the tab is not already `sleep.sleeping`;
  - the tab is not on the New Tab page (`newTabPage`), not `crashed`, not in `readerActive` and has
    no `devToolsOpen`;
  - `sleep.inactive_seconds(now) >= Settings.tabSleepMinutes * 60`.
- **Clock:** the constructor takes the clock as an optional parameter
  (`clock: Callable[[], float] = time.monotonic`) so tests move time without waiting.
- A tab that the view refuses to put to sleep (4) is asked again at the next tick; that is expected.

### 4. The view: `PageSleep.qml` (QML)

New component `qml/browser/view/PageSleep.qml` (the 10th file of the folder), instantiated in
`WebViewTab.qml` next to `PageZoom`, with `required property Tab tab` and
`required property WebEngineView webView`. It is the only place that touches `lifecycleState`.

- **Idle sleep** (`onIdleSleepRequested`):
  1. return if the view is visible or `webView.recommendedState === WebEngineView.Active` (it plays
     audio or video, captures the camera, microphone or screen, or is being inspected);
  2. run a script in `WebEngineScript.ApplicationWorld` that answers whether the page has **edited
     form fields**: an `input` or `textarea` whose `value` differs from its `defaultValue`, a
     checkbox or radio whose `checked` differs from `defaultChecked`, or a `select` option whose
     `selected` differs from `defaultSelected` (main frame only);
  3. in the callback, if nothing is edited and the view is still not visible, set
     `webView.lifecycleState = WebEngineView.Discarded`.
- **Manual sleep** (`onSleepRequested`): if the view is not visible, set
  `lifecycleState = WebEngineView.Discarded` at once. The user asked, so audio, video and edited
  forms do not stop it (see "Decisions").
- **State:** `onLifecycleStateChanged` (on the `WebEngineView`) calls
  `tab.sleep.setSleeping(webView.lifecycleState === WebEngineView.Discarded)`.
- **Waking up:** when the `WebViewTab` becomes visible (the tab was selected) and the view is not
  `Active`, set `lifecycleState = WebEngineView.Active`; the page loads its current history entry
  again (same URL, back/forward history kept). Do it before anything else reacts to the visibility,
  so Qt never sees a visible discarded view.
- **Title, URL and favicon stay:** while `tab.sleep.sleeping` is true, `PageView.qml` must not pass
  an empty title, an empty or `about:blank` URL, or an empty icon to the `Tab` (discarding may
  clear them in the view). The tab keeps what it showed before it slept, so the tab strip, the
  session file and Reopen Closed Tab still see the real page.
- **Reload while asleep:** **Reload** from the tab's context menu on a sleeping tab wakes it
  (`lifecycleState = Active`) instead of calling `reload()` on the discarded view.

### 5. Look: a sleeping tab is dimmed (QML)

Prototypes `257-sleeping-tabs.qml` (floating tab strip) and `257b-sleeping-tabs-vertical.qml`
(side bar).

- `TabIcon.qml`: the favicon `Kirigami.Icon` gets `opacity: 0.5` while the tab sleeps. This dims
  the icon everywhere: the strip, the side bar rows and the pinned buttons.
- The title `Label` of `TabButtonDelegate.qml` and of `SideBarTabRow.qml` gets
  `enabled: !tab.sleep.sleeping` (the theme's disabled text color).
- The tab itself stays fully enabled: hover, click, drag, close button and context menu work as
  for any other tab.
- **Words for screen readers:** `TabInfo.qml` gets `readonly property bool isSleeping` and
  `readonly property string stateDescription` (`qsTr("Sleeping")` while asleep, else `""`). The
  strip delegate, the side bar row and the pinned button set `Accessible.description:
  info.stateDescription`. No visible label is added.

### 6. Context menu: **Put Tab to Sleep** (QML)

Prototype `257-sleeping-tabs.qml`.

- New `MenuItem` in `TabContextMenu.qml`, right after **Pin Tab / Unpin Tab**:
  - `text: qsTr("Put Tab to Sleep")`, `icon.name: "system-suspend"`;
  - `onTriggered: menu.tab.sleep.putToSleep()`;
  - `enabled` only when the tab may be put to sleep by hand, in a small function
    `canPutToSleep()`: a tab is set, it is **not the window's current tab**, it is not already
    sleeping, not on the New Tab page, not crashed, and has no DevTools open.
- Pinned tabs can be put to sleep from the menu (the automatic timer skips them).
- There is no "Wake Up" item: selecting the tab wakes it.

### 7. Settings dialog: General → **Performance** (QML)

Prototype `257c-settings-sleeping-tabs.qml`.

- `SettingsPageHeader.qml`: a fourth `TabButton { text: qsTr("Performance") }` after Appearance.
- New file `qml/settings/pages/GeneralPerformanceTab.qml` (a `ScrollView` + `Kirigami.FormLayout`
  like the other General tabs), added as the fourth child of the `StackLayout` in
  `GeneralSettingsPage.qml` with `draft: root.draft`. Keeping it in its own file keeps
  `GeneralSettingsPage.qml` under 200 lines.
  - `CheckBox`, `Kirigami.FormData.label: qsTr("Memory:")`,
    `text: qsTr("Put inactive tabs to sleep")`, bound to `draft.tabSleepEnabled` (with a `Binding`
    and `onToggled`, like `topSitesCheck`).
  - `ComboBox`, `Kirigami.FormData.label: qsTr("Sleep after:")`, `enabled` only while the check box
    is checked, bound to `draft.tabSleepMinutes`. Entries, in this order:
    `qsTr("%n minute(s)", "", 15)`, `qsTr("%n minute(s)", "", 30)`, `qsTr("%n hour(s)", "", 1)`,
    `qsTr("%n hour(s)", "", 2)`, `qsTr("%n hour(s)", "", 4)`, mapped to `15, 30, 60, 120, 240`
    (`textRole` / `valueRole` with `indexOfValue`).
- `SettingsDraft.qml`: `tabSleepEnabled` and `tabSleepMinutes`, in `optionNames` and `values`.
- `SettingsPages.qml`, General page: `options` gets `"tabSleepEnabled", "tabSleepMinutes"` (so
  **Defaults** resets them), `keywords` gets `qsTr("Performance")`, `qsTr("Memory:")`,
  `qsTr("Put inactive tabs to sleep")` and `qsTr("Sleep after:")` (the search field finds them).
- Changes apply with OK/Apply like every other option. Turning the feature off does not wake tabs
  that are already asleep; it only stops new ones from sleeping.

### 8. Private tabs

Sleeping works the same in private tabs and private windows. The discarded page keeps its own
off-the-record profile (owned by the tab), so its cookies and cache in memory survive the sleep.
Nothing about sleep is written to disk: the idle time and the `sleeping` state live only in memory,
and the session file is not changed by this issue.

### 9. Strings, README

- **New strings:** "Put Tab to Sleep", "Sleeping", "Performance", "Memory:", "Put inactive tabs to
  sleep", "Sleep after:", "%n minute(s)", "%n hour(s)" (with every plural form filled).
- **Translations:** run `update_translations` and translate every new string in every
  `i18n/*.ts` file, with no `unfinished` messages.
- **`README.md`:** add to the tabs group of "Features": **Sleeping tabs**: idle tabs free their
  memory and reload when selected.

### 10. Tests (pytest, through `scripts/run-pytests.sh`)

- `tests/browser/tabs/features/test_tabsleep.py`: `setSleeping` notifies only on a change;
  `putToSleep` emits `sleepRequested`; `requestIdleSleep` emits `idleSleepRequested`;
  `inactive_seconds` is `0` while active and grows after `mark_inactive`.
- `tests/browser/tabs/test_tabsleepscheduler.py` (fake clock): an idle background tab is asked to
  sleep after the limit and not before; the current tab, a pinned tab, a sleeping tab, a New Tab page
  tab, a crashed tab, a tab in reader mode and a tab with DevTools open are never asked; selecting a
  tab resets its idle time; turning `tabSleepEnabled` off stops requests; `tabSleepMinutes` is
  followed after a change.
- `tests/core/test_settings.py` / `settingsrows.py`: the two keys and defaults; an unknown
  `tabSleepMinutes` normalizes to `30`.
- Settings dialog (in `tests/settings/`): the Performance tab exists; the combo box is disabled when
  the check box is off; Apply writes both options; Defaults restores `True` / `30`.
- Tab context menu: **Put Tab to Sleep** is disabled on the current tab and on a sleeping tab, and
  calls `putToSleep()` on a background tab.
- `PageSleep.qml` with a real `WebEngineView` (as in `tests/extensions/bridge/extensionpageharness.py`):
  a hidden view with a loaded page is discarded by `idleSleepRequested` and `tab.sleep.sleeping`
  becomes true; a hidden view whose page has an edited `<input>` is not discarded; making the view
  visible sets it `Active`, `sleeping` becomes false and the same URL loads again; the tab's title
  is unchanged while asleep.

## Acceptance criteria

- [ ] With the defaults, a background tab not selected for 30 minutes is discarded
      (`lifecycleState` `Discarded`) and `tab.sleep.sleeping` is true; selecting it loads the same
      URL again with its back/forward history kept.
- [ ] The current tab of every window, pinned tabs, tabs playing audio or video or using the camera,
      microphone or screen, tabs with DevTools open, tabs with edited form fields, tabs in reader
      mode, crashed tabs and New Tab page tabs never sleep automatically.
- [ ] **Put Tab to Sleep** (`system-suspend`) in the tab context menu, after Pin Tab, puts a
      background tab to sleep at once (also a pinned one); it is disabled on the current tab, a
      sleeping tab, a New Tab page tab, a crashed tab and a tab with DevTools open.
- [ ] Sleeping tabs keep their title and favicon, with a dimmed icon and title, matching
      `prototypes/257-sleeping-tabs.qml` and `257b-sleeping-tabs-vertical.qml`; screen readers get
      "Sleeping" as the tab's description.
- [ ] Settings → General → Performance matches `prototypes/257c-settings-sleeping-tabs.qml`:
      **Put inactive tabs to sleep** (on by default) and **Sleep after:** 15 minutes … 4 hours
      (30 minutes by default), applied with OK/Apply, reset by Defaults, found by the search field.
- [ ] Private tabs sleep and wake the same way; nothing about them is written to disk.
- [ ] The session file, Reopen Closed Tab and the tab strip show the real URL and title of a
      sleeping tab.
- [ ] The tests of "Design → Tests" exist and pass, with all Python checks of AGENTS.md
      (`ruff`, `mypy --strict`, `scripts/build.py`, `scripts/run-pytests.sh`,
      `scripts/check-qml-api.py`); the smoke test prints no QML errors;
      `scripts/check-code-quality.py --changed origin/main` is clean.
- [ ] Translations complete; `README.md` Features updated.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Open five tabs with real pages (for example kde.org, wikipedia.org, a YouTube video, a page with
   a search form, docs.qt.io). Note the memory of the `QtWebEngineProcess` processes
   (`ps -o rss,cmd -C QtWebEngineProcess`).
2. Settings → General → Performance: the check box is on, **Sleep after:** shows 30 minutes. Pick
   15 minutes, Apply.
3. Start the video and switch to another tab. In the form page, type into the search field without
   submitting, and switch away. Wait 16 minutes without selecting the other tabs.
4. The idle tabs are dimmed; the video tab (still playing) and the form tab are not. A renderer
   process has gone or shrunk.
5. Select a dimmed tab: it loads the same page again and is no longer dimmed; **Back** still goes to
   the page before it.
6. Right-click another background tab → **Put Tab to Sleep**: it dims at once. Right-click the
   current tab: the item is disabled.
7. Pin a tab and wait past the limit: it never sleeps; **Put Tab to Sleep** on it works.
8. Start a large download from a tab, switch away and put that tab to sleep: the download goes on in
   the Downloads panel.
9. With **Open the tabs from last time** on startup, put a tab to sleep, quit and start Kondor: the
   tab comes back with its real title and URL.
10. Open a private window, open two pages, put the background one to sleep and select it again: it
    wakes up and stays logged in on a site where you signed in. No new file appears in the
    temporary data folders for it.
11. Switch the side bar tab style (#212): sleeping rows and pinned buttons are dimmed there too.
12. Turn the check box off, Apply: the combo box is disabled and no more tabs fall asleep.

## Out of scope

- Restoring the session's background tabs asleep at startup (lazy session restore).
- Freezing tabs (`WebEngineView.Frozen`) as an intermediate step.
- A memory-pressure trigger, a per-site "never sleep" list, or showing how much memory a tab uses.
- A "Wake Up" or "Put Other Tabs to Sleep" menu item, a keyboard shortcut, or a main-menu entry.
- Writing the sleeping state to the session file.
- Detecting edits in `contenteditable` elements or in frames.

## Dependencies

- None open. Builds on #12 (tab context menu, pinned tabs), #212 (side bar), #174 (Python app) and
  the Settings block (#3, #57), all closed.

## Prototype

- Floating tab strip with two sleeping tabs and the tab context menu:
  [`prototypes/257-sleeping-tabs.qml`](../../prototypes/257-sleeping-tabs.qml),
  [screenshot](../../prototypes/screenshots/257-sleeping-tabs.png).
- Side bar with sleeping rows and a sleeping pinned tab:
  [`prototypes/257b-sleeping-tabs-vertical.qml`](../../prototypes/257b-sleeping-tabs-vertical.qml),
  [screenshot](../../prototypes/screenshots/257b-sleeping-tabs-vertical.png).
- Settings → General → Performance:
  [`prototypes/257c-settings-sleeping-tabs.qml`](../../prototypes/257c-settings-sleeping-tabs.qml),
  [screenshot](../../prototypes/screenshots/257c-settings-sleeping-tabs.png).
- Shared mocks: `prototypes/common/TabStyleFrame.qml` (`sleeping` on a tab),
  `prototypes/common/SettingsDialogMock.qml` (`withPerformance`).

## Decisions

| Question | Decision |
| --- | --- |
| Do pinned tabs sleep automatically? | No. Pinned tabs are the user's always-on apps (mail, chat, music) that must keep receiving updates; the context menu can still put one to sleep. |
| Do tabs with an active download stay awake? | Not needed: downloads belong to the profile and go on after the page is discarded (checked in the manual test). |
| Which tabs does the automatic timer skip, and who decides? | Python skips what `Tab` already knows (current, pinned, asleep, New Tab page, crashed, reader mode, DevTools). The view also refuses when `recommendedState` is `Active` (audio, video, capture, inspection) or the page has edited form fields, since only the view can see those. |
| Does manual sleep check audio and edited forms? | No: the user asked for it on that tab. It still needs a background tab with no DevTools open. |
| Discard or freeze? | Discard. Freezing saves CPU but keeps the memory, and memory is the goal of this issue. |
| How does a sleeping tab look? | Icon and title dimmed, the tab still fully interactive, "Sleeping" in `Accessible.description` (the #183 dimming rule). A moon badge or a "(sleeping)" suffix in the title was rejected as noise (show, don't tell). |
| Where do the settings go? | A new **Performance** tab in General. Startup, New Tabs and Appearance are about other things, and Privacy is about data. |
| A spin box for the idle time? | No: a combo box with five presets (15 min to 4 h), like Plasma's screen locking delay. Free values add nothing. |
| "Inactive tabs:" as the form label? | Rejected: it repeated the check box text. "Memory:" says why the option exists. |
| Wake-up item in the menu? | No: selecting the tab wakes it, which is what the user wants anyway. |
| Icon of **Put Tab to Sleep**? | `system-suspend` (the Breeze moon), the same image Plasma uses for "Sleep". |
| Lazy session restore? | Out of scope; a later issue can start restored background tabs asleep. |
