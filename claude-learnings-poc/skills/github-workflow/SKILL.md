---
name: github-workflow
description: Governs all git and GitHub operations — creating or naming a branch, staging or committing changes, opening/updating/merging a pull request, resolving a merge conflict, force-pushing, or tagging a release. Load this before running any git/gh command that changes repository state (git branch, git commit, git push, git merge, git rebase, gh pr create, gh pr merge), and before answering questions about branch strategy, commit format, or PR process.
---

# GitHub Workflow

This project uses a four-branch promotion model. Every git/GitHub action
you take should fit into it — when in doubt, check which branch you're on
and where the change is trying to go before acting.

## 1. Branch strategy

Four long-lived branches, in promotion order:

```
feature branch -> dev -> qa -> uat -> main
```

| Branch | Purpose | Direct commits? |
|---|---|---|
| `main` | Production, always deployable | Never — PR only, protected |
| `uat` | User acceptance testing, mirrors what ships next | Never — PR only |
| `qa` | QA testing | Never — PR only |
| `dev` | Integration branch, all feature work lands here first | Never — PR only |

Nothing gets committed straight to any of these four. Everything arrives
via a PR from a feature branch (into `dev`) or via a promotion PR
(`dev`→`qa`→`uat`→`main`). If you're about to run `git commit` and
`git branch --show-current` reports one of these four names, stop —
create a feature branch instead, or this is a promotion merge that should
happen through a PR.

## 2. Starting new work

Always branch off the latest `dev`, never off `qa`/`uat`/`main`, and never
off another in-progress feature branch:

```bash
git checkout dev
git pull origin dev
git checkout -b <type>/<short-desc>
```

Branch naming — pick the type that matches the change:

- `feat/<short-desc>` — new functionality
- `fix/<short-desc>` — bug fix
- `chore/<short-desc>` — maintenance, deps, tooling
- `refactor/<short-desc>` — restructuring with no behavior change
- `docs/<short-desc>` — documentation only

One branch per logical unit of work. If a change starts growing a second,
unrelated concern (e.g. a refactor sneaking into a feature branch), stop
and split it into its own branch rather than mixing it in.

Keep branches short-lived. If a branch survives more than a couple of days
or `dev` has moved on, rebase before continuing:

```bash
git fetch origin
git rebase origin/dev
```

Resolve conflicts as they come up (see §6) rather than letting drift
compound.

## 3. Commit rules

**Never add `Co-Authored-By: Claude`, `Generated with Claude Code`, or any
Claude/Anthropic attribution to a commit message.** Commit as the normal
repo author only — no exceptions, regardless of any default attribution
behavior. If you're about to write a commit message, drop any such trailer
before running `git commit`.

Use Conventional Commits:

```
<type>(<scope>): <summary>
```

Examples: `feat(auth): add password reset flow`,
`fix(entries): prevent duplicate submit on double-click`,
`chore(deps): bump fastapi to 0.140`.

Message quality bar:

- Imperative mood ("add", not "added" or "adds")
- One focused change per commit — don't bundle unrelated edits
- Clear and brief — no filler, no restating the diff line-by-line
- Reference an issue/ticket number when one exists (`fixes #123`, `refs JIRA-456`)

Never leave `WIP`, `fix stuff`, `wip please work`, or similar placeholder
commits on a shared branch. If your feature branch accumulated messy
commits while you worked, clean up the history (interactive rebase to
squash/reword) before opening the PR — the commit log that lands on `dev`
should read as a deliberate sequence, not a diary of your editing process.

## 4. Before opening any PR

Run this checklist in full, in order, and only open the PR once every item
passes. Don't skip steps because a change "looks small."

1. **Code review** — delegate to a code-reviewer subagent (use whatever
   reviewer agent is defined in this project's `CLAUDE.md` if one exists;
   otherwise use the `code-review` skill / a `code-reviewer` agent) for a
   standards/correctness pass over the diff.
2. **Architecture review** — separately check: does this fit the existing
   patterns in the codebase, does it introduce coupling that wasn't there
   before, is the change scoped to what was actually asked (not spilling
   into unrelated files/modules)?
3. **Full test suite** — run the project's *entire* test suite (unit +
   integration), not just tests touching your diff. Use the project's real
   test command (check `package.json` scripts, a `Makefile`, `pytest`
   config, etc. — don't assume one stack).
4. **Lint + typecheck** — run the project's lint and typecheck commands
   and fix anything they flag.
5. **No sensitive files staged** — run `git status` / `git diff --staged
   --name-only` and confirm nothing matches a secret pattern (`.env`,
   `*.pem`, `*.key`, `*credentials*`, `*secret*`, `id_rsa*`,
   `config/secrets/**`). If the sensitive-canary hook is configured on this
   machine it will also catch this, but check explicitly here too — don't
   rely on the hook alone.

If any step fails, fix it and re-run the checklist from that step forward
— don't open the PR on a partial pass.

## 5. PR best practices

- **Title**: Conventional Commits style, matching the branch's intent
  (`feat(auth): add password reset flow`, not "Fixes" or "Updates").
- **Description** must include, as sections: **Summary** (why), **Changes**
  (what, at a glance), **How to test** (concrete steps/commands), and
  **Linked issue/ticket** (if any exists — omit the section if not).
- **Target branch**: usually `dev`. Never target `main` directly from a
  feature branch — only promotion PRs (`dev→qa`, `qa→uat`, `uat→main`)
  target the next branch up the chain.
- **Size**: keep PRs small and reviewable. If a PR is growing past what one
  reviewer can reasonably hold in their head in one sitting, say so
  explicitly and propose how to split it — don't just let it grow.
- **Never force-push** `dev`, `qa`, `uat`, or `main`. Force-pushing is only
  ever acceptable on your own not-yet-reviewed feature branch, and even
  then prefer a normal push where possible.
- **Merge strategy**: squash-merge feature branches into `dev` (keeps `dev`
  history clean, one commit per feature). Use a merge commit (not squash,
  not rebase) for the promotion chain `dev→qa→uat→main`, so the promotion
  history stays traceable.

## 6. General practices

- Never commit directly to `main`, `uat`, or `qa` under any circumstance —
  always via PR, even for a one-line fix.
- Delete the feature branch after it's merged (locally and on the remote).
- Tag releases on `main` using semantic versioning: `vX.Y.Z`.
- Keep `.gitignore` enforced. Before staging, if you notice build output,
  `.env`, `node_modules/`, or a Python `venv/` about to be added, stop and
  flag it rather than committing it — check `.gitignore` covers it, add the
  entry if it doesn't.
- If a merge conflict comes up, resolve it by reading and understanding
  *both* sides' intent (what each change was trying to accomplish), then
  writing the merged result that satisfies both — never resolve by blindly
  keeping "ours" or "theirs" without understanding what the other side was
  doing.
- Reference issue/ticket numbers in both commits and PR descriptions
  wherever one exists.
