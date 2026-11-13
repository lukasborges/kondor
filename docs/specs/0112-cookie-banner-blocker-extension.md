# Cookie Banner Blocker extension (#112)

> **Issue:** [#112](https://github.com/lukasborges/kondor/issues/112) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the catalog extension **Cookie Banner Blocker** in `extensions/cookie-banners/`. On
pages that use one of the common consent platforms, it:
- hides the cookie consent banner and restores page scrolling;
- clicks "Reject all" (or "Only necessary") when the platform has such a button, unless the user
  chose "Hide banners only, never click".

Each platform is described by one readable rule file, so the community can add platforms by pull
request. "Run on <site>" turns the extension off for sites it breaks.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md) and
  [`docs/extensions/api.md`](../extensions/api.md)). This issue uses them as they are. If it
  needs a change, ask a question.
- **Injection (#107 item 3):** all `js` files of a content script are concatenated into **one
  closure**, in manifest order. They share top-level names without leaking globals. The platform
  already skips sites turned off with "Run on <site>". It also skips private windows unless the
  user allowed the extension there.
- **No package file reading:** an extension cannot read its own package files at run time. So the
  rules are JavaScript files that hold **data only** (item 3), not JSON files.
- **Frames:** with `allFrames`, every frame runs its own copy. Some platforms (Sourcepoint) draw
  their buttons inside an `<iframe>` from their own domain. That copy finds and clicks the button
  there. Kondor delivers `kondor.settings.onChanged` to the **main frame only**, so a frame picks
  up a changed setting at its next load.
- **Repository rules (#108):**
  - `tools/validate.py` must pass: README sections, every file referenced by the manifest (files
    in a subfolder are allowed when the manifest lists them), no minified code, no `eval` and the
    other forbidden patterns;
  - `CONTRIBUTING.md` applies: **no network access** and no remote code.
- **Code quality:** AGENTS.md → "Code quality" applies to the JavaScript, as for #109 and #110:
  - functions of at most 10 lines and at most 3 parameters;
  - nesting depth at most 2;
  - files of at most 200 lines;
  - no comments.

  A rule file is one statement (item 3), so its length is not a function length.
  `scripts/check-code-quality.py --root` from this repository can check the files when they are
  copied under a `src/` folder of a temporary root.

## Design / behavior

1. **Files** in `extensions/cookie-banners/`:
   ```
   manifest.json
   rules.js           the empty rule list, `cookieBannerRules`
   rules/onetrust.js  one rule file per platform (item 3), ten files:
   rules/cookiebot.js       onetrust, cookiebot, didomi, quantcast, trustarc, usercentrics,
   rules/…                  sourcepoint, funding-choices, complianz, cookieyes
   hiding.js          the hiding style sheet
   scrolling.js       restoring page scrolling
   rejecting.js       finding and clicking a rule's reject button
   content.js         wiring: settings, the page watcher, the per-rule state
   icon.svg           original artwork (a cookie with a diagonal stroke); not copied from another project
   README.md          "What it does", "Permissions", "Network", "Adding a platform"
   ```
   The `js` order in the manifest is: `rules.js`, the ten `rules/*.js` files in alphabetical
   order, `hiding.js`, `scrolling.js`, `rejecting.js` and `content.js`. Only the rule files (one
   `push` each) and `content.js` run code at the top level. The other files only declare
   functions and constants.
2. **Manifest** (`kondor: 1`):
   - `id` `cookie-banners` and `version` `1.0.0`;
   - `name` "Cookie Banner Blocker" and `name[pt_BR]` "Bloqueador de Avisos de Cookies";
   - `description` "Rejects or hides cookie consent banners." and `description[pt_BR]` "Recusa
     ou oculta avisos de consentimento de cookies.";
   - `author` "Kondor contributors" and `license` `GPL-3.0-or-later`;
   - `homepage` `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/cookie-banners`;
   - `icon` `icon.svg`;
   - **no `permissions`**;
   - one content script with:
     - `matches` `["https://*/*", "http://*/*"]`;
     - the `js` files of item 1, and no `css` (the style is built from the rules, item 4);
     - `runAt` `document-start` and `allFrames` `true`;
   - **`settings`**: one entry, `{ "key": "hideOnly", "type": "bool", "label": "Hide banners
     only, never click", "label[pt_BR]": "Apenas ocultar os avisos, nunca clicar", "default":
     false }`;
   - **`action`**: `{ "siteToggle": true }` and no items. This adds the platform's "Run on
     <site>".
3. **Rules.**
   - `rules.js` declares `const cookieBannerRules = [];`.
   - Each `rules/<platform>.js` holds exactly one statement, `cookieBannerRules.push({ … });`,
     with an object literal. It has no functions or other code.
   - Rule fields:

     | Field | Type | Meaning |
     | --- | --- | --- |
     | `id` | string | the file name without `.js` |
     | `name` | string | the platform's name, for the README |
     | `detect` | string[] | CSS selectors. The platform is present when one matches in the document. |
     | `reject` | string[] | optional. CSS selectors of the "Reject all" / "Only necessary" button, tried in order. Empty or absent means the rule only hides. |
     | `shadowHost` | string | optional. A selector of an element with an **open** shadow root. When set, `reject` is looked up inside that shadow root instead of the document. |
     | `hide` | string[] | CSS selectors of the banner, its overlay and its container. |
     | `scrollLockClasses` | string[] | optional. Classes the platform puts on `html` or `body` to block scrolling. |

   - **Starting selectors.** Use these values, and check each rule against a live site of that
     platform before the PR (item 9). When a `reject` selector can match a button other than
     reject/necessary-only on a real site, leave `reject` empty for that platform rather than risk
     an "Accept". Mention it in the PR.

     | id | detect | reject | shadowHost | hide | scrollLockClasses |
     | --- | --- | --- | --- | --- | --- |
     | `onetrust` | `#onetrust-banner-sdk` | `#onetrust-reject-all-handler` | | `#onetrust-banner-sdk`, `.onetrust-pc-dark-filter` | |
     | `cookiebot` | `#CybotCookiebotDialog` | `#CybotCookiebotDialogBodyButtonDecline`, `#CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll` | | `#CybotCookiebotDialog`, `#CybotCookiebotDialogBodyUnderlay` | `CybotCookiebotDialogActive` |
     | `didomi` | `#didomi-host` | `#didomi-notice-disagree-button` | | `#didomi-popup`, `#didomi-notice` | `didomi-popup-open` |
     | `quantcast` | `#qc-cmp2-container` | (none) | | `#qc-cmp2-container` | `qc-cmp-ui-showing` |
     | `trustarc` | `#truste-consent-track` | `#truste-consent-required` | | `#truste-consent-track`, `.truste_overlay`, `.truste_box_overlay` | |
     | `usercentrics` | `#usercentrics-root` | `button[data-testid="uc-deny-all-button"]` | `#usercentrics-root` | `#usercentrics-root` | |
     | `sourcepoint` | `[id^="sp_message_container_"]`, `.message-container .sp_choice_type_11` | `.sp_choice_type_13` | | `[id^="sp_message_container_"]` | `sp-message-open` |
     | `funding-choices` | `.fc-consent-root` | `.fc-cta-do-not-consent` | | `.fc-consent-root` | |
     | `complianz` | `#cmplz-cookiebanner-container` | `.cmplz-cookiebanner .cmplz-deny` | | `#cmplz-cookiebanner-container`, `.cmplz-cookiebanner` | |
     | `cookieyes` | `.cky-consent-container` | `.cky-btn-reject` | | `.cky-consent-container`, `.cky-overlay` | |

     The Sourcepoint `detect` has two selectors. The first finds the container in the page. The
     second finds the message inside its `<iframe>`, where the copy of the extension in that frame
     clicks `.sp_choice_type_13` (Sourcepoint's reject-all choice).
4. **Hiding (`hiding.js`).**
   - At start, build one style sheet with one rule per `hide` selector of every rule:
     `<selector> { display: none !important; }`.
   - Insert it as a `<style id="kondor-cookie-banners">` into `document.documentElement` as soon
     as that element exists. At `document-start` it may not exist yet. Then wait with a
     `MutationObserver` on `document` (`childList`), as Dark Mode does (#109).
   - The style is added in **both** modes and on every page, so a banner never flashes. Hiding
     an element that a page does not have does nothing.
   - An invalid selector must not drop the others. Check each with `document.querySelector`
     inside `try`/`catch` (it throws on invalid syntax) and leave out the ones that throw.
5. **Restoring scrolling (`scrolling.js`).** For a detected rule (item 7), on `html` and `body`:
   - remove every class of its `scrollLockClasses`;
   - when the element's computed `overflow-y` is `hidden`, set
     `style.setProperty("overflow-y", "auto", "important")`.

   This runs at every check while the rule is detected, because some platforms lock scrolling
   again after a delay. It does nothing on pages where no rule is detected.
6. **Rejecting (`rejecting.js`).** For a detected rule with a non-empty `reject`, when
   `hideOnly` is off:
   - look up the `reject` selectors in order, in the shadow root of `shadowHost` when the rule
     has one, else in the document. A missing host or a closed shadow root means "not found
     yet";
   - the first element found that is not `disabled` is clicked with `element.click()`. It works
     while the banner is hidden by item 4;
   - **one click per rule per document**: after a click, the rule is marked as rejected and never
     clicked again in that document, so a page that shows its banner again is not clicked in a
     loop. Hiding (item 4) still covers it;
   - when no element is found yet, the next check tries again.
7. **Watching the page (`content.js`).**
   - **Checks:** a check goes through every rule. A rule is **detected** when one of its `detect`
     selectors matches. For a detected rule, the check restores scrolling (item 5) and tries to
     reject (item 6).
   - **When:** one check at start. A `MutationObserver` on `document` (`childList`, `subtree`,
     `attributes` with `attributeFilter: ["class", "style"]`) schedules more checks, at most one
     per animation frame. Observing `document` works at `document-start`.
   - **Stopping:** 60 s after the document's `load` event, the observer disconnects. Banners
     appear within seconds, and this keeps long-lived pages from checking forever.
   - **Invalid selectors** in `detect` or `reject` count as "no match" (`try`/`catch` around
     each query) and never stop the other rules.
   - **Settings:** read `kondor.settings.values.hideOnly` at start, and update it in
     `kondor.settings.onChanged`. Turning `hideOnly` on stops further clicks in the open page.
     Turning it off lets the next check click.
8. **No storage and no network.** The extension does not use `kondor.storage`, `kondor.notify`
   or any network API. So private tabs behave the same and write nothing.
9. **README.md** of the extension:
   - **What it does:** it hides the consent banners of the listed platforms (name them), restores
     scrolling, and clicks "Reject all" or "Only necessary" when the platform has it. Also cover
     the "Hide banners only, never click" setting, and "Run on <site>" for sites that break. Say
     that a hidden banner also hides the platform's own settings dialog on that site; turn the
     extension off there to change cookie choices.
   - **Permissions:** one line for each match pattern, saying it is needed to find banners on
     every site, and a line saying it asks for no API permission.
   - **Network:** "None".
   - **Adding a platform:** the rule fields (item 3), adding the file to `rules/` and to the
     manifest's `js` list, a version bump, and testing on a live site of that platform.

## Acceptance criteria

- [ ] `extensions/cookie-banners/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists Cookie Banner Blocker.
- [ ] Installed in Kondor (from `main`) with "Install from File…", on the test pages of the
  manual test:
  - each platform's banner is hidden without flashing;
  - the page scrolls again;
  - the reject button is clicked once for every rule with a `reject`.
- [ ] With "Hide banners only, never click" on, banners are hidden and scrolling works, but no
  button is clicked.
- [ ] Rules with a `shadowHost` find their button in the open shadow root. A rule whose button is
  inside an `<iframe>` is clicked by the frame's copy.
- [ ] A banner added late (after a few seconds) is still handled. A page that shows its banner
  again is not clicked a second time.
- [ ] An invalid selector in one rule does not stop the others.
- [ ] Unchecking "Run on <site>" leaves the banner visible after the reload.
- [ ] In a private window, with the extension allowed there, it works the same, and nothing is
  written to `extension_storage`.
- [ ] Checked on at least one live site for each platform. The PR lists the sites, and any
  platform whose `reject` was left empty.
- [ ] No page errors in the console from the extension. No network requests from the extension.
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, no comments.

## Manual test

Use a Kondor build from `main` with isolated `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
`XDG_CACHE_HOME` (AGENTS.md).

1. **Install.** Run `python3 tools/pack.py extensions/cookie-banners`, then Settings → Extensions →
   Install from File….
2. **Test pages.** In a temporary directory (not in the repository), write one page per platform.
   Each page has:
   - long content, so the page needs scrolling;
   - a banner that uses the platform's `detect` and `hide` markup, with a reject button that
     matches `reject` and an accept button;
   - the platform's `scrollLockClasses` on `body`, and `overflow: hidden` on `body`;
   - buttons that write "rejected" or "accepted" into `document.title`.

   Also write these pages:
   - `usercentrics.html` puts its buttons in an **open** shadow root of `#usercentrics-root`;
   - `late.html` adds a OneTrust-like banner after 3 s and shows it again after another 3 s;
   - `sourcepoint.html` embeds `sp-frame.html` from the second server in a
     `[id^="sp_message_container_"]` element, and the frame holds `.message-container` with
     `.sp_choice_type_11` and `.sp_choice_type_13` buttons;
   - a page with a OneTrust banner and an invalid selector in a copy of the rules. For this one,
     install a locally edited package, then reinstall the clean one.

   Serve the directory with `python3 -m http.server 8000` and `python3 -m http.server 8001`.
3. **Reject.** Open each page:
   - the banner is never visible;
   - the page scrolls;
   - the title reads "rejected", except on `quantcast.html`, which has no `reject`.
4. **Late banner.** On `late.html` the first banner is rejected and the second one is hidden but
   not clicked again (the title counter in the page stays at 1).
5. **Hide only.** Turn on "Hide banners only, never click" and reload the pages: hidden, scrollable,
   and the title never changes.
6. **Site toggle.** Uncheck "Run on localhost" and reload: the banner shows and the page does not
   scroll.
7. **Private window.** Allow the extension in private windows, open a test page in a private
   window: same result as step 3, no error. Run
   `sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from extension_storage"`: no row.
8. **Live sites.** Visit one live site per platform and check that the banner is gone and, where
   a `reject` exists, that the site's cookie settings afterwards show only necessary cookies.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
- Platforms other than the ten of item 3, and generic heuristics for unknown banners (lists of
  site-specific selectors, as "I still don't care about cookies" ships).
- Opting out of individual purposes or vendors (Consent-O-Matic's per-category choices), and
  clicking through multi-step dialogs ("Settings" → toggles → "Save").
- Closed shadow roots, and banners whose buttons can only be found by their text.
- A toolbar counter, a per-site list other than "Run on <site>", and any notification.
- Translations other than pt_BR, and JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged) and #108 (the extensions repository and its tools,
merged).

## Prototype

No prototype. The extension's only UI is generated by Kondor from the manifest:
- the Configure dialog with one checkbox, as in `prototypes/107e-extensions-install-file.qml`;
- the platform's "Run on <site>" item in the toolbar Extensions menu, as in
  `prototypes/107f-extensions-menu.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| Rules as JSON files? | No. An extension cannot read its package files at run time, and fetching them would be network access. Each rule is a JavaScript file with one `push` of an object literal: readable data, reviewable in a pull request, and loaded by the manifest's `js` list. |
| Hide always, or only when rejecting fails? | Always. A style sheet with every rule's `hide` selectors is inserted at `document-start`, so banners never flash. Clicking "Reject all" while the banner is hidden still records the refusal. |
| Detect the reject button by its text? | No. Text changes with the language and the site, and a wrong match could click "Accept". Only the platform's stable selectors are clicked. A platform without a reliable one only hides (Quantcast). |
| How often to click? | Once per rule per document. A page that shows its banner again is hidden but not clicked again, so a broken site cannot loop. |
| What about the site's own cookie settings dialog, hidden by the same selectors? | Accepted. The README tells the user to turn the extension off for that site ("Run on <site>") to change cookie choices. |
| When to stop watching the page? | 60 s after `load`. Banners appear within seconds, and a watcher that never stops costs time on long-lived pages. |
| Any API permission or storage? | None. Nothing is remembered: rejecting is redone on every page, and private tabs need no special case. |
| How to do the live-site check (item 9) and the Kondor manual test without a display? ([PR #5](https://github.com/lukasborges/kondor-extensions/pull/5#issuecomment-6862611174)) | Run the live check headless: open one site per platform in an offscreen QtWebEngine page without the extension. Each `reject` match must read as reject/necessary-only, and after the click the platform's consent record (`OptanonConsent`, `CookieConsent`, `cookieyes-consent`, `cmplz_*`, `notice_gdpr_prefs`, `__tcfapi` getTCData, Usercentrics stored consent) must grant only necessary. Empty `reject` for any platform not verified that way, with no follow-up issue. The PR lists site, matched text, result and kept/emptied per platform. Manual steps 1, 6 and 7 need a person and do not block the merge (as in #109 and #110). They are listed as "Not done" for the maintainer. Rejected: emptying every `reject` (throws away verifiable selectors), and waiting on the maintainer. |
