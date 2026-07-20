---
name: pre-qa-handoff
description: Trigger whenever about to hand a build off to QA, mark a ticket "ready for QA," deploy to a QA/staging environment, or when asked "is this ready for QA" or similar, in any project or language. Runs a pre-QA-handoff gate — clean build verification, full test pass with no hidden skips, new-behavior coverage, manual sanity check against the ticket, leftover debug-code sweep, and a written QA handoff note — before anything is marked ready for QA.
---

# Pre-QA Handoff Gate

A checklist to run, in order, before marking anything "ready for QA."
Don't hand it off until every step below has actually passed.

## 0. Check for a project-specific process first

Before using the default note format in step 7, check whether this project
already has its own QA checklist or handoff template:

- A project-scoped skill with the same name (`.claude/skills/pre-qa-handoff/`
  inside the project) — wins automatically if present.
- A QA checklist or handoff template documented in `CLAUDE.md`,
  `CONTRIBUTING.md`, a `docs/` folder, or the ticket system itself.

If one exists, follow it instead of the default note in step 7 — steps
1–6 below (the actual verification work) still apply regardless of which
note format you end up writing.

## 1. Clean build check

Build from a genuinely fresh state — not whatever is already sitting
built in your working directory. Actually run the fresh-install path:

- `npm ci && npm run build` (or the project's real equivalent) —
  not `npm install`, which can mask a broken lockfile.
- For a Python project: fresh venv, `pip install -r requirements.txt`,
  run migrations, confirm the app starts.
- Confirm zero errors. "It's fine, I already had it running" is not a
  substitute for this — that's exactly the "works on my machine" gap this
  step exists to catch.

## 2. Full automated test pass

- Run the entire unit + integration suite, not a subset.
- Explicitly search for skipped/disabled tests: `.skip`, `.only` left in
  by accident, `xfail`, `@pytest.mark.skip`, `@Disabled`, commented-out
  test blocks. A skipped test silently hiding a failure is worse than no
  test at all — flag every one you find and confirm it's skipped for a
  legitimate, current reason, not forgotten.

## 3. New-behavior coverage check

- Confirm the specific new/changed behavior has a test that actually
  exercises it — passing *old* tests proves nothing about *this* change.
- If the new behavior has no test covering it, add one before proceeding.
  Don't hand off coverage gaps to QA to discover manually.

## 4. Manual sanity check against the ticket

- Re-read the original requirement/ticket in full.
- Actually exercise the feature yourself (run it, hit the endpoint, click
  through the UI) rather than reasoning about it from the diff.
- Confirm the behavior matches what was asked, including every edge case
  the ticket explicitly mentions — not just the happy path.

## 5. Leftover debug-code sweep

Grep the diff (not just skim it) for:

- `console.log`, `print(`, `debugger`, or equivalent debug output left in
- Commented-out code blocks
- `TODO`/`FIXME` markers sitting on a critical path
- Hardcoded test data, test credentials, or sample values that should be
  config/env-driven instead

## 6. Environment/config documentation

Confirm QA can actually run this without asking you first:

- New env vars — documented and named clearly (not just added silently)
- Feature flags — documented, including default state
- Migrations — noted, with the order they need to run in
- Seed/fixture data QA needs — either provided or the steps to generate it

If any of this exists only in your head, write it down now.

## 7. Write the QA handoff note

Unless a project-specific template exists (step 0), use this format:

```
## What changed
<one or two sentences — the actual behavior change, not the implementation>

## How to test
<concrete steps: URLs, commands, accounts/data needed>

## Edge cases already verified
<bullet list — what you personally exercised in step 4>

## Known limitations / out of scope
<anything intentionally not covered, so QA doesn't file it as a surprise bug>
```

Don't skip the last section — an unlisted limitation reads as a missed
bug; a listed one reads as a scoping decision.
