# Dark Mode extension (#109)

> **Issue:** [#109](https://github.com/lukasborges/kondor/issues/109) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the first catalog extension, **Dark Mode**, in `extensions/dark-mode/`. It shows every
site with dark colors:
- the colors come from the page's own colors, not a plain invert;
- images and videos keep their colors;
- there is no white flash while the page loads.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md), items 1, 3 and 4, and
  [`docs/extensions/api.md`](../extensions/api.md)). This issue uses them as they are. If it
  needs a change, ask a question.
- **Injection details that matter here (#107 item 3):**
  - all `js` files of a content script are concatenated into **one closure**, so they share
    top-level functions and variables without leaking globals;
  - the platform already skips sites the user turned off with "Run on <site>";
  - it skips private windows unless the user allowed them.
- **Repository rules:** `lukasborges/kondor-extensions` (#108).
  - `tools/validate.py` must pass. That covers the README sections, no forbidden or minified
    code, every file referenced, the license and the icon.
  - `CONTRIBUTING.md` applies, so the extension has **no network access** and no remote code.
- **Code quality:** AGENTS.md → "Code quality" applies to the extension's JavaScript, as it did to
  the #108 tools:
  - functions of at most 10 lines;
  - at most 3 parameters;
  - nesting depth at most 2;
  - files of at most 200 lines;
  - no comments.

## Design / behavior

1. **Files** in `extensions/dark-mode/`:
   ```
   manifest.json
   color.js          color parsing, the three color roles, brightness/contrast/sepia
   stylesheets.js    layer A: override sheet generated from the page's readable style sheets
   elements.js       layer B: computed-style fallback for what layer A cannot see
   theme.js          base style, already-dark detection, start/stop of the theme
   content.js        wiring: settings, system color scheme, toolbar action, Dim Images
   icon.svg          original artwork (a crescent moon); not copied from another project
   README.md         "What it does", "Permissions", "Network"
   ```
   The `js` order in the manifest is the order above. `content.js` is last and the only file
   that runs code at the top level. The other files only declare functions and constants.
2. **Manifest** (`kondor: 1`):
   - `id` `dark-mode` and `version` `1.0.0`;
   - `name` "Dark Mode" and `name[pt_BR]` "Modo Escuro";
   - `description` "Shows every site with dark colors." and `description[pt_BR]` "Mostra todos
     os sites com cores escuras.";
   - `author` "Kondor contributors" and `license` `GPL-3.0-or-later`;
   - `homepage` `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/dark-mode`;
   - `icon` `icon.svg`;
   - **no `permissions`**, since settings and storage need none;
   - one content script with:
     - `matches` `["https://*/*", "http://*/*"]`;
     - the five `js` files, and no `css`;
     - `runAt` `document-start` and `allFrames` `true`;
   - **`settings`** (every `label` also has `label[pt_BR]`):

     | key | type | label / pt_BR | default | range |
     | --- | --- | --- | --- | --- |
     | `brightness` | number | Brightness / Brilho | 100 | 50–150, step 5, suffix `%` |
     | `contrast` | number | Contrast / Contraste | 100 | 50–150, step 5, suffix `%` |
     | `sepia` | number | Sepia / Sépia | 0 | 0–100, step 5, suffix `%` |
     | `onlyWhenSystemDark` | bool | Only when the system uses a dark color scheme / Somente quando o sistema usa um esquema de cores escuro | false | |

   - **`action`:**
     - `items`: `{ "id": "dim-images", "title": "Dim Images", "title[pt_BR]": "Escurecer
       Imagens", "checkable": true }`;
     - `siteToggle` `true`, which adds the platform's "Run on <site>".
3. **Color roles (`color.js`).** Parse every color with a 2D canvas context: set `fillStyle` to
   the value and read it back as `#rrggbb` or `rgba(…)`. That covers hex, `rgb()`, `hsl()` and
   named colors.
   - `transparent`, `currentcolor`, `inherit`, `initial`, `unset` and anything that does not
     parse are left unchanged.
   - Convert the color to HSL, keeping hue, saturation and alpha, and change only the
     lightness `L` (0–1) by role:
     - **background**: `L ≤ 0.3` unchanged; otherwise `L' = 0.1 + 0.2 × (1 − L) / 0.7`
       (white → 0.10).
     - **text**: `L ≥ 0.6` unchanged; otherwise `L' = 0.6 + 0.3 × (0.6 − L) / 0.6`
       (black → 0.90).
     - **border**: `L' = 0.2 + 0.3 × (1 − L)` (white → 0.20, black → 0.50).
   - Then apply the settings to each RGB channel `x` (0–1), in this order, and clamp to 0–1:
     1. **brightness** `x × b/100`;
     2. **contrast** `(x − 0.5) × c/100 + 0.5`;
     3. **sepia** `s/100`: mix the color with the standard sepia matrix
        `[[.393,.769,.189],[.349,.686,.168],[.272,.534,.131]]`.
   - Output `rgb()` or `rgba()`.
   - **Which properties take which role:**
     - background: `background-color`, and every color inside the
       `linear-`/`radial-`/`conic-gradient(…)` of `background-image`;
     - text: `color`, `text-decoration-color`, `caret-color`, `fill`, `stroke`;
     - border: `border-{top,right,bottom,left}-color`, `outline-color`, `column-rule-color`.
4. **Base style (`theme.js`).** At `document-start`, as soon as `document.documentElement`
   exists, add `<style id="kondor-dark-mode-base">` with:
   - `html, body`: the transformed white as `background-color` and the transformed black as
     `color`, both `!important`;
   - `html { color-scheme: dark; }`, so form controls and scrollbars are dark.

   This is what prevents the white flash.
5. **Already-dark pages.** At `DOMContentLoaded`, disable the base style for one read:
   - the page is **already dark** when the computed background of `body` (or of `html`, if
     `body`'s is transparent) has alpha > 0 and `L < 0.3`, or when
     `<meta name="color-scheme">` is exactly `dark`;
   - an already-dark page gets nothing: remove the base style and do not start layers A and B;
   - otherwise re-enable the base style and start both layers.
6. **Layer A: style sheets (`stylesheets.js`).**
   - **Source rules:** for every `document.styleSheets` entry whose `cssRules` can be read
     (same-origin or CORS-enabled; reading a cross-origin sheet throws, so skip it), walk the
     rules. Recurse into `@media` and `@supports` and keep their condition. For each style rule
     that sets a property of item 3, emit the same selector with the transformed values, each
     `!important`.
   - **Custom properties:** a `--name` declaration whose value parses as a color gets the role of
     the first property seen using `var(--name)` in any readable rule. When no use is seen, it
     gets the background role. The custom property is emitted transformed with its own selector.
   - **Output:** everything goes into one `<style id="kondor-dark-mode-rules">`, appended after
     the base style.
   - **Rebuild:** the sheet is rebuilt, at most once per animation frame, at `DOMContentLoaded`,
     on every `load` of a `<link rel="stylesheet">`, and when a `<style>` or `<link>` is added or
     removed (`MutationObserver`).
   - **Never fetch:** sheets are never fetched; the extension has no network access. Layer B
     covers what cannot be read.
7. **Layer B: elements (`elements.js`).** It covers inline styles, cross-origin sheets and rules
   added with `insertRule`.
   - **When:** after layer A, walk all elements in chunks of 500 per animation frame. Then a
     `MutationObserver` re-checks added elements and `style`/`class` attribute changes, batched
     per animation frame.
   - **Background:** when its computed `background-color` has alpha > 0 and `L > 0.6`, set the
     transformed value inline with `style.setProperty(…, "important")`.
   - **Text:** when its computed `color` has `L < 0.25`, do the same.

     These thresholds keep layer B off the colors that layer A already produced, at any setting.
   - **Saving the page's values:** before the first change, save the element's original inline
     value and priority in a `WeakMap`, and mark the element with `data-kondor-dark-mode`.
8. **Start and stop.** The theme is **active** when the setting `onlyWhenSystemDark` is off, or
   `matchMedia("(prefers-color-scheme: dark)")` matches.
   - `stop()` removes both style elements and disconnects the observers. It also restores every
     marked element from the `WeakMap` and removes the marker. The page then looks exactly as
     it would without the extension.
   - `start()` runs items 4–7.
   - These events call `stop()` and then `start()` when active:
     - `kondor.settings.onChanged`, with the new values;
     - a `change` of that media query.
9. **Dim Images (`content.js`).**
   - **Checked:** add `<style id="kondor-dark-mode-images">` with
     `img, video, canvas, svg image { filter: brightness(80%) !important; }`. It works only
     while the theme is active.
   - **Saved state:** it is remembered with `kondor.storage.set("dimImages", checked)`.
     - Read it at start and call `kondor.action.setChecked("dim-images", value)`.
     - The default is unchecked.
   - **Toggling:** `kondor.onAction` toggles it in the current tab and saves it.
   - **Private tabs:** `set` rejects there. Catch the rejection, so the change applies to that
     tab only and nothing is written.
10. **Frames:** with `allFrames`, each frame runs its own copy of the extension, with the same
    rules.
11. **README.md** of the extension:
    - **What it does:** the dark theme, the settings, Dim Images and "Run on <site>".
    - **Permissions:** one line for each match pattern, saying it is needed to darken every
      site, and a line saying it asks for no API permission.
    - **Network:** "None".

## Acceptance criteria

- [ ] `extensions/dark-mode/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists Dark Mode.
- [ ] Installed in Kondor (from `main`) with "Install from File…":
  - light pages turn dark with readable text;
  - images and videos keep their colors;
  - there is no white flash on load;
  - hover colors defined in readable style sheets are dark too.
- [ ] Inline-styled elements and elements styled by a cross-origin sheet are darkened by layer B.
- [ ] Already-dark pages are left unchanged.
- [ ] Brightness, contrast and sepia change the colors of open tabs without a reload.
  - "Only when the system uses a dark color scheme" follows the system scheme live.
- [ ] "Dim Images" dims images and videos, keeps its checked state across tabs and restarts, and
  writes nothing in private tabs.
- [ ] Turning the theme off (setting, system scheme) restores the page exactly. Unchecking
  "Run on <site>" leaves the page unchanged after the reload.
- [ ] No page errors in the console from the extension. No network requests from the extension.
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, no comments.

## Manual test

Use a Kondor build from `main` with isolated `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
`XDG_CACHE_HOME` (AGENTS.md).

1. **Install.** Run `python3 tools/pack.py extensions/dark-mode`, then Settings → Extensions →
   Install from File….
2. **Test site.** In a temporary directory, create:
   - `index.html` with:
     - a white body with dark text;
     - a link with a `:hover` color;
     - an element with an inline `style="background:#fff;color:#000"`;
     - a CSS variable `--card: #f5f5f5` used as `background`;
     - an `<img>` and a `<video>` (any local files);
     - a `<link>` to `http://127.0.0.1:8001/other.css`, which styles one `.remote` box white;
   - `other.css`;
   - `dark.html`, whose body background is `#111`.

   Serve the directory twice, with `python3 -m http.server 8000` and `python3 -m http.server
   8001`, and open `http://localhost:8000/`. Port 8001 is cross-origin to it.
3. **Check the page:**
   - the page, the inline element, the variable card and the `.remote` box are dark;
   - the hover color is light on dark;
   - the image keeps its colors;
   - reloading shows no white flash;
   - `dark.html` is unchanged.
4. **Settings and Dim Images:**
   - Extensions → Dark Mode → Configure: set brightness to 70 % and sepia to 50 %. The open tab
     changes without a reload.
   - Check "Dim Images": the image is dimmed. Open a new tab on the same page: it is still
     checked.
5. **System scheme.** Turn on "Only when the system uses a dark color scheme". Switch the Plasma
   color scheme between Breeze and Breeze Dark: the page follows.
6. **Site toggle.** Uncheck "Run on localhost": after the reload the page is the original light
   page.
7. **Private window.**
   - Allow the extension in private windows and open the page in a private window. Check
     "Dim Images": no error, and it is not remembered in the normal window.
   - Run `sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from extension_storage"`: no row
     was written from the private tab.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
- Fetching cross-origin style sheets, shadow DOM, `adoptedStyleSheets` and `@layer` ordering.
- `box-shadow` and `text-shadow` colors, inverting images, and per-site settings other than "Run
  on <site>".
- Translations other than pt_BR, and JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged) and #108 (the extensions repository and its tools, merged).

## Prototype

No prototype. The extension's UI is generated by Kondor from the manifest:
- the Configure dialog and the toolbar Extensions menu, as in the #107 prototypes
  `prototypes/107f-extensions-menu.qml` and `prototypes/107e-extensions-install-file.qml`;
- the labels and titles of item 2.

## Decisions

| Question | Decision |
| --- | --- |
| How is the dark theme computed? | By lightness remapping per color role (background, text, border), keeping hue, saturation and alpha. Brightness, contrast and sepia are applied in the same color math, never as a page `filter`, so images keep their colors. |
| How are colors found? | Layer A rewrites readable style sheets, so `:hover` and media queries keep working. Layer B fixes computed colors on elements for what layer A cannot read. Cross-origin sheets are not fetched: "Network: None". |
| Where is "Dim Images" remembered? | In `kondor.storage` (`dimImages`). An extension cannot write its own settings, and the toolbar item is per tab. In private tabs it applies to the tab only. |
| Which API permissions? | None. Storage and settings need none, and the site patterns are the only access the extension asks for. |
