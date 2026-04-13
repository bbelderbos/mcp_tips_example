# tips-mcp

An MCP server that exposes your local coding tips (markdown notes) as tools and resources to Claude and other MCP clients.

## What it does

Reads markdown files from `~/code/bobcodesit/notes/` and exposes them via two tools and one resource:

- **`search_tips(query)`** — keyword search across tip titles, bodies, and tags
- **`get_tip(tip_id)`** — fetch the full content of a single tip by filename (without `.md`)
- **`tips://all`** — resource listing all tips with IDs, titles, and tags

Tips are markdown files where the first line is the title (`# Title`) and the last line can contain hashtag-style tags (`#python #decorators`).

## Setup

```bash
uv sync
```

## Run

```bash
uv run python server.py
```

## Claude Code integration

Add to your MCP config (e.g. `~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "code-tips": {
      "command": "uv",
      "args": ["run", "python", "/path/to/tips-mcp/server.py"]
    }
  }
}
```

## Note format

```markdown
# Your tip title

Tip body content here...

#tag1 #tag2
```
