#!/usr/bin/env python3
"""
Export Claude Code sessions to readable formats.

Usage:
    python export_session.py --list                    # List available sessions
    python export_session.py --format markdown         # Export current session
    python export_session.py --all --format training   # Export all as training data
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"


def get_project_dirs() -> List[Path]:
    """Get all project directories in ~/.claude/projects/"""
    if not PROJECTS_DIR.exists():
        return []
    return [d for d in PROJECTS_DIR.iterdir() if d.is_dir()]


def get_sessions(project_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Get all session files, optionally filtered by project."""
    sessions = []

    dirs = [project_dir] if project_dir else get_project_dirs()

    for pdir in dirs:
        if not pdir or not pdir.exists():
            continue
        for f in pdir.glob("*.jsonl"):
            if f.name.endswith(".jsonl"):
                # Parse first few lines to get metadata
                try:
                    with open(f, 'r') as fp:
                        first_lines = []
                        for i, line in enumerate(fp):
                            if i >= 5:
                                break
                            first_lines.append(json.loads(line))

                    # Extract metadata
                    session_info = {
                        "path": f,
                        "project_dir": pdir.name,
                        "session_id": f.stem,
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime),
                    }

                    # Look for session metadata in first lines
                    for entry in first_lines:
                        if entry.get("type") == "user" and "slug" in entry:
                            session_info["slug"] = entry.get("slug", "")
                            session_info["version"] = entry.get("version", "")
                            break

                    sessions.append(session_info)
                except Exception as e:
                    print(f"Warning: Could not read {f}: {e}", file=sys.stderr)

    return sorted(sessions, key=lambda x: x["modified"], reverse=True)


def parse_session(session_path: Path, include_thinking: bool = False, include_tools: str = "summary") -> List[Dict[str, Any]]:
    """Parse a session JSONL file into structured messages."""
    messages = []

    with open(session_path, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Skip non-message entries
            if entry.get("type") == "file-history-snapshot":
                continue

            # Handle user messages
            if entry.get("type") == "user":
                msg = entry.get("message", {})
                if msg.get("role") == "user":
                    messages.append({
                        "role": "user",
                        "content": msg.get("content", ""),
                        "timestamp": entry.get("timestamp", ""),
                        "uuid": entry.get("uuid", ""),
                    })

            # Handle assistant messages
            elif "message" in entry:
                msg = entry.get("message", {})
                if msg.get("role") == "assistant":
                    content_parts = []
                    tool_calls = []
                    thinking = []

                    for block in msg.get("content", []):
                        if isinstance(block, str):
                            content_parts.append(block)
                        elif isinstance(block, dict):
                            if block.get("type") == "text":
                                content_parts.append(block.get("text", ""))
                            elif block.get("type") == "thinking" and include_thinking:
                                thinking.append(block.get("thinking", ""))
                            elif block.get("type") == "tool_use":
                                tool_calls.append({
                                    "name": block.get("name", ""),
                                    "input": block.get("input", {}),
                                })

                    assistant_msg = {
                        "role": "assistant",
                        "content": "\n".join(content_parts),
                        "timestamp": entry.get("timestamp", ""),
                        "model": msg.get("model", ""),
                    }

                    if thinking:
                        assistant_msg["thinking"] = "\n\n".join(thinking)

                    if tool_calls:
                        if include_tools == "full":
                            assistant_msg["tool_calls"] = tool_calls
                        elif include_tools == "summary":
                            assistant_msg["tools_used"] = [t["name"] for t in tool_calls]

                    messages.append(assistant_msg)

    return messages


def export_markdown(messages: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
    """Export messages to markdown format."""
    lines = [
        f"# Session: {metadata.get('slug', metadata.get('session_id', 'unknown'))}",
        f"**Project:** {metadata.get('project_dir', 'unknown')}",
        f"**Date:** {metadata.get('modified', '')}",
        f"**Model:** {messages[0].get('model', 'unknown') if messages else 'unknown'}",
        "",
        "---",
        "",
    ]

    for msg in messages:
        role = msg["role"].capitalize()
        lines.append(f"## {role}")
        lines.append("")
        content = msg["content"]
        if isinstance(content, list):
            content = "\n".join(str(c) for c in content)
        lines.append(str(content) if content else "")

        if "thinking" in msg:
            lines.append("")
            lines.append("<details><summary>Thinking</summary>")
            lines.append("")
            lines.append(msg["thinking"])
            lines.append("")
            lines.append("</details>")

        if "tools_used" in msg:
            lines.append("")
            lines.append(f"*Tools used: {', '.join(msg['tools_used'])}*")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def export_training(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Export messages to training data format (JSONL-ready)."""
    # Group into conversation pairs
    training_examples = []
    current_conversation = []

    for msg in messages:
        content = msg["content"]
        if isinstance(content, list):
            content = "\n".join(str(c) for c in content)
        current_conversation.append({
            "role": msg["role"],
            "content": str(content) if content else ""
        })

        # After each assistant message, we have a complete turn
        if msg["role"] == "assistant" and len(current_conversation) >= 2:
            training_examples.append({
                "messages": current_conversation.copy()
            })

    return training_examples


def export_json(messages: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Export messages to full JSON format."""
    return {
        "metadata": metadata,
        "messages": messages,
        "exported_at": datetime.now().isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Export Claude Code sessions")
    parser.add_argument("--list", action="store_true", help="List available sessions")
    parser.add_argument("--session", help="Specific session ID to export")
    parser.add_argument("--project", help="Project path to filter sessions")
    parser.add_argument("--all", action="store_true", help="Export all sessions")
    parser.add_argument("--format", choices=["markdown", "json", "training"], default="markdown")
    parser.add_argument("--output", "-o", help="Output path (file or directory)")
    parser.add_argument("--include-thinking", action="store_true", help="Include thinking blocks")
    parser.add_argument("--include-tools", choices=["none", "summary", "full"], default="summary")
    parser.add_argument("--after", help="Only sessions after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Only sessions before date (YYYY-MM-DD)")

    args = parser.parse_args()

    # Handle project path
    project_dir = None
    if args.project:
        # Convert project path to slug format
        project_slug = args.project.replace("/", "-")
        if project_slug.startswith("-"):
            project_slug = project_slug[1:]
        project_dir = PROJECTS_DIR / project_slug
        if not project_dir.exists():
            # Try exact match
            project_dir = PROJECTS_DIR / f"-{project_slug}"

    # List sessions
    if args.list:
        sessions = get_sessions(project_dir)
        if not sessions:
            print("No sessions found.")
            return

        print(f"Found {len(sessions)} session(s):\n")
        for s in sessions[:20]:  # Show first 20
            slug = s.get("slug", "")
            slug_str = f" ({slug})" if slug else ""
            size_kb = s["size"] / 1024
            print(f"  {s['session_id']}{slug_str}")
            print(f"    Project: {s['project_dir']}")
            print(f"    Modified: {s['modified'].strftime('%Y-%m-%d %H:%M')}")
            print(f"    Size: {size_kb:.1f} KB")
            print()
        return

    # Get sessions to export
    sessions = get_sessions(project_dir)

    if args.session:
        sessions = [s for s in sessions if s["session_id"] == args.session]
        if not sessions:
            print(f"Session {args.session} not found.", file=sys.stderr)
            sys.exit(1)

    if not args.all and not args.session:
        # Default to most recent session
        sessions = sessions[:1]

    # Date filtering
    if args.after:
        after_date = datetime.strptime(args.after, "%Y-%m-%d")
        sessions = [s for s in sessions if s["modified"] >= after_date]

    if args.before:
        before_date = datetime.strptime(args.before, "%Y-%m-%d")
        sessions = [s for s in sessions if s["modified"] <= before_date]

    if not sessions:
        print("No sessions to export.", file=sys.stderr)
        sys.exit(1)

    # Determine output
    output_path = Path(args.output) if args.output else Path(".")

    if output_path.suffix and len(sessions) > 1:
        print("Output path must be a directory when exporting multiple sessions.", file=sys.stderr)
        sys.exit(1)

    if not output_path.suffix:
        output_path.mkdir(parents=True, exist_ok=True)

    # Export sessions
    all_training = []

    for session in sessions:
        print(f"Exporting: {session['session_id']}...", file=sys.stderr)

        messages = parse_session(
            session["path"],
            include_thinking=args.include_thinking,
            include_tools=args.include_tools,
        )

        if not messages:
            print(f"  No messages found, skipping.", file=sys.stderr)
            continue

        metadata = {
            "session_id": session["session_id"],
            "slug": session.get("slug", ""),
            "project_dir": session["project_dir"],
            "modified": session["modified"].isoformat(),
        }

        if args.format == "markdown":
            content = export_markdown(messages, metadata)
            ext = ".md"
        elif args.format == "json":
            content = json.dumps(export_json(messages, metadata), indent=2)
            ext = ".json"
        elif args.format == "training":
            training_data = export_training(messages)
            all_training.extend(training_data)
            continue  # Aggregate all training data

        # Write output
        if output_path.suffix:
            out_file = output_path
        else:
            slug = session.get("slug", session["session_id"])
            out_file = output_path / f"{slug}{ext}"

        with open(out_file, "w") as f:
            f.write(content)

        print(f"  Exported to: {out_file}", file=sys.stderr)

    # Write training data (aggregated)
    if args.format == "training" and all_training:
        if output_path.suffix:
            out_file = output_path
        else:
            out_file = output_path / "training_data.jsonl"

        with open(out_file, "w") as f:
            for example in all_training:
                f.write(json.dumps(example) + "\n")

        print(f"Exported {len(all_training)} training examples to: {out_file}", file=sys.stderr)

    print("Done!", file=sys.stderr)


if __name__ == "__main__":
    main()
