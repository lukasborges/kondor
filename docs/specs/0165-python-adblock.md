# Python port 3/12: Ad blocking (#165)

> **Issue:** [#165](https://github.com/lukasborges/kondor/issues/165) · **Priority:** P3 (low) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md), the umbrella spec [`0162-python-backend.md`](0162-python-backend.md) (items 2-5 and 9, "Rules for every phase") and the phase 2 spec [`0164-python-core.md`](0164-python-core.md) first. This file details phase 3 and must follow the umbrella. Only the architect edits it.

## Objective

Port `src/adblock/` to Python in `kondor/adblock/`, port `tests/adblock/` to `pytests/adblock/`, and add `scripts/bench-adblock.py`:

- **Same matching:** the Python `FilterEngine` blocks exactly the requests the C++ engine blocks. A parity test proves it on real filter lists and real request URLs.
- **Same QML API:** `AdBlockManager` is a QML singleton in `Kondor` 1.0, paired with its C++ twin by `check-qml-api.py`.
- **Same data:** the same cache folder and file names (`AppDataLocation/adblock/easylist.txt`, `easyprivacy.txt`), and the same settings (`adBlockEnabled`, `adBlockAllowList`, `adBlockLastUpdate`, through the Python `Settings` of #164).
- **Fast enough:** the benchmark meets the umbrella budget (item 5): median at most **50 µs** and p99 at most **500 µs** per request.
- **C++ untouched:** nothing in `src/`, `qml/`, `tests/` or `CMakeLists.txt` changes.

## Context

- **Phase 2 (#164, merged in 69ebf86)** added `kondor/core/` (`Settings`, `Database`, `sql`, `Notifier`, `FileHelper`), the `isolated_profile` and `kondor_types` fixtures, and `pytests/core/test_singletons.py`, which checks every `SINGLETON` entry of every `qmltypes.py`. `check-qml-api.py` prints `3 classes checked, 41 C++ classes not ported yet`.
- **`src/adblock/`** (1,076 lines). It uses only `core/settings`:

  | C++ file | What it does |
  | --- | --- |
  | `adblockmanager.{h,cpp}` | QML singleton `AdBlockManager`: properties `enabled` (read/write, stored in `Settings.adBlockEnabled`), `updating`, `lastUpdate`; invokables `isAllowed`, `setAllowed(host, allowed, persistent = true)`, `blockedCount`, `updateLists`; signals `blockedCountChanged(host)`, `allowListChanged`. C++-only: `install(profile)`, `start()`, `setEngine()`, `cacheDirectory()`. Loads the cached lists off the UI thread (`QtConcurrent::run` + `QFutureWatcher`), and queues one more load when one is running |
  | `adblockinterceptor.{h,cpp}` | `QWebEngineUrlRequestInterceptor`: a main-frame request emits `pageStarted(host)`; any other request, when enabled, is checked against the engine unless its first-party host is allowed, and a match is blocked and emits `blocked(firstPartyHost)` |
  | `adblockallowlist.{h,cpp}` | plain class: the persistent list (in `Settings.adBlockAllowList`) plus session allows and session blocks, all lower-cased |
  | `filters/filterrule.{h,cpp}` | `FilterRule` and `parseFilterRule(line)`: skips comments, `[…]` headers, cosmetic rules, regex rules and rules with an unknown option |
  | `filters/filteroptions.{h,cpp}` | `$` options: `third-party`, `~third-party`, `domain=a|~b`, the five type options; `optionsMatch` |
  | `filters/filterpattern.{h,cpp}` | pattern matching with `*` and `^`, tokens (ASCII `[a-z0-9]` runs of 3 or more), `registrableDomain`, `hostMatches` |
  | `filters/filterrequest.h` | `FilterRequest` and `makeFilterRequest(url, firstPartyHost, kind)` (implemented in `filterpattern.cpp`) |
  | `filters/filterengine.{h,cpp}` | `FilterEngine`: rules indexed by host, by token, and the rest; `shouldBlock(url, firstPartyHost, kind)` = any blocking rule matches and no exception rule matches |
  | `lists/filterlists.{h,cpp}` | the two list sources (EasyList, EasyPrivacy), the cache paths, `isCacheStale` (4 days, or a missing file), `parseFilterLists(files)` |
  | `lists/filterlistdownloader.{h,cpp}` | `QNetworkAccessManager` downloads with `If-Modified-Since`, `NoLessSafeRedirectPolicy`, a 60 s transfer timeout, `QSaveFile`, and a 1,024-byte minimum; `finished(isAnyListCurrent)` |

- **Users outside the folder:** `browser/profile/profilesetup.cpp` calls `install(profile)` for every profile, and `app/startup/appstartup.cpp` calls `start()`. Both are ported in later phases (#169, #173).
- **QML users:** `qml/adblock/AdBlockButton.qml`, `qml/adblock/AdBlockPopup.qml` and `qml/settings/pages/PrivacySettingsPage.qml`. `AdBlockPopup.qml` calls `setAllowed` with 3 arguments, passing `!tab.isPrivate` as `persistent`, so a private tab never writes the allow list.
- **`tests/adblock/`:**

  | C++ test | Cases |
  | --- | --- |
  | `tst_filterengine.cpp` | `domainAnchor`, `domainWithPath`, `exceptionsWin`, `thirdPartyOption`, `typeOptions`, `substringAndWildcard`, `separatorCaret`, `skippedRules`, `mainFrameNeverBlocked`, `addList`, `domainOptionIncludesAndExcludesSites`, `countryCodeSecondLevelDomainIsFirstParty`, `endAnchorRequiresTheEndOfTheAddress` |
  | `tst_adblockallowlist.cpp` | `sessionAllowDoesNotTouchSettings`, `sessionBlockOverridesThePersistentList`, `persistentChoiceReplacesTheSessionChoice` |

## Design / behavior

Port, don't redesign (umbrella item 9): the same behavior and edge cases as the C++, with the Python conventions of umbrella item 3. C++ free functions become module functions in snake_case.

### 1. Layout

```
kondor/adblock/
  __init__.py                (empty)
  qmltypes.py
  adblockmanager.py
  adblockinterceptor.py
  adblockallowlist.py
  filters/
    __init__.py              (empty)
    filterrule.py
    filteroptions.py
    filterpattern.py
    filterrequest.py
    filterengine.py
  lists/
    __init__.py              (empty)
    filterlists.py
    filterlistdownloader.py
    filterlistloader.py
scripts/bench-adblock.py
pytests/adblock/
  __init__.py                (empty)
  enginecases.py
  test_filterengine.py
  test_filterrequest.py
  test_filterlists.py
  test_engine_parity.py
  test_adblockallowlist.py
  test_adblock_qml.py
pytests/data/adblock/
  easylist.txt
  easyprivacy.txt
  requests.txt
  expected.json
```

- `filterrequest.py` holds `FilterRequest` and `make_filter_request` (in C++ the function lives in `filterpattern.cpp`; here it moves next to its type).
- `filterlistloader.py` is the only new module name: it replaces `QFutureWatcher` (item 7).
- `enginecases.py` holds the small helper the engine tests share (the C++ `Request` struct and `blocked()`), so each test file stays under 200 lines.
- Further splits for the limits are allowed if they keep the C++ base names for the existing modules.

### 2. `qmltypes.py`

```python
QML_TYPES: tuple[QmlType, ...] = (
    QmlType(AdBlockManager, "AdBlockManager", QmlKind.SINGLETON),
)

def register_types() -> None:
    register(QML_TYPES)
```

Importing it must not create any instance (`check-qml-api.py` imports it without a `QCoreApplication`). `AdBlockInterceptor` and `FilterListDownloader` are not registered: QML never sees them.

### 3. Filters (`kondor/adblock/filters/`)

- **`ResourceKind`** (in `filterengine.py`): an `enum.IntFlag` with the C++ values: `MAIN_FRAME = 1`, `SUB_FRAME = 2`, `STYLESHEET = 4`, `SCRIPT = 8`, `IMAGE = 16`, `XML_HTTP_REQUEST = 32`, `OTHER = 64`.
- **`FilterRule`:** a `@dataclass(slots=True)` with `pattern`, `host`, `anchor_start`, `anchor_end`, `exception`, `type_mask`, `third_party` (an `enum.Enum` `ThirdParty`: `ANY`, `ONLY_THIRD_PARTY`, `ONLY_FIRST_PARTY`), `domains_include` and `domains_exclude` (`list[str]`). `parse_filter_rule(line: str) -> FilterRule | None`.
- **`FilterRequest`:** a `NamedTuple` or slotted dataclass with `url`, `rest`, `host`, `first_party_host`, `third_party`, `kind`. `make_filter_request(url: QUrl, first_party_host: str, kind: ResourceKind) -> FilterRequest`:
  - `url` is `url.toString(FullyEncoded | RemoveFragment)` lower-cased, exactly as C++;
  - `host` is `url.host()` lower-cased;
  - `rest` is the text after the first occurrence of the host after `://`, or `""`.
- **`FilterEngine`:** `add_list(text: bytes)`, `add_rule(line: str) -> bool`, `rule_count() -> int`, `should_block(url: QUrl, first_party_host: str, kind: ResourceKind) -> bool`.
  - `add_list` splits on `b"\n"` and decodes each line as UTF-8 with `errors="replace"` (the counterpart of `QString::fromUtf8`).
  - The three indexes are `dict[str, list[FilterRule]]` by host, `dict[str, list[FilterRule]]` by token, and `list[FilterRule]`, filled in the same order as C++.
  - `should_block` returns false for `MAIN_FRAME`, for an empty engine and for schemes other than `http`, `https`, `ws`, `wss`.
- **Character rules that must not drift:**
  - "Alphanumeric" means ASCII `a-z` and `0-9` only, as `isAlnum` in `filterpattern.cpp`. Do **not** use `str.isalnum()`, which accepts any Unicode letter and digit and would change the tokens.
  - A separator (`^`) is any character that is not ASCII `a-z0-9` and not one of `_-.%`, or the end of the text.
  - The token length minimum is 3. A pattern's token is its longest run that is bounded on both sides (not next to `*`; at the pattern edge only when the matching anchor is set); the first of equal-length runs wins, as in C++.
  - `trimmed()` becomes `str.strip()`, `toLower()` becomes `str.lower()`, `split()` keeps empty parts as `str.split()` does, `lastIndexOf('$')` becomes `str.rfind("$")`.
- **Speed:** matching runs on the UI thread for every subresource request (umbrella item 5). Keep the C++ data structures; inside them, Python-level speed-ups are allowed when the parity test still passes, for example:
  - pre-splitting a rule's pattern on `*` once at parse time instead of on every match;
  - returning early from the token loop as soon as a rule matches.

  If the budget cannot be met with the same index structure, ask (`question`) before changing the algorithm (umbrella item 5).

### 4. `AdBlockAllowList`

A plain class (not a `QObject`), the same as C++: `is_allowed(host)`, `set_persistent(host, allowed)`, `set_for_session(host, allowed)`, `hosts() -> set[str]`. Hosts are lower-cased; an empty host is ignored. The persistent part is `Settings.instance().adBlockAllowList`, written through its setter.

### 5. `AdBlockInterceptor`

- A `QWebEngineUrlRequestInterceptor` subclass with `interceptRequest(info)` (Qt's name), `set_engine(engine: FilterEngine | None)`, `set_enabled(enabled: bool)`, `set_allowed_hosts(hosts: set[str])`, and the signals `blocked(str)` and `pageStarted(str)` (kept as in C++).
- The resource-type mapping is the C++ one: `ResourceTypeSubFrame`, `ResourceTypeStylesheet`, `ResourceTypeScript`, `ResourceTypeImage` and `ResourceTypeXhr` map to their kinds, everything else to `OTHER`. A `ResourceTypeMainFrame` request only emits `pageStarted` with the lower-cased host.
- **No lock.** In Qt 6 a profile's interceptor runs on the UI thread, and the loader hands the new engine over on the UI thread (item 7), so `QReadWriteLock` and `std::atomic` are dropped. An engine is never changed after it is handed over.

### 6. `AdBlockManager`

- **Singleton:** `instance()` returns one module-level object (umbrella item 3). The constructor does what the C++ one does: creates the interceptor and the downloader as its children, applies `adBlockEnabled` to the interceptor, syncs the allowed hosts, and connects to the `Settings.instance()` signals, the interceptor, the loader and the downloader.
- **QML API** (checked by `check-qml-api.py`):
  - `enabled` (`bool`, read/write, notify `enabledChanged`): reads and writes `Settings.adBlockEnabled`; `enabledChanged` is emitted when that setting changes, as in C++;
  - `updating` (`bool`, read-only, notify `updatingChanged`): the downloader's state;
  - `lastUpdate` (`QDateTime`, read-only, notify `lastUpdateChanged`): `Settings.adBlockLastUpdate`;
  - `isAllowed(host) -> bool`, `blockedCount(host) -> int` (host lower-cased), `updateLists()`;
  - `setAllowed(host, allowed, persistent = True)`: it must accept **2 and 3** arguments, as the C++ default argument does. Stack two `@Slot` decorators (`(str, bool)` and `(str, bool, bool)`) on one method;
  - signals `enabledChanged`, `updatingChanged`, `lastUpdateChanged`, `blockedCountChanged(str)`, `allowListChanged`.
- **Python-only methods** (snake_case; called by the phases that port `profilesetup` and `appstartup`): `install(profile: QQuickWebEngineProfile)` calls `profile.setUrlRequestInterceptor(self._interceptor)`; `start()` loads the cached lists, then calls `updateLists()` when `is_cache_stale(lastUpdate)`; `set_engine(engine)`; `cache_directory()` (static).
- **Counts:** in memory only, per first-party host, as C++: `blocked` adds one and emits `blockedCountChanged`; `pageStarted` resets to 0 and emits only when the count was not 0.
- **After a download:** when `finished(is_any_list_current)` is true, set `Settings.adBlockLastUpdate` to `QDateTime.currentDateTime()` and reload the cached lists.

### 7. Lists (`kondor/adblock/lists/`)

- **`filterlists.py`:** `FilterListSource` (`url`, `file_name`), `filter_list_sources()`, `filter_cache_directory()` (`AppDataLocation + "/adblock"`), `filter_cache_path(source)`, `cached_filter_list_files()`, `is_cache_stale(last_update: QDateTime) -> bool` (invalid, at least 4 days old by `daysTo`, or a list file missing), `parse_filter_lists(files: list[str]) -> FilterEngine` (files that cannot be opened are skipped).
- **`filterlistdownloader.py`:** `FilterListDownloader(QObject)` with `update()`, `is_updating()`, and the signals `updatingChanged` and `finished(bool)`. The same request (`NoLessSafeRedirectPolicy`, `setTransferTimeout(60000)`, `If-Modified-Since` from the cached file's `lastModified().toUTC()`), the same save rule (`QSaveFile`, only when the error is `NoError`, the status is 200 and the body is longer than 1,024 bytes), and a 304 counts as current. The `QNetworkAccessManager` is created on the first `update()`.
- **`filterlistloader.py`:** `FilterListLoader(QObject)` replaces `QtConcurrent::run` + `QFutureWatcher` (PySide6 cannot run a Python callable with `QtConcurrent`):
  - `load(files: list[str])` starts `parse_filter_lists(files)` on a daemon `threading.Thread` and returns at once;
  - `is_running() -> bool`;
  - signal `loaded(object)`, emitted from the worker thread with the new `FilterEngine`. The loader lives on the UI thread, so the connection is queued and the manager receives the engine on the UI thread.
  - The manager keeps the C++ rule: when `loadCachedLists` is called while a load runs, it loads again once the running one has handed over its engine.

### 8. Benchmark: `scripts/bench-adblock.py`

- Builds a `FilterEngine` from `pytests/data/adblock/easylist.txt` and `easyprivacy.txt` (the lists Kondor enables by default) with `parse_filter_lists`, and builds every `QUrl` of `requests.txt` before timing.
- Times each `should_block` call with `time.perf_counter_ns()` over all the requests, 5 rounds, after one warm-up round.
- Prints one line each: rule count, parse time in seconds, number of requests, number blocked, median µs and p99 µs.
- Exits 1 when the median is above 50 µs or the p99 above 500 µs, else 0.
- It is not run in CI (timings depend on the machine). The PR body reports its output on the developer's machine.
- Add it to `[tool.ruff] include` in `pyproject.toml`. It must pass `ruff check`, `mypy --strict scripts/bench-adblock.py` and the code-quality limits.

### 9. Test data: `pytests/data/adblock/`

- **`easylist.txt` and `easyprivacy.txt`:** unmodified snapshots of `https://easylist.to/easylist/easylist.txt` and `https://easylist.to/easylist/easyprivacy.txt`, downloaded once. Their own header keeps the version and license lines (GPLv3 or CC BY-SA 3.0, compatible with Kondor's GPLv3). The PR body gives the download date.
- **`requests.txt`:** at least **2,000** real subresource requests, one per line: `<kind> <first-party host> <url>`, where `<kind>` is a `ResourceKind` name (`SUB_FRAME`, `STYLESHEET`, `SCRIPT`, `IMAGE`, `XML_HTTP_REQUEST`, `OTHER`).
  - Record them by loading about 20 public news, shopping and video home pages with ad blocking **off**, on an isolated profile, with a throw-away Python script (not committed) that logs what a `QWebEngineUrlRequestInterceptor` sees.
  - Drop exact duplicate lines. Keep the file order.
  - No logged-in pages and no personal data in any URL.
  - At least 10% of the lines must be blocked by the snapshots.
- **`expected.json`:** `{"ruleCount": <n>, "blocked": [<0-based line numbers>]}` from the **C++** `FilterEngine` over the same three files. The developer writes it with a throw-away local change to `tests/adblock/tst_filterengine.cpp`, run on an isolated profile, then discards the change. Nothing in `tests/` is committed. The PR body says how the file was made (as for the #164 fixtures).

### 10. Tests: `pytests/adblock/`

Each C++ case becomes a test with the same intent (umbrella item 9). Test functions have at most 20 lines.

- **`test_filterengine.py`:** the 13 cases of `tst_filterengine.cpp`, as `test_domain_anchor`, `test_domain_with_path`, … `test_end_anchor_requires_the_end_of_the_address`.
- **`test_filterrequest.py`:**
  - `test_drops_the_fragment_and_lower_cases`: `https://Ads.Example.com/A.js?x=1#Frag` gives the url `https://ads.example.com/a.js?x=1`, the host `ads.example.com` and the rest `/a.js?x=1`;
  - `test_encodes_non_ascii_paths`: a path with `é` comes out percent-encoded, as `QUrl::FullyEncoded`;
  - `test_tokens_are_ascii_only`: `url_tokens` of `https://a.org/abcé123/xy` gives `{"https", "org", "abc", "123"}`.
- **`test_filterlists.py`:**
  - `test_cache_is_stale_without_an_update_or_a_file`: an invalid `QDateTime` is stale; a current one is stale while a list file is missing, and not stale once both files exist in the isolated `AppDataLocation/adblock`;
  - `test_cache_is_stale_after_four_days`;
  - `test_parse_skips_missing_files`: one existing file with two rules plus one missing path gives `rule_count() == 2`.
- **`test_engine_parity.py`:** `test_matches_the_cpp_engine_on_real_requests`: the snapshots give `expected.json`'s `ruleCount`, and the set of blocked line numbers of `requests.txt` equals `expected.json`'s `blocked`. On failure, the message lists the first 10 differing lines.
- **`test_adblockallowlist.py`:** the 3 cases of `tst_adblockallowlist.cpp`, on `AdBlockManager.instance()`, with the same reset fixture as the C++ `init()`.
- **`test_adblock_qml.py`:** `import Kondor; QtObject { … }` reads `AdBlockManager.enabled`, `updating`, `lastUpdate` and `blockedCount("example.org")`, calls `setAllowed("example.org", true)` with **2** arguments and then `isAllowed("example.org")`. It loads from the staged module with no warnings, and the result is `true`. Reset the allow list afterwards.
- **`test_singletons.py`** needs no change: it picks up `AdBlockManager` from `kondor/adblock/qmltypes.py`.
- **No network in tests.** No test calls `updateLists()` or `start()` with a stale cache.

### 11. API check result

`python3 scripts/check-qml-api.py` reports `AdBlockManager` checked with no problem, and the number of C++ classes not ported yet drops by one (`4 classes checked, 40 C++ classes not ported yet` when this phase merges right after #164; one more checked class for each other phase merged before it). `AdBlockInterceptor` and `FilterListDownloader` stay in the "not ported yet" count, because QML never sees them.

## Acceptance criteria

- [ ] `kondor/adblock/` has the modules of item 1, and `kondor/adblock/qmltypes.py` registers `AdBlockManager` as a singleton.
- [ ] `ruff check`, `mypy --strict kondor`, `mypy --strict scripts/bench-adblock.py` and `python3 scripts/check-code-quality.py` pass, and `scripts/code-quality-baseline.json` is unchanged.
- [ ] `python3 scripts/check-qml-api.py` checks `AdBlockManager` with no problem (item 11).
- [ ] Every C++ case of `tests/adblock/` has its pytest twin, and the extra tests of item 10 exist and pass with `QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests`.
- [ ] `test_engine_parity.py` passes against `expected.json` written by the **C++** engine, on at least 2,000 real requests of which at least 10% are blocked.
- [ ] `python3 scripts/bench-adblock.py` exits 0 on the developer's machine (median ≤ 50 µs, p99 ≤ 500 µs), and its output is in the PR body.
- [ ] `setAllowed` accepts 2 and 3 arguments from QML.
- [ ] The `python` job and the `build` job are green.
- [ ] Nothing changes in `src/`, `qml/`, `tests/`, `CMakeLists.txt`, `.github/` or the packaging files. No pip.

## Manual test

On Fedora 45 with the packages of the #163 spec, in a clean checkout of the PR branch, with temporary `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_CACHE_HOME` (AGENTS.md):

1. `ruff check && mypy --strict kondor && python3 scripts/build.py && QT_QPA_PLATFORM=offscreen dbus-run-session -- pytest pytests && python3 scripts/check-qml-api.py`: all pass, and the last checks `AdBlockManager`.
2. `python3 scripts/bench-adblock.py`: exits 0; the numbers are close to the PR body's.
3. **Cache written by C++:** build `main` with CMake and start `./build/kondor` on the temporary profile; wait until `AppDataLocation/adblock/` has both lists, then quit. With the same `XDG_*` variables, a short Python snippet run from the PR checkout (`QGuiApplication` with organization `KDE` and application `Kondor`) must show:
   - `is_cache_stale(Settings.instance().adBlockLastUpdate)` is false;
   - `parse_filter_lists(cached_filter_list_files()).rule_count()` is above 50,000;
   - for the host of a `||<host>^` line with no `$` options in the cached `easylist.txt`, `should_block(QUrl("https://<host>/x.js"), "example.com", ResourceKind.SCRIPT)` is true.
4. **Real download:** in a snippet with a running event loop, on a new temporary profile, `AdBlockManager.instance().updateLists()` downloads both lists into `AppDataLocation/adblock/`, `updating` goes true then false, and `lastUpdate` becomes the current time.
5. `python3 scripts/check-code-quality.py --changed origin/main`: no output.

## Out of scope

- Any class outside `src/adblock/`. Calling `install()` and `start()` from the profile setup and the app startup is done by #169 and #173.
- Brave's `adblock` engine, regex rules, cosmetic rules, or any other change to what is matched (umbrella item 5).
- A different index or matching algorithm without a `question` first (umbrella item 5).
- Running the benchmark in CI.
- Any change to `src/`, `qml/`, `tests/`, `CMakeLists.txt`, `.github/`, `scripts/build.py`, `scripts/check-qml-api.py` or the quality checker, unless a phase-3 file shows a bug in them. In that case, ask first (`question`).
- Translating Python strings (phase 12).

## Dependencies

#164 (core, merged). Umbrella #162.

## Prototype

None: no UI.

## Decisions

| Question | Decision |
| --- | --- |
| How is "same matching" proven? | A parity test over about 2,000 real request URLs and the two real lists, against block verdicts written by the **C++** engine (`expected.json`). The ported unit tests cover the rule syntax; only real data catches drift in tokens, Unicode and URL encoding. Rejected: Python-only expected values, which would only prove Python agrees with itself. |
| `QtConcurrent::run` + `QFutureWatcher` in PySide6? | `FilterListLoader`: a daemon `threading.Thread` that emits `loaded(object)` to a `QObject` on the UI thread (queued). PySide6 cannot run Python callables with `QtConcurrent`. Parsing holds the GIL in slices, so the UI may stutter briefly during a load; the benchmark reports the parse time. Rejected: parsing on the UI thread, which freezes the window for the whole parse. |
| Keep `QReadWriteLock` and `std::atomic` in the interceptor? | No. In Qt 6 the profile interceptor runs on the UI thread, and the engine is handed over on the UI thread, so there is no concurrent access. |
| Where does `makeFilterRequest` go? | `filterrequest.py`, next to `FilterRequest`. In C++ it sits in `filterpattern.cpp` only because `filterrequest.h` has no `.cpp`. |
| How does Python accept `setAllowed` with 2 or 3 arguments? | Two stacked `@Slot` decorators on one method, so `check-qml-api.py` sees both counts, as moc generates for a C++ default argument. |
| Should the benchmark run in CI? | No: timings depend on the runner. It exits non-zero over budget, the developer runs it, and the PR body reports the numbers. |
