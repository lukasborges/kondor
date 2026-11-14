# Python port 4/12: Downloads and history (#166)

> **Issue:** [#166](https://github.com/lukasborges/kondor/issues/166) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-4, 8 and 9, "Rules for every phase") and the phase 2 spec [`0164-python-core.md`](0164-python-core.md) first. This file details phase 4 and must follow the umbrella. Only the architect edits it.

## Objective

Port `src/downloads/`, `src/history/` and `src/browser/favicons/` to Python, and port their tests:

- **Same QML API:** `DownloadManager`, `HistoryManager` and `FaviconStore` are QML singletons in `Kondor` 1.0. `DownloadModel` and `HistoryModel` are registered as uncreatable types. `check-qml-api.py` pairs all five with their C++ twins.
- **Same data:** the Python classes read and write the `history` and `favicons` tables of the same `kondor.sqlite` as the C++ app, with the same statements.
- **Same privacy:** downloads from private tabs are dropped from the list when the app quits, as in C++.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Phase 2 (#164, merged in 69ebf86)** added `kondor/core/`: `Database` (with `reset_instance()` for tests), `sql` (`run`, `ids`, `in_transaction`, `id_or_null`), `Settings`, `Notifier`, `FileHelper`, and the pytest fixtures `isolated_profile`, `kondor_types` and `kondor_engine`. Phase 3 (#165, ad blocking) may run in parallel; it touches none of the files below.
- **`src/downloads/`** (633 lines):

  | C++ file | What it does |
  | --- | --- |
  | `downloadmanager.{h,cpp}` | QML singleton `DownloadManager`: `model`, `hasActiveDownloads`, `activeProgress`, `hasFinishedDownloads` (notify `activeChanged`); enum `State` (the five `QWebEngineDownloadRequest::DownloadState` values); `handleRequest(download, isPrivate)` (called by `ProfileManager`); invokables `pause`, `resume`, `cancel`, `openFile`, `showInFolder`, `removeFromList`, `clearFinished`, `openDownloadsFolder`; signals `saveLocationRequested(request, suggestedFile)`, `downloadStarted`, `activeChanged`. It notifies through `Notifier` on completion and on failure, and shows a file with `org.freedesktop.FileManager1.ShowItems`. |
  | `downloadmodel.{h,cpp}` | `QML_ANONYMOUS` list model of `DownloadItem{QPointer download, isPrivate, TransferSpeed}`: `count`, roles, add/remove/`clearFinished`/`removePrivateDownloads`, `downloadAt`; it follows each request's signals and removes the row when the request is destroyed |
  | `downloadroles.{h,cpp}` | the 12 role readers and names, `isActiveDownload`, `isFinishedDownload`, `averageActiveProgress`, `liveDownloadsOf` |
  | `transferspeed.{h,cpp}` | bytes per second, sampled at most once a second |

- **`src/history/`** (601 lines):

  | C++ file | What it does |
  | --- | --- |
  | `historymanager.{h,cpp}` | QML singleton `HistoryManager`: `model`; invokables `addVisit`, `updateTitle`, `removeEntry`, `clearAll`, `clearSince`, `topSites`, `suggest(text, limit = 6)`, `recentToday`, `hostCompletion`. A visit to the same URL within 30 s only updates the title. Clearing history also clears favicons. |
  | `historymodel.{h,cpp}` | `QML_UNCREATABLE` list model: `filter`, `count`, `active`; roles `id`, `url`, `title`, `visitedAt`, `dayLabel`, `time`; at most 500 rows; `refresh()`, `scheduleRefresh()` (250 ms debounce, only while `active`); invokable `urlAt` |
  | `historysearch.{h,cpp}` | namespace: `suggest`, `recentToday`, `hostCompletion`, `likePattern` |
  | `topsitesranking.{h,cpp}` | namespace: `topSites(limit)` over the last 90 days, grouped by host without `www.`, minus `Settings.hiddenTopSites` |

- **`src/browser/favicons/`** (205 lines):

  | C++ file | What it does |
  | --- | --- |
  | `faviconstore.{h,cpp}` | QML singleton `FaviconStore`: `revision` (notify `revisionChanged`); invokable `store(pageUrl, iconSource)`, which asks the engine's `favicon` image provider (Qt WebEngine's, a `QQuickAsyncImageProvider`) for the icon and stores it as PNG, at most 32×32, per host; `storeImage`, `clearAll`, `clearSince`, `imageForHost`. `create()` keeps the `QQmlEngine`. |
  | `faviconimageprovider.{h,cpp}` | the `image://kondor-favicon/<page URL>` provider: `FaviconStore::imageForHost(QUrl(id).host())`. `appStartup` adds it to the engine. |

- **Tests to port:**

  | C++ test | Cases |
  | --- | --- |
  | `tests/downloads/tst_transferspeed.cpp` | `reportsBytesPerSecondAfterOneSecond`, `keepsSpeedWithinOneSecond`, `stopResetsSpeed` |
  | `tests/downloads/tst_downloadstatus.cpp` | `describesEveryState` (data-driven, 11 rows, loads `qml/downloads/DownloadStatus.qml`) |
  | `tests/history/tst_historymanager.cpp` | `addVisitIgnoresUnsupportedSchemes`, `revisitWithinWindowUpdatesTitleOnly`, `updateTitleLeavesOlderVisitsUntouched`, `clearSinceKeepsOlderVisits`, `removeEntryDeletesOnlyThatRow` |
  | `tests/history/tst_historysuggestions.cpp` + `topsitesharness.h` | `suggestMatchesUrlAndTitle`, `suggestSortsByVisitsAndLimit`, `suggestEscapesWildcards`, `hostCompletionPrefersMostVisitedHost`, `recentTodayExcludesYesterday` |
  | `tests/history/tst_topsites.cpp` | `groupsByHostAndSortsByVisits`, `stripsWwwAndIgnoresOtherSchemes`, `skipsHiddenHosts`, `ignoresVisitsOlderThanNinetyDays` |
  | `tests/browser/tst_faviconstore.cpp` | `storesAndLooksUpByHost`, `replacesOnlyWhenBytesChange`, `clearHistorySinceKeepsOlderFavicons`, `clearAllRemovesEveryFavicon`, `clearHistoryAlsoClearsFavicons` |

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior, statements and edge cases as the C++, with the Python conventions of umbrella item 3. A C++ helper namespace becomes a module of functions.

### 1. Layout

```
kondor/downloads/
  __init__.py
  qmltypes.py
  downloadmanager.py
  downloadmodel.py
  downloadroles.py
  transferspeed.py
kondor/history/
  __init__.py
  qmltypes.py
  historymanager.py
  historymodel.py
  historysearch.py
  topsitesranking.py
kondor/browser/
  __init__.py
  qmltypes.py
  favicons/
    __init__.py
    faviconstore.py
    faviconimageprovider.py
```

Further splits for the size limits are allowed if the existing modules keep their C++ base names (for example `downloadactions.py` for the `pause`…`openDownloadsFolder` helpers).

### 2. `qmltypes.py`

```python
# kondor/downloads/qmltypes.py
QML_TYPES = (
    QmlType(DownloadManager, "DownloadManager", QmlKind.SINGLETON),
    QmlType(DownloadModel, "DownloadModel", QmlKind.UNCREATABLE),
)
# kondor/history/qmltypes.py
QML_TYPES = (
    QmlType(HistoryManager, "HistoryManager", QmlKind.SINGLETON),
    QmlType(HistoryModel, "HistoryModel", QmlKind.UNCREATABLE),
)
# kondor/browser/qmltypes.py (phases 7 and 8 add their browser types here)
QML_TYPES = (QmlType(FaviconStore, "FaviconStore", QmlKind.SINGLETON),)
```

Each module also has `register_types()`, as in `kondor/core/qmltypes.py`. Importing them must not create any instance (`check-qml-api.py` imports them without a `QCoreApplication`).

### 3. Names and types

- **Snake case** for everything QML does not see (umbrella item 3): `handle_request`, `refresh`, `schedule_refresh`, `store_image`, `clear_all`, `clear_since`, `image_for_host`, `add_download`, `remove_download`, `clear_finished` and `remove_private_downloads` on the model, `download_at`, and every module-level function (`historysearch.suggest`, `like_pattern`, `topsitesranking.top_sites`, `is_active_download`, …).
- **64-bit arguments:** `removeEntry(id)` and `clearSince(msecsSinceEpoch)` take `qint64` in C++. Declare them `Slot("qint64")`, because `Slot(int)` is 32-bit and a time in ms since the epoch does not fit.
- **`suggest`:** QML calls it with two arguments, and the C++ default makes it accept one too. The Python slot accepts both counts, so `check-qml-api.py` sees 1 and 2.
- **Enums:**
  - `DownloadManager.State` is a `QEnum`-decorated `IntEnum` inside the class, with the names `Requested`, `InProgress`, `Completed`, `Cancelled`, `Interrupted` and the values of `QWebEngineDownloadRequest.DownloadState`. QML reads them as `DownloadManager.Completed`.
  - `DownloadModel.Role` and `HistoryModel.Roles` keep their C++ names and values (`Qt.UserRole + 1`, …).
- **Request types:** production code is typed with `QWebEngineDownloadRequest`; `saveLocationRequested` is `Signal(QQuickWebEngineDownloadRequest, QUrl)`. The "is it a Quick request" test (`qobject_cast` in C++) is `isinstance(download, QQuickWebEngineDownloadRequest)`.
- **Translations:** `QCoreApplication.translate("DownloadManager", "Download completed")`, `"Download failed"`, and `QCoreApplication.translate("HistoryModel", "Today")`, `"Yesterday"`, so the `.ts` contexts stay the same (umbrella item 8).

### 4. Downloads

- **`QPointer` semantics:** a `DownloadItem` (a small dataclass: `download`, `is_private`, `speed`) keeps the Python wrapper of the request. "The pointer is null" becomes `not shiboken6.isValid(item.download)`. `downloadRoleValue`, `liveDownloadsOf` and `download_at` treat an invalid request like a null one (no value, skipped, `None`). Rows are found by identity (`item.download is download`).
- **Model signals:** connect the same request signals as `downloadmodel.cpp` (`receivedBytesChanged`, `totalBytesChanged`, `downloadFileNameChanged`, `stateChanged`, `isPausedChanged`, `interruptReasonChanged`, `destroyed`), with the same role lists in `dataChanged`, and emit `activeChanged` after each. `destroyed` removes the row.
- **Roles:** the same 12 names and readers as `downloadroles.cpp`:
  - `progress`: `-1.0` when `totalBytes <= 0`, else `min(received / total, 1.0)`;
  - `speedText`: empty unless the request is in progress, not paused and the speed is above 0; then `QLocale().formattedDataSize(n) + "/s"`, where `n` rounds the speed half away from zero (`qRound64`, not Python's `round`);
  - `mimeIconName`: `QMimeDatabase().mimeTypeForName(type or "application/octet-stream").iconName()`, or `application-octet-stream` when that is empty;
  - `state`: the state as an `int`.
- **`activeProgress`:** the mean of `received / total` over active requests with `totalBytes > 0`, clamped to 0…1, or `-1.0` when there is none.
- **`TransferSpeed`:** `restart(received)`, `update(received, elapsed_ms=None)` (with `None`, the elapsed time of its `QElapsedTimer`), `stop()`, `bytes_per_second()`. Samples shorter than 1000 ms are ignored, as in C++.
- **`DownloadManager`:**
  - The constructor connects `QCoreApplication.instance().aboutToQuit` to the model's `remove_private_downloads`, and the model's `activeChanged` to its own.
  - `handle_request(download, is_private=False)` does what `handleRequest` does: choose the target (`Settings.downloadDirectory`, the suggested file name when the name is empty; never for a save-page download), add the row, connect the notifications, accept or emit `saveLocationRequested` (when `askWhereToSave` is on and it is not a save-page download; a non-Quick request is accepted), then emit `downloadStarted`.
  - The invokables keep their guards (`pause` only an in-progress unpaused request, `openFile` only a completed one, …). `showInFolder` calls `ShowItems` on `org.freedesktop.FileManager1` with `[file URL]` and `""` on the session bus, and opens the folder with `QDesktopServices` when the interface is invalid or the call fails.

### 5. History

- **Statements:** every SQL statement of `historymanager.cpp`, `historymodel.cpp`, `historysearch.cpp` and `topsitesranking.cpp`, character for character, through `kondor.core.database.sql`.
- **`HistoryManager`:**
  - Tracked URLs: not empty, and scheme `http`, `https` or `file`. The stored text is `QUrl.toString()`.
  - `addVisit`: the latest row (by `visited_at DESC, id DESC`) gets the new title when it has the same URL and is less than 30000 ms old; otherwise a row is inserted. On success, `model.schedule_refresh()`.
  - `updateTitle`, `removeEntry` (then `refresh()`), `clearAll` (then `refresh()` and `FaviconStore.instance().clear_all()`) and `clearSince` (then `refresh()` and `FaviconStore.instance().clear_since(ms)`) as in C++.
  - `topSites`, `suggest`, `recentToday` and `hostCompletion` return Python lists of dicts (`QVariantList` of maps) with the same keys: `{type: "history", url, title}`, `{url, title}`, `{url, title, host}`, and a `str` for `hostCompletion`.
- **`HistoryModel`:**
  - `setFilter` refreshes at once; `scheduleRefresh` starts a 250 ms single-shot `QTimer` only while `active`; setting `active` to true stops the timer and refreshes.
  - A filter is trimmed, escaped with `like_pattern` and matched against `url` or `title`; at most 500 rows.
  - Roles: `id` (int), `url` (`QUrl(text).toString()`), `title`, `visitedAt` (`QDateTime.fromMSecsSinceEpoch`), `dayLabel` (`Today`, `Yesterday`, else `QLocale().toString(date, QLocale.FormatType.LongFormat)`), `time` (`QLocale().toString(time, QLocale.FormatType.ShortFormat)`). `dayLabel` is computed when the rows are loaded, `time` when it is read, as in C++.
- **`historysearch.like_pattern`:** escape `\` first, then `%` and `_`, and wrap in `%…%`.
- **`topsitesranking.top_sites`:** the same grouping and ranking: only `http`/`https` URLs with a host; host without a leading `www.`; host score = number of visits, ties by latest visit; the tile URL is the host's URL with most visits, ties by latest visit; a URL's title is the first non-empty title in `visited_at DESC, id DESC` order; hosts in `Settings.hiddenTopSites` are skipped. Use a stable sort; where C++ leaves a full tie unspecified (hash order), keep the first host or URL met in row order.

### 6. Favicons

- **`FaviconStore.attach_engine(engine: QQmlEngine)`** replaces what `create()` does in C++ (keep the engine), because `qmlRegisterSingletonInstance` has no `create()` hook. `store()` returns early while no engine is attached. Tests call it; the app calls it in phase 11.
- **Reaching Qt WebEngine's provider:** in PySide6, `engine.imageProvider("favicon")` returns the provider wrapped as `QQuickImageProvider`, without `requestImageResponse`. Get the async provider with:
  1. `pointer = shiboken6.getCppPointer(provider)[0]`;
  2. `shiboken6.invalidate(provider)`, so shiboken drops its cached wrapper;
  3. `shiboken6.wrapInstance(pointer, QQuickAsyncImageProvider)`, which is not owned by Python.

  Do this only when the wrapper is not already a `QQuickAsyncImageProvider` (a Python provider in a test already is). The architect checked this with PySide6 6.11.2 on Fedora: the result's `requestImageResponse` returns a `QQuickImageResponse`.
- **`store(pageUrl, iconSource)`:** only for `http`/`https` page URLs and icon sources starting with `image://favicon/`. Request the icon id (the source without that prefix) at 32×32; on `finished`, take `textureFactory().image()`, scale it to fit 32×32 (`KeepAspectRatio`, `SmoothTransformation`) when it is larger, and `store_image(host, image)`; then `deleteLater()` the response. Keep the response alive from Python until `finished` arrives.
- **`store_image`:** PNG bytes through a `QBuffer`; nothing is written, and `revision` does not change, when the stored bytes for the host are the same. `INSERT OR REPLACE INTO favicons (host, image, updated_at) VALUES (?, ?, ?)` with the current time in ms.
- **`clear_all` / `clear_since`:** `revision` goes up only when `numRowsAffected() > 0`.
- **`FaviconImageProvider`:** a `QQuickImageProvider` of type `Image` whose `requestImage(id, size, requested_size)` returns `FaviconStore.instance().image_for_host(QUrl(id).host())`, with the image's size reported when it is not null. Adding it to the app's engine is phase 11.

### 7. Privacy

- `remove_private_downloads` runs on `aboutToQuit`, as in C++, so a private download is never kept in the list after quitting. Nothing in this phase writes a download to disk.
- `HistoryManager.addVisit` and `FaviconStore.store` have no private-tab check in C++: their callers (`WebViewTab.qml`, `PageView.qml`) only call them for normal tabs. Keep that, and do not add new callers.

### 8. Tests

Each C++ case becomes a test with the same intent (umbrella item 9). Test functions have at most 20 lines. Database tests use the session `isolated_profile` and clear the `history` or `favicons` table first, as the C++ `init()` does; they do not delete the file.

```
pytests/downloads/
  __init__.py
  fakedownload.py
  test_transferspeed.py
  test_downloadstatus.py
  test_downloadmodel.py
  test_downloadmanager.py
pytests/history/
  __init__.py
  historyrows.py
  test_historymanager.py
  test_historysuggestions.py
  test_topsites.py
  test_historymodel.py
pytests/browser/
  __init__.py
  fakefaviconprovider.py
  test_faviconstore.py
```

- **`fakedownload.py`:** `FakeDownload(QObject)` with the request signals the model connects and the getters and setters it calls (`state`, `isPaused`, `receivedBytes`, `totalBytes`, `mimeType`, `downloadFileName`, `downloadDirectory`, `isSavePageDownload`, `accept`, `pause`, …), plus setters that emit the signals. Tests pass it with `typing.cast(QWebEngineDownloadRequest, fake)`.
- **`test_transferspeed.py`:** the three C++ cases.
- **`test_downloadstatus.py`:** `test_describes_every_state`, parametrized over the same 11 rows. It loads the staged `downloads/DownloadStatus.qml` in `kondor_engine` (so `DownloadManager.State` comes from Python) and calls its `text(download)` function with a map. Sizes use `QLocale().formattedDataSize`.
- **`test_downloadmodel.py`** (new):
  - `test_adds_a_download_once`: adding the same request twice gives one row and `count` 1.
  - `test_progress_is_unknown_without_total` and `test_progress_is_capped_at_one`.
  - `test_active_progress_averages_active_downloads`: two in-progress requests at 25 % and 75 % and a completed one give 0.5; none gives -1.
  - `test_clear_finished_keeps_active_downloads`.
  - `test_removes_private_downloads_only`: a private and a normal request; after `remove_private_downloads()` only the normal one is left.
  - `test_destroyed_download_leaves_the_list`: deleting the fake (`deleteLater` + processing deferred deletes) removes its row.
  - `test_speed_text_rounds_half_away_from_zero`.
- **`test_downloadmanager.py`** (new): `Notifier.instance().notify` is replaced with a recorder through `monkeypatch`.
  - `test_handle_request_uses_the_download_directory_and_accepts`;
  - `test_save_page_download_keeps_its_target`;
  - `test_completed_download_notifies_with_its_file_name` and `test_failed_download_notifies_with_its_reason`;
  - `test_quit_drops_private_downloads`: after `QCoreApplication.instance().aboutToQuit.emit()` (PySide6 allows it; nothing else in `kondor/` listens to it yet), a private row added through `handle_request` is gone and a normal one stays.
- **`historyrows.py`** (twin of `topsitesharness.h`): `reset_history()` (clears `history`, sets `hiddenTopSites` to `[]`), `add_visit(url, title, visited_at)`, `add_grouped_visits()`.
- **`test_historymanager.py`**, **`test_historysuggestions.py`**, **`test_topsites.py`:** the 14 C++ cases.
- **`test_historymodel.py`** (new):
  - `test_filter_matches_url_or_title_and_escapes_wildcards`;
  - `test_day_labels_say_today_and_yesterday`;
  - `test_url_at_is_empty_outside_the_rows`;
  - `test_schedule_refresh_waits_until_active`: while inactive, `schedule_refresh()` does not start the timer; `active = True` loads the rows at once.
  - `test_clear_since_accepts_milliseconds_since_epoch`: calling `clearSince` from QML (`kondor_engine`, `HistoryManager.clearSince(Date.now() - 2000)`) works, which fails with a 32-bit slot.
- **`fakefaviconprovider.py`:** a `QQuickAsyncImageProvider` subclass whose `requestImageResponse` returns a `QQuickImageResponse` subclass that serves a given `QImage` through `QQuickTextureFactory.textureFactoryForImage` and emits `finished` from a zero-delay timer.
- **`test_faviconstore.py`:** the five C++ cases, plus:
  - `test_store_saves_the_provider_icon_scaled_to_32`: a `QQmlEngine` with the fake provider added as `favicon` serving a 64×64 image, `attach_engine`, `store(QUrl("https://kde.org/"), QUrl("image://favicon/https://kde.org/icon.png"))`, wait for `revisionChanged` (`qtbot.waitSignal`): `image_for_host("kde.org")` is 32×32.
  - `test_store_ignores_other_pages_and_sources`: `about:blank`, `file:` and an icon source outside `image://favicon/` store nothing.
  - `test_image_provider_serves_the_host_of_the_page_url`: `FaviconImageProvider().requestImage("https://kde.org/a?b", size, QSize())` returns the stored `kde.org` image and fills the size.
- **`pytests/core/test_singletons.py`** needs no change: it finds the three new singletons through `kondor_types`.

### 9. API check result

After this phase, `python3 scripts/check-qml-api.py` reports **five more** classes checked and five fewer not ported than on the PR's base (`3 classes checked, 41 C++ classes not ported yet` → `8 classes checked, 36 C++ classes not ported yet` if #165 is not merged first), and exits 0.

## Acceptance criteria

- [ ] `kondor/downloads/`, `kondor/history/` and `kondor/browser/` have the modules of item 1, and their `qmltypes.py` register the five types of item 2.
- [ ] `ruff check`, `mypy --strict kondor` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` reports five more classes checked than on the base, with no problems.
- [ ] Every C++ case of the six test files in "Context" has its pytest twin, and the new tests of item 8 exist and pass: `QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests`.
- [ ] `removeEntry` and `clearSince` accept 64-bit values from QML; `suggest` accepts one or two arguments.
- [ ] Private downloads are removed from the list on quit (test).
- [ ] The `python` and `build` jobs are green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt` or the workflows. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md):

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests && python3 scripts/check-qml-api.py`: all pass, and the last reports five more classes than `main`.
2. **Profile written by C++:** build `main` with CMake and start `./build/kondor` on the temporary profile. Visit `https://kde.org/`, `https://kde.org/applications/` and `https://www.wikipedia.org/` so they get favicons, then quit. With the same `XDG_*` variables, a short Python snippet run from the PR checkout (`QGuiApplication` with organization `KDE` and application `Kondor`) must show:
   - `HistoryManager.instance().topSites(8)` lists `kde.org` first and `wikipedia.org`;
   - `HistoryManager.instance().suggest("kde", 6)` and `hostCompletion("wi")` (`wikipedia.org`) match what the C++ address bar suggests;
   - `FaviconStore.instance().image_for_host("kde.org")` is not null, and at most 32×32.
3. **Real WebEngine provider:** a throw-away script (`QtWebEngineQuick.initialize()`, a `QQmlApplicationEngine` with a `WebEngineView` loading `https://kde.org/`, `FaviconStore.instance().attach_engine(engine)`, and `FaviconStore.store(url, icon)` called from `onIconChanged`) stores a `kde.org` row in a fresh profile. The PR body says this was run.
4. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- Any class outside the three folders: `ProfileManager` (which calls `handle_request` and `clearAll`), `Tab`, the address bar and the session wait for phases 7 and 8. So does calling `attach_engine`, adding `FaviconImageProvider` to an engine, and `register_types()` from an app entry point (phase 11).
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, the C++ tests or the workflows.
- Changes to `kondor/core/`, `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker, unless a phase-4 file shows a bug in them. In that case, ask first (`question`).
- New behavior: no private-tab checks beyond the C++ ones, no history or download persistence the C++ does not have.
- Translating Python strings, or running `pyside6-lupdate` (phase 12).

## Dependencies

#164 (core, merged). Umbrella #162. Runs in parallel with #165, which touches other folders.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| How does `FaviconStore` get the engine without `create()`? | `attach_engine(engine)`, called by the app in phase 11 and by tests. `qmlRegisterSingletonInstance` gives no hook. |
| How does Python call `requestImageResponse` on Qt WebEngine's `favicon` provider? | `shiboken6.invalidate` the base-class wrapper, then `wrapInstance(pointer, QQuickAsyncImageProvider)` (checked on PySide6 6.11.2). Fetching icons another way (`QWebEngineProfile.requestIconForPageURL`) would change behavior and needs the Core profile, which QML views do not expose. |
| `DownloadModel` is `QML_ANONYMOUS` in C++: how is it registered? | As an uncreatable type `DownloadModel`, so `check-qml-api.py` pairs it with its C++ twin. QML never names it, so the extra type name is harmless. |
| How are `QPointer` downloads ported? | Keep the wrapper and check `shiboken6.isValid`; rows also leave on `destroyed`, as in C++. |
| Test the model without Qt WebEngine downloads? | A `FakeDownload` `QObject` with the same signals and methods, cast to `QWebEngineDownloadRequest` in tests. Production code keeps the real type. |
