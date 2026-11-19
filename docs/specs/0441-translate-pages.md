# Translate pages on the device (#441)

> **Issue:** [#441](https://github.com/lukasborges/kondor/issues/441) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Translate a web page into the user's language **on this computer**, like Firefox: no text of the
page is sent anywhere, it works offline after a one-time download per language pair, and it
works on pages behind a login. The engine and the language models are Mozilla's (Bergamot), the
same files Firefox downloads.

## Context

- Address bar buttons: the popup blocker button of #375 (`window-duplicate-symbolic`) and its
  panel are the pattern to follow (button on the right of the address field, `Popup` panel).
- Per-tab state follows the Tab bridge pattern: a `tab.translation` group object (`TabTranslation`),
  like `tab.security` / `tab.permissions`.
- Page scripts in an isolated world and the WebChannel bridge already exist for extensions
  (`src/kondor/extensions/…/bridge`, #218) and the agent tab (#417); reuse the same approach.
- Settings singleton (`Settings`), Notifier, downloads of app data with `QNetworkAccessManager`.

## Design / behavior

Prototypes: `441-translate-offer`, `441b-translate-menu`, `441c-translate-downloading`,
`441d-page-translated`, `441e-manage-languages` (all approved).

### 1. When the button shows

- After a page finishes loading, its language is found:
  1. the `lang` attribute of `<html>` (primary subtag, lower case: `en-US` → `en`);
  2. if missing or `und`, detection on up to 2 000 characters of visible text with the Python
     package **`langdetect`** (Apache-2.0, pure Python; added to the Python dependencies, the
     Flatpak and the AppImage);
  3. no result → no button.
- The target language is the setting `translateTo` (default: Kondor's UI language, primary
  subtag; `pt_BR` → `pt`).
- The **Translate** button (`translate`, tooltip/`Accessible.name` "Translate Page") shows in the
  address bar, left of the bookmark star, when the page language differs from the target and
  Mozilla offers that pair (directly or through English), and the language and host are not on
  the "never" lists. It never opens the panel by itself.
- If the page language is on the "always" list, the page is translated on load (the button
  shows checked) without opening the panel.

### 2. Panel (`441-translate-offer`)

- Heading "Translate Page"; `Kirigami.FormLayout` with **From:** (`ComboBox`, first entry
  "<language> (detected)", then every supported language) and **To:** (supported languages);
  buttons **Not Now** (closes) and **Translate** (`translate`, highlighted, default).
- **More Options** (`overflow-menu`, `441b`): checkable "Always Translate <language>",
  "Never Translate <language>" (mutually exclusive), "Never Translate <host>", a separator and
  "Manage Languages…" (`languages`). Language names come from `QLocale` in the UI language.
- In **private tabs** the "Always/Never" items are hidden (they would be written to disk);
  translating works.

### 3. First use of a pair (`441c`)

- When the needed files are missing, Translate downloads them in the panel: a `ProgressBar` and
  "Downloading <from> → <to>: N of M MB" (small, `disabledTextColor`); the combos are disabled;
  **Cancel** stops and deletes the partial files. Closing the panel does not cancel; reopening
  shows the progress.
- Pairs without a direct model go through English (two pairs downloaded, like Firefox).
- A failed download (offline, hash mismatch) shows an inline error in the panel
  ("Could not download the language files.") with **Try Again**.

### 4. Translated page (`441d`)

- The page text is replaced in place, progressively from the top of the viewport; the button
  is checked; the panel shows "Page Translated" with the combos (changing **To** translates
  again from the original) and **Show Original** (`edit-undo`), which restores the original text
  without reloading.
- Text added later (infinite scroll, SPA navigation within the page) is translated too
  (`MutationObserver`), until Show Original or a navigation to another document.
- Form fields' values, `contenteditable`, `<code>`, `<pre>`, `<script>`, `<style>`, `<textarea>`
  and elements with `translate="no"` / class `notranslate` are left alone. `title`, `alt`,
  `placeholder` and `aria-label` attributes are translated.
- A navigation to another page keeps translating only if the language is on "always"; otherwise
  the new page starts untranslated.

### 5. Manage Languages (`441e`)

- Dialog "Manage Languages" listing the downloaded pairs ("English → Portuguese", size in MB,
  `disabledTextColor`) with a **Remove** button (`edit-delete`, tooltip "Remove") each, and
  **Close**. An empty list shows a `Kirigami.PlaceholderMessage` "No languages downloaded".

### 6. Engine and files

- **Source**: Mozilla Remote Settings, collections `translations-wasm` (record
  `bergamot-translator`) and `translations-models` (per pair: `model`, `lex`, `vocab`, and
  `srcvocab`/`trgvocab` when present), from `https://firefox.settings.services.mozilla.com/v1/
  buckets/main/collections/<name>/records`; attachments from the server's
  `capabilities.attachments.base_url`. Only records with an empty `filter_expression`. Version
  choice mirrors Firefox's `TranslationsParent.sys.mjs`: the newest engine, and per pair the
  newest model files whose major version that engine supports. Every file is checked against the
  record's `hash` (SHA-256) before use.
- **Storage**: `AppDataLocation/translations/engine/` and `…/models/<from>-<to>/`, plus the
  record metadata used. Never in a profile's web storage. Files are shared by all profiles.
- **Running**: the Bergamot WASM runs in a hidden Kondor-owned `WebEngineView` (internal page in
  the app's resources, off-the-record profile, no network) with a Web Worker, as Firefox does;
  page text goes page script (isolated world) → Python → engine page and back. No text leaves
  the computer; the only network traffic is the file download from Mozilla's servers.
- Text is sent in batches of HTML fragments (Bergamot's HTML mode keeps inline tags), visible
  ones first.
- The engine page is created on first use and closed after 5 minutes without translations.

### 7. Settings and privacy

- New settings: `translateTo` (string), `translateAlways` and `translateNever` (lists of language
  codes), `translateNeverHosts` (list of hosts). Never written from private tabs.
- Nothing about translated pages is stored (no cache of translations).

## Acceptance criteria

- [ ] An English page (`lang="en"`) with Kondor in Portuguese shows the button; a Portuguese
      page does not; a page without `lang` is detected.
- [ ] Translate on first use downloads en→pt with progress, verifies the hashes, and translates;
      Cancel removes partial files; offline shows the error with Try Again.
- [ ] A second translation works with the network off.
- [ ] German → Portuguese works through English.
- [ ] Show Original restores the exact original DOM text without reloading; changing To
      re-translates.
- [ ] Content added after translation is translated; `translate="no"`, code and form fields are
      untouched; links and inline formatting still work.
- [ ] Always / Never language and Never site behave as described and are hidden in private tabs;
      nothing is written from a private tab.
- [ ] Manage Languages lists the pairs with sizes and Remove deletes their files.
- [ ] No page text appears in any network request (checked with the network panel of the engine
      page and a proxy log in the manual test).
- [ ] Matches the five prototypes in Breeze and Breeze Dark; strings in `qsTr()`, translations
      complete; README: one "Translate pages" bullet; the About dialog / README credits
      Mozilla's Bergamot engine (MPL-2.0) and models.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`,
      `check-qml-api.py`, `check-code-quality.py --changed origin/main`); pytest covers record
      selection, hash checks, pivot planning and the language lists.

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`, UI in
Portuguese.

1. Open an English article: button shows; Translate: download progress, then Portuguese text.
2. Show Original; Translate again: instant, no download.
3. Turn the network off, open another English page and translate: works.
4. Open a German page: translates through English (two pairs in Manage Languages).
5. Always Translate English: the next English page is translated on load. Never Translate the
   site: no button there. In a private tab, the menu has no Always/Never.

## Out of scope

- Online translation services (Google, DeepL, Microsoft): rejected, see Decisions.
- Translating selected text only, PDFs, images, page titles in the tab strip.
- Settings page for translation (the panel and Manage Languages cover it).

## Dependencies

- None.

## Prototype

- [`441-translate-offer.qml`](../../prototypes/441-translate-offer.qml) →
  [screenshot](../../prototypes/screenshots/441-translate-offer.png)
- [`441b-translate-menu.qml`](../../prototypes/441b-translate-menu.qml) →
  [screenshot](../../prototypes/screenshots/441b-translate-menu.png)
- [`441c-translate-downloading.qml`](../../prototypes/441c-translate-downloading.qml) →
  [screenshot](../../prototypes/screenshots/441c-translate-downloading.png)
- [`441d-page-translated.qml`](../../prototypes/441d-page-translated.qml) →
  [screenshot](../../prototypes/screenshots/441d-page-translated.png)
- [`441e-manage-languages.qml`](../../prototypes/441e-manage-languages.qml) →
  [screenshot](../../prototypes/screenshots/441e-manage-languages.png)

## Decisions

| Question | Decision |
| --- | --- |
| Online service or on the device? | On the device (maintainer's choice). Google and DuckDuckGo/Edge's Microsoft endpoints are unofficial and can break; DeepL and Azure need each user's account and key; Microsoft's whole-page translation site no longer exists; Google's page proxy cannot see pages behind a login and sends the address to Google. |
| Which engine? | Mozilla's Bergamot (MPL-2.0), the files Firefox uses, from Mozilla's Remote Settings: no vendored binaries, about 25–40 MB per pair, 100+ pairs. |
| Open the panel automatically? | No: only the address bar button, so pages are not interrupted (KDE HIG); "Always Translate" covers the automatic case. |
| Language detection? | The page's `lang` first, `langdetect` only when it is missing: small, pure Python, no extra download. |
