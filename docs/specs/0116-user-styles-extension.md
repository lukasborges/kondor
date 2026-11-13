# User Styles extension (#116)

> **Issue:** [#116](https://github.com/lukasborges/kondor/issues/116) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Publish the catalog extension **User Styles** in `extensions/user-styles/`. It restyles websites
with the user's own CSS, as Stylus does:
- **Edit:** "Edit Style for This Site…" opens an in-page editor with a live preview. It edits the
  CSS of the current site.
- **Install:** opening a `.user.css` link (UserCSS format) shows an install panel.
- **Manage:** "Manage Styles…" lists every style. In the list the user can turn a style on or
  off, remove it (with undo), and open a `.user.css` link.
- **Run:** enabled styles are applied from `document-start` on the pages they match.

The extension itself sends nothing over the network.

## Context

- **Format and API:** the package format, the manifest and the JavaScript API are those of #107
  ([`0107-kondor-extensions.md`](0107-kondor-extensions.md) and
  [`docs/extensions/api.md`](../extensions/api.md)), with item icons from #182. This issue uses
  them as they are. If it needs a change, ask a question.
- **Injection (#107 item 3):**
  - all `js` files of a content script are concatenated into **one closure**, in manifest order;
  - scripts run in Qt WebEngine's **application world**: they share the page's DOM, not its
    JavaScript objects;
  - `<all_urls>` becomes the glob `*`;
  - toolbar actions (`kondor.onAction`) reach the main frame only.
- **Storage:** `kondor.storage` holds JSON values, **1 MiB per extension**. A full store makes
  `set` reject with "The extension's storage is full (limit: 1 MiB)". In a private tab `set` and
  `remove` reject, and `get` works. Storage has no change event, so a change made in one tab
  reaches other tabs only when they load their next page.
- **Measured on 2026-11-13** (Qt 6.11, Chromium 140, headless view with the content script
  injected at document creation in the application world):
  - A constructable style sheet (`new CSSStyleSheet()` + `replaceSync`) added to
    `document.adoptedStyleSheets` **at document creation** applies, also under
    `default-src 'none'` (`api.github.com`) and on `github.com`. A `<style>` element is blocked
    by a strict policy (#115). The same is true for `shadowRoot.adoptedStyleSheets` in a closed
    shadow root.
  - **`.user.css` links:**
    - `raw.githubusercontent.com` serves `text/plain` with
      `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox`;
    - `userstyles.world/api/style/<n>.user.css` is redirected to `text/css`;
    - both show a `<body>` with one `<pre>` holding the file.
  - **On the sandboxed `raw.githubusercontent.com` page**, the content script still runs, and so
    do:
    - Promises, `requestAnimationFrame`, `DOMContentLoaded` and click listeners;
    - a QWebChannel round trip (the bridge behind `kondor.storage`).

    **`setTimeout` callbacks are blocked** ("Blocked script execution … the document's frame is
    sandboxed"). So the extension uses **no timers** anywhere.
  - The storage answer arrives after the first `DOMContentLoaded` on fast pages. A style can
    therefore appear a moment after the first paint. Nothing in API version 1 gives scripts a
    synchronous read, and the platform is out of scope.
- **UserCSS:** the format of Stylus
  (<https://github.com/openstyles/stylus/wiki/Writing-UserCSS>):
  - a `/* ==UserStyle== … ==/UserStyle== */` metadata comment;
  - `@-moz-document` blocks that choose where each part applies.

  Chromium does not support `@-moz-document`, so the extension splits the code into sections
  itself (item 4). Real files often set `@preprocessor uso` and have `@advanced` variables, for
  example GitHub Dark
  (`https://raw.githubusercontent.com/StylishThemes/GitHub-Dark/master/github-dark.user.css`,
  123 KB, 6 `@-moz-document` blocks, `dropdown` options with `<<<EOT … EOT;`).
- **Repository rules (#108):**
  - `tools/validate.py` must pass;
  - `CONTRIBUTING.md` applies: no remote code, and the README lists the network use.

  CSS is not code. The extension fetches nothing: the user opens a `.user.css` page like any
  page, and the extension reads the page's text.
- **Code quality:** AGENTS.md → "Code quality" applies to the JavaScript, as for #109–#115:
  - functions of at most 10 lines and 3 parameters;
  - nesting depth at most 2;
  - files of at most 200 lines, at most 10 files in the folder;
  - no comments.

  `scripts/check-code-quality.py --root` from this repository checks the `.js` files when they
  are copied under `src/user-styles/` of a temporary root that also holds an empty
  `scripts/code-quality-baseline.json` (`{}`).

## Design / behavior

1. **Files** in `extensions/user-styles/`. Each line gives the file and what it holds:
   ```
   manifest.json
   texts.js      the in-page texts
   metadata.js   the UserCSS metadata block and the default values of its variables
   sections.js   splitting CSS into @-moz-document sections
   matching.js   matching sections to a URL, and the readable list of a style's sites
   store.js      reading and writing the styles in kondor.storage
   panel.js      the side panel: shadow root, header, close, Esc, its style sheet
   editor.js     the site style editor and its live preview
   manager.js    the style list, Remove and Undo, opening a link
   installer.js  the install panel on .user.css pages
   content.js    applying the page's style sheet, and wiring
   icon.svg      original artwork: a paintbrush over a page; not copied from another project
   README.md     "What it does", "Permissions", "Network"
   ```
   - The `js` order in the manifest is the order above.
   - `content.js` is last and the only file that runs code at the top level. The other files only
     declare functions and constants.
   - **No timers:** no `setTimeout` or `setInterval`, and no `MutationObserver`.
2. **Manifest** (`kondor: 1`):
   - `id` `user-styles`, `version` `1.0.0`;
   - `name` "User Styles", `name[pt_BR]` "Estilos do Usuário";
   - `description` "Restyles websites with your own CSS.", `description[pt_BR]` "Muda a
     aparência dos sites com o seu próprio CSS.";
   - `author` "Kondor contributors", `license` `GPL-3.0-or-later`;
   - `homepage` `https://github.com/lukasborges/kondor-extensions/tree/main/extensions/user-styles`;
   - `icon` `icon.svg`;
   - **no `permissions`** and **no `settings`**;
   - one content script:
     - `matches` `["<all_urls>"]` and the ten `js` files of item 1;
     - **no `css`**;
     - `runAt` `document-start`, `allFrames` `false`;
   - `action`:
     - `siteToggle: true`;
     - `items`:
       - `{ "id": "edit-style", "title": "Edit Style for This Site…", "title[pt_BR]": "Editar Estilo deste Site…", "icon": "document-edit" }`;
       - `{ "id": "manage-styles", "title": "Manage Styles…", "title[pt_BR]": "Gerenciar Estilos…", "icon": "configure" }`.
3. **The stored data (`store.js`).** One storage key, `styles`, holds an array of style objects:
   ```
   { id, name, kind, enabled, sections: [{ matchers: [{ type, value }], css }],
     namespace, version, author, description }
   ```
   - **`kind` `"site"`:** a style written in the editor.
     - `id` is `site:<host>`, `name` is the host;
     - it has one section with the matcher `{ type: "host", value: <host> }`;
     - the last four fields are empty strings.
   - **`kind` `"usercss"`:** an installed `.user.css`.
     - `id` is `usercss:<namespace>:<name>`;
     - the sections are stored with their variables already replaced (item 5);
     - the original file is not kept.
   - **Load:** `loadStyles()` returns `get("styles")`, or `[]` when it is missing or not an array.
   - **Save:** `saveStyles(styles)` writes the whole array. A rejected `set` resolves to the
     error's message, so the panel can show it (items 7 to 9); success resolves to `null`.
   - **Order:** styles keep their order in the array, and new styles are appended.
4. **Sections (`sections.js`).** `splitSections(code)` returns `[{ matchers, css }]`.
   - **Scanning:** the scan skips `/* … */` comments and `"…"` / `'…'` strings with `\`
     escapes, so braces inside them do not count.
   - **Blocks:**
     - each top-level `@-moz-document <matchers> { … }` (also `@document`) gives one section:
       its matchers and the text between its braces;
     - the code outside such blocks, if it is not blank, gives one section with **no matchers**
       (it applies everywhere).
   - **Matchers:** a comma-separated list of `url(…)`, `url-prefix(…)`, `domain(…)` and
     `regexp(…)`. The argument is a quoted string (with `\` escapes) or an unquoted value up to
     `)`.
   - **Malformed code:** an unknown matcher function or an unclosed block makes the whole file
     unreadable (item 9).
5. **Metadata and variables (`metadata.js`).** `readUserCss(text)` returns
   `{ meta, sections }` or `{ error }`.
   - **Metadata block:** the first comment that starts with `==UserStyle==` and ends with
     `==/UserStyle==`.
     - Each line `@key value` sets a key: `name`, `namespace`, `version`, `description`, `author`
       and `preprocessor`. Other keys are ignored, except variables.
     - `name` is required. A missing `namespace` is `""`.
   - **Variables:** a line `@var` or `@advanced`, then `<type> <name> <label> <value>`.
     - The label is a quoted string or one word.
     - The value is the rest of the line. When it starts with `{` or `[`, it runs to the
       matching closer, across lines, and `<<<EOT … EOT;` blocks inside it are read as one
       string.
     - **Default value by type:**
       - `text`, `color`, `number`: the value as written, trimmed;
       - `checkbox`: `1` or `0`;
       - `range`: the first element of a `[value, min, max, step, unit]` array plus its unit,
         or the plain number;
       - `select`, `dropdown`, `image`: the option whose name ends with `*` (the `*` removed),
         else the first option. An option list is one of:
         - a JSON array (`["a", "b*"]`, value = item);
         - a JSON object (`{"Label": "value"}`, value = the value);
         - `uso` lines `name "Label" <<<EOT value EOT;` or `name "Label" "value"`.
   - **Preprocessors:**
     - **none or `default`:** the variables become one rule, `:root { --<name>: <default>; }`,
       added before the first section's CSS. The rule is not added when there are no variables;
     - **`uso`:** every `/*[[<name>]]*/` in the code is replaced by the variable's default;
     - **`stylus`, `less` or any other value:** `{ error: "preprocessor", preprocessor }`
       (item 9).
   - **Errors:** a missing block, a missing `@name`, an unreadable variable or a malformed
     section gives `{ error: "unreadable" }`.
6. **Matching and applying (`matching.js`, `content.js`).**
   - **Matchers** are tested against `location.href` and `location.hostname`:
     - `url`: the URL equals the value;
     - `url-prefix`: the URL starts with the value (`""` matches every URL);
     - `domain`: the host equals the value or ends with `.` + value;
     - `regexp`: `new RegExp("^(?:" + value + ")$")` matches the whole URL. An invalid
       expression matches nothing;
     - `host` (site styles): the host equals the value.
   - **Sections:** a section applies when it has no matchers or any matcher matches.
   - **The page's sheet:** at document start, `content.js` loads the styles. It puts the CSS of
     every applying section of every **enabled** style, in array order and joined with
     newlines, into **one** constructable `CSSStyleSheet`, appended to
     `document.adoptedStyleSheets` (keeping the sheets already there). No `<style>` element.
     When no section applies, no sheet is added.
   - **CSS errors:** `replaceSync` ignores rules it cannot parse and `@import` rules, as browsers
     do. The README says that `@import` is not supported.
   - **Re-applying:** `applyStyles(styles)` replaces the sheet's text with `replaceSync`. It is
     used by the editor preview and by the list's checkboxes, Remove and Undo, so the page
     changes at once. It adds the sheet when it was not added yet.
   - **When matching runs:** at document start only. A page that changes its URL without
     loading is matched again on its next load.
   - **Sites list:** `describeSites(style)` returns readable lines. It is used by the list and
     the install panel:
     - `domain` → the domain;
     - `host` → the host;
     - `url-prefix` → "Pages starting with %1";
     - `url` → "The page %1";
     - `regexp` → "Pages matching %1";
     - a section without matchers → "All sites".

     Duplicate lines are listed once.
7. **The panel (`panel.js`).** All three views share one side panel.
   - **Host:** one `<div>` appended to `document.documentElement`, with a **closed** shadow root
     and one constructable sheet in `shadowRoot.adoptedStyleSheets`. The host gets
     `all: initial` through CSSOM (`style.setProperty`), so page CSS cannot reach it.
     - Only one panel exists at a time: opening a view replaces the panel's content.
     - Opening a view while the editor has unsaved changes goes through the discard question
       first (item 8).
     - The DOM is built with `createElement` and `textContent` only (no `innerHTML`; sites with
       Trusted Types reject it).
   - **Layout:**
     - **Frame:** `position: fixed`, full height at the inline end (`inset-block: 0;
       inset-inline-end: 0`), `width: min(440px, 100vw)`, `z-index: 2147483647`, and a
       flex column.
     - **Colors:** `Canvas` / `CanvasText`, a 1 px start border in
       `color-mix(in srgb, CanvasText 20%, transparent)` and a soft shadow.
     - **Font:** `13px/1.4 system-ui, sans-serif`.
     - The panel has `role="dialog"` and `aria-label` equal to its title. It is not modal: the
       page stays usable.
   - **Header:**
     - the title, bold, 14 px, wrapping;
     - a close button `✕` with `aria-label` and `title` "Close";
     - a bottom line.
   - **Body:** scrolls.
   - **Footer:** a top line, buttons at the end, wrapping.
   - **Buttons:**
     - `ButtonFace` / `ButtonText`, a 1 px line border and a 4 px radius;
     - the default button uses `Highlight` / `HighlightText`;
     - disabled buttons have `opacity: 0.5`;
     - focus shows a `2px solid Highlight` outline (`:focus-visible`).
   - **Closing:** the close button and Esc, while focus is in the panel, close it. Closing
     returns focus to the page.
   - **Messages:** a line in the body with a 3 px start border and a 12 % tint:
     - neutral `#f67400` for private windows;
     - negative `#da4453` for errors.

     These are the Breeze neutral and negative colors, as in #115's syntax colors.
   - **Light and dark:** system colors follow the page's color scheme. The host also sets
     `color-scheme: light dark`.
8. **Editor (`editor.js`)**, opened by the item `edit-style`. It edits the site style of the
   current host.
   - **Title:** "Style for %1" (host).
   - **Body:** one `<textarea>` filling the body:
     - `font: 13px/1.5 monospace`, `Field` / `FieldText`;
     - `spellcheck="false"`, `aria-label` "CSS";
     - it holds the saved CSS of this site's style, or nothing. It gets focus when the editor
       opens.
   - **Live preview:** on every `input` event, the site style's CSS in memory becomes the text,
     and `applyStyles` re-applies. No delay, no timer.
   - **Footer:**
     - **Save** (default): disabled while the text equals the saved text. After a successful
       save it reads **"Saved"** and stays disabled until the next edit. Then it reads "Save"
       again.
     - **Close**.
   - **Saving:**
     - updates or appends the `site:<host>` style, enabled, with the text;
     - saving an empty or blank text removes the site style;
     - a failed save shows the error message (item 7) with the storage's text, and Save stays
       enabled.
   - **Unsaved changes:** Close, ✕ and Esc with unsaved changes replace the footer with:
     - "Discard the unsaved changes?";
     - **Discard**: restores the saved CSS in the preview and closes;
     - **Keep Editing** (default, focused).
   - **Private windows:**
     - the message "Styles cannot be saved in private windows." at the top of the body;
     - no Save button, and the preview still works;
     - Close never asks, and restores the saved CSS.
9. **Install panel (`installer.js`).** It opens by itself, at `DOMContentLoaded`, when all of
   these hold:
   - the URL's path ends with `.user.css`;
   - `document.contentType` is `text/plain` or `text/css`;
   - the `<body>`'s only element child is one `<pre>`.

   Otherwise it does nothing.
   - **Title:** "Install Style".
   - **Body:** a two-column list (`<dl>`):
     - Name, Version, Author and Description, each only when not empty;
     - Sites, one line each from `describeSites`.
   - **Already installed** (same `id`): the Version reads "%1 (installed: %2)" and the default
     button reads **Update** instead of **Install**.
   - **Footer:** **Install** (or **Update**, default) and **Cancel**.
     - **Install** or **Update** replaces the style with the same `id`, keeping its position and
       its `enabled` state, or appends a new one, enabled.
     - Then `applyStyles` runs, and the button reads **"Installed"**, disabled. Cancel becomes
       **Close**.
     - A failed save shows the error message and keeps the button.
   - **Unsupported or unreadable file:** an error message and only **Close** in the footer:
     - preprocessor: "This style needs the “%1” preprocessor, which User Styles does not
       support.";
     - unreadable: "This file is not a style User Styles can read."
   - **Private windows:** the details, the message "Styles cannot be installed in private
     windows." and only **Close**.
10. **Style list (`manager.js`)**, opened by the item `manage-styles`.
    - **Title:** "Styles".
    - **Link field** at the top of the body:
      - an `<input type="url">` with placeholder and `aria-label` "Link to a .user.css file",
        and an **Open** button;
      - Open is enabled only when the text parses with `new URL` as `http:` or `https:`, and
        Enter in the field does the same;
      - Open calls `window.open(link, "_blank", "noopener")`, which opens a new tab where the
        install panel appears (item 9).
    - **Groups:** "This Site" (styles with at least one applying section on this page), then
      "Other Sites". Each group has a small bold heading and is left out when empty. In each
      group the styles are sorted by name (`localeCompare`).
    - **Rows:**
      - a `<ul role="listbox" aria-label="Styles">` of `<li role="option">`;
      - each row has a **checkbox** labelled by the style's name, and under the name the sites
        (`describeSites`) on one dimmed line: the first two joined with ", ", then "+%1 more";
      - the checkbox turns the style on or off at once: it saves, then `applyStyles`;
      - a turned-off row has its name dimmed (`opacity: 0.6`).
    - **Selection:**
      - a click on a row (outside the checkbox) selects it, and so do Up and Down while the
        list has focus;
      - a selected row has `aria-selected="true"`, a 25 % `Highlight` background, a
        `1px solid Highlight` outline and a 3 px radius;
      - the first row is selected when the list opens.
    - **Footer:** **Remove** at the start. It removes the selected style (and Delete does the
      same in the list), saves and re-applies.
      - The footer then shows "Removed “%1”" and **Undo** instead of Remove. Undo puts the style
        back at its old position, saves, re-applies and restores the footer.
      - The undo lasts until the next Remove or until the panel closes.
      - Remove is disabled when the list is empty.
    - **Empty:** "No styles" in the body, centered and dimmed, under the link field.
    - **Private windows:**
      - the message "Styles cannot be changed in private windows." at the top;
      - the checkboxes are disabled and there is no Remove;
      - the link field stays, since opening a link writes nothing.
    - **Save errors** show the error message, and the checkbox goes back to its saved state.
11. **Wiring (`content.js`):**
    - **At document start:** load the styles and apply.
    - **At `DOMContentLoaded`:** check for the install panel.
    - **`kondor.onAction`:** `edit-style` → editor, `manage-styles` → list. An action that
      arrives before `DOMContentLoaded` waits for it (Promise), never for a timer.
    - No `kondor.settings`, no network request. `window.open` is called only from the user's
      Open.
12. **Texts (`texts.js`).** The pt_BR texts are used when `kondor.locale` starts with `pt`, the
    English ones otherwise.

    | text | English | pt_BR |
    | --- | --- | --- |
    | close button | Close | Fechar |
    | editor title | Style for %1 | Estilo de %1 |
    | editor field | CSS | CSS |
    | save | Save | Salvar |
    | saved | Saved | Salvo |
    | discard question | Discard the unsaved changes? | Descartar as alterações não salvas? |
    | discard | Discard | Descartar |
    | keep editing | Keep Editing | Continuar Editando |
    | install title | Install Style | Instalar Estilo |
    | name / version / author / description / sites | Name / Version / Author / Description / Sites | Nome / Versão / Autor / Descrição / Sites |
    | installed version | %1 (installed: %2) | %1 (instalada: %2) |
    | install / update / installed | Install / Update / Installed | Instalar / Atualizar / Instalado |
    | cancel | Cancel | Cancelar |
    | preprocessor error | This style needs the “%1” preprocessor, which User Styles does not support. | Este estilo precisa do pré-processador “%1”, que o Estilos do Usuário não suporta. |
    | unreadable error | This file is not a style User Styles can read. | Este arquivo não é um estilo que o Estilos do Usuário consiga ler. |
    | list title | Styles | Estilos |
    | link field | Link to a .user.css file | Link para um arquivo .user.css |
    | open | Open | Abrir |
    | groups | This Site / Other Sites | Este Site / Outros Sites |
    | more sites | +%1 more | +%1 outros |
    | all sites | All sites | Todos os sites |
    | prefix / page / pattern | Pages starting with %1 / The page %1 / Pages matching %1 | Páginas que começam com %1 / A página %1 / Páginas que correspondem a %1 |
    | remove / undo | Remove / Undo | Remover / Desfazer |
    | removed | Removed “%1” | “%1” removido |
    | empty list | No styles | Nenhum estilo |
    | private: editor | Styles cannot be saved in private windows. | Estilos não podem ser salvos em janelas privativas. |
    | private: install | Styles cannot be installed in private windows. | Estilos não podem ser instalados em janelas privativas. |
    | private: list | Styles cannot be changed in private windows. | Estilos não podem ser alterados em janelas privativas. |
13. **README.md** of the extension:
    - **What it does:**
      - editing a site's CSS with a live preview;
      - installing `.user.css` files by opening their link, with UserCSS `@-moz-document`
        sections and the default values of `@var` / `@advanced` variables;
      - the preprocessors supported (none, `default`, `uso`; not `stylus` or `less`);
      - the style list: on/off, remove with undo, open a link;
      - `@import` is not supported, and styles cannot be changed in private windows;
      - "Run on <site>" turns it off for a site.
    - **Permissions:**
      - one line for `<all_urls>`: styles can target any site, and `.user.css` links must be
        recognized;
      - a line saying it asks for no API permission.
    - **Network:**
      - the extension sends nothing;
      - opening a `.user.css` link loads it like any page;
      - images or fonts named in a style's CSS are loaded by the page that uses the style.

## Acceptance criteria

- [ ] `extensions/user-styles/` exists with the files of item 1.
  - `python3 tools/validate.py` passes, and so does the `build` check of the PR.
  - The catalog built by `tools/build-catalog.py` lists User Styles.
  - `python3 tools/pack.py extensions/user-styles` produces the package.
- [ ] Editor:
  - typing CSS changes the page at once;
  - Save stores it, and a reload shows it applied from `document-start`;
  - Save reads "Saved" until the next edit;
  - an empty Save removes the site style;
  - Close with changes asks, and Discard restores the saved look.
- [ ] Opening the GitHub Dark `.user.css` link (sandboxed `raw.githubusercontent.com`) shows the
  install panel:
  - Name, Version, Author and the sites;
  - Install stores it, and `github.com` is then dark;
  - opening the link again shows "Update" and "(installed: …)".
- [ ] A `default`-preprocessor style with `@var color` gets `:root { --name: … }`. A `uso` style
  gets its `/*[[name]]*/` placeholders replaced by the defaults, including a `dropdown` with
  `<<<EOT` options. A `stylus` style shows the preprocessor error and cannot be installed.
- [ ] Sections apply as in item 6, and code outside `@-moz-document` applies everywhere:
  - `domain("example.org")` matches `www.example.org`, but not `notexample.org`;
  - `url-prefix`, `url` and `regexp` also behave as in item 6.
- [ ] Style list:
  - "This Site" and "Other Sites" groups;
  - the checkbox turns a style off and on at once;
  - Remove then Undo restores it in place;
  - Up, Down and Delete work in the list;
  - the empty state.
- [ ] Open in the list opens the link in a new tab, where the install panel appears.
- [ ] The panel works on `api.github.com` (`default-src 'none'`) and `github.com` with no CSP
  violation and no console error, in light and dark. Esc closes it, and page CSS does not
  change it.
- [ ] Private windows (extension allowed there): styles apply, nothing can be saved, and the
  messages of item 12 show. No storage write is attempted.
- [ ] No timer, no `MutationObserver`, no network request, no `innerHTML`.
- [ ] The texts of item 12 in English and pt_BR.
- [ ] The README has the three sections of item 13.
- [ ] The JavaScript follows AGENTS.md → "Code quality": functions ≤ 10 lines, ≤ 3 parameters,
  depth ≤ 2, files ≤ 200 lines, ≤ 10 `.js` files, no comments.

## Manual test

The developer runs without a display, so the check is done headless, as decided for #112–#115.
Use temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md).

Tips for the harness: the same as #115.
- Qt's runtimes are `/usr/lib64/qt6/bin/qml` and `qmltestrunner`.
- Set `QT_LOGGING_RULES="qml.debug=true"` and `QT_FORCE_STDERR_LOGGING=1` for `console.log`.
- Run a nested `kwin_wayland --virtual` for screenshots and real clicks.
- For the dark scheme, set `QTWEBENGINE_CHROMIUM_FLAGS=--blink-settings=preferredColorScheme=0`.
- `QML_XHR_ALLOW_FILE_READ=1` lets QML read local probe files.

**`kondor` stub:** the harness injects the ten scripts in one closure, in the application world at
document creation. It passes a stub `kondor` with:
- `locale` and `isPrivate`;
- an in-memory `storage` whose `set` rejects when `isPrivate` is true or above 1 MiB of JSON;
- `onAction` that the harness can trigger.

It logs console messages and `securitypolicyviolation` events.

Steps:

1. **Package.** `python3 tools/validate.py`, `python3 tools/pack.py extensions/user-styles` and
   `python3 tools/build-catalog.py <dir>`.
2. **Editor** on `https://example.org/`:
   - type `h1 { color: red !important }`: the heading turns red;
   - Save, then reload: it is red from the start;
   - edit, then Close → Discard: back to the saved look;
   - clear and Save: no style.
3. **Install** `https://raw.githubusercontent.com/StylishThemes/GitHub-Dark/master/github-dark.user.css`:
   - the panel shows its details;
   - Install, then open `https://github.com/`: the background is dark;
   - open the link again: "Update".
4. **Variables and preprocessors.** Local files served by `python3 -m http.server` with a
   `.user.css` path:
   - one `default` style with a `@var color`;
   - one `uso` style with a `dropdown`;
   - one `stylus` style.

   Check item 5 by reading `document.adoptedStyleSheets`.
5. **Matching.** One style with `domain`, `url-prefix`, `url` and `regexp` sections plus global
   code, checked on four local URLs.
6. **List.** Open it on `github.com`:
   - groups, checkbox off and on;
   - select with Down, Delete, Undo;
   - Open a link: a new tab with the install panel.
7. **CSP and look.** Open the editor and the list on `https://api.github.com/` and on
   `https://github.com/`, in light and dark. Attach screenshots of the three views to the PR.
8. **Private.** `isPrivate: true`: the messages, no Save or Remove, and no `set` call.
9. **pt_BR.** With `locale` `pt_BR`: "Estilo de …", "Salvar", "Instalar Estilo", "Estilos"…

The steps that need a person at a running Kondor do not block the merge (as in #109–#115). They
are listed under "Not done" in the PR's Testing section for the maintainer:
- "Install from File…";
- the two toolbar items in the Extensions panel;
- "Run on <site>";
- a private window, with `sqlite3 "$XDG_DATA_HOME"/*/kondor.sqlite "select * from
  extension_storage"` unchanged after trying to save there.

The PR names the pages and files used and the result of each step above.

## Out of scope

- Any change to Kondor itself (#107 platform), to the manifest format or to the #108 tools.
- Editing variables after install, `stylus` and `less` preprocessors, and `@import`.
- Updating installed styles from `@updateURL`, or any check for new versions.
- Importing from a file, exporting or backing up styles, and syncing.
- Matching again after an in-page URL change (single-page apps), frames (`allFrames`), and
  injection into shadow roots of the page.
- Syntax highlighting, autocomplete or linting in the editor, and moving or resizing the panel.
- Settings, keyboard shortcuts for the two items, and translations other than pt_BR.
- JavaScript unit tests (the repository's CI is Python only).

## Dependencies

#107 (the extension platform, merged), #108 (the extensions repository and its tools, merged)
and #182 (item icons, merged).

## Prototype

No new QML prototype. The Kondor UI is generated from the manifest: the two items and "Run on
<site>" in the toolbar Extensions panel, as in the #183 prototypes.

The side panel is web content, not Kondor QML, and items 7 to 10 describe it fully. On
2026-11-13 the architect mocked its views in a nested `kwin_wayland --virtual` session, over a
plain page in light and dark:
- the editor;
- the discard question;
- the list with 11 styles;
- the undo footer;
- the empty list;
- the install panel and its error.

The screenshots were reviewed with the `kde-ux` checklist. Changes after that review, already in
this spec:
- the list's per-row Remove buttons became one Remove for the selected row, with Undo;
- a bold "applies here" name became the "This Site" / "Other Sites" groups;
- Close with unsaved changes asks before discarding.

## Decisions

| Question | Decision |
| --- | --- |
| Where is the UI, with no popup pages in API version 1? | One in-page side panel (closed shadow root, constructable sheet), as the issue asks. It is fixed at the inline end and not modal, so the page stays visible for the live preview. Rejected: a centered dialog, which covers the page being styled. |
| How are styles applied under strict CSP? | One constructable style sheet in `document.adoptedStyleSheets`, measured to work at document creation and under `default-src 'none'`. Rejected: `<style>` elements and a manifest `css` file, which a strict policy blocks (#115). |
| How is a `.user.css` imported "from a URL"? | The user opens the link: in any tab, or with Open in the list, which opens a new tab. The extension reads the page's `<pre>` and shows the install panel. The extension makes no request of its own, so its README says "sends nothing". Rejected: `fetch` from the content script, which runs under the current page's CSP and CORS and would fail on many sites. |
| Timers? | None. On sandboxed pages such as `raw.githubusercontent.com`, `setTimeout` callbacks are blocked, and Promises, events and the storage bridge work. The preview applies on every `input`, and "Saved" / "Installed" last until the next change instead of 2 s. |
| What is "this site" for the editor? | The exact host (`www.example.org`), the same unit as "Run on <site>". Rejected: the domain and its subdomains, which would restyle unrelated subdomains. |
| How to remove styles in the list? | Select a row, then Remove in the footer, with Undo. Rejected: a Remove button on every row, ten identical buttons next to the checkboxes, as #183 rejected repeated row controls. |
| How does the list show which styles apply here? | Two groups, "This Site" and "Other Sites". Rejected: a bold name, whose meaning was not obvious. |
| Unsaved editor changes on Close? | Ask "Discard the unsaved changes?" with Discard and Keep Editing (default). Closing an editor must not lose typed CSS. Rejected: discarding silently, and keeping a hidden draft. |
| Which UserCSS features? | `@-moz-document` sections, metadata, and variable defaults for no preprocessor, `default` and `uso`. Rejected: shipping the Stylus and Less compilers (large third-party code to review) and a variable editor (out of scope). Popular legacy styles use `uso`, so it is supported. |
| Storage layout? | One `styles` key with the whole array: one read per page load, under the 1 MiB limit. Rejected: one key per style, which needs several round trips before anything applies. |
| Private windows? | Styles apply (reading is allowed). Saving, installing and changing are not offered, with a message, and no `set` is attempted. AGENTS.md: private tabs never offer anything that writes to disk. |
| Manual test without a display? | Headless QtWebEngine harness with a stub `kondor`, plus a nested `kwin_wayland --virtual` session, as for #112–#115. The interactive Kondor steps are listed as "Not done" for the maintainer and do not block the merge. |
