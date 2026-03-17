# Session Export

[![Governance Score](https://walseth.ai/api/badge/douglasrw/session-export)](https://walseth.ai/scan?repo=douglasrw/session-export)

Export Claude Code session history to readable, shareable, or training-ready formats.

## Installation

### As a Claude Code Skill
```bash
# Copy to your skills directory
cp -r session-export ~/.claude/skills/
```

### Standalone
```bash
# Just use the script directly
python scripts/export_session.py --help
```

## Usage

### List Available Sessions
```bash
python scripts/export_session.py --list
```

### Export to Markdown
```bash
# Export most recent session
python scripts/export_session.py --format markdown --output ./exports/

# Export specific session
python scripts/export_session.py --session abc123-def456 --format markdown

# Export all sessions for a project
python scripts/export_session.py --project /path/to/project --all --format markdown
```

### Export as Training Data
```bash
python scripts/export_session.py --all --format training --output ~/training_data/
```

### Export Options
```
--format       Output format: markdown, json, training
--output       Output path (file or directory)
--session      Specific session ID to export
--project      Filter by project path
--all          Export all sessions
--include-thinking  Include thinking blocks (default: excluded)
--include-tools     Tool output level: none, summary, full (default: summary)
--after        Only sessions after date (YYYY-MM-DD)
--before       Only sessions before date (YYYY-MM-DD)
```

## Output Formats

| Format | Use Case |
|--------|----------|
| `markdown` | Readable conversation log, sharing, documentation |
| `json` | Programmatic access, analysis, debugging |
| `training` | Fine-tuning datasets, JSONL format |

## Requirements

- Python 3.8+
- No additional dependencies

## License

MIT
