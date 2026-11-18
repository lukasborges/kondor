# HTTPS-only mode (#409)

> **Issue:** [#409](https://github.com/lukasborges/kondor/issues/409) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

An opt-in mode where Kondor always tries the secure version of a site and warns before loading a
site that only offers plain HTTP.

## Context

- Request interceptors are chained per profile: `src/kondor/site/identity/identityinterceptor.py`
  wraps `src/kondor/adblock/adblockinterceptor.py`, set in `profileidentity.py`.
- Error pages: `qml/browser/pages/CertificateErrorPage.qml` (layout to copy), shown from
  `qml/browser/view/WebViewTab.qml`. Security indicator: `tab.security` (#9).
- Settings: `src/kondor/core/settings/`, page `qml/settings/pages/PrivacySettingsPage.qml`.

## Design / behavior

### 1. Setting (`prototypes/409b-settings-https-only.qml`)

- New setting `httpsOnly` (bool, default `false`). Settings → Privacy, row **Connections:**,
  check box "Always use secure connections (HTTPS)". It applies at once (OK/Apply) to every
  profile, private ones included (reading a setting writes nothing).

### 2. Upgrade

- A new interceptor in the same chain upgrades **main-frame navigations** from `http://` to
  `https://` (same host, port 80 → default, path and query kept) with `info.redirect()`.
  Sub-resources are not touched (mixed content stays Chromium's business).
- Never upgraded: `localhost`, `*.localhost`, `127.0.0.0/8`, `[::1]`, single-label hosts
  (`router`, `intranet`), IP addresses of private ranges (10/8, 172.16/12, 192.168/16), and hosts
  the user allowed (below).
- The tab remembers the original `http://` URL of an upgraded navigation (`tab.security`, a new
  property `upgradedFrom`), cleared when the load finishes successfully.

### 3. Warning page (`prototypes/409-https-only-warning.qml`)

- When an upgraded navigation fails (connection error, certificate error, or no response in
  **10 s**), the tab shows `HttpsOnlyPage` instead of Chromium's error or the certificate page:
  `security-medium` icon, heading "Secure site not available", "<b>host</b> does not support
  HTTPS. Anyone on the network could see or change what is sent to it.", a flat **Continue to HTTP
  Site** and a highlighted **Go Back** (`go-previous`; closes the tab's error state like
  `CertificateErrorPage` does, or shows the New Tab page when there is no history).
- The address bar shows the original `http://` URL and the "Not Secure" indicator in the neutral
  color.
- **Continue to HTTP Site** allows the host until Kondor quits (in memory, per profile; never
  written to disk) and loads the `http://` URL.

## Acceptance criteria

- [ ] Off by default; with it on, `http://example.com` loads `https://example.com`.
- [ ] `http://neverssl.com` (or a local test server without TLS on a public-looking host in the
      pytest) shows the warning page; Continue loads it over HTTP, and later visits to that host
      in the same run go straight through; after a restart the page shows again.
- [ ] `http://localhost:8000`, `http://192.168.1.1` and `http://router/` are never upgraded.
- [ ] Sub-resources of an HTTPS page are untouched.
- [ ] Private tabs upgrade too, and their allowed hosts are forgotten with their profile.
- [ ] Matches `409-https-only-warning.png` and `409b-settings-https-only.png`, Breeze and Breeze
      Dark.
- [ ] Strings in `qsTr()`, translations complete; README "Privacy and security" gets a bullet.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`.

1. Turn the option on; open `http://kde.org`: it loads over HTTPS.
2. Open `http://neverssl.com`: warning; Go Back; open again, Continue: the site loads with "Not
   Secure".
3. Open the router page of the local network: loads without a warning.

## Out of scope

- Upgrading sub-resources, HSTS preload management, a per-site permanent exception list in
  Settings, DNS over HTTPS.

## Dependencies

- None (uses #9, done).

## Prototype

- [`prototypes/409-https-only-warning.qml`](../../prototypes/409-https-only-warning.qml) →
  [screenshot](../../prototypes/screenshots/409-https-only-warning.png)
- [`prototypes/409b-settings-https-only.qml`](../../prototypes/409b-settings-https-only.qml) →
  [screenshot](../../prototypes/screenshots/409b-settings-https-only.png)
  (`withHttpsOnly` in `prototypes/common/SettingsDialogMock.qml`)

## Decisions

| Question | Decision |
| --- | --- |
| Remember "Continue to HTTP Site" for good? | No: only until Kondor quits, like Firefox; a permanent list would quietly weaken the mode and need its own UI. |
| Upgrade local addresses? | No: routers, printers and dev servers rarely have certificates, and warning on them every time would push users to turn the mode off. |
| On by default? | No: the maintainer's choice; some sites still break without HTTP, and the mode is opt-in like in Firefox. |
| Approved | Prototypes approved by the maintainer. |
