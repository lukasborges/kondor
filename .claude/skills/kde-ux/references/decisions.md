# Kondor UX decisions

Past designs that were rejected or fixed, and why. Read this before designing something similar.
Add a row whenever a design is rejected in review or a UX bug is filed.

| Issue | Rejected or broken | Chosen | Why |
| --- | --- | --- | --- |
| #176 | "Copy Username" / "Copy Password" submenus under the Fill Saved Password menu | A `Popup` panel: one row per account (click fills), and `edit-copy` / `password-copy` icon buttons at the end of each row | The submenus listed every account three times, put the action before the account, hid copying behind hover and gave no feedback |
| #176 | A green `Kirigami.InlineMessage` "Password copied…" | The copy button turns into `dialog-ok-apply` for 2 s, with the tooltip "Copied" and `Accessible.announce()` | The HIG shows success as a visual change on the item, and keeps messages for things that need attention |
| #177 | A system notification at the end of a password import whenever the Passwords page is closed | Notify only when no Kondor window is active; otherwise show the result the next time the page opens | The HIG says no system notifications while the app is in the foreground |
| #177 | A blocking import: the Import button looked stuck | Background work with a determinate `ProgressBar` ("%1 of %2 sites") | Show progress for anything longer than 1 s, and never freeze the UI |
| #157 | A `PlaceholderMessage` declared before a `ListView` with `anchors.fill`: its button got no clicks | The placeholder above the list in z-order | An empty state must be actionable |
| #158 | Icon-only buttons that are `[button] ''` for screen readers | `Accessible.name` on every icon-only button | Screen readers must announce a distinct label |
