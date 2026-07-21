#!/usr/bin/env python
"""
Parse a list of commits (raw messages, `git log --oneline`, or full `git log`
output) and classify each one for the release-notes skill.

Usage:
    python classify_commits.py < commits.txt
    git log --oneline v1.2.0..v1.3.0 | python classify_commits.py
    python classify_commits.py commits.txt

Output: JSON on stdout — a list of per-commit records. This script only
classifies and extracts structure; it never invents prose. Rewriting terse
subjects into user-facing sentences and assembling the final document is the
skill's job (done by Claude reading this script's output), not this script's.
"""
import json
import re
import sys

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)"
    r"(?:\((?P<scope>[\w\-/. ]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<subject>.+)$",
    re.IGNORECASE,
)

# Types whose commits never belong in release notes, regardless of wording.
# These are internal-process commits with no user-facing effect.
EXCLUDED_TYPES = {"chore", "test", "ci", "build", "style", "docs"}

# refactor/revert are borderline: usually internal, but the skill (Claude)
# should double check the subject line for user-facing wording before
# trusting this default.
BORDERLINE_TYPES = {"refactor", "revert"}

MERGE_RE = re.compile(
    r"^Merge (pull request|branch|remote-tracking branch)", re.IGNORECASE
)

FIX_KEYWORDS = re.compile(
    r"\b(fix(e[sd])?|bug|resolve[sd]?|correct(ed|s)?|broken|crash|incorrect(ly)?"
    r"|error|defect|issue|regression)\b",
    re.IGNORECASE,
)
FEAT_KEYWORDS = re.compile(
    r"\b(add(ed|s)?|implement(ed|s)?|introduce[sd]?|support(ed|s)?|new|enable[sd]?"
    r"|allow(ed|s)?)\b",
    re.IGNORECASE,
)
CHORE_KEYWORDS = re.compile(
    r"\b(wip|typo|lint(ing)?|formatting|bump version|version bump|release v?\d)\b",
    re.IGNORECASE,
)

# Ticket/PR reference patterns, in priority order.
TICKET_PATTERNS = [
    ("bug", re.compile(r"\bBug\s*#?\s*(\d+)\b", re.IGNORECASE)),
    ("jira", re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")),
    ("pr", re.compile(r"#(\d+)\b")),
    ("bare_colon", re.compile(r"(?:^|\s)(\d{4,6}):\s")),
    ("paren", re.compile(r"\((\d{4,6})\)")),
]

BREAKING_FOOTER_RE = re.compile(r"BREAKING[ -]CHANGE:\s*(.+)", re.IGNORECASE)


def extract_ticket(subject, body):
    text = subject + "\n" + body
    for kind, pat in TICKET_PATTERNS:
        m = pat.search(text)
        if m:
            ticket_id = m.group(1)
            is_bug = kind == "bug"
            return ticket_id, is_bug
    return None, False


def classify_one(raw_subject, body=""):
    raw_subject = raw_subject.strip()
    record = {
        "raw": raw_subject,
        "type": None,
        "scope": None,
        "subject": raw_subject,
        "ticket_id": None,
        "is_bug": False,
        "breaking": False,
        "excluded": False,
        "exclude_reason": None,
    }

    if not raw_subject:
        record["excluded"] = True
        record["exclude_reason"] = "empty"
        return record

    if MERGE_RE.match(raw_subject):
        record["excluded"] = True
        record["exclude_reason"] = "merge commit"
        return record

    m = CONVENTIONAL_RE.match(raw_subject)
    if m:
        record["type"] = m.group("type").lower()
        record["scope"] = m.group("scope")
        record["subject"] = m.group("subject").strip()
        record["breaking"] = bool(m.group("breaking"))
        if record["type"] in EXCLUDED_TYPES:
            record["excluded"] = True
            record["exclude_reason"] = f"conventional type '{record['type']}' is non-user-facing"
        elif record["type"] in BORDERLINE_TYPES:
            record["exclude_reason"] = (
                f"conventional type '{record['type']}' is usually internal — "
                "verify the subject is actually user-facing before including"
            )
        if record["type"] == "fix":
            record["is_bug"] = True
    else:
        # No conventional prefix — fall back to keyword heuristics.
        if CHORE_KEYWORDS.search(raw_subject):
            record["excluded"] = True
            record["exclude_reason"] = "matches chore/noise keyword pattern"
            return record
        if FIX_KEYWORDS.search(raw_subject):
            record["type"] = "fix"
            record["is_bug"] = True
        elif FEAT_KEYWORDS.search(raw_subject):
            record["type"] = "feat"
        else:
            record["type"] = "unknown"
            record["exclude_reason"] = (
                "no conventional prefix and no recognizable keyword — "
                "classify manually"
            )

    if BREAKING_FOOTER_RE.search(body):
        record["breaking"] = True

    ticket_id, is_bug_from_ticket = extract_ticket(raw_subject, body)
    if ticket_id:
        record["ticket_id"] = ticket_id
        if is_bug_from_ticket:
            record["is_bug"] = True

    return record


def parse_full_git_log(text):
    """Parse `git log` (default, non --oneline) output into (subject, body) pairs."""
    blocks = re.split(r"(?=^commit [0-9a-f]{7,40})", text, flags=re.MULTILINE)
    commits = []
    for block in blocks:
        block = block.strip()
        if not block.startswith("commit "):
            continue
        lines = block.splitlines()
        msg_lines = []
        in_msg = False
        for line in lines:
            if in_msg:
                msg_lines.append(line[4:] if line.startswith("    ") else line)
            elif line.strip() == "":
                in_msg = True
        msg = "\n".join(msg_lines).strip()
        if not msg:
            continue
        parts = msg.split("\n\n", 1)
        subject = parts[0].strip()
        body = parts[1] if len(parts) > 1 else ""
        commits.append((subject, body))
    return commits


def parse_oneline(text):
    """Parse `git log --oneline` (hash + subject per line) or plain subject-per-line input."""
    commits = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        m = re.match(r"^[0-9a-f]{7,40}\s+(.*)$", line)
        subject = m.group(1) if m else line
        commits.append((subject, ""))
    return commits


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if re.search(r"^commit [0-9a-f]{7,40}", text, re.MULTILINE):
        pairs = parse_full_git_log(text)
    else:
        pairs = parse_oneline(text)

    records = [classify_one(subject, body) for subject, body in pairs]
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
