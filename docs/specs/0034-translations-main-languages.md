# Translations for the main KDE languages (#34)

> **Issue:** [#34](https://github.com/lukasborges/kondor/issues/34) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Ship Kondor in the main languages of the KDE community, the way most KDE applications do, instead of only English and Brazilian Portuguese. Every language must be complete, and it must stay complete as new features add strings.

## Context

Issue #19 (merged in `37fa64e`) built the whole mechanism:

- English source strings in `qsTr()`;
- `qt_add_translations(kondor TS_FILES i18n/kondor_pt_BR.ts …)` in `CMakeLists.txt`, with the `.qm` files embedded under `:/i18n`;
- the `update_translations` target;
- in `src/main.cpp`, a `QTranslator` for `kondor_<locale>` plus one for Qt's own `qt_<locale>`, both chosen from the system locale;
- `setHttpAcceptLanguage()` in `ProfileManager`.

`i18n/kondor_pt_BR.ts` has 101 messages, all finished. Only pt_BR exists. Unlike real KDE apps, Kondor has no translator community, so the developer agent writes the translations itself.

## Design / behavior

1. **Languages.** Add one `.ts` file per language below, with the file name using the locale code shown. These are the KDE languages with the most complete translations of the core applications.

   | Code | Language | Code | Language |
   | --- | --- | --- | --- |
   | `ca` | Catalan | `pl` | Polish |
   | `cs` | Czech | `pt_PT` | Portuguese (Portugal) |
   | `de` | German | `ru` | Russian |
   | `es` | Spanish | `sv` | Swedish |
   | `fr` | French | `tr` | Turkish |
   | `it` | Italian | `uk` | Ukrainian |
   | `ja` | Japanese | `zh_CN` | Chinese (Simplified) |
   | `ko` | Korean | `zh_TW` | Chinese (Traditional) |
   | `nl` | Dutch | `pt_BR` | Portuguese (Brazil), already exists |

   Add them to `TS_FILES` in `CMakeLists.txt`, keeping alphabetical order. Generate each file with the `update_translations` target, then fill in every message.
2. **Translation quality.**
   - Use the terminology KDE translation teams already use in each language: for example "Einstellungen" / "Lesezeichen" in German, "Paramètres" / "Marque-pages" in French, and the matching menu wording.
   - When a KDE application's `.mo` file is installed for a language (`/usr/share/locale/<lang>/LC_MESSAGES/*.mo`), you may read it with `msgunfmt` as a glossary. Never copy whole files.
   - Keep the placeholders (`%1`, `%n`) and the `&` accelerators. Every message must contain the same placeholders as its source.
   - Fill in every plural form (`numerus="yes"`) that the language needs: for example 3 forms for Russian, Ukrainian, Polish and Czech, and 1 for Japanese, Korean and Chinese.
   - Leave no message `type="unfinished"` or empty. `lrelease` skips unfinished messages, which would silently show English instead.
3. **Layout.** Longer languages (German, Dutch, Russian) must not truncate toolbar tooltips, menu items, the find bar, settings labels or the downloads panel. Fix any truncation through layout (`Layout.fillWidth`, `elide` only where text is secondary). Do not shorten source strings.
4. **Keeping them complete (CI).** In `.github/workflows/build.yml`, after "Build", add a step "Check translations" that runs `cmake --build build --target update_translations` and then fails when either:
   - `git diff --exit-code -- i18n/` shows a change, meaning a source string was added or changed without updating the `.ts` files; or
   - any `i18n/*.ts` contains `type="unfinished"` or an empty `<translation>` / `<numerusform>`.

   Print the file and source text of each offending message.
5. **Docs.**
   - README "Translations": list the shipped languages and explain the CI check.
   - `AGENTS.md` already requires that new user-visible strings be translated in every `i18n/*.ts` file in the same PR. Follow it here and in every later issue.
6. **Locale fallback.** No code change is expected: `QTranslator::load(QLocale(), …)` already tries `de_DE` → `de` and `zh_TW` → `zh_TW`. Verify it with the manual test, including `pt_PT` (which must not fall back to `pt_BR`) and `zh_TW` (which must not fall back to `zh_CN`).

## Acceptance criteria

- [ ] The 17 new `.ts` files exist, are listed in `TS_FILES` and have no unfinished or empty messages, with plural forms complete.
- [ ] With `LANG=<lang>.UTF-8` (for example `de_DE`, `fr_FR`, `ru_RU`, `ja_JP`, `zh_TW`, `pt_PT`), every menu, tooltip, bar, dialog and panel is in that language. Qt's own strings follow it as well when Qt ships that language.
- [ ] No text is cut off in German or Russian in the main window, menu, find bar, settings, history and downloads.
- [ ] The "Check translations" CI step passes, and fails when a `qsTr()` string is added without translations. Show that in the PR by describing a local run.
- [ ] README lists the languages.

## Manual test

Use an isolated profile, as `AGENTS.md` requires. For each of `de_DE`, `ru_RU`, `ja_JP`, `zh_TW` and `pt_PT`, run `LANG=<lang>.UTF-8 ./build/kondor` and open:
- the main menu;
- New Tab and New Private Tab;
- the find bar (Ctrl+F);
- Settings, History and Downloads.

Check the wording and look for truncation. Screenshots of German and Japanese in the PR are welcome.

## Out of scope

- Right-to-left languages (Arabic, Hebrew), which need a separate layout-mirroring pass.
- A language selector in Settings: the system locale decides.
- Translating web content.
- Moving to KDE i18n (ki18n) or to KDE's translation infrastructure.

## Dependencies

#19 (merged).

## Prototype

No new UI, so there is no prototype.

## Decisions

| Question | Decision |
| --- | --- |
| Which languages? | The 17 listed above plus the existing pt_BR, chosen by the maintainer's request to cover "the main languages, like most KDE apps". RTL languages come later in their own issue. |
| Who keeps them complete? | Every PR that adds or changes a user-visible string updates all `i18n/*.ts` files; the CI "Check translations" step enforces it. |
