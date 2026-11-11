# Browser extensions: compatibility report

Measured for [#105](https://github.com/lukasborges/kondor/issues/105), the follow-up of the #88
spike ([spec](specs/0088-browser-extensions-spike.md)). It records only what was observed.

## Setup

- Kondor `main` at 6bd759c, built on Fedora with **Qt 6.11.2** (Qt WebEngine based on Chromium 140),
  in a real window on KDE Plasma.
- Each run used a fresh isolated profile (temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
  `XDG_CACHE_HOME`), with `./build/kondor --new-instance --load-extension <dir> <page>`.
- The built-in ad blocker (#20) was turned off for these runs (`[AdBlock] Enabled=false`). Otherwise
  it blocks the same requests and hides what uBlock Origin Lite does.
- Measurements came from the Chrome DevTools Protocol (`QTWEBENGINE_REMOTE_DEBUGGING`) on the page,
  the extension's service worker and the popup page:
  - **Isolated worlds:** the content-script worlds of the page were listed. A world named after the
    extension means its content scripts were injected.
  - **API probe:** every `chrome.*` namespace and a call into each API family were tried in the
    service worker or the popup.
  - **Errors:** console errors and the extension errors Qt WebEngine prints to stderr were recorded.
- **Where the extensions came from:**
  - On this network, `scripts/fetch-extension.sh` gets the redirect from the Chrome Web Store, but the
    download from `clients2.googleusercontent.com` stalls after the TLS handshake with 0 bytes. The
    script then fails cleanly after its 120 s limit.
  - So the four open-source extensions were taken from their official GitHub releases:
    - Dark Reader `darkreader-chrome-mv3.zip`;
    - uBlock Origin Lite `uBOLite_*.chromium.zip`;
    - Bitwarden `dist-chrome-*.zip`;
    - Video Speed Controller `videospeed-*.zip`.
  - Google Translate and Tampermonkey are only published on the Chrome Web Store, so they were not
    measured.
- **Extension ids:** an unpacked extension without a manifest `key` gets an id derived from its
  path, so the ids below differ from the Chrome Web Store ids.

## Results

| Extension | Version / Manifest | Loads? | Content scripts work? | Popup in a tab works? | What fails (`chrome.*` API) | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Dark Reader | 4.9.135 / MV3 | Yes (`ohbdbfgf…`) | Injected (its isolated world exists on kde.org), but the page is not darkened: no `style.darkreader` and the background stays `rgb(252, 252, 252)`. | No: stays on "Loading, please wait". | The service worker throws at start on `chrome.tabs.onRemoved` (undefined: `chrome.tabs` only has `update` and `TAB_ID_NONE`), then repeatedly on `startBarrier.isPending` (null). `chrome.scripting`, `chrome.fontSettings`, `chrome.permissions` are absent, and `storage.sync` fails with "\"sync\" is not available in this instance of Chrome". | No |
| uBlock Origin Lite | 2026.1110.1816 / MV3 | Yes (`aainnknc…`) | It has no static content scripts. Blocking was measured instead: with the built-in blocker off, `pagead2.googlesyndication.com` and `googletagmanager.com` still load, as they do without the extension. | Partly: the page renders its frame, but without data (no site name, no counters). | "Service worker registration failed. Status code: 15", after `chrome.tabs.onRemoved` (undefined). `chrome.declarativeNetRequest` exists, but `getEnabledRulesets()` returns `[]`: the rulesets enabled in the manifest are not applied. `chrome.userScripts`, `chrome.scripting` and `chrome.action` are absent. | No |
| Bitwarden Password Manager | 2026.10.2 / MV3 | Yes (`chbhmmig…`) | Injected (its isolated world exists on kde.org). Without a working background, they have nothing to fill. | No: blank page. | The service worker fails to register (status 15) after `chrome.webNavigation.onCommitted` (undefined). The popup throws on `chrome.extension.getBackgroundPage` (undefined) and `chrome.tabs.getCurrent is not a function`. Declared but absent: `contextMenus`, `webNavigation`, `scripting`, `notifications`, `sidePanel`, `permissions`. Exposed: `alarms, clipboard, i18n, idle, management, offscreen, runtime, storage, tabs, webRequest`. | No |
| Google Translate | — | Not measured | — | — | Not downloadable on this network (Chrome Web Store only, see Setup). It relies on `contextMenus`, which is absent in every extension above that declares it. | Not measured |
| Video Speed Controller | 0.11.1 / MV3 | Yes (`npijgefe…`) | Injected (isolated world present, and `window.VSC` set in the page), but no controller is attached to the `<video>`: "[VSC] Initial settings load failed: Error: \"sync\" is not available in this instance of Chrome". | Partly: the speed buttons render, but the settings fail to load (`storage.sync`). The buttons need `chrome.tabs.query`/`tabs.sendMessage`, which are not functions. | `chrome.storage.sync`, `chrome.tabs.query`, `chrome.tabs.sendMessage`, and `chrome.action.setIcon` ("Failed to update icon"). | No |
| Tampermonkey | — | Not measured | — | — | Not downloadable on this network (Chrome Web Store only, see Setup). It relies on `userScripts`, which is absent even for uBlock Origin Lite, which declares it. | Not measured |

**#88 "Manual test":**
- Step 2 does not pass: Dark Reader loads but the page is not darkened (row above).
- Step 4 passes: with `--private`, kde.org has no Dark Reader content-script world, so extensions
  stay out of private profiles.

## Summary

- **What works in Qt WebEngine 6.11:**
  - loading an unpacked MV3 extension;
  - starting its service worker;
  - injecting its manifest content scripts into normal tabs (never into private ones);
  - opening `chrome-extension://…` pages in a tab;
  - `runtime` and `i18n`;
  - `storage.local` and `storage.session`;
  - `alarms`, `management`, `offscreen`, `clipboard`, `idle`, `webRequest`.
- **What fails:**
  - **Tabs:** `chrome.tabs` has only `update`, with no `query`, `sendMessage`, `getCurrent` or
    events.
  - **Absent namespaces:** `windows`, `action`, `contextMenus`, `scripting`, `webNavigation`,
    `userScripts`, `permissions`, `notifications`, `sidePanel`, `fontSettings`, `commands` and
    `extension.getBackgroundPage`.
  - **Sync storage:** `storage.sync` reports it "is not available".
  - **declarativeNetRequest:** manifest rulesets are not enabled.
- **Effect on real extensions:**
  - Every real extension here uses at least one of the missing APIs during startup. A missing
    `chrome.tabs` event or `storage.sync` call is enough to stop the background or the content
    script.
  - So none of the four measured extensions does its job, even though all of them load.
- **Popup in a tab:** this approach does not give a usable popup UI. Popups render at best partly,
  because they read settings through the missing APIs and act on "the active tab" through
  `chrome.tabs.query`, which Qt WebEngine does not provide.
- **Consequence for the follow-up:**
  - A user-facing installation flow (an "Add to Kondor" button, an Extensions page, toolbar popups)
    would install extensions that do not work.
  - Making them work would mean implementing Chrome's browser-layer APIs (`tabs`, `windows`,
    `action`, `scripting`, `storage.sync`…) inside Kondor. That is out of scope for #88 and much
    larger than an installation flow.
  - The report recommends waiting for a Qt WebEngine release that exposes more of these APIs and
    repeating this measurement then.
