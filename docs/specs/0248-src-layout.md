# Move the Python package to src/kondor (src layout) (#248)

> **Issue:** [#248](https://github.com/lukasborges/kondor/issues/248) · **Priority:** P1 (high) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read `AGENTS.md` first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Now that the C++ code is gone (#174), put the Python package in the standard **src layout**:
`kondor/` moves to `src/kondor/`. The package keeps its name, so every import
(`from kondor.core.settings import Settings`) and `python3 -m kondor` stay the same. The top level
of the repository then reads `src/`, `qml/`, `tests/`, `scripts/`, `packaging/`, as it did with C++.

## Context

- `kondor/` holds the whole app (`app/`, `browser/`, `core/`, `extensions/`, `passwords/`, …),
  with `__main__.py`. `qml/` is loaded from the staged build, not from the package folder.
- Paths that name the folder today (search for `kondor/` and `"kondor"` used as a path, not as the
  package or app name):
  - `pyproject.toml`: ruff `include` (`kondor/**/*.py`), pytest and mypy settings;
  - `scripts/build.py` and `scripts/staging/` (`resources.py` lists the `.js` files under
    `kondor/passwords/bridge/`, `kondor/extensions/bridge/`, `kondor/extensions/scripts/`);
  - `scripts/update-translations.py` (`pyside6-lupdate` scans `kondor/**/*.py`);
  - `scripts/check-code-quality*`, `scripts/check-qml-api.py` and their tests in `scripts/tests/`;
  - `scripts/needs-cpp-checks.sh` if it still exists (it may be gone with #174);
  - `packaging/` (Flatpak manifest, AppImage recipe), `.github/workflows/*.yml`;
  - `README.md` and `docs/agents/developer.md`.
- Paths such as `share/kondor/…`, `packaging/kondor`, the D-Bus/app names and the GitHub URLs
  are **not** the package folder: leave them.

## Design / behavior

1. `git mv kondor src/kondor`, so `git log --follow` keeps the history. Nothing else moves.
2. **Running from the checkout:** the commands documented today keep working unchanged:
   - `python3 scripts/build.py && python3 -m kondor` — `scripts/build.py` and any wrapper put
     `src` on the import path for the staged run; if `python3 -m kondor` from the repository root
     cannot find the package any more, document `PYTHONPATH=src python3 -m kondor` in the README
     and in `docs/agents/developer.md` instead, and use it in every script and workflow;
   - `scripts/run-pytests.sh` and plain `python3 -m pytest`: pytest gets `pythonpath = ["src"]`
     in `pyproject.toml`;
   - mypy: `mypy_path = "src"` (or `files`/`packages` pointing at `src/kondor`); ruff `include`
     becomes `src/**/*.py`.
3. **Installed app:** `scripts/build.py --install`, the Flatpak and the AppImage install the same
   files to the same places as today (`…/kondor/` package in site-packages or the app's lib dir).
   No installed path changes.
4. **Quality rules:** the folder and file limits of `scripts/check-code-quality*` apply to
   `src/kondor/` as they applied to `kondor/`; `src/` itself holds only `kondor/`.
5. No code or behavior change: imports, QML type names, settings keys and data paths are
   untouched.

## Acceptance criteria

- [ ] `kondor/` no longer exists; `src/kondor/` has the same files (`git diff -M --stat` shows only
      renames, plus the path edits listed in Context).
- [ ] `scripts/run-pytests.sh`, ruff, mypy, the code-quality check, `check-qml-api.py`,
      `scripts/check-translations.py` and the `scripts/tests/` tests all pass.
- [ ] `i18n/*.ts` are unchanged after `scripts/update-translations.py` (the `.ts` hold no file
      locations, so moving files must not change them).
- [ ] The offscreen smoke test of the staged build and of `scripts/build.py --install` prints no
      QML or Python errors.
- [ ] CI is green, and the Flatpak and AppImage jobs (or `workflow_dispatch` runs) build and start.
- [ ] README and `docs/agents/developer.md` show the new paths and the run command.

## Manual test

1. `python3 scripts/build.py && python3 -m kondor` (or the documented `PYTHONPATH=src` form)
   opens the browser from the checkout.
2. `T=$(mktemp -d) && python3 scripts/build.py --install "$T/usr" && "$T/usr/bin/kondor"`
   opens it from the install, with temporary XDG dirs.

## Out of scope

- Renaming modules or classes, or moving `qml/`, `tests/` or `scripts/`.
- Packaging changes beyond the paths (no wheel, no PyPI).

## Dependencies

- #174 (the switch to Python).

## Decisions

| Question | Decision |
| --- | --- |
| `src/` as the package itself, or `src/kondor/`? | `src/kondor/`, chosen by the maintainer: the standard Python src layout. `src/` as the package would make imports `from src…` and `python3 -m src`, which is unusual and wrong once installed. |
| Do in-flight branches break? | They need a rebase; git follows the renames, so changes to moved files apply to the new paths. The developer rebases open PRs after this merges. |
