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
| #13 Page context menu | `13-page-context-menu.qml` |
| #14 Multiple windows | `14-private-window.qml`, `00-main-menu.qml` |
| #16 Developer tools | `16-devtools.qml` |
| #17 Print / save as PDF | `00-main-menu.qml` |
| #18 Crashed page | `18-crashed-tab.qml` |
| #20 Ad and tracker blocking | `20-adblock.qml` |
| #21 Passwords | `21-passwords.qml` |
| #22 Reader mode | `22-reader-mode.qml` |
| #23 Spell checking | `23-spellcheck.qml` |
| #24 Per-site zoom | `24-site-zoom.qml` |
| #43 New Tab page | `43-new-tab-page.qml`, `43b-new-private-tab-page.qml`, `03-settings.qml` ("Home Page", "New Tabs") |
| — Target main menu | `00-main-menu.qml` (all menu entries added by the roadmap) |

Issues without UI (#10 default browser, #15 single instance, #19 translations, #25 Flatpak,
#26 tests) have no prototype.
