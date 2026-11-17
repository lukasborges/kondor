# Browser identity (user agent) per site (#376)

> **Issue:** [#376](https://github.com/lukasborges/kondor/issues/376) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Some sites refuse or degrade browsers they do not recognize (banks, intranets, video sites). Let the
user choose, for one site, how Kondor identifies itself: as Kondor (default), Firefox, Chrome or a
custom user agent. The maintainer asked for it after comparing Kondor with Dooble.

## Context

- Python app; QML in `qml/`. `src/kondor/browser/profile/profilesetup.py` sets the profile's user
  agent: the QtWebEngine token is replaced by a Kondor token (`Kondor/<version>`), the rest is
  Chromium's.
- `QWebEngineProfile.httpUserAgent` is per profile, so a per-site identity needs two parts: the
  `User-Agent` request header (and Client Hints) per request, and the JavaScript values
  (`navigator.userAgent`, `appVersion`, `platform`, `userAgentData`) per page.
- A profile has one URL request interceptor, `AdBlockInterceptor`
  (`src/kondor/adblock/adblockinterceptor.py`), installed by `AdBlockManager`. `interceptRequest`
  runs on QtWebEngine's IO thread.
- Site settings store from #375: table `site_settings(host, allow_popups, user_agent)` and the
  `SiteSettings` singleton. This issue adds the user agent part; **no migration**.
- Site information popup (`qml/site/SiteInfoPopup.qml`) and Site Permissions dialog
  (`qml/site/SitePermissionsDialog.qml`); `InlineBar` in `qml/common/` for the reload offer (#180
  pattern: save, then offer Reload).

## Design / behavior

### 1. Identities

- **Kondor (default)**: the profile's user agent, unchanged; stored as no value.
- **Firefox**: a current Firefox for Linux string (`Mozilla/5.0 (X11; Linux x86_64; rv:<N>.0)
  Gecko/20100101 Firefox/<N>.0`, `<N>` a constant updated with Kondor releases).
- **Chrome**: the profile's user agent with the Kondor token removed (plain Chromium/Chrome
  string with the same Chrome version).
- **Custom…**: any non-empty text the user types (`376b-custom-browser-identity.png`).
- Stored per host in `site_settings.user_agent` (`SiteSettings.userAgent(host)`,
  `setUserAgent(host, text)`; an empty value removes it, and a row with nothing left is deleted).
  Presets are stored as their resulting text, so changing Kondor's version later does not change a
  Firefox choice made earlier.

### 2. Applying it

- **Request headers:** the profile's interceptor becomes a small composite: ad blocking as now,
  then the identity step, which sets `User-Agent` for requests whose **first-party host** has an
  identity. For the Firefox and Custom identities it also removes the `Sec-CH-UA*` Client Hints
  headers; for Chrome it leaves them. The identity step reads an in-memory `host → user agent` map
  that the main thread updates (copy-on-write or a lock), never the database from the IO thread.
- **Page values:** for a page whose host has an identity, a document-creation script in the main
  world defines `navigator.userAgent` and `navigator.appVersion` from it, `navigator.platform` as
  `Linux x86_64`, and, for Firefox and Custom, removes `navigator.userAgentData`. It runs before the
  page's scripts in every frame of that first-party host.
- Applies in normal and private tabs. Workers started by the page get the header but not the
  script (accepted limit).

### 3. Site information popup (`prototypes/376-site-browser-identity.qml`)

- Among "Permissions for this site", a row: icon `preferences-web-browser-identification`, label
  "Identify as:", and a `ComboBox` with "Kondor (default)", "Firefox", "Chrome", "Custom…",
  showing the current choice (a custom one shows "Custom…").
- Choosing an item saves at once (except Custom…, below) and shows the `InlineBar` "Reload the page
  to use the new browser identity." with **Reload** (`view-refresh`). The page is never reloaded by
  itself. Choosing "Kondor (default)" removes the identity.
- **Custom…** opens the dialog "Custom Browser Identity" (`376b`): "Site:" with the host,
  "User agent:" a wrapping text area, prefilled with the current custom value or the profile's
  user agent; **OK** (disabled while empty) saves, **Cancel** keeps the previous choice.
- Private windows: the row works but changes apply to that window's tabs only, in memory, and are
  gone when it closes; nothing is written. Saved identities apply to private tabs too.

### 4. Site Permissions dialog

- A host with an identity lists **Browser identity — Firefox** (or Chrome, or Custom) with
  **Revoke**, which removes it. The filter by site includes these rows.

## Acceptance criteria

- [ ] `https://www.whatismybrowser.com/` (or a local page that echoes the `User-Agent` header and
      `navigator.userAgent`) shows Kondor's user agent by default, Firefox's after choosing Firefox
      and reloading, in **both** the header and `navigator.userAgent`; other sites keep Kondor's
      (pytest with a local HTTP server echoing the header).
- [ ] Subresources of the site (images, XHR, iframes of the same first-party host) send the same
      identity; a different site in an iframe does not change it.
- [ ] Firefox and Custom remove `Sec-CH-UA*` headers and `navigator.userAgentData`; Chrome keeps
      them.
- [ ] The popup row, the InlineBar with Reload and the Custom dialog match `376-site-browser-identity.png`
      and `376b-custom-browser-identity.png`; choosing "Kondor (default)" removes the identity.
- [ ] The Site Permissions dialog lists and revokes identities.
- [ ] Private windows: a change works for that window only and nothing is written to disk.
- [ ] No database access from the IO thread; ad blocking still works (existing tests pass).
- [ ] Strings in `qsTr()`, translations complete; README "Features" gets one bullet: **Browser
      identity per site**.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with its own XDG folders under `~/kondor-test` (the maintainer keeps their own
Kondor open).

1. Open a page that shows the user agent; site information → Identify as: Firefox; the InlineBar
   offers Reload; reload: the page shows the Firefox string.
2. Open another site: it shows Kondor's string.
3. Custom…: type a string, OK, reload: the page shows it.
4. Site Permissions dialog: the entry is listed; Revoke; reload: Kondor's string again.
5. Private window: choose Chrome, reload: Chrome string; close the window, open a new private window:
   back to Kondor's; nothing written to disk.

## Out of scope

- A global user agent setting, rotating or random user agents, per-tab identities.
- Faking other fingerprinting values (screen, fonts, WebGL).

## Dependencies

- #375 (site settings store and its table). #7, #9 (site information popup and permissions dialog).

## Prototype

- [`prototypes/376-site-browser-identity.qml`](../../prototypes/376-site-browser-identity.qml) →
  [screenshot](../../prototypes/screenshots/376-site-browser-identity.png)
- [`prototypes/376b-custom-browser-identity.qml`](../../prototypes/376b-custom-browser-identity.qml) →
  [screenshot](../../prototypes/screenshots/376b-custom-browser-identity.png)

## Decisions

| Question | Decision |
| --- | --- |
| Where does the user change it? | In the site information popup, next to the site's permissions: it is a per-site choice made while on that site. A global Settings page was rejected: the problem is always one site. |
| Header only? | No: many sites read `navigator.userAgent` in JavaScript, so a header-only change would half work. Both are set, and Client Hints are kept consistent. |
| Reload by itself after a change? | No (#180): the user may have typed something; Reload is offered in the InlineBar. |
| Presets? | Kondor, Firefox, Chrome and Custom cover what sites check; more presets (Safari, Edge, mobile) were left out to keep the menu short. |
| Words? | "Identify as:" and "Browser identity", not "user agent", which only the Custom dialog shows for the value itself. |
| Private windows: per window or per tab? | Per private tab (PR #393 review). Every private tab has its own off-the-record profile, so an identity chosen there lives in that tab's profile and is gone when the tab closes; nothing is written to disk. A window-wide store shared across profiles was not worth it. |
| How are Client Hints "removed"? | Qt has no API to remove a request header, so clearing one means setting it to an empty value. Only the `Sec-CH-UA*` headers the request already carries are cleared; none is added (PR #393 review). |
