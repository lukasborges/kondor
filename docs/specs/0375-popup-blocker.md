# Pop-up blocker with per-site exceptions (#375)

> **Issue:** [#375](https://github.com/lukasborges/kondor/issues/375) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Kondor has **no pop-up blocker today**: a page can open a new tab with `window.open()` from a timer,
without any click, and that tab becomes the current one (checked by the architect on `main`,
2026-11-17, with a page that calls `window.open()` 1.5 s after loading). This issue:

1. blocks pop-ups that a page opens **without a user click** (pop-ups opened by a click keep
   working, as now);
2. shows what was blocked and lets the user open it;
3. lets the user allow pop-ups for one site from then on, and revoke that later.

The maintainer asked for the per-site exceptions after comparing Kondor with Dooble.

## Context

- Python app; QML in `qml/`. Profiles (#349): each profile has its own database, so everything
  stored here is per profile automatically.
- `WebEngineView.settings.javascriptCanOpenWindows` (Qt default `true`) is what lets a page open
  windows without a user gesture; with `false`, Blink still allows `window.open()` during a click
  and returns `null` otherwise. Kondor never sets it.
- QtWebEngine sends **no signal** for a pop-up Blink refused, so the page side must report it:
  `qml/browser/view/PageScriptBridges.qml` already runs page scripts with a `WebChannel`
  (passwords, media, extensions bridges).
- Site information popup: `qml/site/SiteInfoPopup.qml` lists the decided permissions of the site
  with a revoke button; `qml/site/SitePermissionsDialog.qml` lists them for every site;
  `PermissionTypeInfo.qml` gives icon and label per permission type.
- Settings → Privacy: `qml/settings/pages/PrivacySettingsPage.qml` (cookies, clear data).
- Database: `src/kondor/core/database/`, `SCHEMA_VERSION = 6`, one `migrate()` step per version.

## Design / behavior

### 1. Site settings store (new shared block)

- New table, next `SCHEMA_VERSION`:
  `site_settings(host TEXT PRIMARY KEY, allow_popups INTEGER NOT NULL DEFAULT 0, user_agent TEXT)`.
  `user_agent` stays unused here; #376 (browser identity per site) uses it, so the migration
  creates it now and #376 adds no migration.
- A small Python class, e.g. `SiteSettings` in `src/kondor/site/` (new folder, or the closest
  existing one within the folder limits), QML singleton by the AGENTS.md singleton pattern:
  `popupsAllowed(host)`, `setPopupsAllowed(host, allowed)` (a row with nothing left is deleted),
  `hostsWithPopupsAllowed()`, and a `changed(host)` signal. Hosts are lower-case, without port,
  exact match (no `www.` folding, no subdomain rules).
- Add the block to the AGENTS.md "Shared building blocks" table in this PR's description; the
  architect copies it into the maintainer's file.

### 2. Blocking

- New setting `blockPopups` (Settings → Privacy, default **on**): label "Pop-ups:", check box
  "Block pop-ups that open without a click". Applied with OK/Apply like the other options.
- Each view sets `settings.javascriptCanOpenWindows` to
  `!Settings.blockPopups || SiteSettings.popupsAllowed(<current host>)`, updated when the URL's
  host changes and on `SiteSettings.changed`. Normal and private tabs alike.
- **Reporting a blocked pop-up:** a document-creation script in the main world wraps
  `window.open`; when the original returns `null` and `navigator.userActivation.isActive` is
  false, it reports the requested URL (resolved against the page, `about:blank` when empty) and the
  target through the existing page channel. Nothing else is reported; the page cannot use it to
  open anything. The script does nothing when blocking is off for the page.
- Per tab, a `tab.popups` feature group (Tab bridge pattern): state `blockedUrls` (newest first,
  at most 10, cleared when the main frame navigates to another document) and `isAllowed`;
  commands `openBlocked(url)` and `setAllowed(allowed)`.

### 3. Address bar button and panel (`prototypes/375-popup-blocked.qml`)

- While `blockedUrls` is not empty, a flat icon-only button in the address bar, before the star:
  icon `window-duplicate-symbolic`, tooltip and `Accessible.name` "Pop-ups blocked",
  `ToolTip.delay: 600`. It appears without animation; nothing else announces it (no bar, no
  notification). `Accessible.announce("Pop-up blocked")` once per page.
- Its panel (a `ToolbarPopup`, like the other address bar popups; Esc closes it):
  - heading "Blocked Pop-ups" (level 4);
  - one `ItemDelegate` per blocked URL, icon `window-new`, text the URL without scheme, elided in
    the middle; the full URL in the tooltip. Click or Enter opens it once in a new foreground tab
    (as a normal navigation: the page's `window.opener` link cannot be restored) and removes it
    from the list; the panel stays open while rows remain;
  - separator, then a `Switch` "Allow pop-ups from <host>", checked when allowed; toggling saves at
    once (`setAllowed`). Its label wraps instead of eliding. **Hidden in private windows**: a
    private tab may open a blocked pop-up once but never stores an exception.
- After "Allow", the page's next `window.open()` works; already blocked ones stay in the list.

### 4. Site information popup and Site Permissions dialog (`prototypes/375b-popup-allowed-site-info.qml`)

- When the site has the exception, the site information popup lists **Pop-ups — Allowed** among
  the permissions (icon `window-duplicate-symbolic`), with the same revoke button as the others;
  revoking deletes the exception and the row disappears.
- The Site Permissions dialog lists the exception under its host the same way (filter by site
  included), with **Revoke**.

## Acceptance criteria

- [ ] With the default settings, a page that calls `window.open()` from a timer opens nothing, and
      the address bar shows the blocked pop-ups button; a `window.open()` inside a click handler
      still opens a tab (local test pages in `tests/data/`, pytest).
- [ ] The panel matches `375-popup-blocked.png`; a row opens its URL once in a new tab.
- [ ] "Allow pop-ups from <host>" stores the exception (pytest on `SiteSettings`), the next
      `window.open()` from a timer on that host opens, and other hosts stay blocked.
- [ ] Site information popup and Site Permissions dialog list and revoke the exception
      (`375b-popup-allowed-site-info.png`).
- [ ] With "Block pop-ups that open without a click" off, nothing is blocked and the button never
      shows.
- [ ] Private windows: blocking works, opening once works, no switch, nothing written to disk.
- [ ] Migration from schema 6 keeps every existing table and row (pytest).
- [ ] Every new string in `qsTr()`, translations complete; README "Features" gets one bullet
      (privacy group): **Pop-up blocker** with per-site exceptions.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with its own `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` (e.g. under
`~/kondor-test`), so the maintainer keeps their own Kondor open.

1. Open a local page that calls `window.open('https://kde.org/')` 1 s after loading: nothing opens,
   the button appears; open the panel, click the row: kde.org opens in a new tab.
2. Turn on "Allow pop-ups from <host>", reload: the pop-up opens by itself.
3. Site information popup: Pop-ups — Allowed; revoke; reload: blocked again.
4. A click-triggered pop-up (a sign-in button) opens normally with blocking on.
5. Private window: same page, button and panel, no switch; nothing new on disk.
6. Settings → Privacy, turn blocking off: the timer pop-up opens.

## Out of scope

- Pattern or wildcard exceptions, `www.` folding, per-profile import/export.
- Blocking pop-ups opened by a click, pop-unders, or redirects of the current tab.
- Keeping the `window.opener` link for a pop-up opened later from the panel.

## Dependencies

- #7 Site permissions, #9 Security indicator (site information popup), #349 Profiles (per-profile
  database). Followed by #376, which reuses the site settings store.

## Prototype

- [`prototypes/375-popup-blocked.qml`](../../prototypes/375-popup-blocked.qml) →
  [screenshot](../../prototypes/screenshots/375-popup-blocked.png)
- [`prototypes/375b-popup-allowed-site-info.qml`](../../prototypes/375b-popup-allowed-site-info.qml) →
  [screenshot](../../prototypes/screenshots/375b-popup-allowed-site-info.png)

## Decisions

| Question | Decision |
| --- | --- |
| Only exceptions, as asked? | A blocker first: exceptions mean nothing while every pop-up opens. The architect's test on `main` showed timer pop-ups opening as the current tab. |
| Block click-opened pop-ups too? | No. Sign-in, payment and print pop-ups open from clicks; blocking them breaks sites (see #361). Blink's user-activation rule is the standard line every browser uses. |
| How is the user told? | Only the address bar button, like Firefox and Chrome. An InlineBar was rejected: ad-like pop-ups are frequent, a bar on every such page would be noise (#256 rule: a passing state is an indicator, not a bar). |
| How is a blocked pop-up detected? | A `window.open` wrapper in the page reports `null` results without user activation; QtWebEngine has no signal for it. Accepted limit: a page could hide it, which only hides the button. |
| Icon? | `window-duplicate-symbolic`: Breeze has no "pop-up blocked" icon; two windows reads as "pop-up" and is monochrome for the address bar. |
| Exceptions in private windows? | Saved exceptions apply (they are read, not written); a private window cannot add or revoke one. |
| Where is the exception stored? | A new `site_settings` table shared with #376, not the QtWebEngine permission store (it has no pop-up type). |
