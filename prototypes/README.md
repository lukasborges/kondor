# Kondor UI prototypes

Static **QML** mockups of every roadmap feature that has a user interface, built with the real
`org.kde.desktop` (Breeze) style, Kirigami and Breeze icons, following the
[KDE Human Interface Guidelines](https://develop.kde.org/hig/).

They are the **visual target** for each issue: when implementing an issue, match the screenshot and
reuse the QML structure (controls, Kirigami components, icon names, spacing). They contain fake
data and no logic — never import them from the app.

## Render

```bash
python3 prototypes/render.py          # all prototypes → prototypes/screenshots/*.png
python3 prototypes/render.py 05       # only files whose name contains "05"
```

Needs `python3-pyqt6` built against the same Qt as the system, plus `kf6-kirigami`,
`kf6-qqc2-desktop-style`, `plasma-integration` and `breeze-icon-theme`. It renders offscreen.

Tips when editing:
- Popups and menus must set `popupType: Popup.Item` and call `open()` in `Component.onCompleted`,
  otherwise they are not captured.
- `common/BrowserFrame.qml` reproduces `qml/Main.qml` (tab bar, toolbar, address bar) with slots:
  `addressLeft`, `addressRight`, `toolbarExtras`, `belowHeader` and the page content (default
  property). Popups placed in the page are positioned relative to the page area (negative `y`
  reaches the toolbar).
- `common/FakePage.qml` is a generic web page; `<mark>`/`<cur>` in its texts render search highlights.

## Prototypes by issue

| Issue | Prototype(s) |
| --- | --- |
| #1 Browsing history | `01-history.qml` |
| #2 Bookmarks | `02-bookmarks.qml`, `02b-bookmarks-manager.qml` |
| #3 Settings page (layout from #57) | `03-settings.qml`, `03b-settings-privacy.qml` (shared mock in `common/SettingsDialogMock.qml`) |
| #4 Download manager | `04-downloads.qml` |
| #5 Find in page | `05-find-in-page.qml` |
| #6 Session restore | `00-main-menu.qml` ("Reopen Closed Tab"), `03-settings.qml` ("On Startup") |
| #7 Site permissions | `07-permissions.qml`, `07b-site-permissions-dialog.qml` |
| #8 Fullscreen | `08-fullscreen.qml` |
| #9 Security indicator / certificate errors | `09-security-indicator.qml`, `09b-certificate-error.qml` |
| #11 Address bar suggestions | `11-address-suggestions.qml` |
| #47 Default bookmarks | `02-bookmarks.qml` (toolbar) |
| #44 Address bar: visit or search | `44-address-visit-or-search.qml` |
| #53 About window | `53-about.qml`, `53b-about-components.qml`, `53c-about-authors.qml` (shared mock in `common/AboutDialogMock.qml`) |
| #12 Tab management | `12-tab-management.qml` |
| #83 Tab sizing and scroll arrows | `83-tab-sizing.qml`, `83b-tab-sizing-shrunk.qml`, `83c-tab-sizing-scroll.qml` (BrowserFrame `tabWidth` / `tabScrollButtons`) |
| #89 App icon without horns | `screenshots/89-icon-without-horns.png` (current icon, target icon, and the target at 48/32/22/16 px), `screenshots/89b-icon-size-in-panel.png` (32 px on a dark panel: current and target next to Dolphin, Firefox and Konqueror) |
| #13 Page context menu | `13-page-context-menu.qml` |
| #14 Multiple windows | `14-private-window.qml`, `00-main-menu.qml` |
| #16 Developer tools | `16-devtools.qml` |
| #17 Print / save as PDF | `00-main-menu.qml` |
| #18 Crashed page | `18-crashed-tab.qml` |
| #20 Ad and tracker blocking | `20-adblock.qml` |
| #21 Passwords | `21-passwords.qml`, `21b-passwords-settings.qml`, `21c-passwords-never-saved.qml`, `21d-passwords-wallet-denied.qml` (Settings page, in `common/SettingsDialogMock.qml`) |
| #22 Reader mode | `22-reader-mode.qml` |
| #23 Spell checking | `23-spellcheck.qml` |
| #24 Per-site zoom | `24-site-zoom.qml` |
| #43 New Tab page | `43-new-tab-page.qml`, `43b-new-private-tab-page.qml`, `03-settings.qml` ("Home Page", "New Tabs") |
| #93 Main menu (target layout) | `00-main-menu.qml`, `93b-main-menu-history.qml`, `93c-main-menu-tools.qml`, `93d-main-menu-help.qml` (shared mock in `common/MainMenuMock.qml`; `common/SubmenuMock.qml` draws an open submenu) |
| #102 Add a password by hand | `102-passwords-add.qml`, `102b-passwords-add-duplicate.qml`, `102c-passwords-empty.qml`, `102d-passwords-no-match.qml` (in `common/SettingsDialogMock.qml`) |
| #106 Import passwords | `106-passwords-import.qml`, `106b-passwords-import-unrecognized.qml`, `106c-passwords-imported.qml`, `102c-passwords-empty.qml` (new explanation) (in `common/SettingsDialogMock.qml`) |
| #107 Kondor extensions | `107-extensions.qml`, `107b-extensions-empty.qml`, `107c-extensions-catalog.qml`, `107d-extensions-install.qml`, `107e-extensions-install-file.qml` (in `common/SettingsDialogMock.qml`), `107f-extensions-menu.qml` (`common/ExtensionsMenuMock.qml`) |
| #176 Copy saved user name and password | `176-passwords-copy.qml` |
| #183 Extensions panel | `183-extensions-panel.qml`, `183b-extensions-panel-actions.qml` (`common/ExtensionsPanelMock.qml`) |

Issues without UI (#10 default browser, #15 single instance, #19 translations, #25 Flatpak,
#26 tests) have no prototype.
