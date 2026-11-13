# Kondor UX decisions

Past designs that were rejected or fixed, and why. Read this before designing something similar.
Add a row whenever a design is rejected in review or a UX bug is filed.

| Issue | Rejected or broken | Chosen | Why |
| --- | --- | --- | --- |
| #176 | "Copy Username" / "Copy Password" submenus under the Fill Saved Password menu | A `Popup` panel: one row per account (click fills), and `edit-copy` / `password-copy` icon buttons at the end of each row | The submenus listed every account three times, put the action before the account, hid copying behind hover and gave no feedback |
| #176 | A green `Kirigami.InlineMessage` "Password copied…" | The copy button turns into `dialog-ok-apply` for 2 s, with the tooltip "Copied" and `Accessible.announce()` | The HIG shows success as a visual change on the item, and keeps messages for things that need attention |
| #177 | A system notification at the end of a password import whenever the Passwords page is closed | Notify only when no Kondor window is active; otherwise show the result the next time the page opens | The HIG says no system notifications while the app is in the foreground |
| #177 | A blocking import: the Import button looked stuck | Background work with a determinate `ProgressBar` ("%1 of %2 sites") | Show progress for anything longer than 1 s, and never freeze the UI |
| #183 | A flat Extensions menu with every item of every extension | A two-level panel: one row per extension (switch for this site, arrow), its actions on level 2, and pinned extensions in the toolbar | 10 extensions made 40+ rows, and the menu closed after each action |
| #183 | A pin button on every row of the extension list | Pin / Unpin on level 2, as a button whose icon and text change | Ten identical icons for a rare action |
| #183 | A status icon or a "Running on this site" subtitle | Text, only for the exception | The icon alone was ambiguous; the subtitle doubled the row height |
| #183 | A `Switch` on every row of the extension list | The switch on level 2 | Ten switches made the list noisy |
| #183 | An "Off on this site" label on rows that are off | The icon and name dimmed (`enabled: false` on those two items only), the row still enabled and clickable, the state in the tooltip and `Accessible.name` | The maintainer found the label noisy. Dimming is fine for "inactive here" **as long as the row stays interactive** and the state is also given in words (unlike #179, where whole items were disabled) |
| #179 | Extension names in the Extensions menu as disabled `MenuItem`s (greyed out), with no line between extensions | A non-interactive section header: icon and bold name in the normal text color, a separator line, and `Accessible.role: Accessible.Heading` | A disabled item means "not available now"; groups must read as separate blocks |
| #180 | Toggling "Run on <host>" reloads the page at once | Save, then offer **Reload** in the `InlineBar` | Do not throw away what the user typed; the user decides when to reload |
| #181 | The colorful category icon `preferences-plugin` on a toolbar button | The monochrome action icon `plugins` | Toolbar and menu icons are monochrome action icons that follow the color scheme |
| #158 | Two "Run on <host>" items with the same accessible name | `Accessible.name` "Run %1 on %2" (extension, host) | Labels must be distinct within a window |
| #157 | A `PlaceholderMessage` declared before a `ListView` with `anchors.fill`: its button got no clicks | The placeholder above the list in z-order | An empty state must be actionable |
| #158 | Icon-only buttons that are `[button] ''` for screen readers | `Accessible.name` on every icon-only button | Screen readers must announce a distinct label |
