# PR Gate Setup

This documents a device-wide (`~/.claude/`) enforcement mechanism that
blocks `gh pr create` until a full quality check actually passes. It
applies to every project on this machine, not just one repo.

## Why this is different from a skill or a CLAUDE.md instruction

Everything else in `~/.claude/skills/` (`pre-pr-review`, `pre-qa-handoff`,
`e2e-quality-check`, `github-workflow`) works by *instructing* Claude —
it's context loaded into the conversation that Claude is expected to
follow. That's real, but it's advisory: if Claude gets distracted, forgets,
or is told to skip a step, nothing stops the PR from going out anyway.

This PR gate is enforced by **Claude Code itself**, not by Claude choosing
to comply. The moment a `gh pr create*` command is about to run, the CLI
intercepts it *before execution*, regardless of what Claude currently
believes or intends, and only lets it through if a spawned checking agent
explicitly returns an `allow` decision. There's no path for a PR to get
raised without this gate firing (subject to the limits below) — it isn't
a suggestion Claude reads, it's a permission decision the harness makes.

## The three pieces

### 1. `~/.claude/agents/pr-gatekeeper.md` — the checklist

A subagent definition (`tools: Read, Grep, Glob, Bash`) that runs six
checks in order — build, full test suite, lint/typecheck, coding
standards vs. `CLAUDE.md`/`.claude/rules/*.md`, a sensitive-file check,
and a full diff self-review — using real tool calls, not assumptions. It
ends with a single verdict: `PASS` (one-line summary of what was actually
run) or `FAIL` (exact failures + fixes).

It's usable two ways:

- **Standalone**: run `@pr-gatekeeper` yourself any time you want a manual
  check, independent of actually raising a PR.
- **Automatically**: the hook below spawns it every time `gh pr create`
  runs.

### 2. The hook in `~/.claude/settings.json`

```jsonc
"PreToolUse": [
  // ...existing Read|Write|Edit sensitive-canary entry...
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "agent",
        "if": "Bash(gh pr create*)",
        "timeout": 300,
        "statusMessage": "Running pr-gatekeeper checks before raising PR...",
        "prompt": "..."
      }
    ]
  }
]
```

- **`matcher: "Bash"`** — this hook only ever considers Bash tool calls.
- **`if: "Bash(gh pr create*)"`** — of those, it only actually fires for
  commands matching this pattern, so ordinary `git status`, `npm test`,
  etc. never spawn an agent. This is what makes it cheap enough to leave
  on permanently.
- **`type: "agent"`** — unlike a `command` hook (which just runs a shell
  script and reads its exit code/stdout), this spawns a real, separate
  agent instance with actual tool access. It doesn't take Claude's own
  word for it — it makes an independent agent go verify.
- **`timeout: 300`** — the agent default is 60s, which a real build + full
  test suite will usually blow through. 300s gives it room.
- **`prompt`** — tells the spawned agent to read
  `$HOME/.claude/agents/pr-gatekeeper.md` and execute its checklist
  exactly, then return one of two exact JSON shapes (see below).

### 3. This file — the writeup

Explains the mechanism, how to verify it, how to test it, and its limits.

## How the allow/deny decision flows

1. Claude (in any project, any conversation) runs a Bash command.
2. Claude Code checks it against every `PreToolUse` hook's `if` filter.
   If it doesn't match `Bash(gh pr create*)`, this hook does nothing.
3. If it matches, Claude Code pauses the `gh pr create` call and spawns a
   fresh agent with the `prompt` above as its instructions.
4. That agent reads `pr-gatekeeper.md`, actually runs the build/test/lint
   commands, checks the diff, etc.
5. It replies with exactly one JSON object:
   - `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}`
     → the original `gh pr create` command proceeds.
   - `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}`
     → the command is blocked, and the reason is surfaced back to Claude
     (and you) so it's clear exactly what needs fixing before trying again.

## Verifying it's wired up correctly

Run `/hooks` inside Claude Code and look for the `Bash` matcher under
`PreToolUse` with the `gh pr create*` filter — it should show `type: agent`
and the 300s timeout. `/hooks` is also where you'd disable it temporarily
if needed.

If you edit `settings.json` again later, re-run:

```bash
python -c "import json; json.load(open(r'C:\Users\Sravya Lokam\.claude\settings.json'))"
```

to confirm it's still valid JSON before assuming the change took effect —
a broken `settings.json` silently disables *everything* configured in that
file, not just this hook.

## Testing the failure path

Intentionally break something, then try to raise a PR, and confirm it
actually gets blocked rather than sailing through:

1. In a real project with a working build/test setup, introduce a
   deliberate failure — e.g. a syntax error, a failing assertion in an
   existing test, or a leftover `console.log`/`print(` in the diff.
2. Stage the change and attempt `gh pr create --title "test" --body
   "test"`.
3. Confirm the command is denied and the reason names the actual failure
   (not a generic message).
4. Revert the deliberate breakage, confirm a clean `gh pr create` is
   allowed through.

Do this once after setup, and again any time you change the hook prompt or
the checklist file, to confirm you didn't quietly break the gate itself.

## Limits — read this before relying on it

- **Agent-based hooks are an evolving/experimental mechanism.** The exact
  behavior (default tool access, timeout semantics, output parsing) may
  change between Claude Code versions. Re-verify this setup after
  upgrading Claude Code.
- **The `if` filter is best-effort pattern matching, not a hard security
  boundary.** `Bash(gh pr create*)` is a string-prefix-style match — it's
  meant to skip unnecessary agent spawns cheaply, not to be relied on as
  the only thing standing between an attacker and an unchecked PR. For
  anything that needs harder enforcement, pair this with explicit
  `permissions.deny` rules (as already exists for sensitive files) rather
  than depending on this hook alone.
- **This only catches `gh`-CLI-based PR creation.** If a PR is opened
  through the GitHub web UI, a different git client, or any path that
  doesn't go through `gh pr create` in a Bash tool call Claude Code sees,
  this gate never fires — nothing here can stop that route. If web-UI PR
  creation is a real risk in your workflow, that needs a different gate
  (e.g. a branch-protection rule requiring a passing CI check on GitHub's
  side), not this hook.
