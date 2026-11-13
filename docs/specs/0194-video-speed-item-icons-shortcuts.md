# Video Speed Controller: action item icons and shortcuts (#194)

> **Issue:** [#194](https://github.com/lukasborges/kondor/issues/194) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

#182 taught Kondor to show an icon and a page shortcut on each level-2 row of the Extensions
panel. The shortcut comes from the item's new `keysSetting` field. This issue is the second half,
in `lukasborges/kondor-extensions`:

- the catalog's schema and validator accept `keysSetting` and reject a wrong one, with the same
  rule and message as Kondor;
- Video Speed Controller uses `icon` and `keysSetting`, so its panel rows show S, D, R and V.

## Context

- **Schema:** `schema/manifest.schema.json`, `$defs/actionItem`, has `id`, `title`, `checkable`
  and `icon`. It has no `additionalProperties: false`, so an unknown key passes today without a
  check.
- **Validator:** `tools/kondorlib/schema.py` checks the schema (supports `type`, `pattern`, …).
  `tools/kondorlib/manifest.py` holds the cross-field rules. `check_choice_settings()` is the model
  for a rule that reads `settings`. `check_manifest_rules()` joins them. Rules run only after the
  schema passed (`validation.py`), so `settings[].key`/`type` and `action.items[]` are well formed
  there. Both `settings` and `action` are optional.
- **Kondor's rule (#182, merged):**
  - `action.items[].keysSetting` is optional;
  - when present, it must be the `key` of a setting of the same manifest whose `type` is `keys`;
  - error text: `action.items[<i>].keysSetting: must name a keys setting`.
  - Older Kondor builds ignore the unknown key, so the manifest's `"kondor": 1` stays.
- **Video Speed Controller:** `extensions/video-speed/manifest.json`, version `1.0.0`.
  - **Keys settings:** `keySlower` (S), `keyFaster` (D), `keyReset` (R) and `keyOverlay` (V).
  - **Action items:** `slower`, `faster`, `reset` and `show-overlay` (checkable).
  - **Version check:** `tools/kondorlib/versions.py` makes CI fail unless a changed extension bumps its
    version.
- **Tests:** `tools/tests/test_manifest_rules.py` (96 lines) uses `support.ExtensionTestCase`
  (`install`, `edit_manifest`, `assertProblem`). The `sample-ext` fixture has one `bool` setting
  `enabled` and one checkable item `toggle`.

## Design / behavior

### 1. Schema

- **New property:** in `$defs/actionItem.properties`, add
  `"keysSetting": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_]*$"}`.
  It uses the same pattern as `setting.key`.
- **`icon`:** stays as it is (`text`). As in Kondor, it is not checked against an icon theme.

### 2. Rule `check_keys_settings(manifest)` in `tools/kondorlib/manifest.py`

- **Behavior:** returns one problem per action item whose `keysSetting` names no setting with
  `type` `keys`:

  `(MANIFEST, f"action.items[{i}].keysSetting: must name a keys setting")`

- **Missing parts:** items without `keysSetting`, a manifest without `action`, or a manifest
  without `settings` give no problem, unless an item names a key, which then fails.
- **Wiring:** add the rule to `check_manifest_rules()`.
- **Size:** keep functions within the AGENTS.md limits. A small helper `keys_setting_names(manifest)`
  returns the set of `keys` setting keys.
- **File:** `manifest.py` stays under 200 lines.

### 3. Video Speed Controller (`extensions/video-speed/manifest.json`)

| Item | Add |
| --- | --- |
| `slower` (Slower) | `"icon": "media-seek-backward", "keysSetting": "keySlower"` |
| `faster` (Faster) | `"icon": "media-seek-forward", "keysSetting": "keyFaster"` |
| `reset` (Reset Speed) | `"icon": "edit-undo", "keysSetting": "keyReset"` |
| `show-overlay` (Show Speed Overlay) | `"keysSetting": "keyOverlay"` (no icon: checkable rows show none) |

- `version` becomes `1.1.0`.
- Nothing else changes: scripts, settings, titles, translations and `README.md` stay the same.

### 4. Tests (`tools/tests/test_manifest_rules.py`)

- `test_accepts_keys_setting_naming_a_keys_setting`: add a `keys` setting to `sample-ext` and
  point `toggle` at it. No problems.
- `test_rejects_keys_setting_naming_no_setting`: the message is
  `action.items[0].keysSetting: must name a keys setting`.
- `test_rejects_keys_setting_naming_another_type`: `keysSetting` is `"enabled"` (a `bool`). Same
  message.
- `test_rejects_keys_setting_with_bad_pattern`: `keysSetting` is `"1x"`, so the schema problem names
  `action.items[0].keysSetting`.
- Keep the file under 200 lines. Move a helper to `support.py` only if a second test file needs it.

## Acceptance criteria

- [ ] The schema accepts an optional string `keysSetting` on action items, with the settings key
      pattern.
- [ ] `python3 tools/validate.py` rejects a `keysSetting` that names no setting or a setting of
      another type, with `action.items[<i>].keysSetting: must name a keys setting`.
- [ ] Video Speed Controller has the icons and `keysSetting` values in §3, version `1.1.0`, and
      `python3 tools/validate.py --base origin/main` passes.
- [ ] The tests in §4 exist, and `python3 -m unittest discover tools/tests` passes.
- [ ] The PR's `build` check is green. The PR body says `Closes lukasborges/kondor#194`.

## Manual test

Use a Kondor build from `main` (with #182), and a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
`XDG_CACHE_HOME` (AGENTS.md).

1. `python3 tools/pack.py extensions/video-speed`, then install the package with
   **Install from File…**.
2. Open a page with a video, open the Extensions panel and then Video Speed Controller. Slower,
   Faster and Reset Speed show their icons and S, D and R. Show Speed Overlay shows V. This matches
   `prototypes/screenshots/183b-extensions-panel-actions.png` in `lukasborges/kondor`.
3. In a copy of the extension, set `"keysSetting": "speedStep"` on Faster and run
   `python3 tools/validate.py`. It prints
   `extensions/video-speed/manifest.json: action.items[1].keysSetting: must name a keys setting`.

## Out of scope

- Any change to Kondor (`lukasborges/kondor`): #182 delivered it.
- Icons or `keysSetting` for other extensions (Dark Mode has no action items with keys).
- Changing Video Speed Controller's scripts, default keys, settings or README.
- Checking icon names against a theme, or bundling icon files.
- Documenting manifest fields in `CONTRIBUTING.md` beyond what it documents today.

## Dependencies

- #182 Extension menu item icons and shortcuts (merged).
- #108 Extensions repository and #110 Video Speed Controller (merged).

## Prototype

No new UI. The rows this issue fills are the ones in
[`prototypes/183b-extensions-panel-actions.qml`](../../prototypes/183b-extensions-panel-actions.qml)
([screenshot](../../prototypes/screenshots/183b-extensions-panel-actions.png)).

## Decisions

| Question | Decision |
| --- | --- |
| Same rule and message as Kondor? | Yes. A manifest that passes the catalog CI must install in Kondor, and the same text makes failures easy to match. |
| Bump the manifest API (`"kondor": 2`)? | No. `keysSetting` is optional, and older Kondor builds ignore unknown keys. |
| Icon for the checkable Show Speed Overlay item? | No. Kondor shows no icon on checkable rows (#182), so it would never be visible. |
| Which version bump? | Minor (`1.1.0`): a new visible feature with no change in behavior. |
