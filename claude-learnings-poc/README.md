# Claude Code Learnings — POC

A snapshot of the Claude Code configuration built while scaffolding the
Track Hub frontend (`track-hub-ui`) and backend (`track-hub-backend`).
This folder exists to document and share what was learned, not to be run
directly — the config that actually governs Claude's behavior lives
**device-wide** in `~/.claude/` on the machine it was built on, not in
either project's repo. Everything here is a copy for reference.

## Why device-wide instead of per-project

`track-hub-ui` and `track-hub-backend` are separate sibling directories,
not subfolders of one repo. A project-scoped `.claude/` config would only
ever cover one half of the product, so every piece below was deliberately
placed in the user-level `~/.claude/` directory instead — it applies to
both projects (and any future one) automatically.

## What's in here, and what it maps to

| In this folder | Lives for real at | What it does |
|---|---|---|
| `claude-md-examples/*.CLAUDE.md` | Project root of each repo | Per-project context: stack, structure, conventions, non-obvious gotchas (e.g. non-default ports). This is the one piece that's genuinely project-scoped — real copies live in each repo's own `CLAUDE.md`. |
| `skills/github-workflow/` | `~/.claude/skills/github-workflow/` | Branch strategy (`feature→dev→qa→uat→main`), commit rules (no Claude attribution, Conventional Commits), PR/merge hygiene. |
| `skills/pre-pr-review/` | `~/.claude/skills/pre-pr-review/` | Lighter review gate before opening a PR — architecture, standards, tests/lint, sensitive files, diff self-review. Generic fallback when a project has no reviewer of its own. |
| `skills/pre-qa-handoff/` | `~/.claude/skills/pre-qa-handoff/` | Gate before marking a build ready for QA — clean build, real test pass, ticket sanity check, debug-code sweep, handoff note. |
| `skills/e2e-quality-check/` | `~/.claude/skills/e2e-quality-check/` | The deep pass: unit/API/UI/DB/security/code-smell/end-to-end, all in one runnable checklist. Deliberately more thorough than the two above. |
| `agents/pr-gatekeeper.md` | `~/.claude/agents/pr-gatekeeper.md` | Subagent that actually runs build/test/lint/standards/sensitive-file/diff checks and returns PASS/FAIL. Usable standalone (`@pr-gatekeeper`) or spawned by the hook below. |
| `hooks/sensitive-canary.sh` | `~/.claude/hooks/sensitive-canary.sh` | Shell script: blocks Read/Write/Edit on `.env`, keys, credentials, secrets, etc. and logs every blocked attempt. |
| `settings.json` | `~/.claude/settings.json` | Wires up both hooks (`sensitive-canary` on Read/Write/Edit, `pr-gatekeeper` agent hook on `gh pr create`) and the `permissions.deny` rules that back them up as a second layer. |
| `PR_GATE_SETUP.md` | `~/.claude/PR_GATE_SETUP.md` | Explains why the PR gate is *enforced* (a real permission decision made by Claude Code) rather than *advisory* (a skill Claude merely tends to follow), plus how to verify/test it and its known limits. |

## The core lesson: advisory vs. enforced

Everything under `skills/` and the project `CLAUDE.md` files works by
Claude reading instructions and (usually) following them — useful, but
not a hard guarantee. `hooks/sensitive-canary.sh` and the `pr-gatekeeper`
agent hook in `settings.json` are different: they're intercepted and
decided by Claude Code itself before the tool call runs, so there's no
path for Claude to "forget" or talk itself out of them. The
`permissions.deny` rules are a third, independent layer under those same
hooks, so a single misconfiguration doesn't remove all protection.

## Known limitation, worth learning from

The `pr-gatekeeper` agent hook's `if: "Bash(gh pr create*)"` filter turned
out not to reliably restrict it to only `gh pr create` commands — it also
fired on a plain `git clone`. It's included here as-is (not silently
fixed) because that's a real, useful lesson: agent-based hooks are new and
the `if` filter should be verified empirically, not assumed to work from
the schema description alone. See `PR_GATE_SETUP.md`'s "Limits" section.
