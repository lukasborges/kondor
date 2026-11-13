# Clean Links extension (#117)

> **Issue:** [#117](https://github.com/lukasborges/kondor/issues/117) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the catalog extension **Clean Links** in `extensions/clean-links/`. It removes tracking
parameters, as ClearURLs does:
- **Address:** the address of the current page loses its tracking parameters
  (`history.replaceState`, no reload).
- **Links:** a link on the page is cleaned just before the user can see or follow it (hover,
  keyboard focus, click, middle click, context menu).
- **Redirect wrappers:** links through the known redirect pages (Google, Facebook, Instagram,
  Reddit, YouTube) go straight to their target.
- **Settings:** extra parameters to remove, and sites whose links and addresses are left alone.

The parameters and wrappers are in one readable rules file. The extension sends nothing over the
network and stores nothing.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md) and
  [`docs/extensions/api.md`](../extensions/api.md)). This issue uses them as they are. If it
  needs a change, ask a question.
- **Injection (#107 item 3):** all `js` files of a content script are concatenated into **one
  closure**, in manifest order, and run in the application world: they share the page's DOM, not
  its JavaScript objects. The platform already skips sites turned off with "Run on <site>", and
  private windows unless the user allowed the extension there.
- **No package file reading:** an extension cannot read its own package files at run time, so the
  rules are a JavaScript file that holds **data only**, as in #112.
- **Settings form:** Kondor builds the Configure dialog from `settings`; a `text` setting is a
  `TextArea` (#107). `kondor.settings.onChanged` reaches the main frame only.
- **Repository rules (#108):** `tools/validate.py` must pass (README sections, listed files, no
  minified code, no `eval` and the other forbidden patterns), and `CONTRIBUTING.md` applies: no
  network access, no remote code, and the **Icons** rules from #205 (no background, legible at
  16 px, Breeze colors that read on light and dark).
- **Code quality:** AGENTS.md → "Code quality" applies to the JavaScript, as for #109–#116:
  functions of at most 10 lines and 3 parameters, nesting depth at most 2, files of at most 200
  lines, no comments. The rules file is one data statement per constant, so its length is not a
  function length. `scripts/check-code-quality.py --root` from this repository can check the files
  when they are copied under a `src/` folder of a temporary root.

## Design / behavior

1. **Files** in `extensions/clean-links/`:
   ```
   manifest.json
   rules.js        data only: cleanLinksParameterRules and cleanLinksRedirectRules (item 3)
   settings.js     reading the two text settings into lists (item 6)
   cleaning.js     cleaning one URL string: query parameters (item 4)
   unwrapping.js   unwrapping one redirect wrapper URL (item 5)
   content.js      wiring: the address, the link events, the settings (items 7 and 8)
   icon.svg        original artwork (a chain link with a sparkle or a broom), CONTRIBUTING.md → Icons
   README.md       "What it does", "Permissions", "Network", "Adding a rule"
   ```
   The `js` order in the manifest is `rules.js`, `settings.js`, `cleaning.js`, `unwrapping.js`,
   `content.js`. Only `content.js` runs code at the top level; the other files declare constants
   and functions.
2. **Manifest** (`kondor: 1`):
   - `id` `clean-links` and `version` `1.0.0`;
   - `name` "Clean Links" and `name[pt_BR]` "Links Limpos";
   - `description` "Removes tracking parameters from links and addresses." and
     `description[pt_BR]` "Remove parâmetros de rastreamento de links e endereços.";
   - `author` "Kondor contributors", `license` `GPL-3.0-or-later`, `homepage`
     `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/clean-links`,
     `icon` `icon.svg`;
   - **no `permissions`**;
   - one content script: `matches` `["https://*/*", "http://*/*"]`, the `js` files of item 1, no
     `css`, `runAt` `document-start`, `allFrames` `false`;
   - **`settings`**, in this order:
     - `{ "key": "extraParameters", "type": "text", "label": "Extra parameters to remove",
       "label[pt_BR]": "Parâmetros extras a remover", "default": "" }`;
     - `{ "key": "keptSites", "type": "text", "label": "Sites to leave alone",
       "label[pt_BR]": "Sites a não alterar", "default": "" }`;
   - **`action`**: `{ "siteToggle": true }` and no items.
3. **Rules (`rules.js`).** Two `const` declarations holding array literals, no functions:
   - `cleanLinksParameterRules`: objects `{ hosts, parameters }`.
     - `hosts`: domain names; a URL matches when its host equals one of them or ends with
       `"." + name`. `["*"]` matches every host.
     - `parameters`: parameter names, compared **case-insensitively**; a name ending in `*` is a
       prefix (`utm_*`).
     - Starting rules:

       | hosts | parameters |
       | --- | --- |
       | `*` | `utm_*`, `fbclid`, `gclid`, `gclsrc`, `dclid`, `gbraid`, `wbraid`, `msclkid`, `yclid`, `twclid`, `ttclid`, `mc_cid`, `mc_eid`, `igshid`, `igsh`, `_hsenc`, `_hsmi`, `__hstc`, `__hssc`, `__hsfp`, `mkt_tok`, `oly_anon_id`, `oly_enc_id`, `vero_id`, `_openstat`, `ref_src`, `ref_url` |
       | `youtube.com`, `youtu.be`, `spotify.com` | `si` |
       | `x.com`, `twitter.com` | `s`, `t` |

       `si`, `s` and `t` are common names that sites use for real data, so they are only removed
       on the hosts that use them for tracking.
   - `cleanLinksRedirectRules`: objects `{ host, path, parameters }`.
     - `host`: a regular expression literal tested against the wrapper's host;
     - `path`: the exact path, or absent for any path;
     - `parameters`: the query parameters that may hold the target, tried in order.
     - Starting rules:

       | host | path | parameters |
       | --- | --- | --- |
       | `/^(www\.)?google\.[a-z.]+$/` | `/url` | `q`, `url` |
       | `/^l[m]?\.facebook\.com$/` | `/l.php` | `u` |
       | `/^l\.instagram\.com$/` | | `u` |
       | `/^out\.reddit\.com$/` | | `url` |
       | `/^(www\.)?youtube\.com$/` | `/redirect` | `q` |

4. **Cleaning a URL (`cleaning.js`).** `cleanUrl(text, settings)` returns the cleaned URL string,
   or the **same string** when nothing changes:
   - only absolute `http:` and `https:` URLs are cleaned; anything else (text that is not an
     absolute URL, `javascript:`, `mailto:`, …) is returned as it is;
   - a URL whose host is in `keptSites` (same host or a subdomain of it) is returned as it is;
   - the query is split on `&` and each segment is **kept byte for byte** unless its decoded name
     matches a parameter of a rule whose `hosts` match the URL, or a parameter of
     `extraParameters` (which apply to every host). Never rebuild the query with
     `URLSearchParams`: it re-encodes the kept values (`%20` becomes `+`) and breaks some sites;
   - when every segment is removed, the `?` goes too; the path and the `#fragment` are kept as
     they are.
5. **Unwrapping (`unwrapping.js`).** `unwrapUrl(text)` returns the target of a redirect wrapper,
   or the same string:
   - the wrapper matches a rule when its host matches `host` and, when the rule has a `path`, its
     path is equal to it;
   - the target is the first non-empty value of the rule's `parameters` (decoded by
     `URLSearchParams.get`);
   - the target is used **only when it parses with `new URL` as an `http:` or `https:` URL**;
     otherwise the wrapper is left alone. This keeps a crafted `?q=javascript:…` from ever
     becoming a link;
   - unwrapping happens before cleaning, so the target is cleaned too; it is not repeated (one
     level of wrapping).
6. **Settings (`settings.js`).** Both text settings are one entry per line: lines are trimmed,
   empty lines and lines starting with `#` are ignored. `extraParameters` entries follow the
   parameter syntax of item 3. `keptSites` entries are host names; an entry written as a URL
   (`https://example.org/path`) uses its host. Invalid entries are ignored.
7. **The address (`content.js`).** At start, `unwrapUrl` is **not** applied to the page's own
   address (a wrapper page is the site's own page). `cleanUrl(location.href)` is computed and,
   when it differs, `history.replaceState(history.state, "", cleaned)` replaces it. No reload, no
   new history entry. This happens once per document; single-page navigations made later by the
   site are out of scope.
8. **Links (`content.js`).**
   - One listener per event on `document`, in the **capture** phase: `mouseover`, `focusin`,
     `click`, `auxclick` and `contextmenu`.
   - The handler takes `event.target.closest("a[href], area[href]")` (targets that are not
     elements are ignored), computes `cleanUrl(unwrapUrl(link.href))` and, when it differs, sets
     `link.href` to it.
   - Hover and focus make the status bar show the clean target; `click`, `auxclick` and
     `contextmenu` clean again in case the page rewrote the link on `mousedown` (Google does), so
     left click, middle click, "Open Link in New Tab" and "Copy Link Address" use the clean URL.
   - No `MutationObserver` and no walk over every link: the cost is one `closest` per event.
   - Links whose page handler navigates with JavaScript instead of the `href` are out of scope.
9. **Settings changes:** read `kondor.settings.values` at start and replace the parsed lists in
   `kondor.settings.onChanged`. Links cleaned earlier are not restored.
10. **No storage and no network.** The extension does not use `kondor.storage`, `kondor.notify`
    or any network API. Private tabs behave the same and write nothing.
11. **README.md** of the extension:
    - **What it does:** the address, the links, the wrappers (list them), the two settings with
      their line format (`*` for a prefix, `#` for a comment), "Run on <site>" for a site that
      breaks, and that `t.co` links are not unwrapped (they need a network request).
    - **Permissions:** one line for each match pattern (needed to clean links on every site) and
      a line saying it asks for no API permission.
    - **Network:** "None".
    - **Adding a rule:** the fields of item 3, why short names need a host, a version bump, and
      testing the rule on a live link.

## Acceptance criteria

- [ ] `extensions/clean-links/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists Clean Links.
  - `icon.svg` follows CONTRIBUTING.md → Icons; the PR shows it at 16 and 64 px on `#eff0f1` and
    `#232629`.
- [ ] Opening a page whose address has tracking parameters shows it without them, the other
  parameters and the fragment unchanged byte for byte, and Back does not return to the tracked
  address.
- [ ] Hovering, focusing, clicking, middle-clicking or copying a link with tracking parameters
  uses the clean URL. A link the page rewrites on `mousedown` is cleaned again before it is
  followed.
- [ ] Links through each wrapper of item 3 go to their cleaned target. A wrapper whose target is
  not `http(s)` is left as it is.
- [ ] `si` is removed from YouTube and Spotify links only; `s`/`t` from X/Twitter links only.
- [ ] `extraParameters` (exact and `*` prefix) removes those parameters on every host;
  `keptSites` leaves links to those sites and their own address untouched, subdomains included.
  Changes apply to the open page without a reload.
- [ ] Unchecking "Run on <site>" leaves that site's address and links untouched after a reload.
- [ ] In a private window, with the extension allowed there, it works the same and nothing is
  written to `extension_storage`.
- [ ] No page errors in the console from the extension. No network requests from the extension.
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, no comments.

## Manual test

Use a Kondor build from `main` with isolated `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
`XDG_CACHE_HOME` (AGENTS.md).

1. **Install.** `python3 tools/pack.py extensions/clean-links`, then Settings → Extensions →
   Install from File….
2. **Test page.** In a temporary directory (not in the repository), write `links.html` with:
   - a link `https://example.org/a?utm_source=x&id=1&q=a%20b&fbclid=y#top`;
   - a link `https://www.youtube.com/watch?v=abc&si=zz` and `https://example.org/?si=keep`;
   - one link through each wrapper of item 3 whose target has a `utm_campaign`, and a Google
     wrapper whose `q` is `javascript:alert(1)`;
   - a link whose `mousedown` handler rewrites its `href` to
     `https://www.google.com/url?q=https%3A%2F%2Fexample.org%2F%3Futm_medium%3Dx`;
   - a script that writes each link's `href` into a list on `click` (with `preventDefault`), so
     the result can be read on the page.

   Serve it with `python3 -m http.server 8000`.
3. **Address.** Open `http://localhost:8000/links.html?utm_source=a&id=3&q=a%20b#top`: the address
   bar shows `…/links.html?id=3&q=a%20b#top`. Back goes to the previous page, not to the tracked
   address.
4. **Links.** Hover each link and check the status bar, then click each one and read the list:
   - `https://example.org/a?id=1&q=a%20b#top`;
   - YouTube without `si`; `example.org/?si=keep` unchanged;
   - each wrapper replaced by its cleaned target; the `javascript:` wrapper unchanged;
   - the `mousedown` link ends as `https://example.org/`.

   Middle-click and "Copy Link Address" on the first link give the clean URL.
5. **Settings.** Configure: `extraParameters` = `id` and `q*`, `keptSites` = `example.org`. Without
   reloading, hover a new link (reload only the list): `example.org` links keep every parameter;
   `id` is removed elsewhere. Clear both settings.
6. **Site toggle.** Uncheck "Run on localhost", reload step 3: the address keeps its parameters
   and links are not changed.
7. **Private window.** Allow the extension in private windows and repeat steps 3–4 there. Run
   `sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from extension_storage"`: no row.
8. **Live sites.** Follow a Google search result, a Facebook outgoing link and a YouTube
   description link: each lands on the target without the wrapper or tracking parameters.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
- Unwrapping `t.co` and other opaque short links: their target is only known by asking the
  server, which would be network access. The issue's "where possible" means: not possible.
- Cleaning requests (images, scripts, `fetch`), form submissions, navigations made by page
  JavaScript, and later single-page-app address changes.
- Cleaning links inside `<iframe>`s, and the address of frames.
- Path-based tracking (Amazon `/ref=…`), fragment tracking, and rule lists downloaded from
  ClearURLs or elsewhere.
- A "Copy Clean Link" menu item, a toolbar counter, notifications, and any per-site list other
  than `keptSites` and "Run on <site>".
- Translations other than pt_BR, and JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged), #108 (the extensions repository and its tools, merged)
and #205 (icon rules, merged).

## Prototype

No prototype. The extension's only UI is generated by Kondor from the manifest:
- the Configure dialog with two text areas, as in `prototypes/107e-extensions-install-file.qml`;
- the platform's "Run on <site>" item in the toolbar Extensions menu, as in
  `prototypes/107f-extensions-menu.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| Rewrite every link on the page with a `MutationObserver`, or clean links on the events that use them? | On the events (`mouseover`, `focusin`, `click`, `auxclick`, `contextmenu`, capture phase). It covers links added later at no cost, and the second clean on `click` beats pages that rewrite on `mousedown`. Rejected: an observer over the whole document (runs forever on long-lived pages and fights pages that rewrite their links). |
| Rebuild the query with `URLSearchParams`? | No. Segments are kept byte for byte; only removed segments change. `URLSearchParams` re-encodes values (`%20` → `+`) and breaks some sites. |
| Remove `si`, `s`, `t` everywhere, as the issue lists `si`? | No. These names carry real data on many sites, so they are host-scoped rules (YouTube/Spotify for `si`, X/Twitter for `s`/`t`). The global list holds only names used only for tracking. |
| `t.co` links? | Not unwrapped: the target is only known by asking `t.co`, and the extension makes no network requests. Stated in the README. |
| Unwrap a wrapper target of any scheme? | No. Only `http:`/`https:` targets replace a link, so a crafted wrapper cannot turn a link into `javascript:`. |
| "Sites to leave alone": the platform's "Run on <site>" or a setting? | Both, for two different needs. "Run on <site>" turns the extension off on the page being viewed. `keptSites` protects a destination: its links are never cleaned on any page, and its own address is not cleaned either. |
| Clean the address of a wrapper page itself (`google.com/url?q=…`)? | No. Only links are unwrapped; the page's own address is only cleaned of parameters. Turning a page into another page is a navigation, not a cleanup. |
| Any API permission or storage? | None. Settings are kept by the platform; nothing else is remembered, so private tabs need no special case. |
| Labels end with ":"? | No. The Configure dialog adds the colon to every setting label (`ExtensionSettingsDialog.qml`). Item 2 first wrote the labels with a colon, which showed "::" (bug #209). |
