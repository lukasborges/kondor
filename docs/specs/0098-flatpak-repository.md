# Self-hosted Flatpak repository (#98)

> **Issue:** [#98](https://github.com/lukasborges/kondor/issues/98) · **Priority:** P2 (medium) · **State:** see the issue's label (`to-spec` / `to-dev` / `in-review`).
> Read [`AGENTS.md`](../../AGENTS.md) first. This file is the source of truth for the issue; only the architect edits it.

## Objective

Let people install Kondor with one click and receive updates through `flatpak update` and Discover,
without Flathub. Every release tag publishes the Flatpak to a signed OSTree repository on GitHub
Pages, at `https://lukasborges.github.io/kondor/`.

## Context

- #25 (PR #97) adds the manifest `packaging/flatpak/io.github.lukasborges.Kondor.yml`, the
  AppStream metainfo, a `flatpak` job in `release.yml` that builds `Kondor.flatpak` with
  `flatpak/flatpak-github-actions/flatpak-builder@v6` in the `ghcr.io/flathub-infra/flatpak-github-actions:kde-6.11`
  container, a `flatpak-upload` job that attaches the bundle to the release, and
  `.github/workflows/flatpak.yml`, which builds the manifest on pull requests. **This issue starts
  after #25 is merged** and extends those files. It adds no new build path.
- A bundle installed with `flatpak install Kondor.flatpak` never updates. Flathub is not an option
  for now because of its policy on AI-generated applications (disclosure required, and reviewers may
  reject; see the [revised policy](https://github.com/flathub-infra/documentation/commit/43e6e1579eee941dcd645c49a7fa9db95c47bc7b)).
- GitHub Pages serves static files, which is all an OSTree repository needs. Limits: a site of at
  most 1 GB and soft bandwidth of 100 GB per month. Each deployment replaces the whole site, so the
  workflow must carry the previous commits forward itself.
- The repository is not enabled for Pages yet (`gh api repos/lukasborges/kondor/pages` → 404).

## Design / behavior

1. **Branch.** The app is exported on branch `stable` (`branch: stable` input of the action, or
   `--default-branch=stable`). The bundle uses the same branch.
2. **Signing key.** CI signs with a dedicated GPG key, read from the repository secret
   `FLATPAK_GPG_PRIVATE_KEY` (ASCII-armored, no passphrase). It is imported into a temporary
   `GNUPGHOME` and the key id is taken from the import. On a tag build, a missing secret fails the
   job with "FLATPAK_GPG_PRIVATE_KEY is not set: see docs/specs/0098-flatpak-repository.md". The key
   must never change after the first release, since installed clients would reject the repository.
   The secret is created by the maintainer (see "Maintainer setup"), not by the developer.
3. **Publishing, in the `flatpak` job of `release.yml`** (tags only):
   1. Restore the published repository. `ostree init --mode=archive-z2 --repo=repo`; if
      `https://lukasborges.github.io/kondor/repo/summary` exists, add it as an OSTree remote
      (`--no-gpg-verify` is fine here, since the content is re-signed below) and `ostree pull
      --mirror` it into `repo`. On the first release, nothing is published yet: start from the
      empty repository and print a notice.
   2. Build with the action into that same `repo` directory, signed (`gpg-sign: <key id>`, with
      `GNUPGHOME` exported), and keep producing `Kondor.flatpak`. If the action cannot export into
      an existing repository, call `flatpak-builder --repo=repo --gpg-sign=… --gpg-homedir=…`
      directly in that step.
   3. `flatpak build-update-repo --gpg-sign=<key id> --gpg-homedir=… --generate-static-deltas
      --prune --prune-depth=2 --title="Kondor Browser" repo`. This also refreshes the summary and
      the AppStream branch, so Discover shows the name, icon, description and screenshots.
   4. Build the site directory: `site/repo/` (the repository), `site/kondor.flatpakrepo` and
      `site/io.github.lukasborges.Kondor.flatpakref` (from the templates in item 4, with `GPGKey=` set
      to `gpg --export <key id> | base64 -w0`), and a `site/index.html` that redirects to the README's
      Download section.
   5. **Size guard:** fail if `du -sb site` is above 900 MB. Print the size of the site and of the
      largest file in the log.
   6. Upload `site/` with `actions/upload-pages-artifact`. A new `pages` job on `ubuntu-24.04` runs
      `actions/deploy-pages` (`needs: flatpak`, `permissions: pages: write, id-token: write`,
      `environment: github-pages`).
4. **Templates** in `packaging/flatpak/`, with `@GPGKEY@` replaced by the workflow:
   - `kondor.flatpakrepo`: `Title=Kondor Browser`,
     `Url=https://lukasborges.github.io/kondor/repo/`, `Homepage=https://github.com/lukasborges/kondor`,
     `Comment`/`Description` (the README tagline), the `Icon` URL of `packaging/kondor.svg` on
     `raw.githubusercontent.com`, and `GPGKey=@GPGKEY@`.
   - `io.github.lukasborges.Kondor.flatpakref`: `Title=Kondor Browser`,
     `Name=io.github.lukasborges.Kondor`, `Branch=stable`, the same `Url`, `SuggestRemoteName=kondor`,
     `Homepage`, `Icon`, `IsRuntime=false`, `GPGKey=@GPGKEY@`, and
     `RuntimeRepo=https://dl.flathub.org/repo/flathub.flatpakrepo`, so the KDE runtime and BaseApp
     still come from Flathub.
5. **Bundle updates.** `Kondor.flatpak` is built with the repository URL and the public key
   (`flatpak build-bundle --repo-url=https://lukasborges.github.io/kondor/repo/ --gpg-keys=<public
   key file> --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo … stable`), so a bundle
   install also receives updates from the repository and can still fetch the KDE runtime on a
   system without the Flathub remote (as the bundle of #25 does). If the action has no input for
   the key, build the bundle with that command in a step after the build.
6. **Pull-request check** (`.github/workflows/flatpak.yml`). It runs steps 3.2–3.5 with a throwaway
   key generated in the job (`gpg --batch --passphrase '' --quick-gen-key "Kondor CI test" rsa3072
   sign never`). It skips the mirror (3.1) and the deployment (3.6). It then checks the result:
   ```bash
   flatpak remote-add --user --gpg-import=<public key file> kondor-test site/repo
   flatpak remote-ls --user kondor-test   # must list io.github.lukasborges.Kondor (stable)
   ```
   Keep the site as a workflow artifact.
7. **README.** The Download section gets Flatpak as the first option:
   - one-click install: open the `.flatpakref` link in Discover, or run
     `flatpak install --user https://lukasborges.github.io/kondor/io.github.lukasborges.Kondor.flatpakref`;
   - updates arrive in Discover and through `flatpak update`;
   - the AppImage stays as the second option.
   - Drop the "Flathub submission is a later step" wording added by #25. Flathub is simply not
     mentioned.

## Maintainer setup (done by the maintainer, before the first tag after the merge)

1. Create the signing key on a trusted machine and keep an offline backup of it:
   `gpg --batch --passphrase '' --quick-gen-key "Kondor Flatpak repository" rsa4096 sign never`.
2. Store it: `gpg --export-secret-keys --armor <key id> | gh secret set FLATPAK_GPG_PRIVATE_KEY --repo lukasborges/kondor`.
3. Enable Pages with GitHub Actions as the source:
   `gh api -X POST repos/lukasborges/kondor/pages -f build_type=workflow`.
4. Allow release tags to deploy to Pages. GitHub creates the `github-pages` environment with a
   deployment policy that only admits the default branch, so a deployment started by a tag is
   rejected ("Tag "v…" is not allowed to deploy to github-pages due to environment protection
   rules"):
   `gh api -X POST repos/lukasborges/kondor/environments/github-pages/deployment-branch-policies -f name='v*' -f type=tag`.

The developer documents these steps in the PR description and does not perform them.

## Acceptance criteria

- [ ] The `Flatpak` pull-request check builds a signed repository, and `flatpak remote-ls` lists
  the app on `stable` with the throwaway key.
- [ ] On a tag, the release gets `Kondor.flatpak` and the Pages site is deployed with `repo/`,
  `kondor.flatpakrepo`, `io.github.lukasborges.Kondor.flatpakref` and `index.html`.
- [ ] A second tag keeps the previous commit (prune depth 2) and adds a static delta; the site stays
  under the 900 MB guard.
- [ ] A tag build without `FLATPAK_GPG_PRIVATE_KEY` fails with the message from item 2. The AppImage
  release is still created, since it is a separate job.
- [ ] `release.yml` and `flatpak.yml` pass `actionlint` (if available) and `README.md` shows the
  Flatpak install.

## Manual test

This is done by the maintainer after the setup and the next tag:
1. On a user without Kondor:
   `flatpak install --user https://lukasborges.github.io/kondor/io.github.lukasborges.Kondor.flatpakref`.
   It installs without GPG errors and pulls the KDE runtime from Flathub.
2. Open the same `.flatpakref` in Discover: it shows Kondor Browser with icon and description.
3. Tag a patch release: `flatpak update` (and Discover's Updates page) offers the new version.
4. Install the `Kondor.flatpak` bundle on another user, then tag a release: `flatpak update`
   updates it as well.

## Out of scope

- Flathub submission;
- RPM/COPR, Snap, a beta or nightly channel, ARM builds;
- a custom domain or a download landing page beyond the redirecting `index.html`;
- signing the AppImage;
- any change to the app itself.

## Dependencies

#25 (PR #97) merged.

## Prototype

No UI for this issue, so there is no prototype.

## Decisions

| Question | Decision |
| --- | --- |
| Where is the repository hosted? | GitHub Pages of `lukasborges/kondor`: no new account, free for a public repository, served over HTTPS. If the site outgrows the 1 GB limit, the repository moves to object storage in a follow-up issue. |
| How are previous commits kept when Pages replaces the whole site? | Each release mirrors the published repository (`ostree pull --mirror`) before exporting the new build, and prunes to depth 2. |
| Does the bundle built by the script still name a runtime repository? (review of PR #101) | Yes: `flatpak build-bundle` gets `--runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo`, like the bundle the action built for #25. Without it, installing `Kondor.flatpak` fails on a system that has no Flathub remote. |
| Can a tag deploy to the `github-pages` environment? (review of PR #101) | Not by default: the environment only admits `main`. The maintainer adds a `v*` tag policy (Maintainer setup, step 4); the workflow keeps `environment: github-pages`. |
