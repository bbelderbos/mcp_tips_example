# tips-mcp

An MCP server that exposes your local coding tips (markdown notes) as tools and resources to Claude and other MCP clients.

**Article:** [Build Your First MCP Server: Code Tips in Claude and Slack](https://belderbos.dev/blog/build-mcp-server-python-tips-slack/)

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

## Run the MCP server

```bash
uv run python server.py
```

No output is expected — the server waits for a client to connect over stdio.

## Claude Code integration

Register the server with Claude Code:

```bash
claude mcp add --scope user code-tips -- uv --project /path/to/tips-mcp run python /path/to/tips-mcp/server.py
```

Or add it to `.mcp.json` in your project root for project-scoped access:

```json
{
  "mcpServers": {
    "code-tips": {
      "type": "stdio",
      "command": "uv",
      "args": ["--project", "/path/to/tips-mcp", "run", "python", "/path/to/tips-mcp/server.py"]
    }
  }
}
```

## Slack bot

`slack_bot.py` adds a `/tip` slash command to Slack. It starts and manages the MCP server as a subprocess internally — you don't need to run `server.py` separately. Queries are routed through the Claude API so Claude does the reasoning and decides which tools to call.

### Additional dependencies

```bash
uv add slack-bolt python-decouple anthropic
```

### Environment variables

Create a `.env` file (and add it to `.gitignore`):

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Slack app setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create an app "From Scratch"
2. Enable **Socket Mode** and generate an App-Level Token (`xapp-...`)
3. Under **OAuth & Permissions → Scopes**, add the `commands` bot scope
4. Under **Slash Commands**, create `/tip` (no Request URL needed in Socket Mode)
5. Install the app to your workspace to get the Bot Token (`xoxb-...`)

### Run the bot

```bash
uv run python slack_bot.py
```

Type `/tip how do generators save memory?` in Slack and Claude responds using your tips. Responses are ephemeral — only visible to you — so it works in any channel without spamming others.

## Note format

```markdown
# Your tip title

Tip body content here...

#tag1 #tag2
```
