# YouTube Dislike Counts extension (#114)

> **Issue:** [#114](https://github.com/lukasborges/kondor/issues/114) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the catalog extension **YouTube Dislike Counts** in `extensions/youtube-dislikes/`. It
uses the public [Return YouTube Dislike](https://returnyoutubedislike.com) API to:
- show the dislike count next to the dislike button on YouTube watch pages;
- show a like/dislike ratio bar under the like and dislike buttons;
- show the dislike count on YouTube Shorts.

The counts update when the user moves between videos inside YouTube, without a page load.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md) and
  [`docs/extensions/api.md`](../extensions/api.md)). This issue uses them as they are. If it
  needs a change, ask a question.
- **Injection (#107 item 3):**
  - all `js` files of a content script are concatenated into **one closure**, in manifest order;
  - scripts run in Qt WebEngine's **application world**. They share the page's DOM but not its
    JavaScript objects, so the extension uses the DOM and the URL only;
  - the platform already skips sites turned off with "Run on <site>", and private windows unless
    the user allowed the extension there.
- **YouTube is a single-page app.** Moving between videos, or scrolling to the next Short, does
  not load a new document. YouTube also re-renders its buttons at any time, for example after a
  click on Like. So the content script matches all of `www.youtube.com` and checks its elements
  again on a timer (item 7).
- **YouTube's page policy:** `www.youtube.com` sends `require-trusted-types-for 'script'`. DOM
  is built with `createElement`, `createElementNS`, `textContent` and `setAttribute`. Never use
  `innerHTML`, `outerHTML`, `insertAdjacentHTML` or `document.write`. `fetch` to
  `returnyoutubedislikeapi.com` is allowed by the page.
- **Return YouTube Dislike API** (checked on 2026-11-13):
  - `GET https://returnyoutubedislikeapi.com/votes?videoId=<id>` answers
    `{ id, dateCreated, likes, dislikes, rating, viewCount, deleted, … }` with
    `Access-Control-Allow-Origin: *`.
  - A malformed id gets 400 and an unknown id gets 404 (the docs) or zeros (seen for
    `AAAAAAAAAAA`).
  - The API has no hashed lookup, so the **video id itself** is sent.
- **API terms** ([usage rights](https://returnyoutubedislike.com/docs/usage-rights), checked on
  2026-11-13): "Third party use of this open API is allowed with the following restrictions":
  - **attribution**, "with either a link to this repo or a link to returnyoutubedislike.com";
  - **rate limits** of 100 requests per minute and 10,000 per day per client, with HTTP 429 when
    exceeded.

  The extension sends at most one request per video per page (item 4), far below the limits.
  The README gives the attribution (item 10).
- **YouTube DOM** (checked on 2026-11-13, logged out, in a headless Qt WebEngine view):
  - **Watch page:**
    - the buttons are `ytd-watch-metadata segmented-like-dislike-button-view-model` (`display:
      block; position: relative`). Inside it are `like-button-view-model` and
      `dislike-button-view-model`, each holding one `<button>`;
    - the like `<button>` holds an icon `div.ytSpecButtonShapeNextIcon` and then the count
      `div.ytSpecButtonShapeNextButtonTextContent` (14 px, weight 500);
    - the dislike `<button>` has only the icon div, and is 56 px wide.
  - **Shorts** (`/shorts/<id>`):
    - the action column is `reel-action-bar-view-model` inside `ytd-reel-video-renderer`. It holds
      `like-button-view-model` (a heart icon with its count in
      `div.ytSpecButtonShapeWithLabelLabel`), then comments, share, remix and the channel;
    - YouTube showed **no dislike button** on Shorts. It may show one for other users (logged in,
      experiments), so item 6 handles both layouts.
- **Repository rules (#108):**
  - `tools/validate.py` must pass: README sections, every file referenced by the manifest, no
    minified code, no `eval` and the other forbidden patterns;
  - `CONTRIBUTING.md` applies: outside services only when needed, **listed under "Network"** in
    the README, and no remote code. The vote data is JSON, never code.
- **Code quality:** AGENTS.md → "Code quality" applies to the JavaScript, as for #109, #110,
  #112 and #113:
  - functions of at most 10 lines and at most 3 parameters;
  - nesting depth at most 2;
  - files of at most 200 lines;
  - no comments.

  `scripts/check-code-quality.py --root` from this repository checks the files when they are
  copied, in their folder layout, under a `src/` folder of a temporary root that also holds an
  empty `scripts/code-quality-baseline.json` (`{}`).

## Design / behavior

1. **Files** in `extensions/youtube-dislikes/`:
   ```
   manifest.json
   texts.js     the in-page texts and number formatting
   lookup.js    the video id of the page, fetching and checking the votes
   watch.js     the count in the dislike button and the ratio bar on watch pages
   shorts.js    the count on Shorts
   content.js   wiring: settings, page changes, the timer, per-video state
   icon.svg     original artwork: a thumbs-down over a two-part bar; not the Return YouTube Dislike logo
   README.md    "What it does", "Permissions", "Network"
   ```
   The `js` order in the manifest is the order above. `content.js` is last and the only file
   that runs code at the top level. The other files only declare functions and constants.
2. **Manifest** (`kondor: 1`):
   - `id` `youtube-dislikes` and `version` `1.0.0`;
   - `name` "YouTube Dislike Counts" and `name[pt_BR]` "Contagem de Não Gostei do YouTube";
   - `description` "Shows dislike counts on YouTube videos and Shorts." and
     `description[pt_BR]` "Mostra a contagem de \"não gostei\" em vídeos e Shorts do YouTube.";
   - `author` "Kondor contributors" and `license` `GPL-3.0-or-later`;
   - `homepage` `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/youtube-dislikes`;
   - `icon` `icon.svg`;
   - **no `permissions`**;
   - one content script with:
     - `matches` `["https://www.youtube.com/*"]`;
     - the five `js` files of item 1, and no `css`;
     - `runAt` `document-end` and `allFrames` `false`;
   - **`settings`**: one `bool` setting:

     | key | label | label[pt_BR] | default |
     | --- | --- | --- | --- |
     | `showRatioBar` | Show the like/dislike ratio bar | Mostrar a barra de proporção entre gostei e não gostei | `true` |

   - **`action`**: `{ "siteToggle": true }` and no items.
3. **The page's video (`lookup.js`).** A video id matches `^[A-Za-z0-9_-]{11}$`.
   - **Watch page:** when `location.pathname` is `/watch`, the `v` parameter of
     `location.search`.
   - **Short:** when `location.pathname` matches `^/shorts/([A-Za-z0-9_-]{11})/?$`, that id.
   - Any other page has no video id, and the extension shows nothing there.
4. **Fetching votes (`lookup.js`).**
   - **Request:** one `fetch` of `https://returnyoutubedislikeapi.com/votes?videoId=` plus the
     `encodeURIComponent`-encoded id, with the options
     `{ credentials: "omit", referrerPolicy: "no-referrer", cache: "no-store" }`.
   - **Answer:** valid only when the status is 200, the JSON parses, `id` equals the video id,
     and `likes` and `dislikes` are both integers `>= 0`. The result is `{ likes, dislikes }`.
   - **Failure:** a network error, any other status (400, 404 and 429 included), invalid JSON or
     a check above that fails all mean "no votes": the extension shows nothing for that video.
     They are caught, and nothing is logged.
   - **One request per video:** the **promise** of the result is kept in a `Map` from video id
     to promise, for this document, so going back to a video or a second lookup while the first
     is running sends nothing. A failure is kept as "no votes" too, and is not retried in this
     document. Nothing goes to `kondor.storage`.
   - **Stale answers:** an answer that arrives after the page moved to another video is stored
     in the map but not shown.
5. **Watch page (`watch.js`).** The host is
   `ytd-watch-metadata segmented-like-dislike-button-view-model`, and the dislike button is its
   `dislike-button-view-model button`.
   - **Count:**
     - a `<div>` with the classes `ytSpecButtonShapeNextButtonTextContent` (YouTube's own, so it
       looks like the like count) and `kondor-youtube-dislikes-count`;
     - it is inserted right after the button's `div.ytSpecButtonShapeNextIcon`, with the inline
       style `margin-inline-start: 6px`;
     - its text is the formatted dislike count (item 8);
     - the dislike button gets the inline style `width: auto`, so it grows to fit the count.
   - **Ratio bar**, when `showRatioBar` is true and `likes + dislikes > 0`:
     - a `<div>` with the class `kondor-youtube-dislikes-ratio`, appended to the host, with
       `position: absolute; inset-inline: 12px; bottom: -6px; height: 3px; border-radius: 2px;
       overflow: hidden; display: flex;
       background: color-mix(in srgb, currentColor 25%, transparent)`;
     - one child `<div>` with `height: 100%`, `width` = `likes / (likes + dislikes) × 100 %`
       and `background: currentColor`. `currentColor` is YouTube's text color, so the bar follows
       YouTube's light and dark themes with no color of its own. The likes part starts at the
       inline start, so it mirrors in right-to-left pages;
     - `title` and `aria-label` "Likes: 1,360 · Dislikes: 11" (item 8, full numbers), and
       `role="img"`.
   - **Looked at:** the mock of this layout (the count right of the dislike icon, the bar 6 px
     under the button pair) matched YouTube's look on 2026-11-13; see "Prototype".
6. **Shorts (`shorts.js`).** The action column is the `reel-action-bar-view-model` of
   `ytd-reel-video-renderer[is-active]`. When no renderer has `is-active` (as seen on
   2026-11-13), it is the first `reel-action-bar-view-model` inside `ytd-shorts`.
   - **With a YouTube dislike button** (`dislike-button-view-model` in the column): the count
     goes in that button's `div.ytSpecButtonShapeWithLabelLabel`, which then holds a `<span>`
     with the class `kondor-youtube-dislikes-count` and the formatted count, the same way the
     like count shows under the like button.
   - **Without one** (the layout seen on 2026-11-13): a read-only item right after
     `like-button-view-model`:
     - a `<div>` with the class `kondor-youtube-dislikes-shorts`, `display: flex;
       flex-direction: column; align-items: center`, `role="img"` and the `aria-label`
       "Dislikes: 1,234" (item 8, full number), and a bottom margin equal to the gap between
       YouTube's like and comments items (16 px on 2026-11-13; check it on a screenshot);
     - a 48 × 48 px box with the icon centered and **no background**, so it does not look like a
       button. The icon is a 24 px SVG built with `createElementNS`: `viewBox="0 0 24 24"`,
       `fill="none"`, `stroke="currentColor"`, `stroke-width="1.5"`,
       `stroke-linejoin="round"`, with the two shapes
       `<rect x="2.75" y="3.75" width="3.5" height="10.5" rx="1"/>` and
       `<path d="M6.25 13.5 L10.5 20.25 L11.6 20.25 A1.6 1.6 0 0 0 13.15 18.25 L12.25 14.25 L18.6 14.25 A2 2 0 0 0 20.55 11.8 L19 5.3 A2 2 0 0 0 17.05 3.75 L6.25 3.75"/>`
       (an original thumbs-down outline). YouTube's like icon on Shorts is a heart, so it is not
       copied or flipped;
     - under it, a `<div>` with YouTube's class `ytSpecButtonShapeWithLabelLabel` and the
       formatted count.
   - **No ratio bar on Shorts** (Decisions).
7. **Keeping it in place (`content.js`).**
   - **Ticks:** one function, `refresh`, runs at start, on `yt-navigate-finish` (on `document`),
     and every **1 s** from a `setInterval`.
   - **Video change:** `refresh` reads the video id (item 3). When it changed:
     - it removes every element the extension added: all `kondor-youtube-dislikes-*` elements,
       and the `width` style it set on the dislike button;
     - it forgets the old votes, and looks up the new video (item 4). A video id that is
       absent needs no lookup.
   - **Drawing:** when the votes of the current video are known, `refresh` makes the page match
     items 5 and 6. It is **idempotent**: it writes to the DOM only when an element is missing
     or its text, width or `title` differs. So a tick that finds everything in place changes
     nothing, and YouTube re-rendering its buttons is repaired within a second.
   - **Settings:** read `kondor.settings.values` at start. In `kondor.settings.onChanged`, keep
     the new values and call `refresh`. Turning `showRatioBar` off removes the bar, and turning
     it on draws it again.
8. **Texts and numbers (`texts.js`).**
   - **Counts** use `Intl.NumberFormat` in the **page's language**
     (`document.documentElement.lang`, or `kondor.locale` with `_` replaced by `-` when the page
     has none), so they match YouTube's like count:
     - next to the buttons: `{ notation: "compact", maximumFractionDigits: 1 }`, for example
       "2,5 mil" in pt-BR and "2.5K" in en-US;
     - in `title` and `aria-label`: the standard format, for example "1.360" in pt-BR and
       "1,360" in en-US.
   - **Texts**, with `%1` and `%2` replaced by the numbers. The pt_BR texts are used when
     `kondor.locale` starts with `pt`, the English ones otherwise:

     | text | English | pt_BR |
     | --- | --- | --- |
     | ratio bar | Likes: %1 · Dislikes: %2 | Gostei: %1 · Não gostei: %2 |
     | Shorts item | Dislikes: %1 | Não gostei: %1 |

9. **No storage.** The extension does not use `kondor.storage` or `kondor.notify`. The only
   network request is item 4. So private tabs behave the same and write nothing.
10. **README.md** of the extension:
    - **What it does:** shows the dislike count next to the dislike button on YouTube watch
      pages and on Shorts, and the like/dislike ratio bar under the buttons (it can be turned
      off in the extension's settings). Say that:
      - the counts come from Return YouTube Dislike and are estimates, since YouTube no longer
        publishes dislikes;
      - the extension does not change votes or send the user's own vote;
      - it works on `www.youtube.com` only, and "Run on <site>" turns it off there.
    - **Permissions:** one line for `https://www.youtube.com/*`, saying it is needed to find the
      like and dislike buttons, and a line saying it asks for no API permission.
    - **Network:** `returnyoutubedislikeapi.com`, with:
      - what is sent: the id of the open video, once per video while the page is open, with no
        cookies and no referrer. Say plainly that the service can see which videos are opened;
      - what is received: the like and dislike counts of that video;
      - the attribution: "Dislike counts from [Return YouTube Dislike](https://returnyoutubedislike.com),
        used under its [usage rights](https://returnyoutubedislike.com/docs/usage-rights). This
        extension is not affiliated with Return YouTube Dislike."

## Acceptance criteria

- [ ] `extensions/youtube-dislikes/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists YouTube Dislike Counts.
  - `python3 tools/pack.py extensions/youtube-dislikes` produces the package.
- [ ] On a YouTube watch page, the dislike button shows the API's dislike count in the compact
  format of the page's language. The ratio bar shows under the like and dislike buttons, with
  the full counts in its tooltip.
- [ ] Turning "Show the like/dislike ratio bar" off removes the bar at once, and the count stays.
- [ ] On a Short, the dislike count shows in the action column: in YouTube's dislike button when
  there is one, otherwise as the read-only item after the like button.
- [ ] Moving to another video or Short inside YouTube (no reload) removes the old count and bar
  and shows the new video's.
- [ ] When YouTube re-renders the buttons (for example after a click on Like), the count and bar
  come back within about a second. A tick with everything in place makes no DOM change.
- [ ] One request per video id per page, to `returnyoutubedislikeapi.com` only, without cookies
  or referrer. No request on pages that are neither a watch page nor a Short.
- [ ] A network failure, a 404 or a 429 shows nothing, with no console error.
- [ ] No page errors in the console from the extension, including no Trusted Types violations.
- [ ] Nothing is written to `extension_storage`, in normal and in private windows.
- [ ] The README has the three sections, the Return YouTube Dislike attribution, and the note
  that the video id is sent (item 10).
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, no comments.

## Manual test

The developer runs without a display, so the check is done headless, as decided for #112 and
#113. Use temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

Tips for the harness:
- Qt's QML runtime is `/usr/lib64/qt6/bin/qml`, which is not on `PATH`.
- Fedora turns QML `console.log` off: set `QT_LOGGING_RULES="qml.debug=true"` and
  `QT_FORCE_STDERR_LOGGING=1`.
- Pass the harness's own arguments after `--`.
- `WebEngineView.grabToImage()` saves screenshots.

Steps:

1. **Package.** `python3 tools/validate.py`, `python3 tools/pack.py extensions/youtube-dislikes`
   and `python3 tools/build-catalog.py`.
2. **Harness.** A small QML file with a `WebEngineView` (`QT_QPA_PLATFORM=offscreen`, an
   off-the-record profile) that injects the five scripts, concatenated in manifest order inside
   one closure, as a `WebEngineScript` in the application world at document end. It has a stub
   `kondor` object (`locale`, `settings.values`, `settings.onChanged`) that the test can change,
   and it wraps `fetch` to log requests.
3. **Watch page.** Open a video and compare with
   `curl "https://returnyoutubedislikeapi.com/votes?videoId=<id>"`:
   - the dislike button holds the compact count;
   - the bar's likes part has the expected width, and its `title` has the full counts;
   - take a screenshot of the buttons for the PR.
4. **Setting.** Set `showRatioBar` to false and fire `onChanged`: the bar is gone and the count
   stays. Set it back: the bar returns.
5. **Re-render.** Remove the count element and the bar with `runJavaScript`: both are back
   within 2 s. Then count DOM mutations of the host with a `MutationObserver` over 3 s while
   nothing changes: there are none.
6. **Navigation.** Go to a second video inside YouTube (click a related video): the old count
   goes, the new count shows, and one new request is logged.
7. **Shorts.** Open `https://www.youtube.com/shorts`, which redirects to a Short: the
   dislike count shows in the action column (say which layout appeared). Take a screenshot. Move
   to the next Short (the "next" button or `ArrowDown`): the count changes, and one new request
   is logged.
8. **Network.** The log has one request per video id, only to `returnyoutubedislikeapi.com`,
   with the options of item 4, and none on the home page.
9. **Failure.** Make the wrapped `fetch` return 404, then 429, then reject: nothing shows, and
   there is no console error.
10. **pt_BR.** With `locale` `pt_BR` the bar's `title` reads "Gostei: … · Não gostei: …".

The steps that need a person at a running Kondor do not block the merge (as in #109, #110, #112
and #113). They are listed under "Not done" in the PR's Testing section for the maintainer:
- "Install from File…";
- the Configure dialog with the checkbox;
- "Run on www.youtube.com";
- a private window with `sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from
  extension_storage"` returning no row.

The PR names the video(s) and Shorts used and the result of each step above.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
- `m.youtube.com`, `/embed/` players on other sites, `youtube-nocookie.com`, YouTube Music,
  video thumbnails and lists (home page, search, sidebar), and the player's fullscreen quick
  action buttons (`yt-player-quick-action-buttons`).
- Sending votes or the user's own like/dislike to the API, the API's registration and
  "puzzle" endpoints, and adjusting the counts after the user clicks Like or Dislike.
- A ratio bar on Shorts, view counts, ratings as stars or percentages, and colors other than
  YouTube's text color.
- Caching counts across documents or in `kondor.storage`, and a rate-limit back-off beyond item
  4's one request per video.
- Keyboard shortcuts, toolbar items, and settings other than `showRatioBar`.
- Translations other than pt_BR, and JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged) and #108 (the extensions repository and its tools,
merged).

## Prototype

No new QML prototype. The Kondor UI is generated from the manifest:
- the Configure dialog, with one checkbox (`bool` setting,
  `qml/extensions/ExtensionSettingControls.qml`), as in `prototypes/107e-extensions-install-file.qml`;
- "Run on <site>" in the toolbar Extensions panel, as in the #183 prototypes.

The count, the bar and the Shorts item are web content on YouTube's page, not Kondor QML.
Items 5 and 6 describe them fully. The architect mocked both in a headless view on 2026-11-13,
with these results:
- **watch page:** "2,5 mil" on the like button and "11" on the dislike button in the same
  font, and the bar as a thin line in the text color under the pair. It reads as part of
  YouTube;
- **Shorts:** the first mock reused YouTube's like icon, which is a heart there, and an upside
  down heart is meaningless. The original thumbs-down outline of item 6 replaces it.

## Decisions

| Question | Decision |
| --- | --- |
| Which data source? | The public Return YouTube Dislike API, as the issue asks. Its terms allow third-party use with attribution and per-client rate limits (100/min, 10,000/day). One request per video per page stays far below them, and the README gives the attribution. |
| The API needs the video id. Is that acceptable? | Yes, with disclosure. The API has no hashed lookup (unlike SponsorBlock in #113). No cookies and no referrer are sent, the answer is kept in memory only, and the README's "Network" section says plainly that the service sees which videos are opened. The user can turn the extension off per site or uninstall it. |
| How does the count look on watch pages? | It reuses YouTube's own text class inside the dislike button, so it matches the like count exactly, and the button grows to fit it. Rejected: a separate label next to the buttons, which looks foreign and wraps in narrow windows. |
| Ratio bar colors? | `currentColor` for likes and a 25 % mix of it for dislikes. It follows YouTube's light and dark themes and needs no color of its own. Rejected: blue/grey or green/red bars, which clash with one of the themes and add meaning (good/bad) the data does not carry. |
| Ratio bar on Shorts? | No. The Shorts action column is a narrow vertical stack of round buttons with no place for a horizontal bar. The issue text named both, but the count alone carries the information there. |
| Shorts with no dislike button? | A read-only item after the like button: an original thumbs-down outline with no background, so it does not look clickable, and the count under it. It has an `aria-label` for screen readers. Rejected: flipping YouTube's like icon (a heart on Shorts), and putting the count under the like count (ambiguous). |
| How does it survive YouTube's re-rendering? | A 1 s idempotent `refresh` plus `yt-navigate-finish`. Rejected: a `MutationObserver` on the whole document, which fires constantly on YouTube and costs more than a cheap timer that usually changes nothing. |
| Number format? | `Intl.NumberFormat` in the page's language, compact next to the buttons and full in the tooltip, so the dislike count matches YouTube's like count. The fixed texts follow Kondor's locale, as in #113. |
| Retry after a failure or a 429? | No retry in the same page. The failure is kept as "no votes" for that video. A person cannot get near the rate limit with one request per video, and a retry loop could. |
| Manual test without a display? | Headless QtWebEngine harness on live YouTube pages (as decided for #112 and #113). The interactive Kondor steps are listed as "Not done" for the maintainer and do not block the merge. |
