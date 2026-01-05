# Quick Start Guide

Get Daily Alpha MCP running in 5 minutes.

## 1. Install Dependencies

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

## 2. Get GitHub Token (Optional but Recommended)

1. Go to: https://github.com/settings/tokens/new
2. Name: "Daily Alpha MCP"
3. Expiration: 90 days (or longer)
4. Scopes: Select `public_repo` only
5. Click "Generate token"
6. Copy the token (you won't see it again!)

```bash
# Add to your shell config (~/.zshrc or ~/.bashrc)
export GITHUB_TOKEN="ghp_your_token_here"

# Or create a .env file (don't commit this!)
echo 'GITHUB_TOKEN="ghp_your_token_here"' > .env
source .env
```

## 3. Test It Works

```bash
# Run the example script
uv run python example.py
```

You should see trending AI/tech repos and MCP servers. If you get rate limit errors, add the GitHub token above.

## 4. Connect to Claude Desktop

### macOS

```bash
# Open Claude Desktop config
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Windows

```bash
# Open Claude Desktop config
notepad %APPDATA%\Claude\claude_desktop_config.json
```

### Add This Configuration

Replace `/absolute/path/to/narratives-ai-agent` with your actual path!

```json
{
  "mcpServers": {
    "daily-alpha": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/narratives-ai-agent",
        "run",
        "python",
        "-m",
        "daily_alpha.server"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

**Important**:
- Use absolute path (like `/Users/yourname/projects/narratives-ai-agent`)
- Don't use `~` or relative paths
- Don't forget the comma if you have other MCP servers

## 5. Restart Claude Desktop

Completely quit and restart Claude Desktop (not just close the window).

## 6. Try It Out

In Claude Desktop, ask:

```
What are the trending MCP servers this week?
```

```
Show me new AI agent frameworks from the last 7 days
```

```
Search for repositories related to langchain
```

```
What are the top LLM tools right now?
```

## Troubleshooting

### "Module not found"
```bash
uv sync
```

### "Rate limit exceeded"
Add your GitHub token (see step 2)

### Claude Desktop doesn't see the server
1. Check the config file path is correct
2. Use absolute paths (no `~`)
3. Restart Claude Desktop completely
4. Check logs: `~/Library/Logs/Claude/mcp*.log` (macOS)

### "Command not found: uv"
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Then restart your terminal
```

## What You Get

### Three MCP Tools

1. **get_ai_trends** - Trending repos and MCP servers
   - Focus: all/mcp/agents/llm
   - Timeframe: daily (7d) or weekly (30d)

2. **search_tech_topic** - Deep dive on any topic
   - Example: "langchain", "cursor", "anthropic"

3. **get_new_releases** - Newly created projects
   - Early alpha before things trend!

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [CLAUDE.md](CLAUDE.md) for architecture details
- Start using it daily to track AI/tech trends
- Phase 2 coming soon: Crypto trends integration!

---

**Need help?** Check the full README or open an issue on GitHub.
