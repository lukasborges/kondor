# Restart Now after changing remote control (#419)

> **Issue:** [#419](https://github.com/lukasborges/kondor/issues/419) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Turning remote control on or off, or changing its port, only takes effect after a restart (Qt
WebEngine reads the debugging port at startup, #256), and today the user has to quit and start
Kondor by hand. The restart message gets a **Restart Now** button that does it, bringing every
window and tab back.

## Context

- Message: `qml/settings/pages/RemoteControlRestartMessage.qml` (`Kirigami.InlineMessage`,
  visible while the saved setting differs from what is running).
- How this installation is started (Flatpak, AppImage, source, and the active profile of #349):
  `src/kondor/app/remotecontrol/mcpcommand.py` (`launch_words`, `profile_words`).
- Quit guard for active downloads: `qml/app/window/WindowCloseGuard.qml`.
- Session: `src/kondor/browser/session/sessionmanager.py`; single instance:
  `src/kondor/app/instance/`.

## Design / behavior (`prototypes/419-restart-now.qml`)

1. The restart message gets the action **Restart Now** (`view-refresh`). It shows whenever the
   message shows (after OK/Apply saved a change that needs a restart).
2. Restart Now:
   - asks the same "Downloads are still in progress. Quit anyway?" confirmation as quitting does
     when downloads are active, and does nothing if the user cancels;
   - saves the session of normal windows now (as on quit; private windows are not saved, as
     today, and the confirmation does not change that);
   - quits the application normally (every window, the settings dialog included);
   - after the single-instance server is closed and the event loop has ended, starts this
     installation again detached (`QProcess.startDetached` with `launch_words()` plus the active
     profile's words) with a new argument `--restore-session`.
3. `--restore-session` makes that start restore the saved session even when the startup setting
   says otherwise; it is not listed in `--help` and has no other effect.
4. If the new process cannot be started, nothing is lost: the session is saved; the failure is
   logged on stderr.

## Acceptance criteria

- [ ] Turn remote control on, Apply: the message shows Restart Now; clicking it brings Kondor back
      with the same windows and tabs, and remote control running (the indicator and the port answer).
- [ ] Same for turning it off and for a port change.
- [ ] With "Start with: home page" in Settings, the restart still restores the session.
- [ ] With an active download: the confirmation shows; Cancel keeps Kondor running.
- [ ] Works for the source run (`python3 -m kondor`), the Flatpak and the AppImage, and keeps a
      non-default profile (#349).
- [ ] The new instance never forwards to the old one (no lost window).
- [ ] Matches `419-restart-now.png`, Breeze and Breeze Dark; strings in `qsTr()`, translations
      complete.
- [ ] Python checks pass (`ruff`, `mypy --strict`, `scripts/run-pytests.sh`, `check-qml-api.py`,
      `check-code-quality.py --changed origin/main`).

## Manual test

Separate instance with isolated XDG folders under `~/kondor-test`, `--new-instance`.

1. Three tabs in two windows. Settings → Privacy, turn remote control on, Apply, Restart Now: both
   windows and their tabs come back, and `http://127.0.0.1:<port>/json/version` answers.
2. Turn it off, Apply, Restart Now: back again, port closed.

## Out of scope

- Restart buttons for other settings, restarting automatically without asking, keeping private
  windows across the restart.

## Dependencies

- None.

## Prototype

- [`prototypes/419-restart-now.qml`](../../prototypes/419-restart-now.qml) →
  [screenshot](../../prototypes/screenshots/419-restart-now.png)
  (`withRestartNow` in `prototypes/common/SettingsDialogMock.qml`)

## Decisions

| Question | Decision |
| --- | --- |
| Where does the button go? | In the restart message itself, the place that says a restart is needed (maintainer's request). |
| Restore the session even if the user starts with the home page? | Yes: the user asked to restart, not to start over; `--restore-session` applies to that one start only. |
| Private windows? | Not kept, as on any quit: nothing from them may be written to disk. |
| Approved | Prototype approved by the maintainer. |
