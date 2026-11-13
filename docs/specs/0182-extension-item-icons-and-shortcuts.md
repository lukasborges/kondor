# Extension menu items: icons and keyboard shortcuts (#182)

> **Issue:** [#182](https://github.com/lukasborges/kondor/issues/182) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Make the actions on level 2 of the Extensions panel (#183) look like KDE menu items:

- **Icon:** the item's `icon`, when it names an icon of the current theme.
- **Shortcut:** the page shortcut that runs the same action, read from one of the extension's own
  `keys` settings. It is right-aligned in `disabledTextColor`.

Video Speed Controller already has page shortcuts (S, D, R, V) in its settings, but nobody can
discover them from the panel.

This issue covers **Kondor only**. The catalog schema, its validator and Video Speed Controller
adopt the new field in #194 (`lukasborges/kondor-extensions`), which comes right after this one.

## Context

- **Manifest:** `action.items[]` already has `id`, `title`, an optional `checkable` and an optional
  `icon` (spec 0107 §1). Unknown keys are ignored.
  - **Validation:** `actionError()` in `src/extensions/manifest/manifestsections.cpp` (113 lines),
    called by `ManifestValidator::checkAction()`.
  - **Settings:** `settings[]` entries have `key` and `type`, and `keys` is one of the types. A
    `keys` value is a string such as `"S"` or `"Ctrl+Shift+S"`, edited with a `TextField`
    (`ExtensionSettingControls.qml` falls back to `stringControl`).
- **Item maps:** `LocalizedManifest::localizedActionItem()` (`src/extensions/manifest/localizedmanifest.cpp`)
  builds `{id, title, checkable, icon}`.
  - `actionEntry()` in `src/extensions/extensionqueries.cpp` puts them in `items` of each
    `ExtensionManager::actionExtensions()` entry.
  - Today `icon` is passed through unchecked: any string, including a path or URL, reaches
    `Kirigami.Icon.source`.
- **Current values:** `ExtensionManager::settingValues(id)` gives the defaults merged with the
  stored values. Changing a setting calls `changed()`, so `ExtensionManager.revision` changes, and
  the panel already rebuilds its data on every `revision` change while open.
- **Panel rows:**
  - `qml/extensions/panel/ExtensionActionRow.qml` is a plain item: an `ItemDelegate` with an
    icon slot and the title.
  - `qml/extensions/panel/ExtensionActionEntry.qml` loads either that row or a `CheckBox` for
    checkable items.
- **Folder limits:**
  - `src/extensions/` and `src/extensions/manifest/` hold 10 files each, so new C++ goes into a
    new sub-feature folder, `src/extensions/action/`;
  - `qml/extensions/panel/` holds 10 files, so the QML changes stay in the existing files;
  - `tests/extensions/` holds 9 files, so the new C++ test goes into a new folder,
    `tests/extensions/action/`.

## Design / behavior

### 1. Manifest field `keysSetting`

- **Field:** `action.items[].keysSetting`, optional, a string.
- **Validation:** when present, it must be the `key` of a setting of the same manifest whose
  `type` is `"keys"`. Otherwise the install fails with:

  `manifest.json: action.items[<i>].keysSetting: must name a keys setting`

  - **Where:** in `manifestsections.cpp`. `actionError` gets the settings as a second parameter:
    `QString actionError(const QJsonValue &action, const QJsonValue &settings)`.
    `ManifestValidator::checkAction()` passes `m_manifest.value("settings")`. Settings are
    validated before the action, so `settings` is a valid list there.
  - **Size:** the item check stays a set of small functions, and the file stays under 200 lines.
- **Icon:** `icon` is **not** validated at install. Themes differ between machines, so it is
  resolved when shown (§2).
- **Item map:** `localizedActionItem()` also copies `keysSetting` (an empty string when absent).

### 2. Display data: `ActionItemDisplay` (`src/extensions/action/actionitemdisplay.{h,cpp}`)

- **API:** a namespace with one public function:

  ```cpp
  namespace ActionItemDisplay {
  QVariantList forDisplay(const QVariantList &items, const QVariantMap &settingValues);
  }
  ```

  It returns the items with two fields replaced or added:

  | Field | Value |
  | --- | --- |
  | `icon` | The item's `icon` when it is a plain theme icon name (`^[A-Za-z0-9_.-]+$`) **and** `QIcon::hasThemeIcon(icon)`. Otherwise `""`. A path, a URL or a missing icon shows nothing. |
  | `shortcut` | When `keysSetting` is not empty: `QKeySequence::fromString(value, QKeySequence::PortableText).toString(QKeySequence::NativeText)` of `settingValues[keysSetting]`. Otherwise, and when the value is empty or does not parse (an empty sequence or `Qt::Key_unknown`), `""`. |

- **Use:** `actionEntry()` in `extensionqueries.cpp` calls
  `ActionItemDisplay::forDisplay(package.actionItems(locale), settingValues(id))`. Pinned and
  private entries go through the same path. Private windows read the setting values, which are
  already on disk, and write nothing.
- **Build:** register both files in `cmake/KondorSources.cmake` (`KONDOR_EXTENSION_MANAGER_SOURCES`).
  `Qt6::Gui` is already linked.
- **Live updates:** no new signal is needed. Changing a `keys` setting changes `revision`, so the
  shortcut text updates when the panel is opened next or rebuilds while open.

### 3. Panel rows (level 2)

Match [`prototypes/183b-extensions-panel-actions.qml`](../../prototypes/183b-extensions-panel-actions.qml).

- **Plain items** (`ExtensionActionRow.qml`): after the title, add a `Label`:
  - `text: item.shortcut`, `color: Kirigami.Theme.disabledTextColor`;
  - `visible` only when the text is not empty. The title keeps `Layout.fillWidth: true`, so the
    shortcut is right-aligned;
  - the icon slot is unchanged: it keeps its width when `icon` is empty, so titles line up.
- **Checkable items** (`ExtensionActionEntry.qml`, `checkRow`): a `RowLayout` with the existing
  `CheckBox` (`Layout.fillWidth: true`) and the same shortcut `Label`.
  - It keeps the left margin it has today.
  - Its right margin is `Kirigami.Units.smallSpacing`, so the shortcut lines up with the plain
    rows' shortcuts.
  - Checkable items still show no item icon: the check box is their visual.
- **Shared label:** the shortcut `Label` is the same in both rows. Keep it inline in each row: the
  `panel/` folder is full, and the label is a single control.
- **Accessibility:** the row's `Accessible.name` stays the title, and `Accessible.description` is
  `item.shortcut`. It adds no new string.
- **Display only:** the shortcut is never registered as a Kondor `Shortcut`. The page script
  handles the key, as today.
- **Right-to-left:** the `RowLayout` mirrors, so the shortcut is on the left.

### 4. Strings and README

- No new user-visible strings: titles and key names come from the extension and from Qt.
- `README.md` stays unchanged.

### 5. Tests

- **`tests/extensions/manifest/tst_manifestvalidator.cpp`:** add rows to
  `reportsTheFirstErrorWithTodaysText_data`:
  - `keysSetting unknown`: names no setting;
  - `keysSetting not keys`: names a `bool` setting.

  Add `acceptsKeysSettingOfKeysType`.
- **`tests/extensions/action/tst_actionitemdisplay.cpp`** (new), registered like the other
  extension tests:
  - `shortcutShowsCurrentKeysValue` (`"Ctrl+S"` → the native text);
  - `itemWithoutKeysSettingHasNoShortcut`;
  - `unparsableKeysValueHasNoShortcut`;
  - `missingThemeIconIsDropped`;
  - `iconPathOrUrlIsDropped` (`/tmp/x.png`, `file:///tmp/x.png`, `https://example.com/x.png`).
- **`tests/extensions/tst_extensionspanel.cpp`:**
  - `actionRowShowsShortcut`: a plain item with `keysSetting` shows its value;
  - `checkableRowShowsShortcut`;
  - `shortcutFollowsChangedSetting`: `applyConfiguration` with a new value updates the open panel.

  The sample extension (`tests/data` or `installPlain`) gets a `keys` setting for this. Keep the
  file under 200 lines; move helpers to `panelfixture.h` if needed.

## Acceptance criteria

- [ ] An item with `keysSetting` naming a `keys` setting shows that setting's current value as the
      shortcut, right-aligned in `disabledTextColor`, on plain and checkable rows. This matches
      `prototypes/screenshots/183b-extensions-panel-actions.png`.
- [ ] Changing the setting in the extension's settings dialog changes the shortcut shown in the
      panel.
- [ ] A `keysSetting` that names no setting, or a setting of another type, is rejected at install
      with the message in §1.
- [ ] An `icon` that is not a theme icon name of the current theme (missing, a path or a URL)
      shows an empty icon slot. Titles stay aligned.
- [ ] Nothing new is written to disk, and private windows behave like normal ones (read only).
- [ ] The tests in "Design → Tests" exist and pass, `ctest` passes, and the smoke test prints no QML
      errors.
- [ ] `scripts/check-code-quality.py --changed origin/main` is clean, and the folder limits hold.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. Copy `extensions/video-speed` from `lukasborges/kondor-extensions` to a temporary directory. In
   its `manifest.json`, add the following to the `action.items`:
   - `"icon": "media-seek-backward", "keysSetting": "keySlower"` to **Slower**;
   - `"icon": "media-seek-forward", "keysSetting": "keyFaster"` to **Faster**;
   - `"icon": "edit-undo", "keysSetting": "keyReset"` to **Reset Speed**;
   - `"keysSetting": "keyOverlay"` to **Show Speed Overlay**.

   Pack it with `python3 tools/pack.py` and install it with **Install from File…**.
2. Open `https://www.youtube.com/`, open the Extensions panel and then Video Speed Controller. The
   rows show the icons and S, D, R and V, right-aligned, as in the prototype.
3. Click **Settings…**, set **Faster** to `Shift+F` and click OK. Reopen the panel: **Faster** shows
   `Shift+F`.
4. Change one icon to `no-such-icon` and one to `/usr/share/icons/hicolor/48x48/apps/kondor.png`.
   Repack and reinstall: both rows have an empty icon slot, and the titles line up.
5. Set `"keysSetting": "speedStep"` (a number setting) and repack. **Install from File…** shows
   "manifest.json: action.items[1].keysSetting: must name a keys setting".

## Out of scope

- The `kondor-extensions` schema, validator and Video Speed Controller manifest: these are #194.
- Running the shortcut from Kondor, or showing it anywhere else (pinned button tooltips, settings
  page).
- Icons for checkable items.
- A stepper row (− 1.25× +), as in the main menu's zoom row: it needs a new item type and its own
  design.
- Validating icons at install, or bundling icon files with an extension.

## Dependencies

- #183 Extensions panel (merged).
- #194 builds on this issue.

## Prototype

- Level 2 with icons and shortcuts, including a checkable row:
  [`prototypes/183b-extensions-panel-actions.qml`](../../prototypes/183b-extensions-panel-actions.qml),
  rendered in
  [`prototypes/screenshots/183b-extensions-panel-actions.png`](../../prototypes/screenshots/183b-extensions-panel-actions.png).

## Decisions

| Question | Decision |
| --- | --- |
| Keep the manifest and the catalog changes in one issue? | No. Kondor first (#182), then the catalog and Video Speed Controller (#194), so each issue has one PR in one repository. |
| A literal `shortcut` string in the manifest? | Rejected. It would go stale when the user changes the key in the extension's settings. `keysSetting` points at the setting, so the panel always shows the current key. |
| Validate `icon` at install? | No. Themes differ between machines. The icon is checked at display time with `QIcon::hasThemeIcon`, and only plain names are accepted, so no path or URL reaches `Kirigami.Icon`. |
| Shortcut on checkable items too? | Yes, for consistency: Video Speed Controller's overlay toggle has a key (V). The prototype was updated to show it (kde-ux review). |
| Register the shortcut in Kondor? | No. It stays display-only, and the page script keeps handling the key, as the extension's settings describe. |
| Accessible text for the shortcut? | `Accessible.description` = the shortcut, with no new translatable string. |
