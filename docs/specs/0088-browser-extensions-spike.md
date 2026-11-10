# Browser extensions: feasibility spike (#88)

> **Issue:** [#88](https://github.com/lukasborges/kondor/issues/88) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Find out which Chrome Web Store extensions work in Kondor before designing the real feature.
This issue adds a **developer-only** way to load unpacked extensions, a script that fetches an
extension from the Chrome Web Store, and a compatibility report. There is no user-facing UI.
The installation flow (an "Add to Kondor" button on the Chrome Web Store, an Extensions page in
Settings, toolbar buttons and popups) is specified in a follow-up issue, based on this report.

## Context

- Qt WebEngine 6.10 added `QWebEngineExtensionManager` (`QWebEngineProfile::extensionManager()`,
  and `QQuickWebEngineProfile::extensionManager`, revision 6.10). It offers
  `loadExtension(path)`, `installExtension(path)`, `unloadExtension()`, `uninstallExtension()`,
  `setExtensionEnabled()`, `extensions`, `installPath`, and the signals `loadFinished`/`installFinished`/….
  `QWebEngineExtensionInfo` exposes `name`, `id`, `description`, `path`, `error`,
  `actionPopupUrl`, `isEnabled`, `isLoaded` and `isInstalled`.
- The API is behind `QT_CONFIG(webengine_extensions)`. Fedora's Qt 6.11.2 enables it
  (`QT_FEATURE_webengine_extensions 1` in `qtwebenginecore-config.h`) and is based on
  **Chromium 140**.
- The minimum Qt of Kondor is 6.8 (`find_package(Qt6 6.8 …)`), so every use must compile out on
  older Qt and on builds without the feature. The `webengine_extensions` feature is public and on
  in Qt 6.8 and 6.9 too (it only served the PDF viewer there), so the feature check alone does not
  tell whether the API exists: the Qt version must be checked as well.
- Most `chrome.*` APIs (tabs, windows, contextMenus, action badges…) are implemented by Chrome's
  browser layer, which Qt WebEngine does not ship. Measuring what actually works is the point of
  this spike.
- `addressUrl()` (`src/addressresolver.cpp`) already opens any text containing `://` as a URL, so
  `chrome-extension://<id>/popup.html` can be typed in the address bar.

## Design / behavior

1. **Build guard.** All extension code lives in `src/extensionloader.{h,cpp}` (registered in
   `CMakeLists.txt`). It is wrapped in
   `#if QT_VERSION >= QT_VERSION_CHECK(6, 10, 0) && QT_CONFIG(webengine_extensions)` and is a no-op
   otherwise. The build must keep working with Qt 6.8 and 6.9.
2. **`--load-extension <dir>` command-line option** (repeatable), parsed with the existing
   `QCommandLineParser` in `src/main.cpp`. Help text: "Load an unpacked extension (developer
   option)". For each directory:
   - call `extensionManager()->loadExtension(dir)` on the **default profile only**, once it exists
     and before the first window loads its pages;
   - on `loadFinished`, print one line to stderr with `qInfo()`:
     `Extension loaded: <name> (<id>) popup: <actionPopupUrl or "none">`, or
     `Extension failed: <dir>: <error>`.
   - Use `loadExtension`, not `installExtension`: nothing is copied into the profile and nothing
     is remembered after Kondor quits. The option is not forwarded to an already running
     instance (#15); document that in `--help` and in the README.
3. **Privacy (hard rule).** Extensions are never loaded into private profiles
   (`createPrivateProfile()`), and the spike adds nothing that persists.
4. **`scripts/fetch-extension.sh <extension-id> <out-dir> [--prodversion <x.y.z>]`.** It downloads
   the CRX from
   `https://clients2.google.com/service/update2/crx?response=redirect&prodversion=<ver>&acceptformat=crx2,crx3&x=id%3D<id>%26uc`.
   - It strips the CRX3 header: the magic `Cr24`, a uint32 version (3), a uint32 header length,
     then the header; the rest is a ZIP. It then unzips the extension into `<out-dir>`.
   - `--prodversion` defaults to the `Chrome/<version>` found in `libQt6WebEngineCore.so.6`
     (`strings … | grep -o 'Chrome/[0-9.]*'`).
   - It fails with a clear message on a non-CRX response.
   - Dependencies: `curl`, `unzip`, coreutils/`od` or `python3`; nothing new to install on Fedora.
5. **Compatibility report:** `docs/extensions-compatibility.md`, one row per extension below, tested
   with a real window on Plasma and an isolated profile. **Moved to follow-up issue
   [#105](https://github.com/lukasborges/kondor/issues/105)** (see "Decisions"): it is produced by
   hand on a machine with network access and a display, not by the PR of this issue. Columns:
   - Extension and version, and Manifest version;
   - Loads? (yes/no + error);
   - Content scripts work?;
   - Popup works when `actionPopupUrl` is opened in a tab?;
   - What fails, with the `chrome.*` API from the console (use the DevTools from #16 on the popup tab and on pages);
   - Verdict: works / partly / no.

   | Extension | ID | Why |
   | --- | --- | --- |
   | Dark Reader | `eimadpbcbfnmbkopoojfekhnkhdbieeh` | content scripts + popup + storage |
   | uBlock Origin Lite | `ddkjiahejlhfcafbddmgiahcphecmpfh` | `declarativeNetRequest` |
   | Bitwarden Password Manager | `nngceckbapebfimnlniiiahkandclblb` | popup, messaging, `tabs` |
   | Google Translate | `aapbdbdomjkkjkaonfhkkikfgjllcleb` | `contextMenus`, popup |
   | Video Speed Controller | `nffaoalbilbmmfgbnbgppjihopabppdk` | content scripts only |
   | Tampermonkey | `dhdgffkkebhmkfjojejmpbldmpobfkfo` | `userScripts` |

   End the file with a short **Summary**: which API families work, which fail, and whether the
   popup-in-a-tab trick is enough to drive a real popup UI.
6. **Test** (`tests/tst_extensionloader.cpp`, skipped with `QSKIP` when the feature is off). It loads a
   minimal MV3 extension from `tests/data/extension/`: a `manifest.json` with `action.default_popup`,
   a `popup.html`, and a content script that sets `document.documentElement.dataset.kondorTest`.
   It checks that:
   - `loadFinished` arrives with `isLoaded()`;
   - `actionPopupUrl()` ends in `popup.html`;
   - the content script ran on a `data:` or local test page (read back with `runJavaScript`);
   - a private profile has no extensions.

## Acceptance criteria

- [ ] Builds with and without `webengine_extensions`, and with Qt 6.8/6.9 (no extension API). Without it, `--load-extension` prints
  "Extensions are not supported by this Qt WebEngine build" and is ignored.
- [ ] `kondor --load-extension <dir>` loads an unpacked extension into normal tabs only, and logs
  its id and popup URL.
- [ ] `scripts/fetch-extension.sh` unpacks a CRX3 and a CRX2 file and fails with a clear message on a
  non-CRX response (checked against synthetic files; fetching the six real extensions is verified in #105).
- [ ] ~~`docs/extensions-compatibility.md` has the six rows and the summary.~~ Moved to #105.
- [ ] Tests pass, and the smoke test is clean.

## Manual test

Steps 1–4 need the Chrome Web Store download and a real window, so they are run in #105. For this
issue, run step 2 with `tests/data/extension` instead: stderr shows the extension id and popup URL.

Isolated profile (temporary `XDG_*` dirs):
1. `scripts/fetch-extension.sh eimadpbcbfnmbkopoojfekhnkhdbieeh /tmp/ext/darkreader`.
2. `./build/kondor --load-extension /tmp/ext/darkreader https://kde.org`: the page turns dark, and
   stderr shows the extension id and popup URL.
3. Open the popup URL in a new tab and toggle the extension off; reload kde.org.
4. Open a private window: kde.org is not dark there.

## Out of scope

- `docs/extensions-compatibility.md` and any measured result for the six extensions (follow-up #105);
- any user-facing UI: an "Add to Kondor" button, an Extensions settings page, toolbar buttons,
  real popups, permission prompts;
- persistent installation (`installExtension`), updates, and an extension list saved in the profile;
- forwarding `--load-extension` to a running instance;
- Firefox add-ons;
- fixing incompatible extensions or implementing missing `chrome.*` APIs.

## Prototype

None: this issue has no user-facing UI.

## Decisions

| Question | Decision |
| --- | --- |
| The Chrome Web Store download sends no body from the developer agent's sandbox and there is no display, so the six extensions cannot be fetched or measured. Merge the loader/script/test now and produce the report by hand (a), or keep the issue open until someone supplies the data (b)? ([PR #104](https://github.com/lukasborges/kondor/pull/104#issuecomment-6781496080)) | **(a).** The architect's machine has the same download failure (HTTP 200, 0 bytes), so no agent can produce the report. #88 delivers the loader, `--load-extension`, `scripts/fetch-extension.sh` and the test; the compatibility report, the real fetch of the six extensions and the Dark Reader manual test move to follow-up issue #105, done by hand on a machine with network access and a display. No results are invented and no placeholder report file is committed. The script is verified against synthetic CRX2/CRX3 files and a non-CRX response. |
| The test page: the spec says "a `data:` or local test page", but extensions cannot touch `file:` pages by default. | Serving the page from a local HTTP server inside the test is fine. |
| After `loadExtension()` the extension is not enabled. | The loader calls `setExtensionEnabled(info, true)` for the extensions it loads; record this and the built-in component extensions listed by `extensions()` as findings in the PR, for the #105 report's summary. |
| Is `#if QT_CONFIG(webengine_extensions)` enough as the build guard? ([PR #104 review](https://github.com/lukasborges/kondor/pull/104)) | No. Qt 6.8 and 6.9 define the feature as on but have no `QWebEngineExtensionManager`, so the build breaks there. The guard is `QT_VERSION >= QT_VERSION_CHECK(6, 10, 0) && QT_CONFIG(webengine_extensions)`, in the loader and in the test. |
| Where does the test's persistent profile live? | In a `QTemporaryDir` (`setPersistentStoragePath`/`setCachePath`), like the other tests that isolate their storage; a test never writes under the real home. |
