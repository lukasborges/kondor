# Native Windows build (#121)

> **Issue:** [#121](https://github.com/lukasborges/kondor/issues/121) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Build and publish Kondor as a native Windows x86_64 application: a self-contained folder, zipped
as `Kondor-windows-x86_64.zip` and attached to every release, with the same Breeze look as on
Plasma. Linux builds (plain, AppImage, Flatpak) must behave exactly as today.

## Context

- The maintainer built `main` at `99ac4b3` on Windows 11 with MSVC 2022 against
  [KDE Craft](https://community.kde.org/Craft) (target `windows-cl-msvc2022-x86_64`, binary cache,
  Qt 6.11.2): it compiles, starts, browses and passes the offscreen smoke test with no QML errors.
  Those code changes are not on any branch; the issue body lists them and this spec takes them over.
- Linux-only code today:
  - `src/main.cpp`: finds the spell checking dictionaries through `/proc/self/exe` before the
    `QApplication` exists; relies on the KDE platform theme for the Breeze style, icons and colors.
  - `src/notifier.cpp`: `org.freedesktop.Notifications` over D-Bus (no session bus on Windows).
  - `src/downloadmanager.cpp` (`showInFolder`): `org.freedesktop.FileManager1` over D-Bus, falling
    back to opening the folder.
  - `src/singleinstance.cpp` (`serverName()`): a socket path in `RuntimeLocation`.
  - `CMakeLists.txt`: Hunspell dictionaries read from `/usr/share/hunspell`.
- CI: `.github/workflows/build.yml` (Fedora container, `build` job) and `release.yml` (AppImage +
  Flatpak). Neither agent machine runs Windows, so the Windows build is verified **only in CI** and
  by the maintainer's manual test on Windows 11.

## Design / behavior

All Windows code is guarded: `if(WIN32)` in CMake, `#ifdef Q_OS_WIN` in C++. No new dependency or
behavior on Linux.

1. **Dependencies (Craft)**. Packages: `libs/qt6/qtwebengine`, `libs/qt6/qttools`,
   `kde/frameworks/tier1/kirigami`, `kde/frameworks/tier3/kwallet`,
   `kde/frameworks/tier3/qqc2-desktop-style`, `kde/frameworks/tier1/breeze-icons`,
   `kde/frameworks/tier3/kiconthemes`, `kde/frameworks/tier3/kconfigwidgets`, `kde/plasma/breeze`
   (use the exact package paths Craft reports; these names are the trial's). Write them once in
   `packaging/windows/craft-packages.txt` (one per line), read by CI and by the README steps.
2. **CMake** (`CMakeLists.txt`), inside `if(WIN32)`:
   - `find_package(KF6IconThemes REQUIRED)` and `find_package(KF6ConfigWidgets REQUIRED)`, linked
     as `KF6::IconThemes` and `KF6::ConfigWidgets`.
   - `set_target_properties(kondor PROPERTIES WIN32_EXECUTABLE ON)` (no console window).
   - Application icon and version info: add `packaging/windows/kondor.ico` (16, 24, 32, 48 and
     256 px, generated from `packaging/kondor.svg`, e.g.
     `magick -background none packaging/kondor.svg -define icon:auto-resize=256,48,32,24,16 packaging/windows/kondor.ico`,
     and committed) and `packaging/windows/kondor.rc.in` (`IDI_ICON1 ICON "…/kondor.ico"` plus a
     `VERSIONINFO` with `ProductName`/`FileDescription` "Kondor Browser", `CompanyName` "KDE",
     `OriginalFilename` "kondor.exe", file and product version from `PROJECT_VERSION`), turned into
     `kondor.rc` with `configure_file()` and added to the `kondor` target's sources.
   - Spell checking: replace the hard-coded `/usr/share/hunspell` with a cache variable
     `KONDOR_HUNSPELL_DIR` (default `/usr/share/hunspell`, so Linux is unchanged). On Windows the
     `.bdic` files are installed to `${CMAKE_INSTALL_BINDIR}/qtwebengine_dictionaries` (next to
     `kondor.exe`, the second candidate `src/main.cpp` already checks); on Linux the install
     destination stays `${CMAKE_INSTALL_DATADIR}/kondor`.
3. **Executable directory** (`src/main.cpp`): on Windows the dictionary lookup gets the executable
   path from `GetModuleFileNameW(nullptr, …)` instead of `/proc/self/exe` (the `QApplication` does
   not exist yet). The candidate list is unchanged.
4. **Breeze look** (`src/main.cpp`, Windows only):
   - `KIconTheme::initTheme()` before the `QApplication` is constructed (Breeze icons, from
     `<KIconTheme>`).
   - `KStyleManager::initStyle()` right after it (Breeze QStyle and the color scheme matching the
     system light/dark mode, from `<KStyleManager>`).
   - Then wrap the application style in a small `QProxyStyle` subclass (in `src/main.cpp`'s
     anonymous namespace, or `src/windowsstyle.{h,cpp}` registered in `CMakeLists.txt`) whose
     `pixelMetric(PM_ToolBarIconSize, …)` returns `22` (Plasma's default) and delegates everything
     else. Without it Qt's Windows default of 24 px makes Breeze pick the colored 32–256 px
     variants of icons like `go-home`.
   - `QQuickStyle::setStyle("org.kde.desktop")` stays as today.
5. **Notifications** (`src/notifier.cpp`): the public API (`Notifier::notify(title, body,
   iconName)`) does not change. On Windows it shows a toast with `QSystemTrayIcon::showMessage(title,
   body, QIcon(":/packaging/kondor.png"), 5000)`:
   - `Notifier` owns one `QSystemTrayIcon` (icon `:/packaging/kondor.png`, tool tip =
     `QGuiApplication::applicationDisplayName()`), created on the first notification.
   - It is shown only while notifications are recent: `show()` before `showMessage()`, and a
     single-shot `QTimer` (10 s, restarted on every notification) hides it again, so no permanent
     tray icon stays behind.
   - If `QSystemTrayIcon::isSystemTrayAvailable()` is false, do nothing (as today without D-Bus).
   - The D-Bus code path stays for every other platform.
6. **Show in folder** (`DownloadManager::showInFolder`): on Windows run
   `QProcess::startDetached("explorer.exe", {"/select," + QDir::toNativeSeparators(path)})`; if it
   fails to start, fall back to `QDesktopServices::openUrl` on the folder, as today.
7. **Single instance** (`SingleInstance::serverName()`): on Windows `QLocalServer` uses named pipes,
   which have no directory, so the name is `kondor-<profile hash>` (same 16-character hash of
   `AppDataLocation` as today; the hash already differs per user because that path contains the
   user's profile folder). `UserAccessOption` stays. Linux and Flatpak paths are unchanged.
8. **Passwords**: KWallet compiles but has no daemon or session bus on Windows. `PasswordStore`
   must end in its existing `"unavailable"` state (the "wallet denied" UI of #21) without hanging,
   crashing or blocking page loads. No other password backend in this issue.
9. **Settings and data**: Qt's Windows defaults stay: settings in the registry
   (`HKCU\Software\KDE\Kondor`), data and the web profile in `%APPDATA%\KDE\Kondor` /
   `%LOCALAPPDATA%\KDE\Kondor`, downloads in the user's Downloads folder.
10. **Packaging** (`packaging/windows/deploy.ps1`, PowerShell, used by CI and documented in the
    README). Arguments: the Craft root, the CMake build directory and the output folder. Steps:
    1. `cmake --install <build> --prefix <out>` (`kondor.exe` and the dictionaries in `bin\`).
    2. Copy Craft's Qt WebEngine resources from `<CraftRoot>\bin` (`qtwebengine_resources*.pak`,
       `qtwebengine_devtools_resources.pak`, `icudtl.dat`, `v8_context_snapshot.bin`) into
       `<CraftRoot>\resources`, where `windeployqt` looks for them, if they are not there already.
    3. `windeployqt --release --qmldir <repo>\qml --qmldir <CraftRoot>\qml\org\kde\desktop
       --dir <out>\bin <out>\bin\kondor.exe` (the second `--qmldir` because `org.kde.desktop` is set
       from C++, so import scanning does not find it).
    4. Copy the plugins `windeployqt` does not know about, keeping their relative paths under
       `<out>\bin`: `kf6\kirigami\platform\org.kde.desktop.dll`, `styles\breeze6.dll`,
       `kiconthemes6\iconengines\KIconEnginePlugin.dll`, `tls\qopensslbackend.dll`, and the data
       folder `data\color-schemes` (from `<CraftRoot>\bin\data`).
    5. Copy the non-Qt DLLs the executable and those plugins need from `<CraftRoot>\bin` (KF6,
       ICU, OpenSSL, zlib, …). Resolve them from the PE imports (`dumpbin /dependents`, recursively)
       instead of a hard-coded list, skipping DLLs that are part of Windows.
    6. Copy `LICENSE` to `<out>`, and write `<out>\README.txt` with one line on how to start Kondor
       (`bin\kondor.exe`).
    7. Fail (non-zero exit) when any of these is missing: `bin\kondor.exe`,
       `bin\QtWebEngineProcess.exe`, `bin\qtwebengine_dictionaries\en-US.bdic`,
       `bin\qtwebengine_dictionaries\pt-BR.bdic`, `bin\styles\breeze6.dll`,
       `bin\kf6\kirigami\platform\org.kde.desktop.dll`.
    The folder is zipped as `Kondor-windows-x86_64.zip` with `Kondor\` as its top-level folder.
11. **CI build** (`.github/workflows/build.yml`): new job `windows` on `windows-latest`, on the
    same triggers as `build`:
    - Restore/save `C:\CraftRoot` with `actions/cache@v4`, keyed on the hash of
      `packaging/windows/craft-packages.txt` and the Craft target.
    - Bootstrap Craft non-interactively for `windows-cl-msvc2022-x86_64` with the binary cache
      (Craft's `CraftBootstrap.py --prefix C:\CraftRoot --use-defaults`, or KDE's CraftMaster —
      whichever runs unattended), then `craft <packages>` from `craft-packages.txt`.
    - Hunspell dictionaries: download `en_US.{dic,aff}` and `pt_BR.{dic,aff}` from
      `https://github.com/LibreOffice/dictionaries` **at a pinned commit** into a temporary folder
      and pass it as `-DKONDOR_HUNSPELL_DIR`.
    - Configure (Ninja, `Release`, `-DBUILD_TESTING=OFF`) and build inside the Craft environment
      (`craftenv.ps1`), with `cmake --build build --parallel 4`.
    - Run `packaging/windows/deploy.ps1`, then the smoke test on the **deployed** folder:
      `QT_QPA_PLATFORM=offscreen`, run `bin\kondor.exe --new-instance` for 15 s, fail if its
      output contains `ReferenceError`, `TypeError`, `Cannot assign` or `is not a type`, or if it
      exits before the 15 s with a non-zero code.
    - Upload the zip as the workflow artifact `kondor-windows`.
12. **Release** (`.github/workflows/release.yml`): new job `windows` (needs `release`) doing the
    same build and packaging steps, then `gh release upload "$GITHUB_REF_NAME"
    Kondor-windows-x86_64.zip --clobber --repo "$GITHUB_REPOSITORY"`. Avoid copy-pasting the long
    steps twice: put the Craft setup and the build in a script (`packaging/windows/build.ps1`)
    called from both workflows.
13. **README**:
    - "Download": one line for Windows (download `Kondor-windows-x86_64.zip` from the latest
      release, unzip, run `Kondor\bin\kondor.exe`; not signed, so SmartScreen may warn).
    - "Requirements" / "Build and run": a short "Windows" subsection: install Craft, `craft` the
      packages of `packaging/windows/craft-packages.txt`, configure/build from the Craft
      environment, deploy with `packaging/windows/deploy.ps1`.
    - "Set as default browser": say it applies to Linux; on Windows it is not available yet.

## Acceptance criteria

- [ ] Linux: the `build` job, AppImage and Flatpak are unchanged in behavior; no new Linux
      dependency; no new warnings in touched files.
- [ ] The `windows` job of `build.yml` is green on the PR: it builds, deploys, passes the
      offscreen smoke test with no QML errors, and uploads `kondor-windows` with the zip.
- [ ] The zip contains `Kondor\bin\kondor.exe`, `QtWebEngineProcess.exe`, both `.bdic`
      dictionaries, the Breeze style, the Kirigami desktop platform plugin, the icon engine,
      `data\color-schemes`, `LICENSE` and `README.txt`.
- [ ] `kondor.exe` has the Kondor icon in Explorer and "Kondor Browser" in its file properties,
      and opens no console window.
- [ ] On Windows 11 (maintainer, from the CI artifact): Breeze style and icons, 22 px toolbar
      icons (monochrome `go-home`), light/dark follows the system; browsing, downloads, "Show in
      Folder" (Explorer with the file selected), a toast on download completion, spell checking in
      a text field, and a second launch with a URL opening it in the running window.
- [ ] Passwords show the existing "unavailable" state on Windows; nothing hangs.
- [ ] Tag builds attach `Kondor-windows-x86_64.zip` to the GitHub release.
- [ ] README updated as in step 13.

## Manual test

Developer (Linux): full build, `ctest`, offscreen smoke test on an isolated profile (`AGENTS.md`),
and a quick run to check nothing changed on Plasma. The Windows part is verified by the green
`windows` CI job and its artifact.

Maintainer (Windows 11, preferably a separate Windows user or after backing up
`HKCU\Software\KDE\Kondor` and `%APPDATA%\KDE\Kondor`, since `XDG_*` variables do not isolate a
profile on Windows): unzip the `kondor-windows` artifact, run `Kondor\bin\kondor.exe`, and go
through the Windows 11 acceptance criterion above in both light and dark mode.

## Out of scope

- An installer (NSIS, Inno Setup, MSIX), Start menu entries, file/URL associations and
  registering Kondor as the default browser on Windows (`StartMenuInternet`,
  `RegisteredApplications`).
- A Windows password backend (Credential Manager) or making KWallet run on Windows.
- Code signing, auto-update, winget/Chocolatey/Microsoft Store.
- Running `ctest` on Windows, ARM64 and 32-bit builds, MinGW.
- Isolating a test profile on Windows (no `KONDOR_*` profile override).
- Any change to Linux behavior.

## Dependencies

None (all features it touches are merged). Independent of #107/#108.

## Prototype

No UI for this issue, so there is no prototype.

## Decisions

| Question | Decision |
| --- | --- |
| Settings in the registry and data in `%APPDATA%` mean `XDG_*` does not isolate a test profile (open point) | Keep Qt's Windows defaults (registry + `%APPDATA%`/`%LOCALAPPDATA%`), like other KDE apps on Windows. Agents never run Kondor on Windows; CI runs on a fresh runner profile; the maintainer tests with a separate Windows user or a backup. No profile-override option. |
| Spell checking dictionaries on Windows (open point) | Built in CI from LibreOffice's Hunspell dictionaries at a pinned commit, through the new `KONDOR_HUNSPELL_DIR` cache variable, and installed next to `kondor.exe` in `qtwebengine_dictionaries`, which `src/main.cpp` already looks for. |
| Passwords / KWallet on Windows (open point) | Not supported in this issue: KWallet stays linked, and the feature must fall into the existing "unavailable" state. A Credential Manager backend would be its own issue. |
| Default browser on Windows (open point) | Out of scope: it needs registry entries an installer writes, and Windows only lets the user choose in "Default apps". The README says so. |
| Executable icon (open point) | `packaging/windows/kondor.ico` + `kondor.rc` (icon and `VERSIONINFO`) compiled into `kondor.exe`. |
| Installer or zip (open point) | Zip only (`Kondor-windows-x86_64.zip`); an installer is a later issue. |
| CI (open point) | `windows` job on `windows-latest` in `build.yml` (PRs and `main`) and in `release.yml` (tags), sharing `packaging/windows/build.ps1` and `deploy.ps1`, caching `C:\CraftRoot`. Its check must be green before the PR is approved, since neither agent can build on Windows. |
| Notifications through the tray icon (open point) | `QSystemTrayIcon::showMessage`, with the tray icon shown only around notifications (hidden 10 s after the last one), so Kondor does not keep a permanent tray icon. Verified by the maintainer on Windows 11. |
| KIconThemes / KConfigWidgets on Linux too? | No: they are only needed where there is no KDE platform theme. Both are found and linked only `if(WIN32)`, so the Linux packages, AppImage and Flatpak are unchanged. |
