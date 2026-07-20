---
name: pre-pr-review
description: Trigger whenever about to raise, open, or prepare a pull request — or when asked to "get this ready for PR," "review before I raise a PR," "is this PR-ready," or similar, in any project or language. Runs a pre-PR review gate — architecture fit, coding standards, full test/lint/typecheck run, sensitive-file staging check, and a full diff self-review — before any PR is opened or its description is drafted.
---

# Pre-PR Review Gate

A checklist to run, in order, before a PR is opened. Don't open the PR
until every step below has actually passed — not "probably fine."

## 0. Check for a more specific process first

Before running this generic checklist, check whether *this* project defines
its own review process that should take precedence:

- A project-scoped skill with the same name (`.claude/skills/pre-pr-review/`
  inside the project) — if one exists, it wins automatically and you
  shouldn't be reading this file for that project.
- A reviewer subagent or checklist named explicitly in this project's
  `CLAUDE.md`.
- A project-specific PR template (`.github/PULL_REQUEST_TEMPLATE.md`) —
  use its sections instead of the generic template in step 6.

If the project also has a device-wide `github-workflow` skill loaded,
that's expected and not a conflict: treat it as covering the *git
mechanics* (branch naming, commit format, merge strategy, target branch)
while this skill covers the *review substance*. Run both.

If nothing project-specific exists, run the full checklist below.

## 1. Architecture review

Ask, honestly, of the actual diff:

- Does this fit the existing patterns in the codebase, or does it invent a
  new way to do something the codebase already has a convention for?
- Does it introduce coupling that wasn't there before (a module reaching
  into another's internals, a new cross-cutting dependency)?
- Is it scoped to one concern? A refactor riding along with a feature, or
  a fix that also "cleans up" unrelated code, should be flagged and split
  out rather than waved through.

## 2. Coding standards review

- Check `CLAUDE.md` (if present) for stated conventions and confirm the
  diff follows them.
- Run the project's actual linter/formatter config (eslint, ruff, black,
  prettier, etc.) rather than eyeballing style.
- Spot-check naming, file placement, and error handling against a couple
  of neighboring files — does this change look like it belongs here?

## 3. Full verification run

- Run the **entire** test suite (unit + integration) — not just tests
  that touch the changed files. Use the project's real command (check
  `package.json` scripts, `Makefile`, `pytest`/`tox` config — don't guess).
- Run lint and typecheck and resolve everything they flag.
- If any of this fails, fix it and re-run from the top of this step —
  don't proceed on a partial pass.

## 4. Sensitive-file check

- Run `git status` and `git diff --staged --name-only`.
- Confirm nothing staged matches a secret pattern: `.env`, `.env.*`,
  `*.pem`, `*.key`, `*credentials*`, `*secret*`, `id_rsa*`, anything under
  `config/secrets/`.
- Do this explicitly even if a sensitive-canary hook is configured on this
  machine — the hook is a backstop, not a substitute for checking.

## 5. Diff self-review

Read the **full** diff top to bottom, once, as if it were someone else's
PR you're reviewing cold — not a final glance at whatever you just typed:

- Does every hunk still make sense in context, or did earlier edits leave
  something half-finished?
- Any leftover debug output, commented-out code, or stray TODOs?
- Any edge case that a genuinely adversarial reviewer would poke at?

## 6. Draft the PR — only after 1–5 pass

- **Description**, in sections: **Summary** (why this change exists),
  **Changes** (what changed, at a glance), **How to test** (concrete
  steps/commands a reviewer can run), **Linked ticket** (if one exists —
  omit the section if not).
- **Target branch**: confirm it's the correct base (typically `dev`, never
  `main` directly) before opening — check the project's branch model if
  one is documented (e.g. a `github-workflow` skill) rather than assuming.

If steps 1–5 haven't all passed, don't draft the description yet — go back
and fix what failed first.
