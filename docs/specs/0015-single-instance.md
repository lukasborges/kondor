# Single instance (#15)

> **Issue:** [#15](https://github.com/lukasborges/kondor/issues/15) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Run a single Kondor process per user session: launching `kondor <url>` while Kondor is running opens the URL as a new tab in the existing window and raises it.

## Context

Every launch starts a new process with its own window and a second use of the same persistent profile (`storageName "kondor"`), which Qt WebEngine does not support well (profile lock / data corruption risk).

## Design / behavior

1. **`src/singleinstance.{h,cpp}`** using `QLocalServer`/`QLocalSocket` (no new dependency, `Qt6::Network`):
   - Socket path (full path passed to `listen()`/`connectToServer()`): `QStandardPaths::writableLocation(QStandardPaths::RuntimeLocation) + "/kondor-" + <first 16 hex chars of the SHA-1 of QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)> + ".socket"`, computed after `setOrganizationName`/`setApplicationName`. The server calls `setSocketOptions(QLocalServer::UserAccessOption)` before `listen()`. See Decisions.
   - In `main()` **before** creating the QML engine (after `QGuiApplication` and command-line parsing from #10): try `QLocalSocket::connectToServer(name)`; if it connects within 500 ms, send one JSON line `{"urls": [...], "private": false, "activationToken": "<XDG_ACTIVATION_TOKEN env or empty>"}` , wait for `bytesWritten`, and `return 0`.
   - Otherwise `QLocalServer::removeServer(name)` (stale socket) and `listen(name)`. On a new connection read the JSON and emit `messageReceived(QList<QUrl> urls, bool privateMode, QByteArray activationToken)`.
2. **Handling** (in C++ next to `WindowManager` (#14) or exposed to QML): open each URL in a new tab of the most recently active window (or a new window if the flag `--new-window` is passed / no window exists); with no URLs, just raise the window.
3. **Raising on Wayland**: before `window->requestActivate()`, set `qputenv("XDG_ACTIVATION_TOKEN", token)` with the token received from the second process (Plasma's launcher sets it in the environment of the launched process; Qt's Wayland plugin consumes it on `requestActivate()`). On X11 `requestActivate()` + `raise()` is enough.
4. Add `--new-instance` option to bypass (useful for development).
### Edge cases

- Crash leaves a stale socket file → `removeServer()` before `listen()` handles it.
- Two launches at the same time: the loser of `listen()` should retry the client connection once.
- Private flag: `kondor --private url` → new private tab (or private window with #14).

## Acceptance criteria

- [ ] With Kondor running, `kondor https://kde.org` from a terminal opens a new tab in the running window and the second process exits immediately.
- [ ] Clicking links in other apps (with Kondor as default browser, #10) reuses the window and raises it on Wayland.
- [ ] `kondor --new-instance` still starts a separate process (dev use).
- [ ] After `kill -9`, the next launch works normally.

## Manual test

Run `kondor`, then `kondor https://kde.org` and `kondor` again; set as default browser and click a link in Konsole; kill -9 and relaunch.

## Out of scope

D-Bus interface for other apps, remote control commands besides opening URLs.

## Dependencies

#10 (command line). Works better with #14 (WindowManager).

## Prototype

No UI for this issue, so there is no prototype.

## Decisions

| Question | Decision |
| --- | --- |
| Where does the single-instance socket live? (review of PR #76) | Not `/tmp/kondor-<uid>`. It goes in the per-user runtime directory (`XDG_RUNTIME_DIR`, mode 0700) and its name includes a hash of the profile data directory (`AppDataLocation`). Why: (1) a name under `/tmp` can be created first by another local user, who then gets every forwarded URL (private ones too) plus the activation token, and the real launch exits; (2) one instance per profile directory is what the feature protects, so a run with isolated `XDG_DATA_HOME` (smoke tests, agent reviews, AGENTS.md) never forwards its URLs into the maintainer's real running Kondor. Socket permissions: `QLocalServer::UserAccessOption`. |
