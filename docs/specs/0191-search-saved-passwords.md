# Search every saved password from the Saved Passwords panel (#191)

> **Issue:** [#191](https://github.com/lukasborges/kondor/issues/191) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Add a search field to the **Saved Passwords** panel (#176), so a login saved for another site can
be filled or copied from the address bar. The panel follows the Bitwarden popup: this site's
logins come first, and the search covers every saved password.

Typical cases: a site that moved to a new domain, a single sign-on page on another host, or a
login saved under `www.` that the page now asks for on `accounts.`.

## Context

- **Panel (#176):** `qml/passwords/bar/PasswordButton.qml` (key button in the address bar, visible
  only when `tab.passwords.usernames` is not empty) opens `SavedPasswordsPopup.qml`: header
  (`dialog-password`, "Saved Passwords", `tab.passwords.host`), one `SavedAccountRow` per user name
  (click fills, `CopyFeedbackButton`s copy), separator, **Manage Passwords…**. The popup closes
  when `usernames` becomes empty.
- **Per-tab object:** `TabPasswords` (`src/kondor/browser/tabs/features/tabpasswords.py`,
  `tab.passwords`): `host`, `usernames`, `fill(username)` (emits `fillRequested(username)`),
  `copyUsername(username)`, `copyPassword(username)` (uses the page origin). Private tabs do
  nothing.
- **Fill path:** `qml/browser/view/PageScriptBridges.qml` forwards `fillRequested(username)` to
  `PasswordBridge.fill(username)` (`src/kondor/passwords/bridge/passwordbridge.py`), which reads
  the password **for the page origin** and emits `PasswordPageApi.fillRequested(origin, username,
  password)`. `passwords.js` (`fillFirstField`) ignores it unless `origin` is the page's origin.
- **All logins:** `PasswordStore.entries` (`src/kondor/passwords/passwordstore.py`) is a list of
  `{origin, host, username}` maps, from `UsernameCache` (no passwords). `PasswordStore.changed`
  fires when the logins change and when the wallet opens. `ensureOpen()` opens the wallet;
  `state` is `"unavailable"` when KWallet is disabled or denied.
- **Search field to reuse:** `qml/bookmarks/panel/BookmarksPanelSearchField.qml` (#227): a
  `TextField` with an `edit-find` icon, `stepDownRequested()` and `openRequested(bool)`.
- **Confirmation:** `qml/common/ConfirmDialog.qml` (message, accept text and icon, Cancel has the
  initial focus).
- **HTML escaping:** `escapeHtml()` exists only inside `qml/passwords/bar/PasswordBar.qml`.
- **Origins and hosts:** `passwordorigin.origin_of(url)` returns `""` for anything but
  `http`/`https` with a host. `host_of_origin()` returns `QUrl.host()`, which may be decoded IDN
  (Unicode), so hosts must be escaped before going into rich text.

## Design / behavior

### 1. Search logic (`src/kondor/passwords/passwordsearch.py`, new)

Pure function, no Qt objects:

`matching_logins(entries: list[dict[str, str]], text: str, site_origin: str) -> list[dict[str, object]]`

- **Empty text** (after `strip()`): only the entries whose `origin == site_origin`.
- **Text:** every entry whose `host` or `username` contains the text, compared with
  `str.casefold()`.
- **Order:** this site's entries first, sorted by user name; then the others sorted by host, then
  user name (all `casefold`).
- **Result items:** `{"origin", "host", "username", "isThisSite": bool}`. Never a password.

### 2. `TabPasswords` (Tab bridge pattern)

| Member | Kind | Behavior |
| --- | --- | --- |
| `isAvailable` | `Property(bool, notify=availabilityChanged)` | `True` when the tab is not private and `origin_of(url)` is not empty (a normal `http`/`https` page). Updated in `update_usernames_for()`, signal only on a real change. |
| `isWalletUnavailable` | `Property(bool, notify=walletStateChanged)` | `PasswordStore.state == "unavailable"`; `walletStateChanged` is relayed from `PasswordStore.stateChanged` (normal tabs only). |
| `matches(text)` | `@Slot(str, result="QVariantList")` | `matching_logins(PasswordStore.entries, text, page origin)`. A query: changes nothing. Returns `[]` in a private tab. |
| `openWallet()` | `@Slot()` | `PasswordStore.ensureOpen()`. Does nothing in a private tab. |
| `fill(origin, username)` | `@Slot(str, str)`, **replaces** `fill(username)` | Emits `fillRequested(origin, username)` (the signal gains the origin). Does nothing in a private tab. |
| `copyPassword(origin, username)` | `@Slot(str, str)`, **replaces** `copyPassword(username)` | `PasswordStore.copyPassword(origin, username)`. Does nothing in a private tab. |

- `copyUsername(username)`, `host` and `usernames` stay as they are.
- `usernamesChanged` keeps firing on `PasswordStore.changed`; the panel re-reads `matches()` on it.
- The origin in `fill`/`copyPassword` always comes from a `matches()` item; no QML builds an
  origin.

### 3. Filling with a saved origin

- `PasswordBridge.fill(saved_origin, username)` (replaces `fill(username)`): reads
  `store.password(saved_origin, username)` and emits `fillRequested(page_origin, username,
  password)`, where `page_origin = origin_of(tab.url)`. It emits nothing when the tab is private,
  the page origin is empty, the wallet is closed, or the password is empty (unknown login).
- `PageScriptBridges.qml`: `function onFillRequested(origin, username) { passwordBridge.fill(origin, username) }`.
- `passwords.js` and `PasswordPageApi` do not change: the page never asks for another site's
  login; only the browser UI can, after the confirmation of item 6.

### 4. Key button (`PasswordButton.qml`)

- **Visible** when `tabs.currentTab.passwords.isAvailable` (every normal `http`/`https` tab, even
  with no saved login). Private tabs: no button.
- **Tooltip and accessible name:** "Saved Passwords" (the panel heading; the string exists).
- **Click:** `tab.passwords.openWallet()`, then opens the panel. The results refresh by themselves
  when the wallet opens (`usernamesChanged`).

### 5. The panel (`SavedPasswordsPopup.qml`)

Header and footer as in #176. Between them:

- **Search field:** the #227 field, moved to `qml/common/PanelSearchField.qml` (shared, "extract
  on the second copy"; the Bookmarks panel sets `placeholderText: qsTr("Search bookmarks")`, the
  passwords panel `qsTr("Search passwords")`; `Accessible.name` stays the placeholder).
  `objectName: "passwordSearchField"`.
- **List:** one `ListView` whose model is `tab.passwords.matches(searchText)`, re-evaluated when
  the text changes and on `usernamesChanged`. Height `Math.min(contentHeight,
  Kirigami.Units.gridUnit * 18)`, then it scrolls (the scroll bar must not cover the row buttons).
  - **Empty search:** this site's accounts as one-line `SavedAccountRow`s, exactly as in #176
    (`prototypes/191b-passwords-search-site.qml`).
  - **With text:** two-line rows (new `SavedLoginResultRow.qml`, `prototypes/191-passwords-search.qml`):
    `SiteIcon` (`pageUrl: origin`, small size), the host, and under it the user name in
    `Kirigami.Theme.smallFont` and `disabledTextColor`; then the two `CopyFeedbackButton`s of #176
    (same icons, tooltips, accessible names with the user name, announcements). Row tooltip
    "Fill", accessible name "Fill %1" with the user name, as `SavedAccountRow`.
  - The current row (`currentIndex`, starts at 0) is highlighted.
- **Empty states** (`Kirigami.PlaceholderMessage`, text only, no icon, no explanation):
  - empty search and no login for this site: **"No Passwords for This Site"**
    (`prototypes/191c-passwords-search-empty.qml`);
  - text with no match: **"No Matches"**;
  - `tab.passwords.isWalletUnavailable`: **"Passwords Unavailable"**, with the explanation of the
    existing string "KWallet is disabled or access to it was denied, so passwords cannot be saved
    or filled.", and the search field disabled.
- **Activating a row** (click, or Enter):
  - `isThisSite`: `tab.passwords.fill(origin, username)`, close the panel.
  - another site: close the panel and open the confirmation of item 6.
- **Copying** from any row: `copyUsername(username)` / `copyPassword(origin, username)`, no
  confirmation; the panel stays open (#176 feedback).
- **Keyboard:**
  - Opening focuses the search field; the first row is highlighted, and Enter in the field
    activates it.
  - Down in the field moves the focus to the highlighted row; Up/Down move between rows; Up on
    the first row goes back to the field.
  - Tab and Shift+Tab move through the row's buttons and the footer, as in #176.
  - Esc: if the field has text, clear it and focus the field; otherwise close the panel and focus
    the page (`tab.focusPage()`).
- **Closing on change:** the panel closes when the current tab changes or when `isAvailable`
  becomes false. It no longer closes when `usernames` becomes empty. The search text is cleared
  every time the panel opens.

### 6. Filling a login saved for another site (`FillFromOtherSiteDialog.qml`, new)

`prototypes/191d-passwords-search-other-site.qml`. A `ConfirmDialog` declared in
`PasswordButton.qml` (outside the popup, so it outlives it):

- `title`: **"Fill Password from Another Site"**.
- `message`: **"This password was saved for <b>%1</b>. Fill it on <b>%2</b>?"**, `%1` the saved
  host, `%2` `tab.passwords.host`, both HTML-escaped (item 7). `//:` translator note for both
  placeholders.
- `acceptText` **"Fill"**, `acceptIcon` `dialog-password`, `destructive: false`. Cancel keeps the
  initial focus.
- It stores the `Tab`, origin and user name it was opened for. **Fill** calls
  `tab.passwords.fill(origin, username)` on that tab; both buttons then give the focus back to the
  page. If the current tab changes while it is open, it closes without filling.

### 7. Shared HTML escaping

Move `escapeHtml()` from `PasswordBar.qml` to `qml/common/html.js` (`.pragma library`, function
`escaped(text)`), used by `PasswordBar.qml` and the dialog.

### 8. Files

- **New:** `src/kondor/passwords/passwordsearch.py`, `qml/passwords/bar/SavedLoginResultRow.qml`,
  `qml/passwords/bar/FillFromOtherSiteDialog.qml`, `qml/common/html.js`,
  `qml/common/PanelSearchField.qml` (moved from `qml/bookmarks/panel/BookmarksPanelSearchField.qml`).
- **Changed:** `tabpasswords.py`, `passwordbridge.py`, `PageScriptBridges.qml`,
  `PasswordButton.qml`, `SavedPasswordsPopup.qml`, `SavedAccountRow.qml` (passes the origin),
  `PasswordBar.qml`, `BookmarksPanel.qml`, and the QML file list / `qmldir` registration the app
  uses.
- Every file and function within the AGENTS.md "Code quality" limits; split the popup (for
  example a `SavedLoginList.qml` for the list and its empty states) if it grows past them.
- **Translations:** new strings "Search passwords", "No Passwords for This Site", "No Matches",
  "Passwords Unavailable", "Fill Password from Another Site" and the dialog message, translated in
  every `i18n/*.ts` with no `unfinished` messages.

### 9. Tests (pytest, through `scripts/run-pytests.sh`)

- `tests/passwords/test_passwordsearch.py` (new): `test_empty_text_returns_this_site_only`,
  `test_matches_host_ignoring_case`, `test_matches_username`, `test_this_site_comes_first`,
  `test_other_sites_sorted_by_host`.
- `tests/browser/tabs/test_tabpasswords.py`: `test_https_tab_without_logins_is_available`,
  `test_non_web_tab_is_not_available`, `test_private_tab_is_not_available`,
  `test_private_tab_has_no_matches`, `test_fill_emits_the_saved_origin`.
- `tests/passwords/bridge/test_passwordfill.py`: `test_fills_login_of_another_origin_on_the_page`
  (password of the saved origin, page origin in the signal), `test_unknown_login_fills_nothing`.
- `tests/passwords/test_passwordsui.py` (split the file if it passes 200 lines): `typing filters
  every site's logins`, `other-site row opens the confirmation`, `cancel does not fill`,
  `fill in the confirmation fills`, `escape clears the text then closes`, `site without logins
  shows the empty state`.

## Acceptance criteria

- [ ] The key button shows on every normal `http`/`https` tab, with tooltip "Saved Passwords"; no
      button in private tabs.
- [ ] The panel matches the four prototypes: search field focused on open, this site's accounts
      for an empty search, two-line results from every site with this site first, the empty
      states, and the scrolling list above `gridUnit * 18`.
- [ ] Matching is on host or user name, case-insensitive, sorted as in item 1.
- [ ] Filling another site's login asks first (Cancel focused); Fill fills it on the page; this
      site's logins fill without asking. Copying never asks.
- [ ] The fill sends the saved origin's password with the page origin, and `passwords.js` is
      unchanged.
- [ ] Keyboard as in item 5: Enter in the field, Down into the list, Up back, Esc clears then
      closes.
- [ ] No QML builds an origin; hosts in the dialog are HTML-escaped through `qml/common/html.js`.
- [ ] Nothing from a private tab: no button, `matches()` returns `[]`, `fill`, `copyPassword` and
      `openWallet` do nothing.
- [ ] The tests of item 9 exist and pass, and every Python check of AGENTS.md passes (`ruff`,
      `mypy --strict`, `scripts/build.py`, `scripts/run-pytests.sh`, `check-qml-api.py`); the
      offscreen smoke test prints no QML errors.
- [ ] Translations complete in every `i18n/*.ts`; `scripts/check-code-quality.py --changed origin/main` is clean.
- [ ] `README.md`: the passwords bullet mentions searching every saved password from the address bar.

## Manual test

Use a temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md). If KWallet
cannot open in the test session, cover the steps with the QML tests and say so in the PR.

1. In Settings → Passwords, add `https://example.org` (`user.one`) and `https://id.example.net`
   (`user.two`, password `secret-two`).
2. Open `https://example.org/`, click the key button: the field has the focus, `user.one` is
   listed and highlighted. Press Enter: the page is filled and the panel closes.
3. Open `https://example.com/` (no saved login): the key button is there; the panel shows
   "No Passwords for This Site".
4. Type `EXAMPLE`: both logins show, with favicons and hosts. Type `zzz`: "No Matches". Press Esc:
   the text clears. Press Esc again: the panel closes.
5. Reopen, type `two`, press Down, Enter: the confirmation "Fill Password from Another Site" names
   `id.example.net` and `example.com`, with Cancel focused. Press Enter (Cancel): nothing is
   filled. Repeat and click **Fill**: the page gets `user.two` / `secret-two`.
6. Click **Copy Password** on a result from another site: no question, the check mark shows,
   pasting gives its password.
7. Open a private window on `https://example.org/`: no key button.

## Out of scope

- "Fill and save for this site", which would add the login to the current site after filling
  (Bitwarden has it).
- Adding or editing logins from the panel.
- Searching passwords from the page itself (`passwords.js`, `PasswordPageApi`), and any change to
  automatic filling.
- Section headers ("This Site" / "Other Sites") in the results.

## Dependencies

- #176 Copy saved user name and password (the panel) — closed.
- #227 Bookmarks panel (the search field that becomes shared) — closed.

## Prototype

- Searching every saved password: [`prototypes/191-passwords-search.qml`](../../prototypes/191-passwords-search.qml),
  [screenshot](../../prototypes/screenshots/191-passwords-search.png).
- Panel on open, this site's accounts: [`prototypes/191b-passwords-search-site.qml`](../../prototypes/191b-passwords-search-site.qml),
  [screenshot](../../prototypes/screenshots/191b-passwords-search-site.png).
- Site with no saved password: [`prototypes/191c-passwords-search-empty.qml`](../../prototypes/191c-passwords-search-empty.qml),
  [screenshot](../../prototypes/screenshots/191c-passwords-search-empty.png).
- Filling a login saved for another site: [`prototypes/191d-passwords-search-other-site.qml`](../../prototypes/191d-passwords-search-other-site.qml),
  [screenshot](../../prototypes/screenshots/191d-passwords-search-other-site.png).
- Shared mocks: `prototypes/common/SavedPasswordsPanelMock.qml`, `prototypes/common/SignInPageMock.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| A search button that opens a field, or a field that is always visible? | Always visible, as in Bitwarden: one click less, and typing works as soon as the panel opens. |
| Show the key button only on pages with a password field? | No. Identifier-first logins (#175) ask for the password on a second step, so the button would be missing on the first one. It shows on every normal `http`/`https` tab. |
| Fill another site's login without asking? | No. A look-alike page could get the password with one click. Copying stays free, because the user pastes it on purpose. |
| `Kirigami.SearchField` with "Search…"? | No: the Bookmarks panel (#227) already has a search field with an `edit-find` icon and a specific placeholder; it moves to `qml/common/PanelSearchField.qml` and both panels share it, so Kondor's panels look and behave the same. |
| Section headers "This Site" / "Other Sites" in the results? | Rejected: each result already shows its host and the header shows this site's host; headers would add two rows to a small popup. This site's logins come first. |
| Separate commands for "fill from another site" next to `fill(username)`? | No: `fill` and `copyPassword` take the origin of the `matches()` item, so there is one fill path and one copy path. The origin still never comes from QML code. |
| Key button tooltip "Fill Saved Password"? | Changed to "Saved Passwords", the panel heading: the panel now also searches and copies, and the button shows on sites with no login to fill. |
| Wallet unavailable | The panel shows "Passwords Unavailable" with the existing KWallet explanation, instead of a misleading "No Passwords for This Site". |
