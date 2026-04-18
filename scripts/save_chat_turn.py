#!/usr/bin/env python3
"""Claude Code Stop-hook: append the latest turn to chat_history/.

Input (stdin, JSON) contains at least:
  - session_id
  - transcript_path   (path to the session JSONL)
  - hook_event_name   ("Stop")

For every Stop event we read the session transcript, take the MOST RECENT
``user`` message and the MOST RECENT ``assistant`` text reply, and append
them as markdown to ``chat_history/YYYY-MM-DD_<session>.md`` under the
project directory.

The script is intentionally defensive: it never raises, because a crashing
hook would visibly interfere with Claude Code. Any failure silently no-ops.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def _read_hook_input() -> dict | None:
    try:
        return json.load(sys.stdin)
    except Exception:
        return None


def _extract_text(blocks) -> str:
    """Join all text chunks in a message.content list, drop tool calls/results."""
    if isinstance(blocks, str):
        return blocks.strip()
    if not isinstance(blocks, list):
        return ""
    parts = []
    for b in blocks:
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(b.get("text", ""))
    return "\n".join(p.strip() for p in parts if p.strip())


def _parse_transcript(path: Path) -> list[dict]:
    out = []
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return out


def _last_user_and_assistant(events: list[dict]) -> tuple[str, str]:
    user_text = ""
    asst_text = ""
    # Walk in reverse to find the most recent of each.
    for ev in reversed(events):
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role == "assistant" and not asst_text:
            asst_text = _extract_text(content)
        elif role == "user" and not user_text:
            user_text = _extract_text(content)
        if user_text and asst_text:
            break
    return user_text, asst_text


def main() -> None:
    data = _read_hook_input()
    if not data:
        return
    transcript_path = data.get("transcript_path")
    session_id      = data.get("session_id", "unknown")
    if not transcript_path:
        return

    events = _parse_transcript(Path(transcript_path))
    if not events:
        return
    user_text, asst_text = _last_user_and_assistant(events)
    if not asst_text:
        return

    # Destination: chat_history/YYYY-MM-DD_<session>.md next to this script's project.
    project_dir = Path(__file__).resolve().parent.parent
    out_dir     = project_dir / "chat_history"
    out_dir.mkdir(exist_ok=True)
    date        = datetime.now().strftime("%Y-%m-%d")
    short_id    = session_id.split("-")[0] if session_id else "s"
    out_file    = out_dir / f"{date}_{short_id}.md"

    timestamp = datetime.now().strftime("%H:%M:%S")
    entry     = [f"\n## {timestamp}\n"]
    if user_text:
        entry.append(f"**You:**\n\n{user_text}\n")
    entry.append(f"**Claude:**\n\n{asst_text}\n")

    with out_file.open("a", encoding="utf-8") as fh:
        if out_file.stat().st_size == 0:
            fh.write(f"# Chat — {date}  (session `{session_id}`)\n")
        fh.write("\n".join(entry))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a hook failure bubble up to the user
        pass
