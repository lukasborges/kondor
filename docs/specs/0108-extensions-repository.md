# Extensions repository: validation and catalog publishing (#108)

> **Issue:** [#108](https://github.com/lukasborges/kondor/issues/108) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> **Repository:** `lukasborges/kondor-extensions` (see AGENTS.md → "Extensions repository").
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Turn [`lukasborges/kondor-extensions`](https://github.com/lukasborges/kondor-extensions) into the
home of Kondor extensions:
- anyone can propose an extension by pull request;
- CI checks it;
- every merge to `main` publishes the catalog that Kondor's "Get New Extensions…" reads (#107):
  `https://lukasborges.github.io/kondor-extensions/catalog.json`.

## Context

- **Repository state:** the repository exists (public, GPL-3.0, branch `main`) with only `LICENSE`
  and a stub `README.md`. Pages is already enabled with GitHub Actions as the source, at
  `https://lukasborges.github.io/kondor-extensions/`, but nothing is deployed yet.
- **Format:** the package format, the manifest and the catalog are defined in
  [`0107-kondor-extensions.md`](0107-kondor-extensions.md), items 1 and 5. This issue implements
  the producer side and must not change the format. If it needs a change, ask a question.
- **Starting point:** no extension exists yet; #109–#118 add the first ten. The tools must work with
  zero extensions.

## Design / behavior

1. **Layout:**
   ```
   extensions/<id>/manifest.json, *.js, *.css, icon (svg/png), README.md
   schema/manifest.schema.json        JSON Schema (draft 2020-12) of the #107 manifest
   tools/validate.py                  checks extensions (stdlib only)
   tools/pack.py                      builds one .kondorext
   tools/build-catalog.py             builds the site: catalog.json, packages/, icons/, index.html
   tools/tests/                       unittest tests and fixtures for the three tools
   .github/workflows/build.yml        pull requests and main: validate + build, job name "build"
   .github/workflows/publish.yml      main and workflow_dispatch: build + deploy to Pages
   .github/pull_request_template.md, .github/ISSUE_TEMPLATE/{extension-request,bug}.yml
   .github/CODEOWNERS                 the maintainer owns everything
   README.md, CONTRIBUTING.md
   ```
2. **`tools/validate.py [--base <git ref>] [<extension dir>…]`** (default: every directory under
   `extensions/`; exit code 1 on any error). The output is one line per problem, as
   `extensions/<id>/<file>: <message>`. It checks:
   - **Schema:** everything `ExtensionPackage::load` checks (#107 item 1), plus the JSON schema.
   - **Id:** `id` equals the directory name.
   - **Package contents:** every file in the directory is referenced by the manifest, except
     `README.md` and the icon. The extension has a `README.md` with the sections "What it does",
     "Permissions" (one line per permission or site pattern, saying why) and "Network" (every
     outside service contacted, or "None").
   - **License:** `license` is an SPDX identifier from an allow list of OSI licenses compatible with
     GPL-3.0.
   - **Version bump:** with `--base`, a changed extension must have a `version` greater than at the
     base, and a removed one is allowed.
   - **Forbidden code** in `.js`, reported as errors:
     - `eval(`, `new Function(`, `setTimeout`/`setInterval` with a string argument;
     - `import(` with a non-literal argument, `importScripts(`;
     - a `<script` tag with a `src` attribute built or written by the extension;
     - `document.write(`.
   - **Minified code:** lines longer than 500 characters, or files with a long average line length,
     are rejected as minified. Extensions must be readable source.
   - **Size:** at most 5 MiB and 200 files per extension, and the icon must be SVG or a PNG of
     128×128.
3. **`tools/pack.py <extension dir> [-o <file>]`** writes a deterministic
   `<id>-<version>.kondorext`:
   - a ZIP with deflate;
   - entries sorted by name;
   - timestamps fixed at 1980-01-01;
   - `manifest.json` first.

   The same input always gives the same SHA-256. Authors use it to try an extension with
   "Install from File…".
4. **`tools/build-catalog.py <out dir>`** validates everything, then writes:
   - `packages/<id>-<version>.kondorext`;
   - `icons/<id>.<ext>`;
   - `catalog.json`, as in #107 item 5. The fields come from the manifest; `matches` is the union of
     all content script matches; `sha256` and `size` come from the package. Extensions are sorted by
     id, and `generated` is in UTC.
   - `index.html`: a simple page listing the extensions (icon, name, description, version, a
     download link to the package, and a link to its folder on GitHub), and how to install them in
     Kondor. It is English only, uses no JavaScript, and has inline CSS that follows
     `prefers-color-scheme`.

   With zero extensions it writes an empty `extensions` array and a page saying none are
   published yet.
5. **CI:**
   - **`build.yml`** runs on `pull_request` and `push` to `main`, on `ubuntu-24.04` with Python 3
     only:
     - `python3 -m unittest discover tools/tests`;
     - `tools/validate.py --base origin/main` (a full checkout with `fetch-depth: 0`);
     - `tools/build-catalog.py site`;
     - uploads `site` as an artifact.

     Its job is named **`build`**, because the Kondor agent loop waits for a check with that name.
   - **`publish.yml`** runs on `push` to `main` and on `workflow_dispatch`. It does the same build,
     then `actions/upload-pages-artifact` and `actions/deploy-pages` (`permissions: pages: write,
     id-token: write`, `environment: github-pages`).
6. **README.md:**
   - what Kondor extensions are;
   - how to install them: in Kondor, Settings → Extensions → Get New Extensions…, or download a
     `.kondorext` from the catalog page and use "Install from File…";
   - a link to the catalog page;
   - a link to CONTRIBUTING.md.
7. **CONTRIBUTING.md**, written for community authors:
   - **Quick start:** copy a folder, edit `manifest.json`, then `python3 tools/pack.py
     extensions/<id>`, then "Install from File…" in Kondor.
   - **Reference:** a link to the format and the JavaScript API,
     `https://github.com/lukasborges/kondor/blob/main/docs/extensions/api.md` (written by #107).
   - **Rules,** each with its reason:
     - one extension per PR;
     - readable source, with no minified or obfuscated code;
     - no remote code;
     - no analytics or tracking;
     - outside services only when needed, and listed under "Network";
     - the fewest permissions and narrowest `matches` that work;
     - a `version` bump on every change;
     - an OSI license compatible with GPL-3.0;
     - English in the code, with translations through `key[<locale>]`.
   - **Review:** what the maintainer checks (behavior, permissions, network, privacy), and that
     the catalog is published on merge.
   - **Requests:** how to ask for an extension (the issue form) or report a bug.
8. **Templates:**
   - **PR template:** a checklist mirroring the rules, plus "Tested in Kondor <version> with
     Install from File…".
   - **`extension-request.yml`:** fields for the name, what it should do, the sites, and similar
     extensions in other browsers.
   - **`bug.yml`:** fields for the extension and version, the Kondor version, the steps, and
     expected vs. actual behavior.

## Maintainer setup (done by the maintainer after the merge, documented in the PR)

1. ~~Enable Pages through GitHub Actions~~: done by the maintainer on 2026-11-10.
2. Protect `main`: require pull requests and the `build` check.
3. Run `publish.yml` once (`gh workflow run publish.yml --repo lukasborges/kondor-extensions`) and
   open the catalog URL.

## Acceptance criteria

- [ ] The tools work with zero extensions and with the test fixtures. `unittest` covers:
  - each validation rule (one passing and one failing fixture each);
  - the deterministic package (the same hash twice);
  - the catalog fields and the SHA-256.
- [ ] `build.yml` passes on the PR, and its job is named `build`.
- [ ] After the maintainer setup, `publish.yml` deploys `catalog.json` and `index.html`.
- [ ] README, CONTRIBUTING, the PR template, the issue forms and CODEOWNERS are in place.

## Manual test

1. Copy a fixture extension into `extensions/` locally, run `tools/validate.py`, then
   `tools/build-catalog.py /tmp/site`. Serve it with `python3 -m http.server -d /tmp/site` and
   open `index.html`.
2. Break a rule (add `eval(`, remove the README, keep the version unchanged with `--base`): each
   prints the expected error.
3. Pack the same extension twice: `sha256sum` matches.

## Out of scope

- the browser side (#107) and the extensions themselves (#109–#118);
- package signing, ratings, comments, statistics, categories;
- a custom domain or a designed website beyond the simple `index.html`.

## Dependencies

None for the tooling. The format comes from the #107 spec, so it does not need #107 merged.

## Prototype

No Kondor UI in this issue, so there is no prototype.

## Decisions

| Question | Decision |
| --- | --- |
| Where does the catalog come from? | From this repository: community pull requests, reviewed by the maintainer, published on merge (maintainer's choice). |
| Why forbid remote and minified code? | Reviewers must be able to read everything an extension runs. Code fetched at run time or obfuscated cannot be reviewed. |
