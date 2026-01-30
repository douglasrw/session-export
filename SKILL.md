---
name: session-export
description: Export Claude Code session history to readable formats. Use when user says "export session", "save conversation", "export history", "create training data", "backup sessions", or wants to preserve, share, or analyze their Claude Code conversations. Exports to markdown, JSON, or training data formats.
---

# Session Export

Export Claude Code sessions to readable, shareable, or training-ready formats.

## Quick Start

Export current session to markdown:
```bash
python scripts/export_session.py --format markdown --output ./exports/
```

Export all sessions for a project:
```bash
python scripts/export_session.py --project /Users/you/dev/myproject --all --format markdown
```

Export as training data (JSONL):
```bash
python scripts/export_session.py --format training --output ./training_data/
```

## Workflow

### 1. Find Sessions

Sessions are stored in `~/.claude/projects/[project-path-slug]/[session-id].jsonl`

List available sessions:
```bash
python scripts/export_session.py --list
```

### 2. Choose Format

| Format | Use Case |
|--------|----------|
| `markdown` | Readable conversation log, sharing, documentation |
| `json` | Programmatic access, analysis, debugging |
| `training` | Fine-tuning, creating training datasets |

### 3. Export Options

```bash
# Export specific session
python scripts/export_session.py --session abc123-def456 --format markdown

# Export with thinking blocks (default: excluded)
python scripts/export_session.py --include-thinking --format markdown

# Export tool calls (default: summarized)
python scripts/export_session.py --include-tools full --format markdown

# Filter by date
python scripts/export_session.py --after 2026-01-01 --before 2026-01-31
```

## Output Formats

### Markdown Format
```markdown
# Session: kind-sniffing-frog
**Project:** /Users/you/dev/myproject
**Date:** 2026-01-30
**Model:** claude-opus-4-5

---

## User
[User message content]

## Assistant
[Assistant response]

---
```

### Training Data Format (JSONL)
```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

### JSON Format
Full structured export with metadata, tool calls, and thinking blocks.

## Scripts

### `scripts/export_session.py`
Main export script. Run with `--help` for all options.

### Usage Examples

Export this project's sessions:
```bash
python scripts/export_session.py --project "$(pwd)" --format markdown --output ./session_exports/
```

Create training dataset from all sessions:
```bash
python scripts/export_session.py --all --format training --output ~/training_data/claude_sessions.jsonl
```

## Notes

- Sessions contain sensitive data - review before sharing
- Training format excludes tool calls and system messages
- Large sessions may be split into multiple files
