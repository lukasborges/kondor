# Patterns: which component for what

Kondor's main window is a QQC2 `ApplicationWindow` with the `org.kde.desktop` style, not a
`Kirigami.ApplicationWindow`. `showPassiveNotification` and other `Kirigami.ApplicationWindow`
features are therefore **not available**; use the patterns below.

## Feedback after an action

| Situation | Use | Not |
| --- | --- | --- |
| Routine success (copied, saved, added) | Change the control or item itself: icon → `dialog-ok-apply` tinted `Kirigami.Theme.positiveTextColor` for 2 s, tooltip "Copied"; a new row appears; a star fills | A green `InlineMessage`, a dialog, a system notification |
| Something needs attention but must not interrupt (save password?, page crashed, permission request) | `InlineBar` (shared block, `Kirigami.InlineMessage` look) between the toolbar and the page, or a `Kirigami.InlineMessage` at the top of a Settings page | A modal dialog |
| Invalid input | `Kirigami.InlineMessage` (Error) near the field, and disable the confirm button | A message box after submit |
| Long task the user may forget (download, big import) | Determinate `ProgressBar` with "%1 of %2"; when it ends and **no Kondor window is active**, `Notifier.notify()` | A notification while the user is looking at Kondor |
| Screen-reader confirmation | `Accessible.announce()` (Qt 6.8+) alongside the visual change | Nothing |

## Choosing actions

| Situation | Use |
| --- | --- |
| A few actions on one thing, opened from a toolbar or address bar button | `Menu`, if every row is a single action with a clear verb |
| A list of things, each with 2+ actions (fill / copy / remove) | A `Popup` panel like the site security popup: heading, one `ItemDelegate` row per thing, its actions as icon-only `ToolButton`s at the end of the row. Do not put the list in submenus |
| A decision the app needs before it can continue | `Kirigami.PromptDialog` (one modal at a time, never a dialog from a dialog) |
| Text input for one value | Inline editing, or `Kirigami.PromptDialog` with a `TextField` |
| Settings form | `Kirigami.FormLayout` with `Kirigami.FormData.label` (sentence case); a `Switch` applies instantly, a `CheckBox` applies with Apply |
| 3 or fewer exclusive options | `RadioButton`s; up to 10 → `ComboBox`; more → a list |

## Menus

- **Section titles** inside a `Menu` are a non-interactive item: icon, bold `Label` in `Kirigami.Theme.textColor`, `Kirigami.Separator` to the right, and `Accessible.role: Accessible.Heading`. **Never** use a disabled `MenuItem`, which reads as "unavailable".
- Show an item's keyboard shortcut when it has one (discoverability).
- A checkable item applies instantly. If applying needs a page reload, save the change and offer **Reload** in the `InlineBar`; never reload by itself.

## Content

| Situation | Use |
| --- | --- |
| Empty list or view | `Kirigami.PlaceholderMessage` with an actionable button (keep it clickable: #157) |
| Text-heavy collection | `ListView` with standard delegates; remove buttons visible on every row, not only on hover |
| Unknown duration | `BusyIndicator`; known count → `ProgressBar`; anything longer than 1 s shows one |
| Explanation of one sentence | A `Label` under the control, not a tooltip; longer → `Kirigami.ContextualHelpButton` |

## Icons

- Toolbar buttons and menu items use **monochrome action icons** (`actions/` in Breeze, for example `plugins`, `configure`, `edit-copy`). Colorful category or app icons (`preferences-*`, app icons) are only for content: extension icons, site favicons, Settings categories.

- Use Breeze names only. Check that the icon exists:
  `find /usr/share/icons/breeze -name '<name>.svg'`.
- Use distinct icons for distinct actions in the same row (`edit-copy` for the user name,
  `password-copy` for the password).
- Size:
  - **Toolbar buttons:** set `icon.name` or `icon.source` on the `ToolButton` and let the style
    size it. Never a custom `contentItem` or an explicit size: every toolbar icon must match (#204).
  - `IconSizes.smallMedium` in list items without a subtitle; `IconSizes.small` in menus;
    `IconSizes.medium` in list items with a subtitle.
- Colorful content icons (extensions, favicons) have **no background tile**: a transparent
  background and a symbol that reads at 16 px on light and dark color schemes (#205).
