# Use Kondor as the default browser (#10)

> **Issue:** [#10](https://github.com/lukasborges/kondor/issues/10) · **Priority:** P1 (high) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Make Kondor usable as the system default browser: it must open URLs/files passed on the command line and be listed (and work) in System Settings → Default Applications.

## Context

- `packaging/kondor.desktop` has `Exec=kondor` (no `%U`) but already declares `MimeType=x-scheme-handler/http;x-scheme-handler/https;`.
- `src/main.cpp` ignores `argv`; `Main.qml` always opens the home page.

## Design / behavior

1. **Command line** in `src/main.cpp` with `QCommandLineParser`:
   - `parser.setApplicationDescription("Kondor web browser")`, `addHelpOption()`, `addVersionOption()` (set `QCoreApplication::setApplicationVersion(QStringLiteral(PROJECT_VERSION))` — add `target_compile_definitions(kondor PRIVATE PROJECT_VERSION="${PROJECT_VERSION}")` in CMake).
   - Option `--private` ("open URLs in a private tab").
   - Positional `urls` ("URLs or files to open").
   - Convert each positional argument with `QUrl::fromUserInput(arg, QDir::currentPath(), QUrl::AssumeLocalFile)`.
2. Pass the list to QML: expose `ProfileManager` (or a tiny `StartupArgs` singleton) property `Q_PROPERTY(QList<QUrl> startupUrls …)` + `bool startupPrivate`, set before `engine.loadFromModule`.
3. **`Main.qml` startup**: if `startupUrls.length > 0` open each in a tab (`tabs.addTab(startupPrivate, url)`) and skip the home page / session restore (#6: restore first, then add the URLs, like Firefox).
4. **Desktop file** `packaging/kondor.desktop`:
   ```ini
   Exec=kondor %U
   MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
   Actions=new-private-window;

   [Desktop Action new-private-window]
   Name=New Private Window
   Exec=kondor --private
   ```
   (Keep the existing keys. Validate with `desktop-file-validate packaging/kondor.desktop`.)
5. AppImage: `release.yml` copies the same desktop file, nothing else needed; README: add a short "Set as default browser" section (`System Settings → Default Applications → Web browser → Kondor`, or `xdg-settings set default-web-browser kondor.desktop`).
### Edge cases

- Arguments that are not URLs (`kondor some words`) → search via `ProfileManager.resolveAddress()` like the address bar.
- Relative file paths are resolved against the current directory.
- When another instance is already running, opening in the existing window is handled by #15 (not here).

## Acceptance criteria

- [ ] `kondor https://kde.org` opens that page instead of the home page; several URLs open several tabs.
- [ ] `kondor ./page.html` opens the local file; `kondor --private https://kde.org` opens a private tab.
- [ ] `kondor --help` / `--version` work.
- [ ] After `xdg-settings set default-web-browser kondor.desktop`, clicking a link in another app (e.g. Konsole, KMail) opens it in Kondor.
- [ ] `desktop-file-validate` passes.

## Manual test

Run the commands above from a terminal; install with `cmake --install` and set as default browser in System Settings; click a link in Konsole.

## Out of scope

Single-instance forwarding (#15), new window support (#14).

## Dependencies

None. #15 builds on this.

## Prototype

No UI for this issue, so there is no prototype.

## Decisions

_None yet._ Answers to developer questions (`question` label) are recorded here as `| Question | Decision |` rows.
