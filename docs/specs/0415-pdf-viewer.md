# Open PDF files in the tab, including PDFs embedded in pages (#415)

> **Issue:** [#415](https://github.com/lukasborges/kondor/issues/415) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Today every PDF link is downloaded, and a PDF embedded in a page (`<embed>`, `<iframe>`,
`<object>`) shows an empty box. Qt WebEngine ships Chromium's PDF viewer, but it needs
`pluginsEnabled`, which Kondor leaves at its default (off). Turn it on so PDFs open in the tab and
embedded PDFs render inside their pages (maintainer's request: embedded PDFs must work too).

## Context

- View settings: `qml/browser/view/PageView.qml` (`settings.fullScreenSupportEnabled` today).
- Downloads: `src/kondor/browser/profile/profilesetup.py` (`downloadRequested`), print:
  `qml/browser/view/PageOutput.qml` (`printRequested` → temporary PDF in the system viewer).
- Request interceptors: ad blocking (`src/kondor/adblock/`), browser identity
  (`src/kondor/site/identity/`).
- Desktop file: `packaging/kondor.desktop` (`MimeType=`).

## Design / behavior

1. `PageView.qml` sets `settings.pluginsEnabled: true` and `settings.pdfViewerEnabled: true`, for
   normal and private tabs alike.
2. **PDF links and addresses** (`application/pdf` responses) open in the tab with Chromium's
   viewer: page navigation, zoom, find, rotate, download and print buttons of the viewer. The
   address bar keeps the PDF's URL; the tab title is the document title or the file name. A
   response with `Content-Disposition: attachment` is still downloaded, as today.
3. **Embedded PDFs** render inside their page (`<embed type="application/pdf">`, `<object>`,
   `<iframe src="….pdf">`), including cross-origin ones.
4. **Local files**: `file:///…/x.pdf` (typed, dropped on the window, or opened with
   `kondor x.pdf`) opens in the viewer. `application/pdf` is added to `MimeType=` in
   `packaging/kondor.desktop`, so Kondor appears in "Open With"; it never makes itself the
   default PDF app.
5. The viewer's **download** button goes through Kondor's download manager (normal rules: ask
   where to save, notification, private downloads not listed after closing). Its **print**
   button and Ctrl+P use Kondor's existing print flow.
6. Nothing else changes: history records PDF URLs like any page (never for private tabs); the ad
   blocker and the browser identity interceptor must not block or alter the viewer's own
   resources (`chrome-extension://` and `chrome://` requests pass through untouched).

## Acceptance criteria

- [ ] A PDF link (e.g. `https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf`) opens in the tab; its download and print buttons work through Kondor.
- [ ] A local test page with a PDF in `<embed>`, `<object>` and `<iframe>` (same origin and another origin, served by the pytest's local HTTP servers) shows the three PDFs.
- [ ] `file:///…/x.pdf` and `kondor x.pdf` open in the viewer; Kondor is listed in Dolphin's "Open With" for PDFs.
- [ ] `Content-Disposition: attachment` PDFs are still downloaded.
- [ ] Works in private tabs, with ad blocking on, and with a custom browser identity (#376) for the site.
- [ ] README: one bullet under "Reading" ("**PDF viewer**: read PDFs, also those embedded in pages").
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`, `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`.

1. Open a PDF link: it shows in the tab; zoom, search, download (lands in the test folder), print.
2. Open a page that embeds a PDF: the PDF shows inside the page.
3. `kondor ~/kondor-test/x.pdf`: opens in a tab.

## Out of scope

- A Kondor-styled (Breeze) PDF viewer, PDF annotation or form saving beyond what Chromium's viewer does, a setting to always download PDFs or open them in Okular.

## Dependencies

- None.

## Prototype

- None: the viewer is Chromium's own and Kondor adds no UI.

## Decisions

| Question | Decision |
| --- | --- |
| Chromium's viewer in the tab, or Okular? | The viewer in the tab: it is the only way to show PDFs embedded in pages, which the maintainer requires; Okular remains one click away through Open With and the print flow. |
| Setting to always download PDFs? | No: the viewer has a download button, and a setting would add UI for a rare need. |
| Make Kondor the default PDF app? | No: only listed in Open With; the user's PDF app stays the default. |
| QtPdf (Breeze viewer) or PDF.js instead? | Considered and set aside by the maintainer: QtPdf cannot render PDFs embedded in pages, and PDF.js would need to rewrite pages' `<embed>` / `<iframe>` elements and a custom scheme to fetch files. A hybrid (QtPdf for top-level PDFs, Chromium for embedded ones) can come later as its own issue. |
