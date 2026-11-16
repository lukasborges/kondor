# Release notes

Each release has its notes here, in `v<version>.md`, and the Release workflow publishes that file
as the GitHub release text. A tag without its notes file fails the release.

Write them for people who use Kondor, not for developers:

- open with one or two sentences on what the release brings;
- group by what the user can do (tabs, passwords, extensions…), not by pull request;
- say what changed for the user in plain words; no issue numbers, file names or refactors;
- end with the fixes a user would have noticed.

To release: write the notes, bump the version (`pyproject.toml`, `PROJECT_VERSION`, the
`--version` test, a `<release>` line in the metainfo), push, then tag `v<version>` and push the tag.
