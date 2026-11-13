# Copy saved user name and password (#176)

> **Issue:** [#176](https://github.com/lukasborges/kondor/issues/176) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

When a site cannot be filled, the user should still be able to get a saved login straight from the
address bar, without opening Settings:

- **Copy:** copy the user name or the password, then paste it by hand.
- **Panel:** the **Fill Saved Password** button opens a small panel instead of today's `Menu`.
- **Fill:** clicking an account still fills the page.
- **Klipper:** a copied password is marked secret, so the clipboard history does not keep it.

## Context

- **Button:** `qml/passwords/bar/PasswordButton.qml` (address bar, through
  `qml/browser/address/AddressBarButtons.qml`). It is visible when
  `tabs.currentTab.passwords.usernames` is not empty, and opens a `Menu` with one `MenuItem` per
  user name that calls `tab.passwords.fill(username)`.
- **Per-tab state:** `TabPasswords` (`src/browser/tabs/features/tabpasswords.{h,cpp}`, the
  `tab.passwords` group object). It keeps the page URL in `m_url`. `updateUsernamesFor(url)`
  fills `usernames` from `PasswordStore::usernames(PasswordStore::originOf(url))`, and only for
  normal tabs: `m_isPrivate` leaves the list empty.
- **Clipboard:** `PasswordStore::copyPassword(origin, username)` (`src/passwords/passwordstore.cpp:176`)
  copies through `PasswordClipboard` (`src/passwords/passwordclipboard.{h,cpp}`). It sets the
  clipboard text and clears it after 30 s if it still holds the secret. The **Copy Password** button in
  Settings → Passwords (`qml/passwords/SavedPasswordDelegate.qml`) uses the same call.
- **Popup model:** the site security popup, `qml/site/SiteInfoPopup.qml`, is a `Popup` under its button,
  with a 32 px icon, a level-4 heading and a subtitle. The new panel uses the same header layout.
- **Settings pages:** `qml/app/window/WindowDialogs.qml` has `openSettings()` and
  `openExtensionsSettings()` (`settingsWindow.showPage("extensions")`). `BrowserWindow.qml` forwards
  `openExtensionsSettings()`. The Passwords page id is `"passwords"` (`qml/settings/SettingsPages.qml`).
- **Address bar wiring:** `AddressBar` has `browserWindow`. `AddressBarButtons` gets only
  `tabs` and `addressField`.

## Design / behavior

### 1. Per-tab commands (`TabPasswords`, Tab bridge pattern)

The panel talks only to `tabs.currentTab.passwords`, never to `PasswordStore` with an origin it
computes itself. Add to `TabPasswords`:

| Member | Kind | Behavior |
| --- | --- | --- |
| `host` | `Q_PROPERTY(QString host READ host NOTIFY usernamesChanged)` | `PasswordStore::hostOfOrigin(PasswordStore::originOf(m_url))`. Shown under the panel heading. |
| `copyUsername(const QString &username)` | `Q_INVOKABLE void` | Copies the user name as plain text, with no secret hint and no clearing. Does nothing in a private tab. |
| `copyPassword(const QString &username)` | `Q_INVOKABLE void` | `PasswordStore::instance()->copyPassword(originOf(m_url), username)`. Does nothing in a private tab. |

Notes:

- **Not page commands:** neither copy command acts on the `WebEngineView`, so neither needs a
  `…Requested` signal.
- **Private tabs:** the private-tab guard repeats the existing rule, because the button is already
  hidden there.
- **Where the copy code lives:** the plain copy goes through `PasswordClipboard` (item 2), so all
  clipboard code stays in one class.

### 2. `PasswordClipboard`

- **`copy(secret)`:** sets a `QMimeData` with the text **and** the MIME type
  `x-kde-passwordManagerHint` with the data `secret`. Klipper and other KDE clipboard managers then
  do not keep it. The 30 s clearing does not change.
- **New `copyText(text)`:** sets plain text only. It has no hint and no timer. If a password is
  still pending clearing, it does not clear the new text: `clearIfStillHolding()` already compares
  the clipboard text.
- **Shared fix:** the hint also applies to the Settings → Passwords copy button, because it uses
  `PasswordStore::copyPassword`.
- **Username path:** `PasswordStore` gets `void copyText(const QString &text)`, which forwards to its
  `PasswordClipboard`. `TabPasswords::copyUsername` calls it. `PasswordStore` keeps owning the one
  `PasswordClipboard`.

### 3. The panel

`PasswordButton` opens a `Popup` (new file `qml/passwords/bar/SavedPasswordsPopup.qml`) under the button
(`y: button.height`, right edge aligned with the button), instead of the `Menu`:

- **Popup settings:** `width: 360`, `padding: Kirigami.Units.largeSpacing`, `modal: false`,
  `focus: true`, `closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside`. The button shows
  `checked: popup.opened`.
- **Header,** as in `SiteInfoPopup`:
  - a `Kirigami.Icon` `dialog-password` at 32×32;
  - next to it, a `Kirigami.Heading { level: 4 }` with **"Saved Passwords"**;
  - under the heading, a `Label` with `tab.passwords.host` in `Kirigami.Theme.disabledTextColor`.
- **No hint text** under the header ("show, don't tell").
- **One row per user name** (new file `SavedAccountRow.qml`, an `ItemDelegate`):
  - **Content:**
    - a `user-identity` icon at `Kirigami.Units.iconSizes.smallMedium`;
    - the user name, `elide: Text.ElideRight`, filling the width;
    - two icon-only `ToolButton`s.
  - **Fill:** clicking the row, or pressing Enter/Return on it, calls `tab.passwords.fill(username)`
    and closes the panel.
  - **Row tooltip:** **"Fill"**, `ToolTip.delay: 600`.
  - **Row accessible name:** **"Fill %1"** with the user name.
- **Copy buttons** (new file `CopyFeedbackButton.qml`, one component for both):

  | Button | Icon | Tooltip | `Accessible.name` | Action | Tooltip after copying | Announcement |
  | --- | --- | --- | --- | --- | --- | --- |
  | user name | `edit-copy` | "Copy Username" | "Copy Username for %1" | `tab.passwords.copyUsername(username)` | "Copied." | "Username copied" |
  | password | `password-copy` | "Copy Password" | "Copy Password for %1" | `tab.passwords.copyPassword(username)` | "Copied. Cleared in 30 seconds." | "Password copied, cleared in 30 seconds" |

  - **Size:** icons at `Kirigami.Units.iconSizes.smallMedium`.
  - **Tooltip:** `ToolTip.delay: 600`.
- **Feedback after copying** (KDE HIG "status changes", no message):
  - **Panel:** stays open.
  - **Button:** for 2 s (one `Timer`, `interval: 2000`, restarted on every click), the icon becomes
    `dialog-ok-apply` with `icon.color: Kirigami.Theme.positiveTextColor`, and the tooltip shows the
    "after copying" text. Then the icon and tooltip return.
  - **Announcement:** `Accessible.announce()` with the announcement text (Qt 6.8+, as in
    `qml/passwords/import/ImportMessage.qml`).
- **Footer:**
  - a `Kirigami.Separator`;
  - a flat `Button` **"Manage Passwords…"** with icon `configure`. It closes the panel and opens
    Settings → Passwords (item 4).
- **Keyboard:**
  - Opening the panel focuses the first row.
  - Up and Down move between rows.
  - Enter/Return fills.
  - Tab and Shift+Tab move through the row's buttons and the footer button.
  - Esc closes and gives focus back to the page.
  - The focused element has a visible focus frame.
- **Closing on change:** the panel closes when the current tab changes, or when `usernames` becomes
  empty (the button hides then).
- **Strings:** every string is in `qsTr()`. `%1` strings use `.arg()`, with a `//:` translator note
  that `%1` is the user name.

### 4. Opening Settings → Passwords

- **`WindowDialogs.qml`:** replace `openExtensionsSettings()` with `openSettingsPage(pageId)`
  (`openSettings()` then `settingsWindow.showPage(pageId)`).
- **`BrowserWindow.qml`:** forward `openSettingsPage(pageId)` the same way.
- **Extensions callers:** `NavigationToolBar.qml:149` calls `openSettingsPage("extensions")`, so the
  two pages share one function. The mock window in `tests/app/tst_toolbaraccessibility.cpp:42`
  declares `openSettingsPage(pageId)` instead of `openExtensionsSettings()`.
- **`PasswordButton`:** gets `signal manageRequested()`. `AddressBarButtons` re-emits it, and
  `AddressBar` connects it to `root.browserWindow.openSettingsPage("passwords")`.

### 5. Files

- **New:** `qml/passwords/bar/SavedPasswordsPopup.qml`, `SavedAccountRow.qml` and
  `CopyFeedbackButton.qml`, added to `QML_FILES` in `CMakeLists.txt`.
- **Changed:**
  - `PasswordButton.qml`, `AddressBarButtons.qml`, `AddressBar.qml`;
  - `WindowDialogs.qml`, `BrowserWindow.qml` and the extensions callers;
  - `TabPasswords`, `PasswordStore` and `PasswordClipboard`.
- **Size limits:** every file stays within the "Code quality" limits.
- **Translations:** run `update_translations` and translate the new strings in every `i18n/*.ts`.
  The new strings are "Saved Passwords", "Fill", "Fill %1", "Copy Username", "Copy Username for %1",
  "Copy Password for %1", "Copied.", "Copied. Cleared in 30 seconds.", "Username copied",
  "Password copied, cleared in 30 seconds" and "Manage Passwords…". "Copy Password" may already
  exist.

### 6. Tests

- **`tests/passwords/tst_passwordclipboard.cpp`** (new, offscreen `QGuiApplication`):
  - `copyMarksPasswordSecret`: the clipboard has `x-kde-passwordManagerHint` = `secret`;
  - `copyTextHasNoSecretHint`;
  - `copyTextIsNotCleared`: after the clear timer fires, the plain text is still there. Expose the
    interval only as far as needed for the test, for example a constructor argument with the 30 s
    default.
- **`tests/browser/tabs/tst_tabpasswords.cpp`:**
  - `privateTabDoesNotCopy`;
  - `hostFollowsUrl`.
- **A QML test of the panel** (in `tests/passwords/`, next to `tst_passwordsui.cpp`, using the same
  harness):
  - `rowClickFillsAndCloses`;
  - `copyButtonShowsCheckMarkAndStaysOpen`;
  - `downKeyMovesToNextRow`.

## Acceptance criteria

- [ ] The **Fill Saved Password** button opens the panel (not a `Menu`), matching the prototype:
      header, one row per account with two copy buttons, separator and **Manage Passwords…**.
- [ ] Clicking a row, or Enter on a focused row, fills the page and closes the panel.
- [ ] **Copy Username** puts the user name on the clipboard, with no secret hint, and it is not cleared.
- [ ] **Copy Password** puts the password on the clipboard with `x-kde-passwordManagerHint: secret`
      and clears it after 30 s if it is unchanged. The Settings → Passwords copy button sets the hint too.
- [ ] After a copy, the button shows a `positiveTextColor` `dialog-ok-apply` for 2 s, and the
      tooltip and the screen reader announcement read as specified. The panel stays open.
- [ ] **Manage Passwords…** closes the panel and opens Settings on the Passwords page.
- [ ] Keyboard: first row focused on open, Up/Down, Enter, Tab through the buttons, Esc closes.
- [ ] Every icon-only button has a tooltip (`ToolTip.delay: 600`) and a distinct `Accessible.name`
      that includes the user name.
- [ ] Private tabs: no button, no panel, and `copyUsername`/`copyPassword` do nothing.
- [ ] The UI only talks to `tabs.currentTab.passwords`. No QML computes an origin.
- [ ] The tests in "Design → Tests" exist and pass. `ctest` passes. The smoke test prints no QML errors.
- [ ] Translations are complete in every `i18n/*.ts`. `scripts/check-code-quality.py --changed origin/main` is clean.
- [ ] `README.md`: the passwords feature bullet mentions copying a saved login from the address bar.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md). The wallet must be
available. If KWallet cannot open in the test session, cover these steps with the QML tests and
say so in the PR.

1. In Settings → Passwords, add two logins for `https://example.org` (`ana@example.org`,
   `bruno@example.org`). Open `https://example.org/`.
2. Click the key button in the address bar. The panel shows "Saved Passwords", `example.org` and
   two rows.
3. Click **Copy Username** on the first row. The icon turns into a green check for about 2 s, and the panel stays
   open. Paste in the address bar: the user name appears.
4. Click **Copy Password**. The check appears and the tooltip says "Copied. Cleared in 30 seconds.".
   Run `qdbus6 org.kde.klipper /klipper getClipboardHistoryMenu`, or open Klipper: the password is not in the history.
   After 30 s, paste: the clipboard is empty.
5. Open the panel with the keyboard. Tab to the address bar, then Tab to the key button and press Space. Then:
   - Down moves to the second row;
   - Enter fills and closes;
   - reopen it, and Esc closes.
6. Click **Manage Passwords…**. Settings opens on the Passwords page.
7. Open a private window on the same site: no key button.

## Out of scope

- The fill itself on identifier-first logins (bug #175).
- The icon and wording of the Settings → Passwords copy button: only the secret hint changes there.
- Searching or filtering the account list, adding or editing logins from the panel.
- Copying anything from private tabs.

## Dependencies

- #21 Passwords (`PasswordStore`, `TabPasswords`), #106 (import, unaffected), #158 (accessibility
  rules for icon-only buttons).

## Prototype

- [`prototypes/176-passwords-copy.qml`](../../prototypes/176-passwords-copy.qml), rendered in
  [`prototypes/screenshots/176-passwords-copy.png`](../../prototypes/screenshots/176-passwords-copy.png).
- It shows three accounts, right after the first account's password was copied: the check mark and
  the "Copied. Cleared in 30 seconds." tooltip.

## Decisions

| Question | Decision |
| --- | --- |
| Submenus "Copy Username" / "Copy Password" in the existing `Menu`? | Rejected. They repeated the account list three times, put the action before the account, hid copying behind hover submenus and gave no feedback. A panel with one row per account and two copy buttons wins. |
| A green `InlineMessage` "Password copied…" after copying? | Rejected. The KDE HIG reserves inline messages for things that need attention. Success is shown by changing the clicked button (check mark for 2 s). "Cleared in 30 seconds" is a detail, so it lives in the tooltip and the screen reader announcement. |
| Hint text under the header ("Click an account to fill it")? | Rejected ("show, don't tell"). The hover highlight, the "Fill" tooltip and the icons say it. |
| Where the copy logic lives | In `TabPasswords` (`copyUsername`, `copyPassword`, `host`), so the UI only talks to `tabs.currentTab` and never computes an origin. All clipboard writes go through the one `PasswordClipboard` owned by `PasswordStore`. |
| Mark copied passwords secret for Klipper | Yes, `x-kde-passwordManagerHint: secret`. It applies to every password copy, including the one in Settings → Passwords. User names are not secret. |
| One function per Settings page in `WindowDialogs`? | No. `openSettingsPage(pageId)` replaces `openExtensionsSettings()`, so adding Passwords does not copy the function a second time. |
