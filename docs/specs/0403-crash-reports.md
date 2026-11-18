# Crash reports: offer a prefilled GitHub issue after Kondor crashes (#403)

> **Issue:** [#403](https://github.com/lukasborges/kondor/issues/403) · **Priority:** P1 (high) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

When the Kondor process itself crashes (a native crash such as #401, not a page crash: those are
#18's crashed page), nothing is left to tell what happened, and the maintainer will not remember to
run `coredumpctl` afterwards. Kondor records the crash itself and, on the next start, offers to
report it as a prefilled GitHub issue that the user reviews and submits. No API, token or server
(maintainer's decision).

## Context

- Startup: `src/kondor/__main__.py` (`start_application`, `run_browser`) and
  `src/kondor/app/startup/`. `--mcp` (#398) runs without a GUI.
- Version and environment: `AboutInfo` (`src/kondor/app/aboutinfo.py`: version, Qt, WebEngine,
  Chromium, windowing system, operating system).
- Remote control connections: `RemoteControl` and `src/kondor/app/remotecontrol/connections/`.
- InlineBar look: `prototypes/111-user-script-bar.qml` (`Kirigami.InlineMessage`, header position).
- Python: 3.13 in the Flatpak runtime (KDE 6.11), newer on Fedora.

## Design / behavior

New feature folders `src/kondor/app/crash/` and `qml/app/crash/`. Everything below runs only in the
GUI app (never in `--mcp`), and the files live in `QStandardPaths.AppLocalDataLocation + "/crash/"`
(not per profile).

### 1. Recording the crash

- Right after `QApplication` is created, `faulthandler.enable(file, all_threads=True)` on
  `crash/crash.log`, opened for writing and kept open for the whole run. It writes only on a fatal
  signal (SIGSEGV, SIGABRT, SIGBUS, SIGFPE, SIGILL). On Python 3.14+ it also writes the C stack
  (`c_stack=True`, the default there); on 3.13 the report has the Python frames and the signal only.
- Before that, if a non-empty `crash/crash.log` is left from the previous run, it is moved to
  `crash/last-crash.log` together with `crash/actions.log` → `crash/last-actions.log` (a newer crash
  replaces an older one not yet reported). A run killed by SIGKILL or a power loss leaves an empty
  `crash.log`, so no false report.

### 2. Last actions

- An `ActionLog` keeps the last **40** entries, `HH:MM:SS event details`, rewriting
  `crash/actions.log` on each entry (small file; it must survive the crash, so no buffering).
- Entries (all from normal windows and tabs only):
  - window opened / closed; tab opened / closed / activated (tab index and count, no titles);
  - navigation started / finished / failed, with `same-site` or `cross-site` and the error code,
    never a host or URL;
  - tab put to sleep / woken (#257); render process terminated with its status (#18);
  - page popups opened: `<select>` dropdown, context menu, JavaScript dialog, file dialog,
    page full screen entered / left;
  - remote control: client connected / disconnected and its kind (`MCP session` or
    `Automation tool`), no names (#398);
  - Qt warnings and critical messages (`qInstallMessageHandler`, chained to the current one), except
    the `js` category, with anything matching `\w+://\S+` replaced by `<url>`.
- **Privacy (hard rule):** nothing from a private tab or private window is ever logged: those
  events are dropped before they reach the `ActionLog`.

### 3. The bar (`prototypes/403-crash-report-bar.qml`)

- On a start where `last-crash.log` exists, the **first normal window** shows an InlineBar above the
  page: Warning type, text "Kondor closed unexpectedly.", action **Report Problem…**
  (`tools-report-bug`), close button. It is shown once per start, in that window only.
- **Report Problem…** opens a new normal tab, active, at
  `https://github.com/lukasborges/kondor/issues/new?labels=bug&title=…&body=…` and closes the bar.
  The close button just closes the bar. Both delete `last-crash.log` and `last-actions.log`.
- Title: `Crash: <signal name> in Kondor <version>` (for example `Crash: Segmentation fault in
  Kondor 0.15.1`).
- Body (Markdown):
  - `### What were you doing?` followed by an empty line for the user;
  - `### Environment`: Kondor version and install type (Flatpak, AppImage or source, as the MCP
    command of #398 detects it), Qt, Chromium, Python, windowing system, operating system, desktop
    (`XDG_CURRENT_DESKTOP`), remote control on or off;
  - `### Last actions` in a code block;
  - `### Crash` in a code block (the faulthandler output).
- **Too long:** if the encoded URL would exceed 8000 characters, the body keeps "What were you
  doing?" and Environment, and the crash and last actions sections are replaced by the line "The
  crash report was copied to the clipboard. Paste it here."; the full body is put on the clipboard
  before the tab opens.

## Acceptance criteria

- [ ] A test instance killed with `kill -SEGV <pid>` shows the bar on its next start, in the first
      window only; a second start without a new crash shows nothing.
- [ ] `kill -KILL` and a normal quit never show the bar.
- [ ] Report Problem… opens the prefilled new-issue page in a normal tab with the title, environment,
      last actions and the faulthandler output; the files are deleted.
- [ ] A report over the URL limit puts the full body on the clipboard and the page says so.
- [ ] The action log never contains a URL, host, page title or any event from a private tab or
      window (pytest over the log with private and normal tabs, and with a Qt warning holding a URL).
- [ ] `--mcp` neither records nor shows anything.
- [ ] Matches `403-crash-report-bar.png`, Breeze and Breeze Dark.
- [ ] Strings in `qsTr()`, translations complete; the body text sent to GitHub stays in English
      (it is for the project, not the user).
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with its own XDG folders under `~/kondor-test`, started with `--new-instance`
(the maintainer keeps their own Kondor open).

1. Open a few tabs, a private window, navigate, open a `<select>`; `kill -SEGV` the instance.
2. Start it again: the bar shows. Report Problem…: GitHub's form is prefilled; check that no address
   and nothing from the private window is in it. Do **not** submit.
3. Start again: no bar.

## Out of scope

- Sending reports without the user (an API, the `gh` CLI or a server): rejected, see Decisions.
- Symbolized native stacks (`gdb`, `coredumpctl`, crashpad).
- Page (renderer) crashes: #18 handles them.

## Dependencies

- None. Helps #401, which is blocked until a crash brings data.

## Prototype

- [`prototypes/403-crash-report-bar.qml`](../../prototypes/403-crash-report-bar.qml) →
  [screenshot](../../prototypes/screenshots/403-crash-report-bar.png)

## Decisions

| Question | Decision |
| --- | --- |
| Send reports automatically? | No: the maintainer chose a prefilled GitHub issue the user reviews and submits. An API needs a token that anyone could extract from the app; an opt-in through the `gh` CLI was proposed and dropped; a relay server is new infrastructure to keep. |
| A dialog showing the error to copy, or a prefilled page? | The prefilled page: the user sees the error there before submitting, and it is one click less. The clipboard is the fallback for reports too long for the URL. |
| Where to tell the user? | An InlineBar in the first window (Warning): a crash is a problem that asks for an action now; a system notification would fire while the window is active. |
| How to know it crashed? | A non-empty faulthandler file. A "running" marker would also fire on SIGKILL and power loss, where there is nothing useful to report. |
| What goes into the last actions? | Event kinds only, never addresses, titles or page content, and nothing from private tabs (AGENTS.md privacy rule): the report is public. |
