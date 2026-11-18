# Version control and release process

Use feature branches, descriptive commits, pull requests and CI checks before merging into main. The root VERSION file records the planned/current development version. Keep CHANGELOG.md updated alongside it.

## Semantic Versioning

- MAJOR: incompatible changes.
- MINOR: backward-compatible features.
- PATCH: backward-compatible fixes.
- Before 1.0.0 the application is still in development.

## Historical milestone tags

From a clean clone, fetch the current repository and check existing tags first:

```bash
git fetch origin --tags
git tag --list
```

If the following tags do not yet exist, create annotated tags at the verified historical commits:

```bash
git tag -a v0.1.0 0b6a41f2914c48cc2601cddddb997c37aacffab0 -m "Sprint 1 milestone"
git tag -a v0.2.0 9581c436a7d305e350f6799792805a2819728eea -m "Sprint 2 milestone"
git push origin v0.1.0 v0.2.0
```

Never overwrite existing published tags. These are retrospective milestone labels.

## Publishing v0.3.0

After the versioning PR is merged, verify all CI jobs and Render deployment. Update local main with `git pull --ff-only origin main`. Confirm the intended release commit and VERSION, then (if the tag does not exist) run:

```bash
git tag -a v0.3.0 -m "Testing and deployment milestone"
git push origin v0.3.0
```

On GitHub, open Releases > Draft a new release, choose the matching existing tag, and use the corresponding changelog section as release notes. Mark development releases as pre-releases. Publish v1.0.0 only after final acceptance, updating VERSION and CHANGELOG first.

## Demonstration

Show branches, commits, merged pull requests, tags, release notes and the CI job results. Inspect a historical version without changing your working files using `git show v0.1.0`. To try old code in isolation, use a separate clone or worktree.
