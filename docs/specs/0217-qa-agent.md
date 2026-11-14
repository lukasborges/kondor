# QA agent: daily user tests and C++/Python parity before the switch (#217)

> **Issue:** [#217](https://github.com/lukasborges/kondor/issues/217) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Add a third agent, **QA**, that tests `main` the way a user does and reports what is broken as
`bug` issues. Its main job comes between #173 and #174: the Python app must do everything the C++
app does before the C++ is deleted. QA runs the same scenarios on both apps and files every
difference.

- It runs **once a day** from a systemd timer, not as a loop: it does not watch the queue, it
  tests whatever `main` is.
- It **only files issues**. It never edits code, specs or docs, never pushes and never comments on
  PRs. The existing flow fixes what it finds: the architect promotes the bug, a developer fixes it.

## Context

- **Agents today:** `scripts/architect-loop.sh` and `scripts/dev-loop.sh` (numbered loops,
  `KONDOR_DEV_ID`), systemd user services, control worktrees at `origin/main` with `AGENTS.md`
  and `opencode.json` linked from `~/.config/kondor-agents/` (`link_agent_files`), and
  `scripts/watch-agents.sh`. Roles live in `docs/agents/architect.md` and `docs/agents/developer.md`.
- **Builds:** `scripts/bin/cmake` caps jobs, uses ccache and runs one build at a time across all
  loops (`KONDOR_BUILD_LOCK`). The Python app is staged with `python3 scripts/build.py` and, from
  #173, starts with `python3 -m kondor`.
- **What to test:** every spec in `docs/specs/` has a "Manual test" section. Bug issues are their
  own spec and have "Steps".
- **Isolation:** AGENTS.md requires temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
  `XDG_CACHE_HOME` for every run of the app. The maintainer's desktop is never used or captured.
- **Tools on the host:** `Xvfb`, `xvfb-run`, ImageMagick (`import`) and `xdotool` are installed
  (checked on 2026-11-14: a private 1280×800 display, `xdotool getdisplaygeometry`, and `import`
  of its root window all work).

## Design / behavior

### 1. Role: `docs/agents/qa.md`

A new role file, in the style of the other two:

- **You own:** testing `main`, filing `bug` issues, the QA state files.
- **You never:** edit files in the repository, push, open or comment on PRs, change labels other
  than on the issues you file, use the maintainer's display or profile.
- **How to test**, **What a bug report contains** and **Parity mode**: items 3 to 6 below.

### 2. Runner: `scripts/qa-run.sh`

Same structure as the other loop scripts (everything inside `main()`, small functions):

- `scripts/qa-run.sh` runs once and exits; `--dry-run` prints what it would test and the prompt;
  `--install` writes and enables `kondor-qa.service` (`Type=oneshot`) and `kondor-qa.timer`
  (`OnCalendar=*-*-* 03:00`, `Persistent=true`); `--uninstall` removes both.
- **Folders:** control worktree `~/.local/share/kondor-qa/control` kept at `origin/main`, with
  `AGENTS.md` and `opencode.json` linked as in the other loops; state `~/.local/state/kondor-qa`
  (`qa.log`, one `run-<date>.log` per run, `last-sha`, `tested.tsv`, and a `shots-<date>/` folder).
- **Skip:** when `origin/main` is the commit in `last-sha`, log "main unchanged since the last
  run" and exit 0.
- **The unit** sets `PATH` with `scripts/bin` first (build cap, ccache, build lock),
  `MemoryHigh=12G`, `MemoryMax=16G`, and unsets `DISPLAY` and `WAYLAND_DISPLAY`.
- **The run:** `claude -p --permission-mode auto --model opus --effort medium` with
  `--append-system-prompt "$(cat docs/agents/qa.md)"` and the prompt below, from the control
  worktree. On success it writes the tested commit to `last-sha`.
- **Prompt:** the commit under test, the scenarios chosen for this run (item 3), whether parity
  mode is on (item 5), the bug limit, and "stop after the report".
- **Environment overrides:** `KONDOR_QA_CONTROL`, `KONDOR_QA_STATE`, `KONDOR_QA_MODEL`,
  `KONDOR_QA_EFFORT`, `KONDOR_QA_MAX_BUGS` (default 5), `KONDOR_QA_SCENARIOS` (default 5).

### 3. What each run tests

- **Always:** build both apps from the commit under test (C++ with CMake into
  `control/build`, Python with `scripts/build.py`), then the offscreen smoke test of each. A QML
  error in either is a bug.
- **Scenarios:** the "Manual test" sections of the specs of closed issues, and the "Steps" of
  closed bug issues. The runner picks the `KONDOR_QA_SCENARIOS` least recently tested ones
  (`tested.tsv`: spec path or bug number, last tested date), never-tested first, and updates the
  file after the run.
- **Steps that cannot run unattended** (a real Google account, a printer, a second monitor) are
  skipped and listed in the run log, never guessed.

### 4. How QA drives the app

- Each app run gets **its own fresh XDG folders** under the run's state folder, and its own
  private X display: `xvfb-run -a -s "-screen 0 1280x800x24"`.
- **Input:** `xdotool` on that display (`search --name Kondor`, `key`, `type`, `mousemove`,
  `click`).
- **Screens:** `import -display "$DISPLAY" -window root shots-<date>/<scenario>-<step>-<app>.png`,
  which the agent then looks at. Only the Xvfb display is ever captured.
- **What it checks:** the screen against the spec and its prototype screenshot, stderr for QML
  errors, and the files the app wrote (`Kondor.conf`, `kondor.sqlite` read with `python3 -c` and
  `sqlite3`, downloads).

### 5. Parity mode

- **On** when `kondor/__main__.py` exists on the commit under test and the C++ app still builds:
  from #173 until #174 deletes the C++.
- Every scenario runs on **both apps**, each with its own fresh profile, the same steps, the same
  window size.
- **A parity bug** is any difference a user could notice: a screen that differs, a missing or
  different setting key or database row, a different file name, an error only one app prints. The
  C++ app is the expected behavior unless its spec says otherwise.
- **Blocking the switch:** for every parity bug it files, QA adds the bug's number to the
  `**Depends on:**` line of #174. The architect loop does not promote #174 while any of them is
  open. This is the only change QA makes to an issue it did not file.
- **Profile migration:** once per run, the C++ app writes a profile through one scenario, then
  the Python app opens that same profile. Lost or changed data is a parity bug.

### 6. Bug reports

- **Before filing:** search open and recently closed issues (`gh issue list --search`) for the
  same problem. If one exists, add a comment with the new evidence instead of a new issue.
- **At most `KONDOR_QA_MAX_BUGS` new issues per run**; the rest go to the run log for the next run.
- **Title:** `<area>: <what is wrong>`, in the same style as the maintainer's bugs.
- **Labels:** `bug`, `qa`, one `priority:` (high for data loss, crashes, privacy; medium for a
  broken feature; low for looks) and one `area:` label.
- **Body** (a bug issue is its own spec): the first line "Found by the QA agent on `<sha>`";
  then **Steps** (exact, from a fresh profile), **Expected** (quote the spec, or "as the C++ app"
  in parity mode), **Actual**, **Evidence** (the stderr lines, the differing file contents, a
  description of the screenshot: GitHub CLI cannot attach images) and **Acceptance**.
- **Privacy:** private windows must write nothing to disk. QA checks the XDG folders after every
  private-window scenario, and any write is a `priority: high` bug.

### 7. Watching and docs

- `scripts/watch-agents.sh` follows QA too: `qa` as an argument, included in `all` when
  `~/.local/state/kondor-qa` exists, in its own color (white, 37).
- `docs/agents/architect.md`: QA's bugs come with `qa`; promote them like any other bug.
- README: one line in the agents section, if the README has one.
- The label `qa` exists already (green, "Found by the QA agent").

## Acceptance criteria

- [ ] `docs/agents/qa.md` exists and covers items 1, 3, 4, 5 and 6.
- [ ] `scripts/qa-run.sh --dry-run` prints the commit, the chosen scenarios, the parity mode and
      the prompt, and starts nothing.
- [ ] `scripts/qa-run.sh --install` creates `kondor-qa.service` and `kondor-qa.timer`, and
      `systemctl --user list-timers` shows the next run at 03:00.
- [ ] A run skips when `main` has not changed since `last-sha`.
- [ ] A full run on the current `main` builds both apps, runs the smoke tests and five scenarios
      on a private Xvfb display, never touches the maintainer's display or profile, and updates
      `tested.tsv` and `last-sha`.
- [ ] In parity mode, a parity bug is filed with the format of item 6 and its number is added to
      the `**Depends on:**` line of #174.
- [ ] A second run does not file a duplicate of an open bug; it comments on it instead.
- [ ] `scripts/watch-agents.sh qa` follows the run.
- [ ] The scripts follow the style of `scripts/dev-loop.sh` (small functions inside `main()`).

## Manual test

1. `scripts/qa-run.sh --dry-run`: check the scenarios and the parity mode it reports.
2. Run `scripts/qa-run.sh` once by hand while `scripts/watch-agents.sh qa` runs in another
   terminal. During the run, the maintainer's desktop shows no Kondor window.
3. Open `~/.local/state/kondor-qa/shots-<date>/`: the screenshots show Kondor on a 1280×800
   screen, never the desktop.
4. Check the new issues labeled `qa` and the `**Depends on:**` line of #174.
5. Run it again at once: it logs "main unchanged since the last run" and exits.
6. `scripts/qa-run.sh --install`, then `systemctl --user list-timers | grep kondor-qa`.

## Out of scope

- Fixing bugs, editing specs or docs, or reviewing PRs.
- Performance and memory measurements, beyond what a scenario states.
- Testing the AppImage or the Flatpak packages: the release workflow and the proof jobs do that.
- Running after every merge; a daily run is enough.
- Attaching screenshots to issues.

## Dependencies

- #173: the Python app starts with `python3 -m kondor`, so parity mode has two apps to compare.
- #174 must wait for this issue (its `**Depends on:**` line lists #217) and for every parity bug
  QA files.

## Decisions

| Question | Decision |
| --- | --- |
| A loop polling the queue, like the architect and the developers? | No: a daily timer. QA tests `main` as it is and does not react to labels; a loop would burn runs while nothing changed. |
| Start QA now? | No: after #173. Until then the C++ app is frozen (bug fixes only) and the Python app cannot start, so there is little to test that the architect's reviews do not already cover. |
| Screenshots of the maintainer's desktop? | Never. QA starts each app on its own Xvfb display and captures only that. |
| How do parity bugs block the switch? | QA adds each one to #174's `**Depends on:**` line, which the architect loop already honors when it promotes. |
| Which GitHub account files the bugs? | The maintainer's (`gh` default, like the architect). The first body line "Found by the QA agent" tells them apart. |
| Could QA fix small bugs itself? | No. Every fix goes through the developer and the architect's review, so the same rules and checks apply. |
