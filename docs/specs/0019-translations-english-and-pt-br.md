# Translations (English and pt_BR) (#19)

> **Issue:** [#19](https://github.com/lukasborges/kondor/issues/19) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Make the UI translatable with English as the source language and ship a Brazilian Portuguese translation, loaded according to the system locale.

## Context

The project standard is **English everywhere** (see `AGENTS.md`), but the original UI strings are Portuguese literals inside `qsTr()` in `qml/Main.qml` (e.g. `qsTr("Nova aba")`, `qsTr("Pesquisar ou digitar um endereço")`), many code comments in `src/` and `qml/` are Portuguese, there are no `.ts` files and nothing loads a `QTranslator`. The `Tab` uncreatable reason in `src/tab.h` is also Portuguese. Features merged after `AGENTS.md` already use English strings.

## Design / behavior

1. **Switch source strings and code comments to English** in every QML/C++/CMake/YAML file (e.g. "New Tab", "New Private Tab", "Close Tab", "Back", "Forward", "Reload", "Stop", "Home", "Search or enter address", "Zoom In", "Zoom Out", "Actual Size", "About Kondor", "Menu"). Use KDE HIG wording (Title Case for menu items and buttons, sentence case for labels/placeholders).
2. **CMake**: add `LinguistTools` to `find_package(Qt6 …)` and:
   ```cmake
   qt_add_translations(kondor
       TS_FILES i18n/kondor_pt_BR.ts
       RESOURCE_PREFIX /i18n
       LUPDATE_OPTIONS -no-obsolete)
   ```
   (Qt ≥ 6.5 syntax; this embeds the `.qm` in the binary and adds the `update_translations` target.) Create `i18n/kondor_pt_BR.ts` by running `cmake --build build --target update_translations`, then fill every `<translation>` with the current Portuguese text (they are exactly the strings being replaced in step 1).
3. **Loading** in `src/main.cpp`, after creating the app and before the QML engine:
   ```cpp
   QTranslator appTranslator;
   if (appTranslator.load(QLocale(), QStringLiteral("kondor"), QStringLiteral("_"), QStringLiteral(":/i18n")))
       app.installTranslator(&appTranslator);
   QTranslator qtTranslator;   // Qt's own strings (dialogs, context menus)
   if (qtTranslator.load(QLocale(), QStringLiteral("qt"), QStringLiteral("_"),
                         QLibraryInfo::path(QLibraryInfo::TranslationsPath)))
       app.installTranslator(&qtTranslator);
   ```
   Also set `profile->setHttpAcceptLanguage(QLocale().bcp47Name())` in `ProfileManager::setupProfile()` so sites get the right language.
4. **AppImage**: Qt base translations come from `/usr/share/qt6/translations` (already copied in `release.yml`); the app's own `.qm` is embedded — nothing else to do. Verify.
5. **Docs**: README section "Translations": how to update (`update_translations` target), how to add a language (new `i18n/kondor_<lang>.ts` in `TS_FILES`).
6. Plurals: use `qsTr("%n tab(s)", "", count)` style where counts appear (e.g. downloads, find results "%1 of %2" with `.arg()`).

## Acceptance criteria

- [ ] All source strings and code comments are English; no Portuguese text remains outside `.ts` files.
- [ ] With `LANG=pt_BR.UTF-8` the UI is fully Portuguese; with `LANG=en_US.UTF-8` (or any other) it is English.
- [ ] Qt's own dialogs/menus follow the locale.
- [ ] `update_translations` target works and README explains it.

## Manual test

`LANG=pt_BR.UTF-8 ./build/kondor` and `LANG=en_US.UTF-8 ./build/kondor`; open every menu and dialog in both.

## Out of scope

Additional languages, translating web content, KDE i18n (ki18n) migration.

## Dependencies

Do it **before** or **after** the big UI issues, not in parallel with them, to avoid merge conflicts on every string. Every issue merged after this one must add its new strings to the `.ts` file.

## Prototype

No UI for this issue, so there is no prototype.

## Decisions

_None yet._ Answers to developer questions (`question` label) are recorded here as `| Question | Decision |` rows.
