# Release notes

Each release has its notes here, in `v<version>.md`, and the Release workflow publishes that file
as the GitHub release text. A tag without its notes file fails the release.

Write them for people who use Kondor, not for developers:

- open with one or two sentences on what the release brings;
- group by what the user can do (tabs, passwords, extensions…), not by pull request;
- say what changed for the user in plain words; no issue numbers, file names or refactors;
- end with the fixes a user would have noticed.

Every merged fix or feature is released (the maintainer's decision): a fix is a patch release, a
feature a minor one. A release with one change gets one or two sentences.

To release, from a worktree at `origin/main`:

```bash
scripts/release.sh --next patch     # prints the next version, e.g. 0.3.1
$EDITOR docs/releases/v0.3.1.md     # write the notes
scripts/release.sh patch            # bumps the version, commits, pushes, tags and pushes the tag
```
