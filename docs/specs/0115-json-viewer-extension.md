# JSON Viewer extension (#115)

> **Issue:** [#115](https://github.com/lukasborges/kondor/issues/115) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the catalog extension **JSON Viewer** in `extensions/json-viewer/`. When a tab shows a
JSON document, the extension shows it as a readable, collapsible tree:
- syntax colors that follow the light or dark color scheme;
- "Pretty" / "Raw" views, and "Collapse All" / "Expand All";
- copying the value or the path (`a.b[2].c`) of a row;
- clickable `http(s)` links;
- documents above a size limit start raw, with a notice and a way to format them anyway.

The extension does nothing on other pages, and uses no network.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md) and
  [`docs/extensions/api.md`](../extensions/api.md)). This issue uses them as they are. If it
  needs a change, ask a question.
- **Injection (#107 item 3):**
  - all `js` files of a content script are concatenated into **one closure**, in manifest order;
  - scripts run in Qt WebEngine's **application world**: they share the page's DOM, not its
    JavaScript objects;
  - `<all_urls>` becomes the glob `*`, so the script also runs on `file://` pages;
  - the platform already skips sites turned off with "Run on <site>", and private windows unless
    the user allowed the extension there.
- **What a JSON document looks like in Qt WebEngine** (Qt 6.11, Chromium 140, checked on
  2026-11-13 in a headless view):
  - `document.contentType` is `application/json`;
  - `<head>` holds `<meta name="color-scheme" content="light dark">`, so the page already
    follows the light or dark scheme;
  - `<body>` holds one `<pre>` with the document's text and, after it, Chromium's own
    `<div class="json-formatter-container">` (20 px high, a "pretty-print" checkbox in a closed
    shadow root). On some pages only the `<pre>` is there.
- **Content Security Policy:** JSON APIs often send a strict policy. `api.github.com` sends
  `Content-Security-Policy: default-src 'none'`. Measured on that page, from the application
  world:
  - a `<style>` element and a `style` attribute set with `setAttribute` are **blocked**, with a
    console error;
  - a **constructable style sheet** (`new CSSStyleSheet()` + `replaceSync`, added to
    `document.adoptedStyleSheets`) and **CSSOM** (`element.style.setProperty`) **work**.

  So the manifest has **no `css` file** (the platform adds CSS as a `<style>` element), and all
  styling goes through one constructable style sheet (item 4).
- **Clipboard** (measured on 2026-11-13 with a real click in a headless KWin session):
  - `navigator.clipboard.writeText` makes Qt WebEngine ask for the `ClipboardReadWrite`
    permission, and the Promise never settles. In Kondor that would show a permission prompt;
  - `document.execCommand("copy")` inside the click handler, with a one-time `copy` event
    listener that calls `event.clipboardData.setData("text/plain", text)` and
    `event.preventDefault()`, returns `true`, copies the text and asks for nothing.
- **Exact numbers:** `JSON.parse(text, reviver)` gives the reviver a third argument with the
  number's `source` text, and `JSON.rawJSON(source)` keeps it exact through `JSON.stringify`
  (checked: `12345678901234567890` and `1.50` round-trip unchanged).
- **Speed:** building a naive DOM tree for a 672 KB document (100 GitHub issues, 42,600 nodes)
  took about 0.55 s. Hence the 1,000,000-character limit of item 3.
- **Repository rules (#108):** `tools/validate.py` must pass (README sections, every file
  referenced, no minified code, no `eval` and the other forbidden patterns), and
  `CONTRIBUTING.md` applies: the extension has **no network access** and no remote code.
- **Code quality:** AGENTS.md → "Code quality" applies to the JavaScript, as for #109–#114:
  functions of at most 10 lines and 3 parameters, nesting depth at most 2, files of at most 200
  lines, no comments. `scripts/check-code-quality.py --root` from this repository checks the
  files when they are copied, in their folder layout, under a `src/` folder of a temporary root
  that also holds an empty `scripts/code-quality-baseline.json` (`{}`).

## Design / behavior

1. **Files** in `extensions/json-viewer/`:
   ```
   manifest.json
   texts.js      the in-page texts, plural counts and the size in the notice
   detect.js     whether the page is a JSON document, its <pre> and text
   parse.js      parsing with exact numbers, the path and the copied value of a row
   styles.js     the constructable style sheet
   tree.js       building the tree, collapsing and expanding
   keyboard.js   selection and keyboard navigation in the tree
   clipboard.js  copying text with the copy event
   toolbar.js    the toolbar, the views and the size notice
   content.js    wiring
   icon.svg      original artwork: braces around a small tree; not copied from another project
   README.md     "What it does", "Permissions", "Network"
   ```
   The `js` order in the manifest is the order above. `content.js` is last and the only file
   that runs code at the top level. The other files only declare functions and constants.
2. **Manifest** (`kondor: 1`):
   - `id` `json-viewer` and `version` `1.0.0`;
   - `name` "JSON Viewer" and `name[pt_BR]` "Visualizador de JSON";
   - `description` "Shows JSON documents as a readable, collapsible tree." and
     `description[pt_BR]` "Mostra documentos JSON como uma árvore legível e recolhível.";
   - `author` "Kondor contributors" and `license` `GPL-3.0-or-later`;
   - `homepage` `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/json-viewer`;
   - `icon` `icon.svg`;
   - **no `permissions`** and **no `settings`**;
   - one content script with `matches` `["<all_urls>"]`, the nine `js` files of item 1, **no
     `css`**, `runAt` `document-end` and `allFrames` `false`;
   - **`action`**: `{ "siteToggle": true }` and no items.
3. **When it runs (`detect.js`).** The page is a JSON document when all of these hold:
   - `document.contentType` is `application/json` or `text/json`, or matches
     `^application/[A-Za-z0-9.-]+\+json$`;
   - the `<body>`'s element children are one `<pre>`, optionally followed by
     `div.json-formatter-container`.

   Otherwise the extension does nothing: no element, no style sheet, no listener.
   - **Size limit:** when the `<pre>`'s text is longer than **1,000,000 characters**, the page
     starts in the "too large" state (item 8) without parsing.
   - **Invalid JSON:** when parsing throws, the extension removes nothing and adds nothing, and
     logs nothing. Chromium's page stays as it was.
4. **Styles (`styles.js`).**
   - **One sheet:** one `CSSStyleSheet` built with `replaceSync`, appended to
     `document.adoptedStyleSheets` (keeping any sheets already there). No `<style>` element and
     no `setAttribute("style", …)`. Every class the extension uses starts with `kondor-json-`.
   - **Hiding the page's own view:** while the viewer is active, the `<pre>` (in Pretty view) and
     `div.json-formatter-container` (always) get `display: none` through CSSOM
     (`style.setProperty`). The body gets `margin: 0`.
   - **Chrome colors** use CSS system colors, which follow the page's color scheme: `Canvas`,
     `CanvasText`, `ButtonFace`, `ButtonText`, `Highlight`, `HighlightText`, and
     `color-mix(in srgb, CanvasText 20%, transparent)` for lines.
   - **Syntax colors** (KDE's Breeze syntax-highlighting colors), with
     `@media (prefers-color-scheme: dark)` for the dark column:

     | role | class | light | dark |
     | --- | --- | --- | --- |
     | key | `kondor-json-key` | `#0057ae` | `#2980b9` |
     | string | `kondor-json-string` | `#bf0303` | `#f44f4f` |
     | number | `kondor-json-number` | `#b08000` | `#f67400` |
     | `true`, `false`, `null` | `kondor-json-literal` (bold) | `#644a9b` | `#a26ac7` |
     | `{ } [ ] , :` and the collapsed count | `kondor-json-punctuation` | `CanvasText` at `opacity: 0.6` | same |

     Links inside strings keep the string color, underlined.
   - **Fonts:** the toolbar uses `13px system-ui, sans-serif`; the tree and the path use
     `13px/1.6 monospace`.
5. **Parsing (`parse.js`).**
   - **Exact numbers:** `JSON.parse(text, reviver)`. For a number the reviver returns
     `JSON.rawJSON(context.source)`, so a number is shown and copied exactly as written
     (`12345678901234567890`, `1.50`). Every other value is returned unchanged.
   - **Path of a row**, built from the root down, with no root prefix:
     - an object key that matches `^[A-Za-z_$][A-Za-z0-9_$]*$` adds `.key` (no dot at the
       start of the path);
     - any other object key adds `[` + `JSON.stringify(key)` + `]`, for example `["user name"]`;
     - an array index adds `[i]`;
     - for example `owner.login`, `items[2].tags[0]`, `[0].id`, `headers["Content-Type"]`.
     - The root row has the empty path.
   - **Copied value of a row:** a string gives the string itself, without quotes or escapes; any
     other value gives `JSON.stringify(value, null, 2)` (exact numbers included).
6. **The tree (`tree.js`).** Inserted at the start of `<body>`, after the toolbar.
   - **Container:** a `<div>` with `role="tree"`, `aria-label` = the document's title text
     (item 10), `dir="ltr"` (JSON is code), and `padding: 6px 8px 6px calc(8px + 2ch)` so the
     root's triangle is not on the window edge.
   - **Rows:** each value is one `<div role="treeitem">` with `aria-level`, holding:
     - one **line** element: the toggle (containers only), the key (`"name"` in quotes, then
       `: `) for object members, then the value;
     - for a non-empty object or array, a `<div role="group">` with its children, indented by
       `2ch`, and a closing line (`}` or `]`);
     - a `,` after every member except the last.
   - **Values:** strings as `JSON.stringify(value)` in the string color; numbers as their
     `rawJSON` text; `true`, `false`, `null`; empty objects and arrays as `{}` and `[]` with no
     toggle.
   - **Links:** a string whose value parses with `new URL(value)` and has the protocol `http:`
     or `https:` shows its text inside an `<a href="value">` (between the quotes). It is a
     normal link: a click opens it in the tab, a middle-click or Ctrl+click in a new tab, and
     the page context menu works. No other protocol becomes a link.
   - **Toggle:** before the key of a non-empty object or array, a `▾` (expanded) or `▸`
     (collapsed) in a `2ch`-wide box placed in the indent (`margin-inline-start: -2ch`), at
     `font-size: 1.2em`, `opacity: 0.6`, `cursor: pointer`, `aria-hidden="true"`. A click on it
     toggles the row.
   - **Collapsed row:** `aria-expanded="false"`; its group and closing line are hidden, and the
     line ends with `{…}` or `[…]` (plus `,` when not last) and, dimmed, the number of members
     (item 10), for example `[…] 3 items`.
   - **Start:** every row is expanded.
   - **Collapse All:** collapses every non-empty container except the root. **Expand All:**
     expands every row. Both keep the selection; when the selected row becomes hidden, the
     selection moves to its nearest visible ancestor.
7. **Selection and keys (`keyboard.js`).**
   - **One selected row** at a time: `aria-selected="true"`, `tabindex="0"`, and the line
     highlighted with `background: color-mix(in srgb, Highlight 25%, transparent)` and a
     `1px solid Highlight` outline, `border-radius: 3px`. Every other row has `tabindex="-1"`.
     At start the root row is selected, without taking focus.
   - **Mouse:** a click on a line, outside the toggle and outside a link, selects that row and
     focuses it.
   - **Keys**, while the tree has focus (WAI-ARIA tree pattern):
     - Down / Up: the next / previous visible row;
     - Right: expands a collapsed row, or moves to the first child of an expanded one;
     - Left: collapses an expanded row, or moves to the parent;
     - Home / End: the first / last visible row;
     - each key calls `preventDefault()` and scrolls the row into view (`block: "nearest"`).
   - **Focus ring:** the browser's focus ring is turned off on the row and drawn on its line
     (`outline: 2px solid Highlight`), so it does not wrap the whole subtree.
8. **Toolbar and views (`toolbar.js`).** A bar inserted as the first child of `<body>`:
   `position: sticky; top: 0`, `Canvas` background, a bottom line, `display: flex;
   flex-wrap: wrap; gap: 6px; align-items: center; padding: 6px 8px`, above the tree
   (`z-index: 1`). All controls are `<button type="button">` with visible text, styled with
   `ButtonFace` / `ButtonText`, a 1 px line border and a 4 px radius.
   - **View switch:** "Pretty" and "Raw" side by side as one segmented group, each with
     `aria-pressed`. The pressed one uses `Highlight` / `HighlightText`. Pretty is pressed at
     start. Raw hides the tree and shows the original `<pre>` again; Pretty does the opposite.
   - **Tree buttons**, after a thin separator: "Collapse All" and "Expand All".
   - **Copy buttons**, after a second separator: "Copy Value" and "Copy Path", then the
     **path** of the selected row in the monospace font, dimmed (`opacity: 0.75`), on one line
     with an ellipsis when too long and the full path in its `title`. "Copy Path" is disabled
     while the root row is selected (empty path).
   - **In Raw view** the tree buttons, the copy buttons, the separators and the path are hidden
     (not disabled), and only the view switch stays.
   - **Copy feedback (`clipboard.js`):** a copy button copies with the copy-event method of
     "Context" (never `navigator.clipboard`). On success, its text and accessible name become
     "Copied" for 2 s, then go back. A failed copy (`execCommand` returns false) leaves the label
     unchanged.
   - **Too large** (item 3): the tree is not built. The `<pre>` stays visible, and the toolbar
     shows only the notice text "This document is too large to format quickly (%1)." and a
     "Format Anyway" button. "Format Anyway" parses the text, builds the tree and switches to
     the normal toolbar in Pretty view. If parsing fails there, the notice and button are
     removed and the page is left raw.
9. **Wiring (`content.js`).** Runs once at document end: detect (item 3), then either the
   too-large state or parse, add the style sheet, build the toolbar and tree, and hide the page's
   own view. No timer, no `MutationObserver`, no `kondor.settings`, no `kondor.storage`, no
   network.
10. **Texts (`texts.js`).** The pt_BR texts are used when `kondor.locale` starts with `pt`, the
    English ones otherwise. `%1` is replaced by a number formatted with
    `Intl.NumberFormat(kondor.locale with "_" replaced by "-")`.

    | text | English | pt_BR |
    | --- | --- | --- |
    | view button | Pretty | Formatado |
    | view button | Raw | Bruto |
    | tree button | Collapse All | Recolher Tudo |
    | tree button | Expand All | Expandir Tudo |
    | copy button | Copy Value | Copiar Valor |
    | copy button | Copy Path | Copiar Caminho |
    | copy feedback | Copied | Copiado |
    | toolbar `aria-label` | JSON viewer | Visualizador de JSON |
    | tree `aria-label` | JSON document | Documento JSON |
    | collapsed count, one | 1 item | 1 item |
    | collapsed count, other | %1 items | %1 itens |
    | notice | This document is too large to format quickly (%1). | Este documento é grande demais para formatar rapidamente (%1). |
    | notice button | Format Anyway | Formatar Mesmo Assim |

    - The count uses `Intl.PluralRules` (`one` → the "one" text).
    - The notice's `%1` is the text length in megabytes with one decimal, formatted with
      `Intl.NumberFormat(locale, { style: "unit", unit: "megabyte", maximumFractionDigits: 1 })`
      on `length / 1,000,000` (for example "1.4 MB", "1,4 MB").
11. **README.md** of the extension:
    - **What it does:** shows JSON documents as a collapsible tree with syntax colors that follow
      the light or dark scheme; Pretty / Raw; Collapse All / Expand All; copying a value or its
      path; clickable `http` and `https` links; documents over 1,000,000 characters start raw
      with "Format Anyway"; it does nothing on other pages; "Run on <site>" turns it off for a
      site.
    - **Permissions:** one line for `<all_urls>`, saying it needs to see every page to recognize
      a JSON document (including local `file://` ones) and changes nothing elsewhere, and a line
      saying it asks for no API permission.
    - **Network:** none.

## Acceptance criteria

- [ ] `extensions/json-viewer/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists JSON Viewer.
  - `python3 tools/pack.py extensions/json-viewer` produces the package.
- [ ] On a JSON document (including `api.github.com`, which sends `default-src 'none'`) the tree
  shows with the colors of item 4 in light and in dark, and the page's own `<pre>` and
  `json-formatter-container` are hidden. No CSP violation and no console error.
- [ ] On an HTML page, a plain-text page and an invalid JSON document, the extension adds no
  element and no style sheet.
- [ ] Toggles collapse and expand rows; collapsed rows show `{…}` / `[…]` and the member count;
  Collapse All and Expand All work as in item 6.
- [ ] Raw shows the original text and hides the tree and the tree and copy controls; Pretty
  brings them back.
- [ ] Copy Value and Copy Path put the text of item 5 on the system clipboard after a click, with
  no permission prompt, and the button reads "Copied" for 2 s.
- [ ] Numbers are shown and copied exactly as in the source (`12345678901234567890`, `1.50`).
- [ ] `http` and `https` string values are links; `javascript:` and other strings are not.
- [ ] The tree works with the keyboard as in item 7, with a visible focus ring on the line.
- [ ] A document over 1,000,000 characters starts raw with the notice; "Format Anyway" builds
  the tree. A 672 KB document renders in under 1.5 s in the harness.
- [ ] No network request, no `kondor.storage`, nothing written in normal or private windows.
- [ ] The texts of item 10 in English and pt_BR.
- [ ] The README has the three sections of item 11.
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, no comments.

## Manual test

The developer runs without a display, so the check is done headless, as decided for #112–#114.
Use temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

Tips for the harness:
- Qt's QML runtime is `/usr/lib64/qt6/bin/qml` and its test runner
  `/usr/lib64/qt6/bin/qmltestrunner`; neither is on `PATH`.
- Fedora turns QML `console.log` off: set `QT_LOGGING_RULES="qml.debug=true"` and
  `QT_FORCE_STDERR_LOGGING=1`.
- **Screenshots and real clicks** need a real window: offscreen `grabToImage` gives a blank
  image. Run the harness in a nested headless KWin:
  `kwin_wayland --virtual --no-lockscreen --socket kondor-test --width 1000 --height 760
  --exit-with-session "env QT_QPA_PLATFORM=wayland WAYLAND_DISPLAY=kondor-test <harness>"`.
  `TestCase.mouseClick` / `keyClick` from `QtTest` under `qmltestrunner` give the page a real
  user gesture, which the copy needs.
- **Dark scheme:** `QTWEBENGINE_CHROMIUM_FLAGS=--blink-settings=preferredColorScheme=0`.

Steps:

1. **Package.** `python3 tools/validate.py`, `python3 tools/pack.py extensions/json-viewer` and
   `python3 tools/build-catalog.py <dir>`.
2. **Harness.** A QML file with a `WebEngineView` (off-the-record profile) that injects the nine
   scripts, concatenated in manifest order inside one closure, as a `WebEngineScript` in the
   application world at document end, with a stub `kondor` (`locale`). It logs console messages
   and `securitypolicyviolation` events.
3. **Pages.** Open `https://api.github.com/repos/lukasborges/kondor`, a local `file://` JSON file
   with a big integer, `1.50`, a `"user name"` key, a `javascript:` string, an empty object and
   an empty array, an HTML page, a `text/plain` page and an invalid local `.json` file. Check
   acceptance criteria 2, 3, 7 and 8. Take light and dark screenshots of the GitHub page for the
   PR.
4. **Tree.** Click a toggle, then Collapse All, then Expand All, and check the counts.
5. **Views.** Raw, then Pretty.
6. **Copy.** Select `owner.login` with a click, press Copy Path and Copy Value, and read the
   clipboard (`wl-paste` inside the KWin session, or `QGuiApplication::clipboard()` from a small
   C++ test helper). No `permissionRequested` signal on the view.
7. **Keyboard.** Focus the tree and use Down, Right, Left, Home and End.
8. **Size.** Open `https://api.github.com/repos/lukasborges/kondor/issues?per_page=100&state=all`
   and log the time from document end to the tree being built. Then a local file over
   1,000,000 characters: the notice shows; "Format Anyway" builds the tree.
9. **pt_BR.** With `locale` `pt_BR` the buttons read "Formatado", "Bruto", "Recolher Tudo"…

The steps that need a person at a running Kondor do not block the merge (as in #109–#114). They
are listed under "Not done" in the PR's Testing section for the maintainer:
- "Install from File…";
- "Run on <site>";
- a private window, with `sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from
  extension_storage"` returning no row.

The PR names the pages used and the result of each step above.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
- Settings, toolbar menu items and keyboard shortcuts other than the tree keys of item 7.
- Remembering the view, collapsed rows or selection across pages, and any use of
  `kondor.storage`.
- JSON inside HTML pages, JSONP, JSON Lines, `application/ld+json` `<script>` blocks, and JSON
  served as `text/plain` or downloaded by the browser.
- Searching or filtering the tree, editing values, sorting keys, and themes other than light and
  dark.
- Lazy or virtual rendering of large trees (the size limit replaces it).
- Translations other than pt_BR, and JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged) and #108 (the extensions repository and its tools,
merged).

## Prototype

No new QML prototype. The Kondor UI is generated from the manifest: "Run on <site>" in the
toolbar Extensions panel, as in the #183 prototypes. The extension has no settings.

The toolbar and tree are web content inside the JSON page, not Kondor QML. Items 4 to 8 describe
them fully. The architect mocked them in a headless view on the `api.github.com` page on
2026-11-13, in light and dark, and reviewed the screenshots with the `kde-ux` checklist:
- the segmented Pretty / Raw switch, the two button groups and the path of the selected row read
  at a glance, and the Breeze syntax colors are readable in both schemes;
- changes made after that review, already in this spec: the toggle grew to `1.2em` (it was hard
  to see and hit), the toolbar wraps (`flex-wrap`) so 50 % longer translations fit in narrow
  windows, and the tree got `2ch` of start padding so the root's toggle is not on the edge.

## Decisions

| Question | Decision |
| --- | --- |
| How to style a page with `default-src 'none'`? | One constructable style sheet in `document.adoptedStyleSheets` and CSSOM `style.setProperty`, both measured to work under that policy. Rejected: a `css` file in the manifest and `<style>` elements, which the policy blocks with a console error on `api.github.com`. |
| How to copy? | `execCommand("copy")` with a one-time `copy` event, inside the click. Rejected: `navigator.clipboard.writeText`, which in Qt WebEngine asks for the `ClipboardReadWrite` permission and never settles, so Kondor would show a permission prompt for a copy. |
| How does the user copy a value or a path? | Select a row (click or keys), then "Copy Value" or "Copy Path" in the toolbar, with the selected path shown next to them. Rejected: copy icons that appear on hover on each row, which hide the main action behind hover, do not work by keyboard or touch, and repeat on tens of thousands of rows. |
| Copy feedback? | The button reads "Copied" for 2 s, as KDE shows success on the control acted on (#176). Rejected: a toast or message. |
| Numbers? | Exact, through the reviver's `source` and `JSON.rawJSON` (Chromium 140). Rejected: plain `JSON.parse`, which silently rounds ids above 2^53 in Pretty view and in copied values. |
| Size limit? | 1,000,000 characters, then raw with a notice and "Format Anyway". A naive 672 KB tree took about 0.55 s, so the limit keeps the eager build around a second. Rejected: lazy or virtual rendering, more code for a rare case; and no way to format big documents at all. |
| Colors? | KDE's Breeze syntax-highlighting colors for the values, CSS system colors for the toolbar and selection, so both follow the page's light or dark scheme. Rejected: hard-coded toolbar colors, which break one of the schemes. |
| Which pages? | `<all_urls>` (including `file://`), with a strict check of the content type and the page's structure, so it does nothing on other pages. "Run on <site>" turns it off per site. |
| Start view? | Pretty, every row expanded, root selected without focus. No setting to start raw or collapsed (out of scope). |
| Manual test without a display? | Headless QtWebEngine harness, as decided for #112–#114, plus a nested `kwin_wayland --virtual` session for screenshots and real clicks. The interactive Kondor steps are listed as "Not done" for the maintainer and do not block the merge. |
