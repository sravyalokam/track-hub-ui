---
name: e2e-quality-check
description: Trigger before raising a PR, before sending a "build ready for QA" notification/email, or when asked to "test this end to end," "do a full check before I ship this," "make sure this is solid before QA," or similar — any language, any project. Runs a deep, comprehensive quality pass across unit tests, API, UI, database/queries, security, code quality, and full end-to-end functional behavior. This goes deeper than the lighter pre-pr-review and pre-qa-handoff checklists — use it when a genuinely thorough pre-ship pass is being asked for, not as a replacement for those on every routine change.
---

# End-to-End Quality Check

This is an execution checklist, not a reading list. For each section below,
actually run the command, grep the diff, or read the file it names — don't
mark a section "passed" from memory or intuition.

## 0. Check for a project-specific process first

- Look for CI config (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`)
  or a documented testing/QA checklist in the repo. If CI already
  automates a category below (e.g. a security-scan job, a full E2E suite),
  treat that as authoritative for that category and don't hand-duplicate
  it — just confirm it's green.
- If a project-scoped skill of this same name exists
  (`.claude/skills/e2e-quality-check/` inside the project), it takes
  precedence — you shouldn't be reading this file for that project.
- This skill is the deep pass. `pre-pr-review` and `pre-qa-handoff` are
  lighter, routine gates. Running this checklist satisfies both of those —
  don't run all three back-to-back for the same change.

## 1. Unit testing

- Find the project's real test runner (`package.json` scripts, `pytest`,
  `go test ./...`, `cargo test`, `mvn test`, etc.) and run the **full**
  suite — not a filtered subset.
- `git diff` the changed files; for each new/changed piece of logic,
  confirm a corresponding test exists. Missing coverage on new logic is
  **Blocking**.
- Open the actual test file content for changed/added tests — check the
  assertions test real behavior, not just "didn't throw"
  (`expect(x).toBeTruthy()`, bare `assert result`, `assert.ok(x)` with no
  value check are red flags — read what they're actually asserting).
- Confirm edge cases are covered for changed logic: empty input,
  null/undefined, boundary values (0, -1, max/overflow), invalid types. If
  a changed function takes input and none of these appear in its tests,
  flag it.
- Grep for skip/disable markers and read each hit for a current, valid
  reason: `.skip(`, `xit(`, `xdescribe(`, `@pytest.mark.skip`, `xfail`,
  `@Disabled`, `t.Skip(`, `#[ignore]`, and commented-out test blocks.

## 2. API testing

For every new or changed endpoint (find them via the diff of router/
controller files):

- Read the handler itself to confirm request validation: required fields
  enforced, types checked, size/length limits applied — don't assume the
  framework does this for free.
- Confirm correct status codes on the success path and on every relevant
  failure path (400/401/403/404/409/422/500 as applicable).
- Compare the error response shape to how other endpoints in this codebase
  format errors — flag inconsistency.
- Grep for the auth middleware/decorator pattern used elsewhere in the
  codebase and confirm the new endpoint uses it, unless it's deliberately
  public. An endpoint with no auth check and no clear reason is
  **Blocking**.
- For `PUT`/`DELETE`: confirm calling the same request twice doesn't
  corrupt state or throw an unhandled error.
- Where relevant, check duplicate/concurrent-request handling (double
  submit, race on a unique constraint).
- For any list/bulk endpoint: confirm pagination or a hard limit exists —
  an endpoint that can return the entire table unbounded is a real risk.
- Actually exercise the endpoint with malformed/unexpected payloads
  (missing fields, wrong types, oversized body, extra unexpected fields),
  not just whatever the happy-path tests already cover.

## 3. UI testing

Skip this section (mark Not Applicable) if no UI code was touched.

- Grep changed components for explicit loading/error/empty-state handling
  — every form, button, and modal touched should branch on these states,
  not just render the success case.
- Run the app locally and actually exercise the main flow touched by the
  change; watch the browser console for errors or warnings.
- If layout/CSS was touched, check responsive behavior at a couple of
  breakpoints for obvious overflow or broken layout.
- Accessibility basics on any new UI: form inputs have an associated
  `<label>`, interactive elements are reachable via Tab/keyboard, and new
  text/background color pairs aren't obviously low-contrast.
- Confirm client-side validation rules (required fields, formats) match
  the server-side rules from section 2 — a mismatch that lets the client
  accept something the server rejects (or vice versa) is a real bug, not
  a nitpick.

## 4. Database / query checks

- Read new/changed queries and ORM calls for N+1 patterns — a query
  issued inside a loop instead of a single joined/batched fetch.
- Check the schema/migration files: does any new filter, join, or sort
  column have an index?
- Flag any query with no `LIMIT`/pagination that could return an unbounded
  result set.
- Read new migrations directly: are they backward-compatible with the
  previous version still running mid-deploy (e.g. a new `NOT NULL` column
  with no default breaks old code inserting rows)? Is there a rollback
  path?
- Grep for raw string-concatenated or template-built SQL (f-strings,
  template literals, `+` concatenation feeding a query). Any
  non-parameterized query built from user input is **Blocking**
  (SQL injection).
- Where multiple writes must succeed or fail together, confirm they're
  wrapped in a transaction.

## 5. Security vulnerability check

- Grep the diff for hardcoded secrets: patterns like
  `api_key\s*=\s*["']`, `password\s*=\s*["']`, `secret`, `AKIA` (AWS key
  prefix), or suspicious long base64/hex literals.
- For every place user input flows into SQL, HTML output, a shell command,
  or a file path: confirm it's validated/escaped/parameterized (SQL
  injection, XSS, command injection, path traversal via `../`).
- Grep for unsafe deserialization or dynamic execution:
  `pickle.loads`, `yaml.load(` without `SafeLoader`, `eval(`, `exec(`, or
  a dynamic `require()`/`import()` built from user-controlled input.
- Cross-check with section 2: every new sensitive route/action has an
  explicit auth/authz check.
- If a dependency manifest changed (`package.json`, `requirements.txt`,
  `go.mod`, etc.), check what changed and whether a bumped/new version has
  a known vulnerability (`npm audit`, `pip-audit`, or the changelog/CVE
  list if no audit tool is available).
- Grep logging statements introduced or touched near the change for
  passwords, tokens, or PII being logged in plaintext.

## 6. Code smell / static quality check

- Search for logic duplicated from elsewhere in the codebase (matching
  function names, similar string literals) — flag a clear extraction
  opportunity as Should Fix.
- Flag functions/files that grew very long, deeply nested conditionals, or
  unclear/abbreviated naming introduced by this change.
- Grep for dead code, commented-out blocks, and leftover debug statements:
  `console.log`, `print(`, `debugger`, `fmt.Println` used for debugging
  rather than intentional output.
- Grep for silently swallowed errors: empty `catch {}` blocks, bare
  `except: pass`, or a caught error that's neither logged nor re-raised.
- Compare the new code's patterns against `CLAUDE.md` (if present) and a
  couple of neighboring files — flag inconsistent error-handling style,
  naming, or structure.

## 7. End-to-end functional check

- Re-read the original ticket/requirement in full, not from memory.
- Actually run the complete user journey touched by the change end to
  end — not just the new function or component in isolation.
- Confirm every edge case the ticket mentions is genuinely handled, not
  assumed handled because the general case works.
- If the change spans layers (frontend↔backend↔DB, or service↔service),
  verify them working together — passing tests in each layer individually
  doesn't prove the integration works.

## 8. Final report

Summarize as a structured report, one line per section (1–7):

- **Passed** — section, brief note on what was actually checked/run
- **Issues Found** — grouped by severity, each with a `file:line`
  reference where applicable:
  - **Blocking** — must fix before shipping (missing auth, SQL injection,
    hardcoded secret, no test on new logic, etc.)
  - **Should Fix** — real problem, not release-blocking (duplicated logic,
    missing edge case test, inconsistent error shape)
  - **Nitpick** — minor, optional (naming, minor style inconsistency)
- **Not Applicable** — section, with a one-line reason (e.g. "No UI
  touched")

End with an explicit verdict:

> **Ready to raise PR / send to QA** — no Blocking items.

or

> **Not ready** — fix Blocking items first: <list>.
