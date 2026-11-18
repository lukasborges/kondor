# Page capture: save or copy an image of the page (#410)

> **Issue:** [#410](https://github.com/lukasborges/kondor/issues/410) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Take an image of the current page, the visible area or the whole page, and copy it or save it as
PNG, without leaving Kondor or opening Spectacle.

## Context

- Page output (print, PDF): `qml/browser/view/PageOutput.qml`, file dialogs in
  `qml/app/window/PageFileDialogs.qml`. Commands follow the Tab bridge pattern (`Tab` command +
  `…Requested` signal, handled in `qml/browser/view/TabCommands.qml`).
- Page context menu: `qml/browser/contextmenu/`; main menu "More Tools" in
  `qml/app/menu/MainMenu.qml`; actions in `qml/app/BrowserActions.qml`.

## Design / behavior

### 1. Entry points (`prototypes/410b-screenshot-context-menu.qml`)

- Action **Take Screenshot…** (`select-rectangular`, **Ctrl+Shift+S**, free today): in the page
  context menu (page background, after Print…) and in More Tools (after Save as PDF…). Disabled
  on the New Tab page, error pages and while the page has not loaded anything.

### 2. Dialog (`prototypes/410-take-screenshot.qml`)

- A modal dialog "Take Screenshot". On open it captures the **visible area** at once (the page
  view only, never the toolbars) and shows it scaled to fit, with its size in pixels under it.
- Two exclusive buttons at the top: **Visible Area** (`select-rectangular`, default) and **Full
  Page** (`zoom-fit-page`); choosing one captures again (a `BusyIndicator` over the preview while
  it works).
- **Full page:** read the document size with `runJavaScript`
  (`document.documentElement.scrollWidth/Height`), lay the view out at that height behind the
  modal dialog, wait for two frames, `grabToImage`, and restore the view and its scroll position.
  The height is capped at 16384 device pixels; when cut, the size label adds "(cut at 16384 px)".
  If the developer finds a direct Qt WebEngine API for it (checked on 6.11), use it and say so in
  the PR.
- Buttons: **Copy** (`edit-copy`, puts the PNG on the clipboard; its icon becomes `checkmark` for
  2 s, tooltip "Copied"), **Save…** (`document-save`, the default button: a file dialog in the
  Pictures folder with the name `<page title> <yyyy-MM-dd hh.mm.ss>.png`, title cleaned of
  characters not allowed in file names), **Close**. Esc closes. The dialog stays open after Copy,
  closes after a successful Save.

### 3. Privacy

- Nothing is written to disk unless the user saves; private tabs work the same. The image stays
  in memory only while the dialog is open.

## Acceptance criteria

- [ ] Ctrl+Shift+S, the context menu and More Tools open the dialog with the visible area; the
      toolbars are not in the image.
- [ ] Full Page captures a long page (e.g. a Wikipedia article) top to bottom; the view returns
      to the same scroll position; pages over 16384 px are cut and say so.
- [ ] Copy puts an image on the clipboard (paste in another app) and shows the check mark; Save…
      writes a PNG with the suggested name.
- [ ] Zoomed pages (150 %) and HiDPI capture at device pixels.
- [ ] Matches `410-take-screenshot.png` and `410b-screenshot-context-menu.png`, Breeze and Breeze
      Dark.
- [ ] Strings in `qsTr()`, translations complete; README shortcut table and the "Print" bullet
      (Reading) updated.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`; save into
that folder.

1. On kde.org, Ctrl+Shift+S: preview of the visible page; Copy, paste in Okular or KolourPaint.
2. Full Page on a long Wikipedia article: the whole article; Save…; open the PNG.
3. Private tab: same, and nothing appears in the profile folder.

## Out of scope

- Selecting a region or an element, annotating, uploading or sharing, capturing video.

## Dependencies

- None.

## Prototype

- [`prototypes/410-take-screenshot.qml`](../../prototypes/410-take-screenshot.qml) →
  [screenshot](../../prototypes/screenshots/410-take-screenshot.png)
- [`prototypes/410b-screenshot-context-menu.qml`](../../prototypes/410b-screenshot-context-menu.qml) →
  [screenshot](../../prototypes/screenshots/410b-screenshot-context-menu.png)

## Decisions

| Question | Decision |
| --- | --- |
| Capture right away or ask first? | Capture the visible area right away and show it: the common case takes one shortcut; Full Page is one click more. |
| Hand the job to Spectacle? | No: Spectacle cannot capture beyond the visible area of a page, and Kondor runs on other desktops too. |
| Save folder | Pictures, like Spectacle; the downloads folder is for files from the web. |
| Approved | Prototypes approved by the maintainer. |
