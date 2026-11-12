# Video Speed Controller extension (#110)

> **Issue:** [#110](https://github.com/lukasborges/kondor/issues/110) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the catalog extension **Video Speed Controller** in `extensions/video-speed/`. It lets
the user control the playback speed of any HTML5 video:
- a small speed overlay on each video;
- configurable keys for slower, faster, reset, rewind, advance and show/hide the overlay;
- the same commands in the toolbar Extensions menu;
- optionally, the speed remembered per site.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md) and
  [`docs/extensions/api.md`](../extensions/api.md)). This issue uses them as they are. If it
  needs a change, ask a question.
- **Injection details that matter here (#107 item 3):**
  - all `js` files of a content script are concatenated into **one closure**, so they share
    top-level functions and variables without leaking globals;
  - the platform already skips sites the user turned off with "Run on <site>";
  - it skips private windows unless the user allowed them.
- **Frames.** With `allFrames`, each frame runs its own copy of the extension. Kondor delivers
  `kondor.settings.onChanged` and `kondor.onAction` **to the main frame only**
  (`qml/browser/PageScriptBridges.qml` calls `runJavaScript` on the view). So:
  - toolbar commands act on the videos of the top page;
  - a video inside an `<iframe>` is controlled with the keys, after the user clicks into the
    frame;
  - an `<iframe>` picks up changed settings at its next load.
- **`keys` settings:** the Configure dialog edits them as a text field (#107 falls back to a
  `TextField`). The value is a string such as `S`, `Shift+S` or `Ctrl+Alt+Right`.
- **Repository rules:** `lukasborges/kondor-extensions` (#108).
  - `tools/validate.py` must pass. That covers the README sections, no forbidden or minified
    code, every file referenced, the license and the icon.
  - `CONTRIBUTING.md` applies, so the extension has **no network access** and no remote code.
- **Code quality:** AGENTS.md → "Code quality" applies to the extension's JavaScript, as it did
  for #109:
  - functions of at most 10 lines;
  - at most 3 parameters;
  - nesting depth at most 2;
  - files of at most 200 lines;
  - no comments.

  Kondor's `scripts/check-code-quality.py` can check the files (copy them under a `src/` folder
  of a temporary root and pass `--root`).

## Design / behavior

1. **Files** in `extensions/video-speed/`:
   ```
   manifest.json
   keys.js       parsing of `keys` settings and matching of keyboard events
   speed.js      the current speed, its bounds, applying it to videos, remembering it per site
   overlay.js    the speed overlay of one video
   videos.js     finding videos, their events, the active video, rewind and advance
   content.js    wiring: settings, keyboard, toolbar actions, overlay visibility
   icon.svg      original artwork (a play triangle with speed lines); not copied from another project
   README.md     "What it does", "Permissions", "Network"
   ```
   The `js` order in the manifest is the order above. `content.js` is last and the only file
   that runs code at the top level. The other files only declare functions and constants.
2. **Manifest** (`kondor: 1`):
   - `id` `video-speed` and `version` `1.0.0`;
   - `name` "Video Speed Controller" and `name[pt_BR]` "Controle de Velocidade de Vídeo";
   - `description` "Changes the playback speed of any video." and `description[pt_BR]` "Muda a
     velocidade de reprodução de qualquer vídeo.";
   - `author` "Kondor contributors" and `license` `GPL-3.0-or-later`;
   - `homepage` `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/video-speed`;
   - `icon` `icon.svg`;
   - **no `permissions`**, since settings and storage need none;
   - one content script with:
     - `matches` `["https://*/*", "http://*/*"]`;
     - the five `js` files, and no `css`;
     - `runAt` `document-start` and `allFrames` `true`;
   - **`settings`** (every `label` also has `label[pt_BR]`):

     | key | type | label / pt_BR | default | range |
     | --- | --- | --- | --- | --- |
     | `speedStep` | number | Speed step / Passo da velocidade | 10 | 5–50, step 5, suffix `%` |
     | `skipSeconds` | number | Rewind and advance by / Voltar e avançar | 10 | 1–60, step 1, suffix ` s` |
     | `rememberSpeed` | bool | Remember the speed for each site / Lembrar a velocidade de cada site | false | |
     | `keySlower` | keys | Slower / Mais lento | `S` | |
     | `keyFaster` | keys | Faster / Mais rápido | `D` | |
     | `keyReset` | keys | Reset speed / Velocidade normal | `R` | |
     | `keyRewind` | keys | Rewind / Voltar | `Z` | |
     | `keyAdvance` | keys | Advance / Avançar | `X` | |
     | `keyOverlay` | keys | Show or hide the overlay / Mostrar ou ocultar o indicador | `V` | |

   - **`action`:**
     - `items`, in this order:
       - `{ "id": "slower", "title": "Slower", "title[pt_BR]": "Mais Lento" }`;
       - `{ "id": "faster", "title": "Faster", "title[pt_BR]": "Mais Rápido" }`;
       - `{ "id": "reset", "title": "Reset Speed", "title[pt_BR]": "Velocidade Normal" }`;
       - `{ "id": "show-overlay", "title": "Show Speed Overlay", "title[pt_BR]": "Mostrar
         Indicador de Velocidade", "checkable": true }`;
     - `siteToggle` `true`, which adds the platform's "Run on <site>".
3. **Speed (`speed.js`).**
   - The extension keeps **one current speed per document**, shared by all its videos. It
     starts at `1`, or at the remembered speed of the site (item 7).
   - **Slower / faster:** subtract / add `speedStep / 100`. Clamp the result to **0.1–16** and
     round it to 2 decimals.
   - **Reset:** set the speed to `1`.
   - **Applying:** after every change, set `playbackRate` of every video of the document to the
     current speed. A video is also set to the current speed on its `loadedmetadata` and `play`
     events, so a site that resets the rate (for example when the next video starts) is
     corrected at the next play.
   - A rate the page sets itself is shown by the overlay (item 5) but does not change the
     current speed.
4. **Videos (`videos.js`).**
   - **Finding:** at start, every `video` element of the document. Then a `MutationObserver`
     on `document` (`childList`, `subtree`) finds added videos, batched per animation frame.
     Observing `document` works at `document-start`, before `document.documentElement` exists.
   - Each video is set up once: listeners for `loadedmetadata`, `play` and `ratechange`, and its
     overlay. A `WeakSet` remembers set-up videos.
   - **Removed videos:** when a video leaves the document, its overlay is removed too.
   - **Active video:** the video that fired `play` last. While none has, it is the first video
     of the document.
   - **Rewind / advance:** move the active video's `currentTime` by `−skipSeconds` /
     `+skipSeconds`, clamped to `0` and to its `duration` (when the duration is finite).
5. **Overlay (`overlay.js`).**
   - **Element:** one host `<div>` per video, inserted just before the video in the same parent,
     with a **shadow root** (`mode: "closed"`), so page CSS cannot change it and its CSS cannot
     leak.
   - **Content:** the video's `playbackRate` with 2 decimals followed by `×`, for example
     `1.50×`. It is updated on `ratechange`.
   - **Look:**
     - a small rounded box with white text on `rgba(0, 0, 0, 0.6)`;
     - 13 px system sans-serif font and padding 2 px 6 px;
     - `pointer-events: none`, so it never blocks clicks on the video;
     - `z-index: 2147483647`.

     These literal colors are allowed here, since a web page has no Kirigami theme.
   - **Position:**
     - `position: absolute`, at `video.offsetTop + 8` px and `video.offsetLeft + 8` px;
     - recomputed on the video's `loadedmetadata`, by a `ResizeObserver` on the video, and on the
       window's `resize`.
   - **Hidden** when the overlay is turned off (item 6), and for videos narrower than 120 px or
     not rendered (`offsetParent === null`).
6. **Overlay visibility.**
   - **Saved state:** it is remembered with `kondor.storage.set("showOverlay", value)`.
     - Read it at start and call `kondor.action.setChecked("show-overlay", value)`.
     - The default is shown (`true`).
   - **Toggling:** the `keyOverlay` key and the "Show Speed Overlay" item toggle it and save it.
   - **Private tabs:** `set` rejects there. Catch the rejection, so the change applies to that
     frame only and nothing is written.
7. **Remembering the speed (`rememberSpeed`).**
   - **Storage key:** `speed:` followed by the document's `location.hostname`. Only when the
     setting is on:
     - read it at start; a number in 0.1–16 becomes the starting speed;
     - after every slower/faster command, write the new speed;
     - after reset, call `kondor.storage.remove` on the key.
   - **Private tabs:** `set` and `remove` reject. Catch the rejection, so nothing is written.
   - **Setting off:** nothing is read or written. Stored speeds stay until the setting is on
     again.
8. **Keys (`keys.js`).**
   - **Parsing:** split the setting on `+`.
     - The last part is the key.
     - The other parts are modifiers: `Ctrl`, `Alt`, `Shift`, `Meta` (any case).
     - An empty value, an unknown modifier or an empty key **disables** that command.
   - **Matching a `keydown` event:**
     - the four modifier flags must equal the event's `ctrlKey`, `altKey`, `shiftKey` and
       `metaKey`;
     - a one-character key matches `event.key` without regard to case;
     - `Left`, `Right`, `Up`, `Down` match `ArrowLeft`, `ArrowRight`, `ArrowUp`, `ArrowDown`;
     - `Space` matches `" "`;
     - any other name matches `event.key` exactly (for example `F2`, `Enter`).
   - **Listener:** `keydown` on `window`, in the capture phase. It does nothing when:
     - the event is already `defaultPrevented`;
     - the target is editable (`input`, `textarea`, `select`, or `isContentEditable`);
     - the document has no video.
   - **Repeats:** a held key repeats its command (`event.repeat` is not filtered).
   - **Handling:** when a key matches a command, run it, then call `preventDefault()` and
     `stopPropagation()` so the page does not also act on it.
   - **Settings:** keys are parsed again whenever the settings change.
9. **Toolbar actions (`content.js`).** `kondor.onAction(itemId, checked)` runs:
   - "slower", "faster" and "reset": the matching speed command;
   - "show-overlay": sets the overlay visibility to `checked` and saves it.
10. **Settings changes.** `kondor.settings.onChanged(values)` stores the new values and parses
    the keys again. The current speed and the overlay are not reset.
11. **README.md** of the extension:
    - **What it does:** the overlay, the default keys and that they can be changed in Configure,
      the toolbar items, remembering the speed and "Run on <site>". Also say that a video inside
      an embedded frame is controlled with the keys after clicking into it.
    - **Permissions:** one line for each match pattern, saying it is needed to control videos on
      every site, and a line saying it asks for no API permission.
    - **Network:** "None".

## Acceptance criteria

- [ ] `extensions/video-speed/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists Video Speed Controller.
- [ ] Installed in Kondor (from `main`) with "Install from File…", on a page with videos:
  - each rendered video of at least 120 px shows the overlay with its speed;
  - the overlay never blocks clicks on the video.
- [ ] S, D and R change the speed of every video of the page in steps of 0.10, within
  0.1–16, and the overlay follows.
  - Z and X move the active video by 10 s.
  - V hides and shows the overlay.
  - The keys do nothing while typing in a text field.
- [ ] Changing a key or the step in Configure takes effect in the open tab without a reload.
  - An emptied key disables its command.
- [ ] The toolbar items Slower, Faster and Reset Speed act on the page's videos.
  - "Show Speed Overlay" follows the V key and keeps its state across tabs and restarts.
- [ ] With "Remember the speed for each site" on, a changed speed is restored after a reload on
  the same site and not on another site. Reset Speed forgets it.
- [ ] In a private tab nothing is written to `extension_storage`, and there is no error.
- [ ] Videos added after the page loaded get the overlay and the current speed.
  - A video in an `<iframe>` is controlled by the keys after clicking into it.
- [ ] Unchecking "Run on <site>" leaves the page without overlay and keys after the reload.
- [ ] No page errors in the console from the extension. No network requests from the extension.
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, no comments.

## Manual test

Use a Kondor build from `main` with isolated `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
`XDG_CACHE_HOME` (AGENTS.md).

1. **Install.** Run `python3 tools/pack.py extensions/video-speed`, then Settings → Extensions →
   Install from File….
2. **Test site.** In a temporary directory:
   - make a test video, for example with
     `ffmpeg -f lavfi -i testsrc=duration=120:size=640x360:rate=30 test.webm`;
   - create `index.html` with:
     - two `<video controls src="test.webm">` elements;
     - a `<input type="text">`;
     - a button that appends a third video with JavaScript;
     - an `<iframe src="http://127.0.0.1:8001/frame.html">`;
   - create `frame.html` with one video.

   Serve the directory twice, with `python3 -m http.server 8000` and `python3 -m http.server
   8001`, and open `http://localhost:8000/`.
3. **Keys:**
   - Play the first video. Press D three times: both overlays show `1.30×`.
   - Press S once (`1.20×`), then R (`1.00×`).
   - Press X and Z: the playing video moves 10 s forward and back.
   - Press V twice: the overlays hide and show again.
   - Type "sdr" in the text field: nothing changes.
   - Add the third video: it shows the overlay with the current speed.
   - Click into the iframe's video and press D: its overlay changes.
4. **Toolbar:** use Faster, Slower and Reset Speed from the Extensions menu. Uncheck "Show Speed
   Overlay", then open a new tab on the page: the overlay is hidden there and the item is
   unchecked.
5. **Configure:**
   - set the speed step to 25 % and the slower key to `Shift+S`. In the open tab, D now adds
     0.25, and S does nothing while Shift+S slows down;
   - empty the rewind key: Z does nothing.
6. **Remember:**
   - turn on "Remember the speed for each site";
   - set `1.50×` and reload: the videos play at `1.50×`;
   - open `http://127.0.0.1:8000/`: it starts at `1.00×`;
   - back on `localhost`, press R and reload: `1.00×`.
7. **Private window.**
   - Allow the extension in private windows, open the page in a private window, change the speed
     and toggle the overlay: no error.
   - Run `sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from extension_storage"`: no row
     was written from the private tab.
8. **Site toggle.** Uncheck "Run on localhost": after the reload there is no overlay, and D does
   nothing.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
  That includes delivering settings changes and toolbar actions to frames.
- `<audio>` elements, videos inside shadow DOM, and Media Source edge cases beyond setting
  `playbackRate` and `currentTime`.
- Buttons inside the overlay, dragging the overlay, and a per-site setting other than "Run on
  <site>" and the remembered speed.
- Forcing a speed against the page between plays (the page's own rate is shown until the next
  `play`).
- Translations other than pt_BR, and JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged) and #108 (the extensions repository and its tools,
merged).

## Prototype

No prototype. The extension's UI is generated by Kondor from the manifest:
- the Configure dialog and the toolbar Extensions menu, as in the #107 prototypes
  `prototypes/107f-extensions-menu.qml` and `prototypes/107e-extensions-install-file.qml`;
- the labels and titles of item 2.

The in-page overlay is fully described in item 5.

## Decisions

| Question | Decision |
| --- | --- |
| One speed per video or per page? | Per document, shared by all its videos. That is simpler to understand, and a page rarely plays two videos at once. Rewind and advance act on the active video (the one played last). |
| How is the step expressed? | As a percentage of normal speed (`speedStep` 10 % = 0.10), since the number setting has no decimal step in the #107 Configure dialog. |
| What does the speed do when the site resets it? | The page's rate is shown, and the current speed is applied again at the video's next `play` or `loadedmetadata`. No continuous forcing, so the site's own speed menu keeps working. |
| What about frames? | Every frame runs its own copy (`allFrames`), and its keys work after a click into it. The platform delivers settings changes and toolbar actions only to the main frame (#107), so those reach the top page only. Changing the platform is out of scope. |
| Where are the overlay state and the remembered speeds kept? | In `kondor.storage` (`showOverlay`, `speed:<host>`). An extension cannot write its own settings. In private tabs nothing is written. |
| Which API permissions? | None. Storage and settings need none, and the site patterns are the only access the extension asks for. |
