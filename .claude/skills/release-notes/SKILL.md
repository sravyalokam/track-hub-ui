---
name: release-notes
description: Generate release notes from a set of git commits (raw messages, `git log` output, or a commit range between tags/branches) in the Chorus PMO deployment-notes format — "Users Stories Targeted", release-pipeline line, and a "Deployed Items" list. Use when asked to draft release notes, deployment notes, or a "what shipped" summary for a PMO/Chorus release, or to turn a commit list into that Word-template style doc.
---

# Release Notes Generator (Chorus PMO format)

This skill turns a list of commits into a single Markdown file that mirrors
the Chorus PMO team's real deployment-notes template (the `PMO-UAT-Release`
/ `PMO-PROD-Release` `.docx` files), **not** a generic conventional-commit
changelog. Do not substitute a Features/Bug Fixes/Improvements-style
markdown structure — this format was confirmed against real prior release
docs and must be followed exactly, even when the commit list doesn't map
neatly onto every section.

## Exact output format

```markdown
# {App}_{Version} Deployment Notes

## OVERALL STEPS
**During the Day:** All things needed for deployment like raising pull
requests from {SOURCE_ENV} to {TARGET_ENV} for ({TARGET_ENV} release) along
with pull request links should be provided here.
**Next Day:** Once production is completed, delete local branch cleanup
party!

## Users Stories Targeted
- Bug {ticket_id}: {rewritten, user-facing sentence}
- {ticket_id}: {rewritten, user-facing sentence}

{Repo label} Repos – Release Pipelines
{Repo name 1} – Release {N}
{Repo name 2} – Release {N}

## {App}: Deployed Items
The following are the updates as per this release:
- {rewritten, user-facing sentence}
- {rewritten, user-facing sentence}
```

Formatting rules that come directly from the real docs:

- The title line is always `{App}_{Version} Deployment Notes`, where
  `Version` is a dotted date like `2026.07.08` (year.month.day of the
  release), not a semver tag.
- `OVERALL STEPS` is a fixed, boilerplate block — reproduce it verbatim
  with only `{SOURCE_ENV}` / `{TARGET_ENV}` substituted (e.g. `QA` →
  `UAT`, or `UAT` → `PROD`). Never rewrite its wording.
- **Users Stories Targeted** lists only commits that carry a ticket
  reference. Bug-tracker tickets get the literal prefix `Bug {id}:`;
  everything else (features, tasks, config changes) gets just `{id}:`
  with no prefix. **Omit this entire heading** if no included commit has
  a ticket id.
- The repo/release-pipeline line is plain text (not a bullet), naming
  each repo that shipped and its release/build number. This information
  is **never derivable from commit messages** — ask the user for it
  (repo name(s) + release number(s)) if not supplied.
- **`{App}: Deployed Items`** is one flat bullet list in plain, user-facing
  English — it is **not** split into Features/Bug Fixes/Breaking Changes
  sections. Real docs mix fixes and enhancements together in one list.
  This list includes every included commit (ticketed and un-ticketed
  alike), each rewritten as a single-line, user-facing sentence.
  - If a release is unusually large and the source docs group items
    under bold sub-headers (e.g. "Project Configuration & Domain
    Management") with nested sub-bullets, that grouping is acceptable —
    but only add it when there are genuinely many related items; default
    to one flat list.
- **Breaking changes**: the template has no dedicated section for these.
  When a commit is marked breaking (`feat!:`, `fix!:`, or a `BREAKING
  CHANGE:` footer), keep it in the Deployed Items list but prefix the
  bullet with `**Breaking Change:** ` so it isn't lost.
- If a whole optional section has zero entries (no ticketed commits, no
  breaking changes), omit that heading entirely — never print a heading
  with no content under it.

## Header fields you cannot get from commits

`{App}`, `{Version}`/date, `{SOURCE_ENV}`, `{TARGET_ENV}`, repo name(s),
and release/build number(s) are operational details, not something a
commit list encodes. Ask the user for these before finalizing rather than
guessing. Reasonable defaults if the user has no preference:
`{Version}` = today's date as `YYYY.MM.DD`; `{SOURCE_ENV}`/`{TARGET_ENV}`
= `UAT`/`PROD` (Chorus's actual release path is QA → UAT → PROD).

## File naming

Match the team's actual convention (confirmed against their real release
docs):

```
PMO-{ENV}-Release (DD-Month-YYYY).docx
```

e.g. `PMO-UAT-Release (20-July-2026).docx`, `PMO-PROD-Release (10-July-2026).docx`.
`{ENV}` is the **target** environment (`UAT` or `PROD`), not the source.
Older docs used a `PMO-{ENV}-Release-Doc(DD-Month-YYYY).docx` variant (no
space before the parenthesis, `-Doc` suffix) — that convention is
deprecated; use the space-and-no-`-Doc` form above for anything new.

While iterating on a draft within a session (before the user has confirmed
final content), do **not** invent descriptive suffixes like `_styled`,
`_v2`, `_final` — they accumulate and aren't informative. Use a plain
`-draft1`, `-draft2`, ... suffix on the working filename instead, and
rename to the real convention above only once the user confirms it's
final.

If the target file is locked (commonly: it's already open in Word),
`scripts/generate_docx.py` falls back to saving as `{name}_new.docx` and
prints a warning rather than failing silently or overwriting blindly once
it becomes writable — surface that fallback path to the user rather than
treating the save as having succeeded at the intended name.

## Locating the actual source of truth

The commits almost never live in the directory you're launched in. Before
asking the user to paste anything, check for a real git repo nearby:
nested subdirectories, sibling folders, or paths referenced in earlier
conversation/memory. A release commonly spans **multiple repos** (e.g. a
UI/frontend repo and a backend repo) that each need their own `qa`/`uat`
check — the format supports this natively (multiple `{repo}` entries under
one `{Repo label} Repos – Release Pipelines` heading).

Once found, treat the remote-tracking branch as ground truth, not the
locally checked-out one — `git fetch origin <branch>` before reading
`origin/<branch>`, since a stale local branch can silently omit recent
pushes. Re-fetch again right before finalizing a doc if meaningful time
has passed in the conversation — branch state changes underneath you
(a commit can be reverted mid-session; see below).

## Scoping to the right app/module

When the user asks for notes on one app/module specifically (e.g. "PMO,
not Process Compliance"), don't rely on commit message wording alone —
check which files each commit actually touched. Look for a consistent
path or class-naming convention that separates modules (e.g. a
`processcompliance/` directory in the frontend, or `Standup*`/
`ClientStandup*`/`ProcessCompliance*` class names in the backend) and
classify each commit by what it touches, not by guessing from the
message. Flag genuinely mixed commits (touching both modules) rather than
silently assigning them to one side.

## Before counting a commit as "new" for this release

Date-filtered logs (`--since`) are not reliable evidence that a commit is
actually new and unreleased. Two failure modes to check for on every
release, not just when something looks suspicious:

1. **Already shipped.** A commit can reappear in a `--since`-filtered log
   of a dev/qa branch even though it's already an ancestor of the branch
   you're releasing *to* (`uat`/`master`) — typically from a rebase or
   cherry-pick that replays old work with a fresh date/hash. Before
   including a commit, check:
   `git branch -r --contains <hash>` (or `git merge-base --is-ancestor
   <hash> origin/<target>`) against the target branch. If it's already
   there, exclude it — it's not part of what this release adds.
2. **Reverted within the window.** If a later commit in the same window
   undoes an earlier one (check the diff, not just the message — messages
   like "Removed X" or "Revert" are hints but the actual line-level
   reversal is the proof), the net effect for this release is zero.
   Exclude both sides rather than reporting a change that will read as
   self-contradictory, and mention the revert to the user since it may
   matter for their planning even though it doesn't belong in the notes.

## Merging multi-commit and cross-repo features

A single user-facing change frequently lands across more than one commit
(e.g. schema + DAO wiring + service wiring landing as three separate
commits over a few days) or across more than one repo (the same fix
committed once on the backend and once on the frontend). Recognize this
by reading the actual diffs, not just titles, and write **one** bullet for
the underlying change — never one bullet per commit when they're really
the same feature/fix. Two commits with near-identical messages and stats
landing at the same timestamp are usually the same change duplicated
across branches (cherry-pick/rebase artifact) — verify with
`git branch -r --contains` before treating them as two separate items.

## Schema-only or unverifiable changes

A DB migration with no corresponding service/controller code in the same
window may be prep for a feature that hasn't landed yet, or a fix for
schema drift — not something a user can currently see. Don't assert it as
a shipped, user-facing feature. Flag it to the user as unconfirmed and let
them decide whether to include it, rather than guessing either way.

## Optional: side-heading bullet style

When the user wants a short, non-technical bold lead-in before each
bullet's full description (e.g. `**Sprint Workdays Accuracy:** The
Timeline now generates...`), keep the heading itself business-facing —
avoid implementation words (backend, API, service names) in the heading
even if the description below it needs them for precision.

## Word (.docx) output

When the user wants a `.docx` instead of (or in addition to) Markdown, use
`scripts/generate_docx.py` rather than reinventing the styling by hand.
It reproduces the exact styling reverse-engineered from a real template
(`PMO-UAT-Release-Doc(04-June-2026).docx`): centered title in dark blue
(`#0F4761`), bold section headers in bright blue (`#0F9ED5`), 12pt
paragraph spacing, and native Word bullets (`List Bullet` style,
justified). Build a spec dict/JSON matching the shape documented in the
script's docstring and run:

```
python scripts/generate_docx.py spec.json "PMO-UAT-Release (DD-Month-YYYY).docx"
```

Don't hand-roll `python-docx` calls inline each time — extend
`generate_docx.py` if the spec shape needs a new field, so the styling
stays centralized and consistent across runs.

## Input handling

Accept commits in any of these forms and pipe the text into
`scripts/classify_commits.py`, which auto-detects the format:

- **Raw commit messages**, one per line.
- **`git log --oneline` output** (hash + subject per line) — the script
  strips the leading hash.
- **Full `git log` output** (`commit <hash>` / `Author:` / `Date:` /
  indented message body) — the script parses each block and also reads
  the message body, which is where `BREAKING CHANGE:` footers live.
- **A commit range between two tags/branches**, e.g.
  `git log v1.2.0..v1.3.0 --oneline`. Note: this means the *list of
  commits in that range*, not a code diff — a raw `git diff` between
  tags has no commit messages to classify, so ask the user to re-run
  with `git log` if they hand you a code diff instead.

Run it like:

```
python "scripts/classify_commits.py" < commits.txt
```

or pipe `git log` output directly into it. It prints one JSON record per
commit:

```json
{
  "raw": "fix: correct percentage rollup on Project Tracker (#15268)",
  "type": "fix",
  "scope": null,
  "subject": "correct percentage rollup on Project Tracker (#15268)",
  "ticket_id": "15268",
  "is_bug": true,
  "breaking": false,
  "excluded": false,
  "exclude_reason": null
}
```

The script only classifies and extracts structure (type, ticket id,
breaking flag, excluded flag). **It never writes prose** — rewriting each
`subject` into a polished, user-facing sentence for the final document is
your job, not the script's.

## Classification rules

1. **Conventional-commit prefix, when present, wins.** `feat:` → feature,
   `fix:` → bug fix, `perf:` → usually user-facing (include),
   `refactor:`/`revert:` → usually internal (excluded by default, but the
   script flags these as borderline — check the subject wording yourself;
   a `refactor:` that changed user-visible behavior should still be
   included). `chore:`, `test:`, `ci:`, `build:`, `style:`, `docs:` are
   **always excluded** — they're process/internal and never appear in
   these release docs.
2. **No prefix? Use keyword heuristics** on the subject line:
   - Fix-shaped: contains fix/fixes/fixed, bug, resolve(d/s), correct(ed),
     broken, crash, incorrect(ly), error, defect, issue, regression.
   - Feature-shaped: contains add(ed/s), implement(ed/s), introduce(d/s),
     support(ed/s), new, enable(d/s), allow(ed/s).
   - Otherwise: excluded with reason "no conventional prefix and no
     recognizable keyword — classify manually", surfaced to you so you
     make the final call instead of silently dropping or misclassifying
     it.
3. **Always excluded, regardless of prefix:** merge commits (`Merge pull
   request ...`, `Merge branch ...`), and messages matching noise
   patterns (`wip`, `typo`, `lint`, `formatting`, version-bump commits).
4. **Ticket/PR extraction**, checked in this order: `Bug #1234` /
   `Bug 1234` (bug-tracker style, sets `is_bug=true`), Jira-style keys
   (`PROJ-1234`), GitHub-style (`#1234`), or a bare leading ticket number
   in the Chorus style (`15268: description`). Preserve whatever id form
   was found — don't renumber or reformat it, and don't invent a link
   URL that wasn't given to you.
5. **Rewriting terse commits**: if a subject is a fragment, uses code
   identifiers, or is otherwise not a clean sentence a non-engineer could
   read (e.g. `fix pagination`, `refactor SprintService.calc()`), rewrite
   it into a complete, user-facing sentence describing the observable
   effect — not the implementation. Never copy a terse or jargon-heavy
   message verbatim into the final doc. Do not fabricate detail that
   isn't implied by the commit message/diff/ticket title you were given.

## Output requirements

- Produce **one Markdown file** in the exact structure above.
- Keep each bullet to one line where possible; if a change genuinely
  needs more explanation, a short nested bullet is acceptable (matches
  the real docs' occasional sub-bullets) but don't default to it.
- Omit any heading that would have zero entries — never emit an empty
  section.
- Before finalizing for a new commit set, show the generated notes to
  the user for confirmation, especially the header fields you had to ask
  about or default.

## Workflow

1. Get the commit input from the user (paste, file, or `git log` command
   output) and the header fields (app name, version/date, source/target
   env, repo name(s) + release number(s)) — ask for whichever of these
   are missing.
2. Run `scripts/classify_commits.py` on the commit input.
3. Read the JSON output. Drop everything with `excluded: true`. For
   anything with a non-null `exclude_reason` but `excluded: false`
   (the borderline `refactor`/`revert`/unknown cases), make an explicit
   judgment call and note briefly why.
4. Rewrite each remaining `subject` into one clean, user-facing sentence.
5. Split into: ticketed items → **Users Stories Targeted** (with
   `Bug`-prefix logic), all included items → **Deployed Items**.
6. Assemble the Markdown file per the exact format above, omitting empty
   sections.
7. Show the result to the user before treating it as final.
