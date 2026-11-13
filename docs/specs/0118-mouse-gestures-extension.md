# Mouse Gestures extension (#118)

> **Issue:** [#118](https://github.com/lukasborges/kondor/issues/118) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the catalog extension **Mouse Gestures** in `extensions/mouse-gestures/`. The user holds
the right mouse button, draws a short stroke on the page and releases it. Kondor then runs the
action mapped to that stroke:
- **Default gestures:**
  - left: go back;
  - right: go forward;
  - up, then down: reload;
  - down, then right: close the tab;
  - down: duplicate the tab (see "Decisions");
  - up: scroll to the top.
- **Trail:** a line follows the pointer while the user draws.
- **Context menu:** it does not open after a gesture. A double right-click opens it (see
  item 6).
- **Settings:** the action of each gesture, the trail color and the minimum distance.

The extension sends nothing over the network and stores nothing.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md) and
  [`docs/extensions/api.md`](../extensions/api.md)). This issue uses them as they are. If it
  needs a change, ask a question.
- **Injection (#107 item 3):** all `js` files of a content script are concatenated into **one
  closure**, in manifest order, and run in the application world: they share the page's DOM, not
  its JavaScript objects. The platform already skips sites turned off with "Run on <site>", and
  private windows unless the user allowed the extension there.
- **Tab commands:** with the `tabs` permission, `kondor.tabs.back()`, `forward()`, `reload()`,
  `close()`, `next()`, `previous()` and `open(url, {background})` act on the tab the script runs
  in. `open` accepts **only `http:` and `https:` addresses** (`src/extensions/bridge/bridgecalls.cpp`,
  `openTab`). So an extension cannot open a blank tab or the New Tab page.
- **Context menu timing.** On Linux, Blink sends the `contextmenu` event on the right button's
  **press**, not on its release (`WebFrameWidgetImpl::HandleMouseDown`; only Windows shows the menu
  on release). When a page cancels that event, Qt WebEngine never emits `contextMenuRequested`, so
  Kondor shows no menu. An extension cannot open the native menu later from JavaScript. Linux
  gesture add-ons for other browsers have the same limit, and they also open the menu with a
  double right-click.
- **Settings form:** Kondor builds the Configure dialog from `settings`. The controls are:
  - a `choice` setting is a `ComboBox` with localized `choices[].label`;
  - a `color` setting is a color button whose value is a `"#rrggbb"` string;
  - a `number` setting is a `SpinBox` that shows `value + suffix`;
  - Kondor adds the `:` after every label (#209).

  `kondor.settings.onChanged` reaches the main frame only.
- **Repository rules (#108):** `tools/validate.py` must pass (README sections, listed files, no
  minified code, no `eval` and the other forbidden patterns). `CONTRIBUTING.md` applies:
  - no network access and no remote code;
  - a version for the new extension;
  - the **Icons** rules from #205 (no background, legible at 16 px, Breeze colors that read on
    light and dark).
- **Code quality:** AGENTS.md → "Code quality" applies to the JavaScript, as for #109–#117:
  - functions of at most 10 lines and 3 parameters;
  - nesting depth at most 2;
  - files of at most 200 lines;
  - no comments.

  `scripts/check-code-quality.py --root` from this repository can check the files when they are
  copied under a `src/` folder of a temporary root.

## Design / behavior

1. **Files** in `extensions/mouse-gestures/`:
   ```
   manifest.json
   directions.js   turning pointer movement into a direction sequence (item 4)
   actions.js      the action table: action value → function (item 5)
   trail.js        the trail overlay (item 7)
   tracking.js     the right-button state machine and the context menu rule (items 3 and 6)
   content.js      wiring: settings, event listeners (items 3 and 8)
   icon.svg        original artwork (a pointer with a curved stroke), CONTRIBUTING.md → Icons
   README.md       "What it does", "Permissions", "Network"
   ```
   The `js` order in the manifest is `directions.js`, `actions.js`, `trail.js`, `tracking.js`,
   `content.js`. Only `content.js` runs code at the top level; the other files declare constants
   and functions.
2. **Manifest** (`kondor: 1`):
   - `id` `mouse-gestures` and `version` `1.0.0`;
   - `name` "Mouse Gestures" and `name[pt_BR]` "Gestos do Mouse";
   - `description` "Navigates by drawing with the right mouse button held down." and
     `description[pt_BR]` "Navega desenhando com o botão direito do mouse pressionado.";
   - `author` "Kondor contributors", `license` `GPL-3.0-or-later`, `homepage`
     `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/mouse-gestures`,
     `icon` `icon.svg`;
   - `permissions` `["tabs"]`;
   - one content script: `matches` `["https://*/*", "http://*/*"]`, the `js` files of item 1, no
     `css`, `runAt` `document-start`, `allFrames` `false`;
   - **`settings`**, in this order:
     - eight `choice` settings, one per gesture, all with the **same `choices`** (the action list
       below):

       | key | label | label[pt_BR] | default |
       | --- | --- | --- | --- |
       | `left` | Drag left | Arrastar para a esquerda | `back` |
       | `right` | Drag right | Arrastar para a direita | `forward` |
       | `up` | Drag up | Arrastar para cima | `scrollTop` |
       | `down` | Drag down | Arrastar para baixo | `duplicateTab` |
       | `upDown` | Drag up, then down | Arrastar para cima e depois para baixo | `reload` |
       | `downUp` | Drag down, then up | Arrastar para baixo e depois para cima | `none` |
       | `downRight` | Drag down, then right | Arrastar para baixo e depois para a direita | `closeTab` |
       | `downLeft` | Drag down, then left | Arrastar para baixo e depois para a esquerda | `none` |

     - the action list (`choices`, in this order):

       | value | label | label[pt_BR] |
       | --- | --- | --- |
       | `none` | Do nothing | Não fazer nada |
       | `back` | Go back | Voltar |
       | `forward` | Go forward | Avançar |
       | `reload` | Reload | Recarregar |
       | `closeTab` | Close tab | Fechar aba |
       | `duplicateTab` | Duplicate tab | Duplicar aba |
       | `nextTab` | Next tab | Próxima aba |
       | `previousTab` | Previous tab | Aba anterior |
       | `scrollTop` | Scroll to top | Rolar até o topo |
       | `scrollBottom` | Scroll to bottom | Rolar até o final |

     - `{ "key": "trailColor", "type": "color", "label": "Trail color", "label[pt_BR]": "Cor do
       rastro", "default": "#3daee9" }`;
     - `{ "key": "minimumDistance", "type": "number", "label": "Minimum stroke length",
       "label[pt_BR]": "Comprimento mínimo do traço", "default": 20, "min": 5, "max": 100,
       "step": 5, "suffix": " px" }`.

     No label ends with `:` (Kondor adds it, #209).
   - **`action`**: `{ "siteToggle": true }` and no items.
3. **Tracking (`tracking.js`, wired in `content.js`).** Listeners go on `window`, in the
   **capture** phase.
   - **Start:** a `mousedown` with `button === 2` and no other button pressed
     (`event.buttons === 2`) starts tracking at `clientX`/`clientY`. Two cases start nothing:
     the double right-click of item 6, and a press while tracking is already on.
   - **Move:** a `mousemove` while tracking feeds the point to item 4.
     - If the right button is no longer pressed (`(event.buttons & 2) === 0`, a release that
       happened outside the window), tracking is **cancelled**.
     - Cancelling removes the trail and runs no action.
   - **End:** a `mouseup` with `button === 2` ends tracking.
     - If the direction sequence is not empty, it is a **gesture**: the action of item 5 runs and
       the trail is removed.
     - Otherwise it is a **plain right-click** (item 6).
   - **Cancel:** `keydown` Escape (also `preventDefault` there) and window `blur` cancel tracking.
   - **After a gesture:** the right button's `auxclick` that follows gets `preventDefault` and
     `stopPropagation`, so the page does not react to the release.
4. **Directions (`directions.js`).** The sequence is built the usual way:
   - **Anchor:** the start point is the first anchor.
   - **New direction:** when the pointer is at least `minimumDistance` CSS pixels from the anchor
     (Euclidean distance), the movement since the anchor is a direction: `L` or `R` when
     `|dx| > |dy|`, else `U` or `D` (screen coordinates: `y` grows downward). The current point
     becomes the new anchor.
   - **Repeats:** a direction equal to the last one in the sequence is not appended.
   - **Lookup:** the sequence maps to a setting key: `L` → `left`, `R` → `right`, `U` → `up`,
     `D` → `down`, `UD` → `upDown`, `DU` → `downUp`, `DR` → `downRight`, `DL` → `downLeft`.
     Any other sequence (`LR`, `RDL`, …) is an **unknown gesture**: no action, but it still
     counts as a gesture for item 6.
5. **Actions (`actions.js`).** A table from action value to a function:

   | Value | Action |
   | --- | --- |
   | `none` | nothing |
   | `back` / `forward` / `reload` | `kondor.tabs.back()` / `forward()` / `reload()` |
   | `closeTab` | `kondor.tabs.close()` |
   | `duplicateTab` | `kondor.tabs.open(location.href, { background: false })` |
   | `nextTab` / `previousTab` | `kondor.tabs.next()` / `previous()` |
   | `scrollTop` / `scrollBottom` | `window.scrollTo({ top: 0 })` / `window.scrollTo({ top: document.scrollingElement.scrollHeight })` |

   - **Unknown value** (a manifest from a later version): treated as `none`.
   - **Rejections:** a promise that rejects is caught and ignored; nothing is logged to the
     console.
6. **Context menu (`tracking.js`).** One `contextmenu` listener (window, capture) applies these
   rules in order:
   1. While the right button is held and tracking is on, the event is cancelled
      (`preventDefault`). This is the Linux case: the event comes on the press.
   2. Just after a gesture (the `contextmenu` arrives after the `mouseup` that ended it, as on
      platforms that open the menu on release), the event is cancelled.
   3. Otherwise the event passes untouched, and the page or Kondor shows its menu.

   **Double right-click:** after a plain right-click, a second right `mousedown` within **500 ms**
   and within `minimumDistance` of the first press does not start tracking. Its `contextmenu`
   passes, so Kondor's menu opens.

   On Linux, a single plain right-click opens no menu: the menu needs the double right-click.
   The README says so (item 9).
7. **Trail (`trail.js`).**
   - **When:** the overlay is created when the first direction is recognized, so a plain
     right-click never touches the DOM. It is removed on end and on cancel.
   - **Element:** one `<canvas>` appended to `document.documentElement`. Its inline styles are
     set with `style.setProperty(…, "important")`, so page CSS cannot move it:
     - `position: fixed`, `inset: 0`;
     - `width: 100vw`, `height: 100vh`;
     - `pointer-events: none`, `z-index: 2147483647`;
     - `margin: 0`, `border: 0`, `padding: 0`;
     - `background: transparent`.
   - **Drawing:** the bitmap is `innerWidth × devicePixelRatio` by
     `innerHeight × devicePixelRatio`. The line is the `trailColor` setting, 3 CSS px wide, with
     round caps and joins.
     - On creation, the line is drawn from the start point through every point received so far.
     - After that, each `mousemove` adds one segment.
   - **Limits:** the trail is not visible over a fullscreen element (the top layer is above any
     `z-index`). The gesture still works there.
8. **Settings changes:** read `kondor.settings.values` at start and replace them in
   `kondor.settings.onChanged`. A gesture in progress keeps the values it started with.
9. **README.md** of the extension:
   - **What it does:**
     - the default gestures as a table;
     - the action list;
     - the trail;
     - the double right-click that opens the context menu (with why: on Linux the menu opens on
       the press);
     - "Run on <site>" for sites with their own right-button drag (maps, drawing tools, games);
     - that gestures over embedded frames (`<iframe>`, such as embedded videos) are not
       recognized.
   - **Permissions:**
     - one line for each match pattern (gestures work on every site);
     - one line for `tabs` (back, forward, reload, close, duplicate and switch tabs).
   - **Network:** "None".
10. **No storage and no network.** The extension does not use `kondor.storage`, `kondor.notify`
    or any network API. Private tabs behave the same and write nothing. In a private window,
    "Duplicate tab" opens the copy in the same private window (platform behavior of
    `tabs.open`).

## Acceptance criteria

- [ ] `extensions/mouse-gestures/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists Mouse Gestures.
  - `icon.svg` follows CONTRIBUTING.md → Icons; the PR shows it at 16 and 64 px on `#eff0f1` and
    `#232629`.
- [ ] The Configure dialog shows the eight gesture rows, then "Trail color:" and "Minimum stroke
  length:", each label with exactly one colon. In pt_BR the labels and choices are those of
  item 2.
- [ ] Each default gesture runs its action: left goes back, right goes forward, up then down
  reloads, down then right closes the tab, down duplicates the tab, up scrolls to the top.
- [ ] Changing a gesture's action in Configure applies to an open page without a reload. `none`
  makes the gesture do nothing.
- [ ] A red trail (with `trailColor` set to red) follows the pointer while drawing. It is gone
  after the release, after Escape and after the window loses focus. A plain right-click adds no
  element to the page.
- [ ] No context menu appears after a gesture, known or unknown. A double right-click opens
  Kondor's page context menu.
- [ ] A movement shorter than `minimumDistance` is not a gesture. Raising the setting to 100 px
  makes a 60 px stroke do nothing.
- [ ] Unchecking "Run on <site>" turns gestures off on that site after a reload: a single
  right-click opens the menu again.
- [ ] In a private window, with the extension allowed there, gestures work and nothing is written
  to `extension_storage`.
- [ ] No page errors in the console from the extension, and no network requests from it.
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, no comments.

## Manual test

Use a Kondor build from `main` with isolated `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
`XDG_CACHE_HOME` (AGENTS.md). Run it in a real Plasma session: offscreen has no pointer.

1. **Install.** `python3 tools/pack.py extensions/mouse-gestures`, then Settings → Extensions →
   Install from File….
2. **Pages.** In a temporary directory (not in the repository):
   - write `a.html`, `b.html` and `long.html` (a page taller than three screens) that link to
     each other;
   - add a script to `long.html` that appends each `contextmenu` and `auxclick` event to a list on
     the page;
   - serve them with `python3 -m http.server 8000`.

   Open `a.html`, follow the link to `b.html`, then to `long.html`.
3. **Navigation.** On `long.html`:
   - drag left: `b.html` is shown;
   - drag right: `long.html` again;
   - drag up then down: the page reloads.
4. **Scroll.** Scroll to the middle and drag up: the page is at the top. Map `downUp` to "Scroll
   to bottom", then drag down then up: the page is at the bottom.
5. **Tabs.**
   - Drag down: a new tab with `long.html` opens in the foreground.
   - Map `downLeft` to "Previous tab" and drag down then left: the first tab is selected.
   - Drag down then right in the copy: it closes.
6. **Context menu.**
   - A single right-click opens no menu.
   - A double right-click opens Kondor's page menu.
   - After each gesture above, no menu opened.
   - The page's list shows no `auxclick` from a gesture.
7. **Trail.** Set the trail color to red and draw a slow circle: a red line follows the pointer
   and disappears on release. Press Escape mid-gesture: the line goes and no action runs.
8. **Distance.** Set the minimum stroke length to 100 px and drag 60 px left: nothing happens.
9. **Site toggle.** Uncheck "Run on localhost" and reload: a single right-click opens the menu
   and drags do nothing.
10. **Private window.** Allow the extension in private windows and repeat step 3 there. Run
    `sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from extension_storage"`: no row.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
  This includes a blank "New Tab" action and showing the context menu on the release of a plain
  right-click (see "Decisions").
- Gestures in `<iframe>`s (`allFrames` is false), and the trail over fullscreen elements.
- Rocker gestures (left + right button), wheel gestures, gestures with other buttons or with
  modifier keys, and gestures of more than two directions.
- Drawing new gestures freely (a recorder) and a custom gesture list beyond the eight of item 2.
- A label showing the recognized action while drawing, and sounds or notifications.
- Actions on the link under the pointer (open it in a new tab, …).
- Translations other than pt_BR, and JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged), #108 (the extensions repository and its tools, merged),
#205 (icon rules, merged) and #209 (the dialog adds the label colon, merged).

## Prototype

No prototype. The extension's only UI is:
- the trail, a plain line over the page (item 7);
- the Configure dialog, generated by Kondor from the manifest with combo boxes, a color button
  and a spin box, as in `prototypes/107e-extensions-install-file.qml`;
- the platform's "Run on <site>" item in the toolbar Extensions menu, as in
  `prototypes/107f-extensions-menu.qml`.

## Decisions

| Question | Decision |
| --- | --- |
| "Down = new tab": the issue's default. | Down **duplicates the tab** (`tabs.open(location.href)`). `kondor.tabs.open` accepts only `http(s)` addresses, so an extension cannot open a blank tab or the New Tab page, and this issue does not change the platform. Rejected: a "New tab address" setting (a home page in disguise, with a made-up default), and leaving Down unmapped. |
| The context menu on a plain right-click. | On Linux, Blink sends `contextmenu` on the press, before anyone knows whether a gesture follows. A cancelled event cannot be replayed. So a single right-click shows no menu, and a **double right-click** (within 500 ms) opens it, as other Linux gesture add-ons do. On a platform that sends the event on release, the single right-click keeps its menu, because rule 3 of item 6 lets it pass. Rejected: never cancelling the press event (the menu would open and grab the pointer, so no gesture could be drawn), and a platform change (out of scope). |
| How is the gesture → action map edited? | One `choice` setting per gesture, all with the same action list. It uses the existing Configure controls, with no text syntax to learn. Rejected: one `text` setting with lines such as `DR=closeTab` (error-prone, untranslatable action names). |
| Which gestures? | The six of the issue plus `downUp` and `downLeft`, unmapped by default, so the extra actions (next and previous tab, scroll to bottom) have a home. Longer sequences are out of scope. |
| Trail element. | A `<canvas>` created on the first recognized direction and removed at the end, with `!important` inline styles. A plain right-click leaves the DOM untouched. Rejected: an always-present overlay (it would sit in every page's DOM for nothing). |
| Labels and choices. | Sentence case: they are labels before controls and combo box items (KDE HIG), as in Skip Sponsors (#113). No trailing colon (#209). pt_BR reuses Kondor's terms ("aba", "Voltar", "Avançar", "Recarregar", "Duplicar aba"). |
