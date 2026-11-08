# Password manager and autofill (#21)

> **Issue:** [#21](https://github.com/lukasborges/kondor/issues/21) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Offer to save login credentials, store them securely in KWallet, autofill them on later visits and manage them in Settings.

## Context

Nothing. Kondor already bundles `QtWebChannel` (see `release.yml`), and `QQuickWebEngineProfile` has `userScripts`. Fedora has `kf6-kwallet` (KWallet 6).

## Design / behavior

1. **Dependency**: `find_package(KF6Wallet REQUIRED)` and `KF6::Wallet`; add `kf6-kwallet-devel` to README/workflows. Add `WebChannel` to Qt components (`Qt6::WebChannel`).
2. **Bridge object** `src/passwords/passwordbridge.{h,cpp}` registered on a `QWebChannel` per `WebEngineView` (`webView.webChannel` in QML, object id `"kondorPasswords"`), with slots:
   - `void formSubmitted(const QString &origin, const QString &username, const QString &password)` → emits a signal the tab turns into a "save password" prompt (only for non-private tabs, only if not already saved with the same password, only for `https:` origins or `localhost`).
   - `QVariantList credentialsFor(const QString &origin)` → returns `[{username, password}]` (JS receives it via callback).
3. **User script** `qrc:/scripts/passwords.js` injected into **every** profile via `WebEngineScript { injectionPoint: WebEngineScript.DocumentReady; worldId: WebEngineScript.ApplicationWorld; runOnSubframes: true; sourceUrl: "qrc:/scripts/passwords.js" }` together with `qrc:///qtwebchannel/qwebchannel.js`:
   - find `input[type=password]` and the closest preceding text/email input as username;
   - on `submit` of the form (and on click of a submit button for JS-driven forms), call `formSubmitted(location.origin, user, pass)`;
   - on load, call `credentialsFor(location.origin)` and if exactly one credential exists fill both fields and dispatch `input`/`change` events; if several, fill nothing (the chooser is part of the UI below).
   - Running in `ApplicationWorld` keeps the bridge invisible to page scripts.
4. **Storage** `src/passwords/passwordstore.{h,cpp}`: KWallet folder `"Kondor"`, one map entry per origin: `{ "<username>": "<password>", … }` via `KWallet::Wallet::openWallet(KWallet::Wallet::NetworkWallet(), 0, KWallet::Wallet::Asynchronous)`, `writeMap`/`readMap`. Handle "wallet disabled/denied": feature silently off with a one-time inline warning.
5. **UI**:
   - Save prompt using the shared `InlineBar` (#5): "Save the password for **user** on **site**?" — "Save", "Not Now", "Never for This Site" (store the origin in setting `Passwords/NeverSave`).
   - Address bar key icon (`dialog-password`) when credentials exist for the site; click → menu of usernames → fills the chosen credential (call a JS function through `runJavaScript(…, WebEngineScript.ApplicationWorld)`).
   - Settings (#3) page "Passwords": list origins/usernames, "Show" (re-reads from wallet), "Delete", checkbox "Offer to save passwords" (default on).
6. **Never** in private tabs: don't inject the script into private profiles, or make the bridge refuse.

## Acceptance criteria

- [ ] Logging into a site offers to save; accepted credentials appear in KWallet (KWalletManager, folder "Kondor").
- [ ] Revisiting the login page autofills a single credential; multiple credentials can be chosen from the key icon.
- [ ] "Never for This Site" works; private tabs never prompt or fill.
- [ ] Credentials can be listed/deleted in Settings; nothing is stored in plain text by Kondor.

## Manual test

Use a test login page (e.g. `https://practicetestautomation.com/practice-test-login/` user `student` / `Password123`), save, log out, return; check KWalletManager; try a private tab.

## Out of scope

Password generator, import from other browsers, passkeys/WebAuthn, non-KWallet keyrings.

## Dependencies

#3 (Settings), #5 (`InlineBar`).

## Prototype

Visual target — match it (controls, Kirigami components, icon names, wording, placement). If it disagrees with this spec, the spec wins.

**Save-password prompt and key icon in the address bar** — [`prototypes/21-passwords.qml`](../../prototypes/21-passwords.qml)

![Save-password prompt and key icon in the address bar](../../prototypes/screenshots/21-passwords.png)

## Decisions

_None yet._ Answers to developer questions (`question` label) are recorded here as `| Question | Decision |` rows.
