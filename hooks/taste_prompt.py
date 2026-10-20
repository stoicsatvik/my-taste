#!/usr/bin/env python3
"""Lightweight, local Claude Code hook for automatic My Taste activation.

Reads a single Claude hook JSON event from stdin. Does not contact a network,
write user preferences, or inject stored private data into the transcript.
The agent is responsible for judging evidence and calling the MCP tools.
"""
from __future__ import annotations

import json
import re
import sys

MAX_PROMPT = 12000
PREFERENCE = re.compile(
    r"\b(?:remember(?: that| this| my)?|save (?:this|my|that) (?:style|preference|design|reference|taste)|"
    r"i (?:really )?(?:like|love|prefer|hate|dislike)|"
    r"(?:don't|do not) (?:use|make|write)|"
    r"(?:too |less |more )(?:corporate|formal|busy|minimal|colorful|verbose)|"
    r"(?:my preference is|i'd rather|i would rather))\b",
    re.IGNORECASE,
)
CREATIVE = re.compile(
    r"\b(?:design|redesign|landing page|website|web app|dashboard|ui|ux|"
    r"caption|copywriting|write (?:a|an|my)|rewrite|tone|style|"
    r"reel|shorts|video edit|thumbnail|branding|visual identity)\b",
    re.IGNORECASE,
)
TECHNICAL_ONLY = re.compile(
    r"\b(?:sql query|unit test|stack trace|dependency error|syntax error|"
    r"build failure|compile error|git merge|security vulnerability)\b",
    re.IGNORECASE,
)


def guidance(prompt: str) -> str | None:
    if not prompt or len(prompt) > MAX_PROMPT:
        return None
    explicit = bool(PREFERENCE.search(prompt))
    creative = bool(CREATIVE.search(prompt))
    if explicit:
        return (
            "My Taste: This message may contain EXPLICIT preference evidence. "
            "Judge whether it really expresses a user's preference rather than a quoted "
            "example or ordinary task constraint. If so, infer the appropriate scope and "
            "save concise evidence with the My Taste MCP tool (observe_artifact, "
            "observe_choice, or observe_edit). Never treat passive use or silence as approval. "
            "If also generating creative work, retrieve a compact taste_brief first. "
            "Do not claim anything was saved unless the tool succeeds."
        )
    if creative and not TECHNICAL_ONLY.search(prompt):
        return (
            "My Taste: This appears taste-sensitive. If the My Taste MCP tools are "
            "available, request one concise taste_brief scoped to this task's domain and "
            "context before making creative choices. Do not force irrelevant preferences; "
            "continue normally if there is no evidence or the tool is unavailable."
        )
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        prompt = payload.get("prompt", payload.get("user_prompt", ""))
        if not isinstance(prompt, str):
            return
        message = guidance(prompt)
        if message:
            print(json.dumps({"continue": True, "systemMessage": message}))
    except (ValueError, OSError, TypeError):
        # A hook must not break the user's normal agent session.
        return


if __name__ == "__main__":
    main()
