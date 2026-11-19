# Responsive mode: Chrome's device list and device pixel ratio (#439)

> **Issue:** [#439](https://github.com/lukasborges/kondor/issues/439) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Responsive design mode (#430) offers five devices of its own and always renders at 1×, so pages
show low-resolution images and ignore `resolution` media queries. The maintainer wants the same
devices Chrome's device toolbar lists by default, each with its default density (device pixel
ratio), as in Chrome.

## Context

- Devices: `src/kondor/browser/responsive/devices.py` (`Device`, `DEVICES`, `mobile_agent`).
- Per-tab state: `src/kondor/browser/responsive/tabresponsive.py` (`TabResponsive`: `isActive`,
  `device`, `width`, `height`, `zoomToFit`, `deviceList`), remembered values in
  `responsivememory.py` (settings `responsiveDevice`, `responsiveSize`).
- UI: `qml/browser/responsive/ResponsiveToolBar.qml`, `PageStage.qml`, `ResponsiveHandles.qml`.
- Page zoom: the tab's zoom (`Tab.zoomFactor`, per-site zoom #24, saved by host for normal tabs).
- Source of the list: Chrome DevTools' `front_end/models/emulation/EmulatedDevices.ts`
  (devices with `show-by-default: true`, in their `order`).

## Design / behavior (`prototypes/430b-responsive-devices.qml`)

### 1. Device list

- The device `ComboBox` lists **Responsive**, then Chrome's default devices in Chrome's order,
  with Chrome's names, portrait CSS sizes and device pixel ratios:

  | Device | Size | Ratio | User agent family |
  | --- | --- | --- | --- |
  | iPhone SE | 375 × 667 | 2 | iPhone (iOS 18.5 Safari) |
  | iPhone 16 | 393 × 852 | 3 | iPhone |
  | iPhone 16 Pro Max | 440 × 956 | 3 | iPhone |
  | Pixel 9 | 412 × 924 | 2.625 | Android 14, `Pixel 9` |
  | Pixel 9 Pro | 427 × 952 | 3 | Android 14, `Pixel 9 Pro` |
  | Pixel 10 | 412 × 924 | 2.625 | Android 16, `Pixel 10` |
  | Samsung Galaxy A55 | 360 × 800 | 2.25 | Android 14, `SM-A556B` |
  | iPad Mini | 768 × 1024 | 2 | iPad (iOS 18.5 Safari) |
  | iPad Pro 13 | 1032 × 1376 | 2 | macOS Safari 18.5 (as Chrome) |
  | Surface Pro 10 | 960 × 1440 | 2 | Windows Chrome (desktop) |
  | Pixel 9 Pro Fold | 412 × 922 | 2.625 | Android 14, `Pixel 9 Pro Fold` |
  | Galaxy Z Fold 6 | 412 × 968 | 2.625 | Android 14, `SM-F956U` |
  | Nest Hub Max | 1280 × 800 | 2 | Linux aarch64 Chrome with `CrKey/1.54.250320` |

- User agents are Chrome's strings for those devices, with `%s` (Chrome version) filled from Qt's
  Chromium version as today (`chrome_version_of`). The table lives in `devices.py` (new
  `ratio` field); the five old devices are removed.
- A remembered `responsiveDevice` key that no longer exists falls back to **iPhone 16**.

### 2. Device pixel ratio control

- A `ComboBox` right after the size boxes (`Accessible.name` and tooltip "Device pixel ratio",
  `ToolTip.delay: 600`) with **1×, 1.5×, 2×, 2.25×, 2.5×, 2.625×, 3×, 3.5×, 4×** (shown with
  the locale's decimal separator).
- Choosing a device selects its ratio; the user can then pick another ratio without leaving the
  device. **Responsive** starts at **1×**. Editing the size boxes or dragging a handle switches to
  Responsive and keeps the current ratio.
- The ratio is per tab, like the rest of the mode; the last one used with Responsive is
  remembered (setting `responsiveRatio`, default 1).
- New `TabResponsive` property `ratio` (`float`, `NOTIFY ratioChanged`) and command
  `setRatio(ratio)`; `deviceList` entries gain `ratio`.

### 3. How the ratio is applied (no CDP)

- Chromium reports `window.devicePixelRatio` = screen scale × page zoom. With the ratio `r` and
  the window's `Screen.devicePixelRatio` `s`, the tab in the mode uses page zoom `z = r / s`,
  and the `WebEngineView` item is sized `width × z` by `height × z` logical pixels, so its CSS
  viewport stays the device size (`window.innerWidth === 412` for Pixel 9) and
  `window.devicePixelRatio === r` (`matchMedia("(resolution: 2.625dppx)")` matches, `srcset`
  picks the matching image).
- The view item is drawn at `scale: fitScale / z`, so on screen it takes the same room as at 1×;
  Zoom to Fit, the percentage label and the handles keep working in CSS pixels. Clicks still
  land on the right element (scaled `Item`, as in #430).
- While the mode is on, the mode owns the page zoom: Zoom In/Out/Reset and their shortcuts are
  disabled for that tab, and nothing is saved to per-site zoom. Turning the mode off restores
  the tab's previous zoom (and its per-site value) exactly.
- Very large textures are capped: if `width × z` or `height × z` would exceed 8192, the ratio
  `ComboBox` disables the ratios that would, and a device whose default does picks the highest
  allowed one.

## Acceptance criteria

- [ ] The device list is exactly the table above, in that order, after Responsive; old devices
      are gone and an old remembered key falls back to iPhone 16.
- [ ] Pixel 9: `innerWidth === 412`, `innerHeight === 924`, `devicePixelRatio === 2.625`,
      `navigator.userAgent` is the Pixel 9 agent; on a 1× and on a 2× screen alike.
- [ ] Changing the ratio to 1× on Pixel 9 keeps 412 × 924 CSS pixels with `devicePixelRatio === 1`;
      Responsive starts at 1× and remembers its last ratio.
- [ ] A `srcset` test page loads the 3× image on iPhone 16 and the 1× image on Responsive.
- [ ] Zoom shortcuts are disabled in the mode; a host with a saved 125 % zoom is back at 125 %
      after the mode is turned off, and its saved value never changed.
- [ ] Rotate, handles, Zoom to Fit and clicks still work at 3× (iPhone 16) and 2× (iPad Pro 13).
- [ ] Matches `430b-responsive-devices.png`, Breeze and Breeze Dark; strings in `qsTr()`,
      translations complete.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`); pytest covers the device table, the
      fallback key and the zoom formula.

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`.

1. Open a page that prints `innerWidth`, `devicePixelRatio` and has a `srcset` image;
   Ctrl+Shift+M, pick Pixel 9: 412 / 2.625, the high-density image.
2. Switch the ratio to 1×: 412 / 1. Pick Responsive: 1×.
3. Set a site zoom of 125 % first, enter and leave the mode: 125 % again.

## Out of scope

- Touch emulation, network throttling, custom or edited device lists, landscape-only devices'
  special frames, Chrome's "Show device frame".

## Dependencies

- #430 (responsive mode, merged).

## Prototype

- [`prototypes/430b-responsive-devices.qml`](../../prototypes/430b-responsive-devices.qml) →
  [screenshot](../../prototypes/screenshots/430b-responsive-devices.png)

## Decisions

| Question | Decision |
| --- | --- |
| Which devices? | Chrome's default list with its sizes, ratios and agents (maintainer's request, prototype approved); Kondor's own five devices are dropped. |
| How to emulate the ratio without CDP? | Page zoom `r / s` with the view enlarged by the same factor and scaled back: Chromium then reports the ratio itself, `srcset` and `resolution` queries follow. CDP (`Emulation.setDeviceMetricsOverride`) needs the remote debugging port, which is only on with remote control. |
| Can the user change a device's ratio? | Yes, like picking a size: the device sets the default, the ComboBox overrides it. |
