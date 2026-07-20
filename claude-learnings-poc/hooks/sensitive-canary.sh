#!/usr/bin/env bash
#
# sensitive-canary — PreToolUse hook for the Read|Write|Edit matcher.
#
# Blocks Claude from reading/writing/editing files that match a known
# sensitive-file pattern (env files, keys, credentials, secrets, anything
# under a config/secrets/ folder) and logs every blocked attempt.
#
# See ~/.claude/settings.md ("Sensitive-canary hook") for the full writeup
# and instructions for adding new patterns.

set -u

# ---------------------------------------------------------------------------
# The sensitive pattern list. Edit this array to add/remove protected
# patterns — nothing else in this file needs to change.
#
# Patterns here are matched against the file's BASENAME (case-insensitive).
# Bash glob syntax: * matches any run of characters.
# ---------------------------------------------------------------------------
NAME_PATTERNS=(
  ".env"
  ".env.*"
  "*.pem"
  "*.key"
  "*credentials*"
  "*secret*"
  "id_rsa*"
)

# Path fragment(s) that mark a sensitive folder — matched against the full
# normalized path (case-insensitive), so this catches the file regardless of
# what it's named, as long as it lives under a config/secrets/ directory.
PATH_PATTERNS=(
  "*/config/secrets/*"
  "config/secrets/*"
)

CANARY_LOG="${CANARY_LOG:-$HOME/.claude/canary.log}"

input="$(cat)"

tool_name="$(printf '%s' "$input" | python -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
print(data.get("tool_name", "") or "")
' 2>/dev/null)"

file_path="$(printf '%s' "$input" | python -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
print((data.get("tool_input", {}) or {}).get("file_path", "") or "")
' 2>/dev/null)"

# No file_path on this tool call (or JSON we could not parse) -> nothing to
# check, let it through.
if [ -z "$file_path" ]; then
  exit 0
fi

# Normalize Windows backslashes so patterns work regardless of separator.
norm_path="${file_path//\\//}"
base_name="${norm_path##*/}"

shopt -s nocasematch

matched_pattern=""

for pattern in "${NAME_PATTERNS[@]}"; do
  if [[ "$base_name" == $pattern ]]; then
    matched_pattern="$pattern"
    break
  fi
done

if [ -z "$matched_pattern" ]; then
  for pattern in "${PATH_PATTERNS[@]}"; do
    if [[ "$norm_path" == $pattern ]]; then
      matched_pattern="config/secrets/ folder"
      break
    fi
  done
fi

if [ -z "$matched_pattern" ]; then
  exit 0
fi

mkdir -p "$(dirname "$CANARY_LOG")"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
printf '%s | tool=%s | file=%s | pattern=%s\n' \
  "$timestamp" "$tool_name" "$file_path" "$matched_pattern" >> "$CANARY_LOG"

warning="Sensitive-canary: blocked $tool_name on '$file_path' — matched sensitive pattern '$matched_pattern'. Logged to $CANARY_LOG."
printf '%s\n' "$warning" >&2

TOOL_NAME="$tool_name" FILE_PATH="$file_path" MATCHED_PATTERN="$matched_pattern" WARNING="$warning" python -c '
import json, os

print(json.dumps({
    "systemMessage": "\U0001F6AB " + os.environ["WARNING"],
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": os.environ["WARNING"],
    },
}))
'

exit 0
