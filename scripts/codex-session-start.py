#!/usr/bin/env python3
"""Inject Superlite instructions from the installed Codex plugin."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
skill = (root / "skills/using-superlite/SKILL.md").read_text(encoding="utf-8")
body = skill.split("---", 2)[2].strip()
context = (
    f"Superlite is the selected workflow for this Codex session.\n\n{body}\n\n"
    f"Read {root / 'skills/using-superlite/references/codex-tools.md'} for tool mappings. "
    f"For /superlite:start or another Superlite command, read the matching file in "
    f"{root / 'commands'} and follow it with the current request as arguments. "
    "For plan approval, end your turn and let the user send it as a normal chat message. "
    "If a Superlite command redirects you into a different worktree, ask the user to launch a "
    "fresh Superlite session there before writing a review plan. Shell cd does not move this chat."
)
print(json.dumps({
    "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context},
}))
