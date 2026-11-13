# Skip Sponsors extension (#113)

> **Issue:** [#113](https://github.com/lukasborges/kondor/issues/113) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the catalog extension **Skip Sponsors** in `extensions/skip-sponsors/`. On YouTube watch
pages it uses the community data of the [SponsorBlock](https://sponsor.ajay.app) project to:
- skip sponsored segments, intros, self-promotion and other categories automatically, or show a
  "Skip" button for them, as the user chose per category;
- mark the segments on the video's progress bar;
- after an automatic skip, show a short notice with an "Undo" button.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md) and
  [`docs/extensions/api.md`](../extensions/api.md)). This issue uses them as they are. If it
  needs a change, ask a question.
- **Injection (#107 item 3):**
  - all `js` files of a content script are concatenated into **one closure**, in manifest order;
  - scripts run in Qt WebEngine's **application world** (`src/extensions/scripts/contentscriptbuilder.cpp`).
    They share the page's DOM but not its JavaScript objects, so YouTube's player API
    (`movie_player.getVideoData()` and so on) is out of reach. The extension uses the DOM, the
    URL and the `<video>` element only;
  - the platform already skips sites turned off with "Run on <site>", and private windows unless
    the user allowed the extension there.
- **YouTube is a single-page app.** Moving from the home page to a video, or from one video to
  the next, does not load a new document. The content script therefore matches all of
  `www.youtube.com` and acts only while the URL is a watch page (item 4).
- **YouTube's page policy:** `www.youtube.com` sends `require-trusted-types-for 'script'` and has
  no `connect-src` limit. So:
  - DOM is built with `createElement`, `textContent` and `setAttribute`. Never use
    `innerHTML`, `outerHTML`, `insertAdjacentHTML` or `document.write`;
  - `fetch` to `sponsor.ajay.app` is allowed by the page. The SponsorBlock API answers with
    `Access-Control-Allow-Origin: *`.
- **SponsorBlock API** (checked on 2026-11-13):
  `GET https://sponsor.ajay.app/api/skipSegments/<prefix>?categories=<JSON array>&actionTypes=["skip"]`,
  where `<prefix>` is the first 4 hex characters of the SHA-256 of the video id. The answer is
  a JSON array of `{ videoID, segments: [{ category, actionType, segment: [start, end], UUID,
  videoDuration, … }] }` for every video whose hash starts with the prefix. An empty array or
  HTTP 404 means no segments.
- **Data license:** SponsorBlock's database is licensed
  [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The extension downloads
  segments at run time for the open video only, keeps them in memory, and ships no data in its
  package. The data is shown, not redistributed, and Kondor is non-commercial. So the
  requirement is attribution, in the README (item 10). The extension code is
  `GPL-3.0-or-later`, like the others.
- **Repository rules (#108):**
  - `tools/validate.py` must pass: README sections, every file referenced by the manifest, no
    minified code, no `eval` and the other forbidden patterns;
  - `CONTRIBUTING.md` applies: outside services only when needed, **listed under "Network"** in
    the README, and no remote code. The segment data is JSON, never code.
- **Code quality:** AGENTS.md → "Code quality" applies to the JavaScript, as for #109, #110 and
  #112:
  - functions of at most 10 lines and at most 3 parameters;
  - nesting depth at most 2;
  - files of at most 200 lines;
  - no comments.

  `scripts/check-code-quality.py --root` from this repository checks the files when they are
  copied, in their folder layout, under a `src/` folder of a temporary root that also holds an
  empty `scripts/code-quality-baseline.json` (`{}`).

## Design / behavior

1. **Files** in `extensions/skip-sponsors/`:
   ```
   manifest.json
   categories.js   the seven categories: id, marker color, in-page names; the in-page texts
   lookup.js       the video id of the page, the hash prefix, fetching and filtering segments
   segments.js     which segments apply now, and the segment at a given time
   markers.js      the segment marks on the progress bar
   notice.js       the in-page "Skip" button and the "Skipped" notice
   content.js      wiring: settings, page changes, video events, per-video state
   icon.svg        original artwork (a play triangle with a skip-forward arrow); not the SponsorBlock logo
   README.md       "What it does", "Permissions", "Network"
   ```
   The `js` order in the manifest is the order above. `content.js` is last and the only file
   that runs code at the top level. The other files only declare functions and constants.
2. **Manifest** (`kondor: 1`):
   - `id` `skip-sponsors` and `version` `1.0.0`;
   - `name` "Skip Sponsors" and `name[pt_BR]` "Pular Patrocínios";
   - `description` "Skips sponsored segments and intros in YouTube videos." and
     `description[pt_BR]` "Pula patrocínios e introduções em vídeos do YouTube.";
   - `author` "Kondor contributors" and `license` `GPL-3.0-or-later`;
   - `homepage` `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/skip-sponsors`;
   - `icon` `icon.svg`;
   - **no `permissions`**;
   - one content script with:
     - `matches` `["https://www.youtube.com/*"]`;
     - the six `js` files of item 1, and no `css`;
     - `runAt` `document-end` and `allFrames` `false`;
   - **`settings`**: seven `choice` settings, one per category, all with the same three
     `choices`:

     | value | label | label[pt_BR] |
     | --- | --- | --- |
     | `skip` | Skip automatically | Pular automaticamente |
     | `button` | Show a Skip button | Mostrar um botão Pular |
     | `ignore` | Do nothing | Não fazer nada |

     | key | label | label[pt_BR] | default |
     | --- | --- | --- | --- |
     | `sponsor` | Sponsor | Patrocínio | `skip` |
     | `selfpromo` | Self-promotion | Autopromoção | `button` |
     | `interaction` | Interaction reminder (subscribe, like) | Lembrete de interação (inscrever-se, curtir) | `button` |
     | `intro` | Intro | Introdução | `ignore` |
     | `outro` | Outro (end cards, credits) | Encerramento (telas finais, créditos) | `ignore` |
     | `preview` | Preview or recap | Prévia ou recapitulação | `ignore` |
     | `filler` | Filler or tangent | Enrolação ou digressão | `ignore` |

     The setting key is also the SponsorBlock category id. The settings appear in this order.
   - **`action`**: `{ "siteToggle": true }` and no items.
3. **Categories (`categories.js`).** One constant list, in the order of item 2, with for each
   category its id, its marker color and its short in-page name in English and pt_BR:

   | id | color | name | pt_BR |
   | --- | --- | --- | --- |
   | `sponsor` | `#00d400` | Sponsor | Patrocínio |
   | `selfpromo` | `#ffff00` | Self-promotion | Autopromoção |
   | `interaction` | `#cc00ff` | Interaction reminder | Lembrete de interação |
   | `intro` | `#00ffff` | Intro | Introdução |
   | `outro` | `#0202ed` | Outro | Encerramento |
   | `preview` | `#008fd6` | Preview | Prévia |
   | `filler` | `#7300ff` | Filler | Enrolação |

   In-page texts, with `%1` replaced by the category name:

   | text | English | pt_BR |
   | --- | --- | --- |
   | skip button | Skip %1 | Pular %1 |
   | skipped notice | Skipped: %1 | Pulado: %1 |
   | undo button | Undo | Desfazer |

   The pt_BR texts are used when `kondor.locale` starts with `pt`, the English ones otherwise.
   These literal colors are allowed here, since a web page has no Kirigami theme (as in #110).
4. **The page's video (`lookup.js`).**
   - **Video id:** only when `location.pathname` is `/watch`, the `v` parameter of
     `location.search`, when it matches `^[A-Za-z0-9_-]{11}$`. Any other page has no video id.
   - **Player:** the `<video>` inside `#movie_player`. An event counts only when its target is
     that element (`event.target.closest("#movie_player")`).
   - **Ads:** while `#movie_player` has the class `ad-showing`, the extension does nothing
     (no skip, no button; item 7 hides a shown button).
5. **Looking up segments (`lookup.js`).**
   - **Prefix:** `crypto.subtle.digest("SHA-256", new TextEncoder().encode(videoId))`, as
     lowercase hex, first 4 characters. Only the prefix is sent, never the video id.
   - **Request:** one `fetch` of the URL in "Context" with `categories` = the JSON array of the
     **seven** category ids and `actionTypes` = `["skip"]`, both `encodeURIComponent`-encoded,
     and the options `{ credentials: "omit", referrerPolicy: "no-referrer", cache: "no-store" }`.
     All seven are always asked, so a settings change needs no new request.
   - **No request** when all seven categories are `ignore`, or when the page has no video id.
   - **Answer:** take the entry whose `videoID` equals the video id, and keep its segments with
     `actionType` `skip`, a known category, and `0 <= start < end`. Sort them by `start`.
   - **Failure:** a network error, a status other than 200 (404 included), invalid JSON or no
     matching entry all mean "no segments". They are caught, and nothing is logged.
   - **Memory only:** the segments are kept in a `Map` from video id to segments, for this
     document. Going back to a video does not ask again. Nothing goes to `kondor.storage`.
   - **Stale answers:** an answer that arrives after the page moved to another video is stored in
     the map but not applied.
6. **Which segments apply (`segments.js`).** A segment applies when:
   - its category's setting is not `ignore`; and
   - its `videoDuration` is 0, or differs from the player's `duration` by at most 2 s (a
     different cut of the video is ignored).

   The **segment at a time `t`** is the first applying segment, in `start` order, with
   `start <= t < end`.
7. **Skipping (`content.js`, `notice.js`).** On every `timeupdate` and `seeked` of the player
   (listeners on `document`, capture phase), when there is no ad:
   - **Category `skip`:** when the segment at `currentTime` has not been undone, and
     `currentTime < end − 0.5`, set `currentTime` to `end`. Then show the **skipped notice**
     for 5 s: the text "Skipped: Sponsor" and an "Undo" button.
     - "Undo" sets `currentTime` to the segment's `start`, marks that segment as **undone** for
       the open video (it plays through and is not skipped again until the video id changes),
       and hides the notice.
   - **Category `button`:** while `currentTime` is inside the segment, show the **skip button**
     "Skip Sponsor". Clicking it sets `currentTime` to `end` and hides it. The button hides
     when the time leaves the segment.
   - With no segment at the current time and no notice timer running, nothing is shown.
   - A segment the user seeks into is handled the same way. That matches SponsorBlock, and the
     user can turn the category to `button` or "Undo".
8. **In-page element (`notice.js`).**
   - **Element:** one host `<div>` appended to `#movie_player`, with a **closed** shadow root,
     so page CSS cannot change it and its CSS cannot leak. It is created on the first need and
     reused. Its content is built with `createElement` and `textContent` only (Trusted Types,
     "Context").
   - **Content:** a label (`<span>`) and one `<button>`. The skip button is the button alone,
     with "Skip Sponsor". The notice is the label "Skipped: Sponsor" followed by the "Undo"
     button.
   - **Look:**
     - `position: absolute`, `right: 12px`, `bottom: 64px` (above YouTube's controls),
       `z-index: 60`;
     - a rounded box (4 px), white text on `rgba(0, 0, 0, 0.75)`, 14 px system sans-serif
       font, padding 6 px 10 px, 8 px between label and button;
     - the button: transparent background, 1 px white border, 4 px radius, white text,
       `cursor: pointer`, and a visible `:focus-visible` outline.
   - **Keyboard and accessibility:** both are real `<button>`s, so Tab reaches them and Enter or
     Space activates them. The host has `role="status"` and `aria-live="polite"`, so a screen
     reader announces the notice. A click or key on the button calls `stopPropagation()`, so
     the player does not also toggle play/pause.
   - **Hidden** (`display: none` on the host) when nothing is to be shown, during ads, and when
     the page leaves the video.
9. **Progress bar marks (`markers.js`).**
   - **Element:** one `<div>` container, with the class `kondor-skip-sponsors-marks`, appended to
     `#movie_player .ytp-progress-bar`, with `position: absolute; inset: 0;
     pointer-events: none; z-index: 40`.
   - **Marks:** one child `<div>` per applying segment, `position: absolute`, `top: 0`,
     `height: 100%`, `left` = `start / duration × 100 %`, `width` = `(end − start) / duration
     × 100 %` (at least 2 px through `min-width`), and its category's color.
   - **When:** drawn again when the segments arrive, on the player's `loadedmetadata` and
     `durationchange`, and after a settings change. Removed when the page has no video id or
     moves to another video. Nothing is drawn while `duration` is not finite, or while the
     progress bar is not in the page.
   - Ignored categories (`ignore`) get no mark.
10. **Page changes and settings (`content.js`).**
    - **Page changes:** YouTube fires `yt-navigate-finish` on `document` after every in-app
      navigation. The extension listens to it and to the player's `loadedmetadata`
      (capture phase on `document`). On each, it reads the video id (item 4). When the id
      changed, it clears the undone segments, hides the in-page element, removes the marks and
      looks up the new video's segments (item 5). It also runs once at start.
    - **Settings:** read `kondor.settings.values` at start. In `kondor.settings.onChanged`,
      keep the new values and draw the marks again. The next `timeupdate` follows the new
      modes. When the old values had every category `ignore` and the new ones do not, look up
      the open video now.
11. **No storage.** The extension does not use `kondor.storage` or `kondor.notify`. The only
    network request is item 5. So private tabs behave the same and write nothing.
12. **README.md** of the extension:
    - **What it does:** skips or offers to skip the segments the SponsorBlock community marked in
      YouTube videos; the seven categories and their default choice; the marks on the progress
      bar; the "Undo" notice; "Run on <site>". Say that segments are found only for videos that
      the SponsorBlock community has marked, and only on `www.youtube.com` watch pages.
    - **Permissions:** one line for `https://www.youtube.com/*`, saying it is needed to find the
      video player and its progress bar, and a line saying it asks for no API permission.
    - **Network:** `sponsor.ajay.app`, with:
      - what is sent: the first 4 characters of the SHA-256 hash of the video id, which is
        shared by many videos, so the server cannot tell which video is watched; no cookies, no
        referrer;
      - what is received: the segments of every video with that hash prefix;
      - the attribution: "Segment data from [SponsorBlock](https://sponsor.ajay.app) by its
        contributors, licensed under
        [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). This extension is
        not affiliated with SponsorBlock, and it keeps no copy of the data."

## Acceptance criteria

- [ ] `extensions/skip-sponsors/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists Skip Sponsors.
  - `python3 tools/pack.py extensions/skip-sponsors` produces the package.
- [ ] On a YouTube video with a `sponsor` segment, with the default settings, the segment is
  skipped once when playback reaches it. The "Skipped: Sponsor" notice shows for 5 s, and
  "Undo" plays the segment without skipping it again.
- [ ] A category set to "Show a Skip button" shows "Skip <name>" while the time is inside the
  segment, and the button skips it. A category set to "Do nothing" is neither skipped nor
  marked.
- [ ] The applying segments are marked on the progress bar in their category colors.
- [ ] Moving to another video inside YouTube (no reload) looks up that video, and clears the old
  marks, button and undone state.
- [ ] Only the 4-character hash prefix is sent, once per video, without cookies or referrer.
  No request is made when every category is "Do nothing" or the page is not a watch page.
  There is no other network request.
- [ ] Nothing happens during an ad, and a different cut of a video (duration off by more than
  2 s) is not skipped.
- [ ] A network failure or a 404 leaves the page as it is, with no console error.
- [ ] No page errors in the console from the extension, including no Trusted Types violations.
- [ ] Nothing is written to `extension_storage`, in normal and in private windows.
- [ ] The README has the three sections, the SponsorBlock attribution and the data license of
  item 12.
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, no comments.

## Manual test

The developer runs without a display, so the check is done headless, as decided for #112. Use
temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

1. **Package.** `python3 tools/validate.py`, `python3 tools/pack.py extensions/skip-sponsors`
   and `python3 tools/build-catalog.py`.
2. **Harness.** A small QML file with a `WebEngineView` (`QT_QPA_PLATFORM=offscreen`) that
   injects the six scripts, concatenated in manifest order inside one closure, as a
   `WebEngineScript` in the application world at document end, with a stub `kondor` object
   (`locale`, `settings.values`, `settings.onChanged`) that the test can change.
3. **Live video.** Pick a YouTube video for which the API returns a `sponsor` segment (query
   `skipSegments/<prefix>` by hand first) and open its watch page in the harness. Start playback
   with `video.play()` (muted) and seek to just before the segment:
   - `currentTime` jumps to the segment's end, and the notice host shows "Skipped: Sponsor";
   - clicking "Undo" through `runJavaScript` returns to `start` and the segment then plays
     through;
   - the progress bar holds the marks container with one mark per applying segment.
4. **Button mode.** Change the stub setting `sponsor` to `button` and fire `onChanged`; seek into
   the segment: the "Skip Sponsor" button shows and no skip happens until it is clicked.
5. **Navigation.** Go to a second video inside YouTube (click a link, or `history.pushState`
   plus YouTube's own navigation): the marks change and a new request is made.
6. **Network.** Log requests in the harness (a `WebEngineUrlRequestInterceptor` in a small C++
   helper, or the DevTools protocol): exactly one request to `sponsor.ajay.app` per video, with
   a 4-character prefix, no `Cookie` and no `Referer`. Set every category to `ignore` and
   reload: no request.
7. **Failure.** Point the stub at a prefix that returns 404, or block the host: no console error.
8. **pt_BR.** With `locale` `pt_BR` the notice reads "Pulado: Patrocínio" and "Desfazer".

The steps that need a person at a running Kondor do not block the merge (as in #109, #110 and
#112). They are listed under "Not done" in the PR's Testing section for the maintainer:
"Install from File…", the Configure dialog, "Run on www.youtube.com", and a private window with
`sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from extension_storage"` returning no row.
The PR names the video(s) used and the result of each step above.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
- `m.youtube.com`, YouTube Shorts, `/embed/` players on other sites, `youtube-nocookie.com`,
  and YouTube Music.
- Other SponsorBlock categories (`music_offtopic`, `poi_highlight`, `exclusive_access`,
  `chapter`) and action types (`mute`, `full`, `poi`, `chapter`).
- Submitting segments, voting, a SponsorBlock user id, statistics ("time saved"), and a
  minimum segment length setting.
- Keyboard shortcuts, toolbar items, a per-video or per-channel whitelist other than
  "Run on <site>".
- Caching segments across documents or in `kondor.storage`.
- Translations other than pt_BR, and JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged) and #108 (the extensions repository and its tools,
merged).

## Prototype

No new prototype. The Kondor UI is generated from the manifest:
- the Configure dialog, with one combo box per category (`choice` setting,
  `qml/extensions/ExtensionSettingControls.qml`), as in `prototypes/107e-extensions-install-file.qml`;
- "Run on <site>" in the toolbar Extensions panel, as in the #183 prototypes.

The in-page button, notice and marks are web content on YouTube's player, not Kondor QML. Items
8 and 9 describe them fully.

## Decisions

| Question | Decision |
| --- | --- |
| How is the video looked up without telling the server which video is watched? | The 4-character SHA-256 prefix API ("Context"), as the issue asks. It also returns other videos' segments, which are filtered out. No cookies and no referrer are sent. |
| Which categories are asked for? | Always all seven, whatever the settings, so a settings change needs no new request and the request says nothing about the user's choices. No request at all when every category is "Do nothing". |
| Are segments cached? | Only in memory, per document. Writing them to `kondor.storage` would keep a viewing history on disk (private tabs could not write it anyway) and copy CC BY-NC-SA data. |
| Which pages? | `www.youtube.com` watch pages only. The script matches all of `www.youtube.com` because YouTube navigates without reloading. Shorts, embeds and `m.youtube.com` have other players and are out of scope. |
| "Unskip" or "Undo"? | "Undo", KDE's standard word for reverting the last action, also in pt_BR ("Desfazer"). An undo button after the action follows the HIG preference for undo over confirmation, and the notice hides by itself after 5 s. Rejected: a confirmation before skipping (one more click on every video), and no notice at all (an unwanted skip could not be reverted). |
| How is the in-page UI built? | One host in `#movie_player` with a closed shadow root, built with `createElement`/`textContent` only, because YouTube enforces Trusted Types. It is a real `<button>` with a live region, so it works with the keyboard and a screen reader. It is placed above YouTube's controls on the right, where SponsorBlock users expect it. |
| Default choices? | Sponsor skips automatically. Self-promotion and interaction reminders show a button. The rest do nothing. That follows SponsorBlock's own defaults: only the least controversial category is skipped without asking. |
| Does an ad or a re-cut video trigger skips? | No. Nothing happens while `#movie_player` has `ad-showing`, and a segment whose `videoDuration` differs from the player's by more than 2 s is ignored. |
| Data license? | CC BY-NC-SA 4.0 data, fetched at run time for the open video and shown, not stored or redistributed; Kondor is non-commercial. The README gives the attribution and the license link. The extension code stays `GPL-3.0-or-later`. The name is "Skip Sponsors", and the icon is original, not SponsorBlock's, so it is not mistaken for the official extension. |
| Manual test without a display? | Headless QtWebEngine harness on a live YouTube video (as decided for #112). The Kondor interactive steps are listed as "Not done" for the maintainer and do not block the merge. |
