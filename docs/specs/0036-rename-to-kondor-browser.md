# Rename the app to Kondor Browser (#36)

> **Issue:** [#36](https://github.com/lukasborges/kondor/issues/36) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Change the name users see from "Kondor" to **"Kondor Browser"**, translated in each language. For example, in Brazilian Portuguese it becomes "Navegador Kondor". Only the display name changes. Technical identifiers stay the same, so existing installs keep their settings, history and file associations.

## Context

The name is hardcoded in several user-visible strings on `main`:

| Where | String |
| --- | --- |
| `qml/Main.qml` | window title `t.title + " — Kondor"` / `qsTr("Kondor")` |
| `qml/Main.qml` | `qsTr("Quit Kondor")` |
| `qml/Main.qml` | `qsTr("Configure Kondor…")` |
| `qml/Main.qml` | `qsTr("About Kondor")` |
| `qml/HistoryWindow.qml` | `qsTr("History — Kondor")` |
| `qml/SettingsWindow.qml` | `qsTr("Configure — Kondor")` |
| `src/notifier.cpp` | notification `app_name` `"Kondor"` |
| `packaging/kondor.desktop` | `Name=Kondor` |

Other places use "Kondor" as an identifier and **must not change**:
- `QCoreApplication::setApplicationName("Kondor")` and `QSettings("KDE", "Kondor")`, which set the config and data paths;
- the binary name `kondor`;
- `kondor.desktop`, `Icon=kondor` and `StartupWMClass=kondor`;
- `setDesktopFileName("kondor")`;
- the QML module `Kondor`;
- the CMake `project(Kondor …)`;
- the user-agent token `Kondor/0.1`.

## Design / behavior

1. **One translatable name.**
   - In `src/main.cpp`, right after the translators are installed, call `QGuiApplication::setApplicationDisplayName(QCoreApplication::translate("Kondor", "Kondor Browser"))`.
   - Add a `//: Application display name: translate "Browser", keep "Kondor"` translator comment so it reaches the `.ts` files with context.
   - Every other place reads the name from there: `Qt.application.displayName` in QML, and `QGuiApplication::applicationDisplayName()` in C++.
2. **Strings that contain the name** use a placeholder, so the name is translated in exactly one message:
   - window title: `t.title + " — " + Qt.application.displayName`, or just `Qt.application.displayName` when the tab has no title. KDE separates the document and app name with an em dash.
   - `qsTr("Quit %1").arg(Qt.application.displayName)`
   - `qsTr("Configure %1…").arg(Qt.application.displayName)`
   - `qsTr("About %1").arg(Qt.application.displayName)`
   - `qsTr("History — %1").arg(Qt.application.displayName)`
   - `qsTr("Configure — %1").arg(Qt.application.displayName)`
   - Add a `//:` translator comment on each one saying that `%1` is the application name.
3. **Notifications:** `Notifier` passes `QGuiApplication::applicationDisplayName()` as `app_name`. Keep `app_icon` = `kondor`.
4. **Desktop entry** (`packaging/kondor.desktop`):
   - `Name=Kondor Browser`
   - `Name[pt_BR]=Navegador Kondor`, plus `GenericName[pt_BR]=Navegador web` and `Comment[pt_BR]=Um navegador web leve para Qt/KDE`
   - Keep `GenericName=Web Browser`.
   - The other languages' `Name[…]` entries are added by #34.
5. **pt_BR:**
   - Run `update_translations`. Translate "Kondor Browser" → **"Navegador Kondor"**.
   - Translate the new placeholder messages: "Sair do %1", "Configurar o %1…", "Sobre o %1", "Histórico — %1", "Configurar — %1". Because "Navegador" is masculine, the article "o" is correct.
   - `-no-obsolete` drops the old messages.
6. **AppImage file name.** linuxdeploy builds the output name from the desktop `Name`, which would become `Kondor_Browser-x86_64.AppImage` and break `gh release create … Kondor-*.AppImage`.
   - In `release.yml` "Create AppImage", set `LDAI_OUTPUT: Kondor-x86_64.AppImage` (and `OUTPUT` with the same value, for older plugin versions), so the file name stays the same.
   - Change the release title to `"Kondor Browser $GITHUB_REF_NAME"`.
7. **README.md** uses the new name wherever it refers to the app:
   - the title `# Kondor Browser`;
   - the logo and screenshot `alt` texts ("Kondor Browser logo", "Kondor Browser screenshot");
   - the opening description;
   - prose such as "Kondor loads the translation…" → "Kondor Browser loads…";
   - the shortcut table ("Configure Kondor Browser (settings)");
   - the release/AppImage section.

   Keep `kondor` wherever it is an identifier: commands (`./build/kondor`), paths (`~/.config/KDE/Kondor.conf`, `kondor.desktop`) and file names (`Kondor-x86_64.AppImage`). Also update `AGENTS.md`'s first line ("Kondor is…" → "Kondor Browser is…"), which the architect owns. Mention in the PR that it needs the architect, and do not edit it yourself.

## Acceptance criteria

- [ ] With `LANG=en_US.UTF-8`:
  - the window title is "<page title> — Kondor Browser";
  - the menu shows "Configure Kondor Browser…" and "About Kondor Browser";
  - the quit dialog says "Quit Kondor Browser";
  - History and Settings windows are titled "History — Kondor Browser" and "Configure — Kondor Browser";
  - desktop notifications show "Kondor Browser".
- [ ] With `LANG=pt_BR.UTF-8`, the same places show "Navegador Kondor":
  - "<título> — Navegador Kondor";
  - "Configurar o Navegador Kondor…";
  - "Sobre o Navegador Kondor";
  - "Sair do Navegador Kondor";
  - "Histórico — Navegador Kondor".
- [ ] The application launcher shows "Kondor Browser" (or "Navegador Kondor" in pt_BR). Settings, history, cookies and the default-browser association from a previous version are still there: same config file `~/.config/KDE/Kondor.conf` and same data directory.
- [ ] No user-visible "Kondor" string is left without "Browser", except the user-agent token.
- [ ] `README.md` says "Kondor Browser" in its title, image alt texts, description and prose. `kondor` remains only in commands, paths and file names.
- [ ] The release workflow still produces `Kondor-x86_64.AppImage`. Check it with a local linuxdeploy run or by reading the plugin's documented variable, and say which in the PR.

## Manual test

Use an isolated profile (see `AGENTS.md`).
1. Run `LANG=en_US.UTF-8 ./build/kondor`, then `LANG=pt_BR.UTF-8 ./build/kondor`.
2. In each, check the window title, the menu, the quit dialog (Ctrl+Q with 2+ tabs, if it applies) and the History and Settings windows.
3. Start a download to see the notification.
4. Run `desktop-file-validate packaging/kondor.desktop`.

## Out of scope

- Changing any identifier listed in Context.
- Adding an About dialog. The menu item keeps its current behavior, only its text changes.
- Translations into languages other than pt_BR (that is #34).

## Dependencies

#19 (merged). It must land **before #34**, so that #34 translates the new messages.

## Prototype

No new UI, so there is no prototype. Only the text changes.

## Decisions

| Question | Decision |
| --- | --- |
| README too? | Yes (maintainer): title, alt texts, description, prose and the shortcut table use "Kondor Browser"; commands/paths/file names keep `kondor`. |
| Display name only, or identifiers too? | Display name only (maintainer's request: "Kondor Browser", translated per language, e.g. "Navegador Kondor"). Identifiers stay so existing settings and associations survive. |
