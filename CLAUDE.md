# CLAUDE.md - Daily Alpha MCP Project

## Project Overview

Building a **MCP (Model Context Protocol) server** called "Daily Alpha MCP" that aggregates trends from crypto AND tech/AI worlds to provide daily briefings.

**Goal**: Learn MCP development while building something useful — a tool that tracks:
- Crypto narratives, mindshare, smart money discussions (via Moni API)
- AI/agents/MCP trending repos and new tools (via GitHub)

**Owner context**: Witcheer is a crypto KOL learning advanced programming (Python, React, SQL), interested in AI agents and MCP technology.

---

## Architecture

```
daily-alpha-mcp/
├── src/
│   └── daily_alpha/
│       ├── __init__.py
│       ├── server.py              # MCP server entry point
│       │
│       ├── sources/               # Each data source = one module
│       │   ├── __init__.py
│       │   ├── moni.py            # Moni API wrapper
│       │   ├── github_trending.py # GitHub trending + search
│       │   ├── awesome_mcp.py     # Parse awesome-mcp-servers repo
│       │   └── kaito.py           # (optional) Kaito scraper
│       │
│       ├── aggregators/           # Combination logic
│       │   ├── __init__.py
│       │   ├── crypto_trends.py   # Combine crypto sources
│       │   ├── tech_trends.py     # Combine tech sources
│       │   └── daily_briefing.py  # Final report generator
│       │
│       └── storage/               # Memory/cache
│           ├── __init__.py
│           └── history.py         # SQLite for tracking evolution
│
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

---

## Data Sources

### Crypto Side
| Source | Data | Access |
|--------|------|--------|
| **Moni API** | Project mindshare, trending categories, smart accounts activity | API key needed (user has it) |
| **Kaito** | Narratives, sentiment, catalyst events | Enterprise API or portal scraping (optional) |

### Tech/AI Side
| Source | Data | Access |
|--------|------|--------|
| **GitHub API** | Trending repos, search by topic (MCP, agents, AI) | Free with auth |
| **awesome-mcp-servers** | Curated list of MCP servers | Raw GitHub file (free) |
| **GitHub Trending** | Daily/weekly repos by language | Scraping or API |

---

## MCP Tools to Implement

### 1. `get_crypto_trends`
```python
@server.tool()
async def get_crypto_trends(
    timeframe: str = "24h",  # 24h, 7d, 30d
    category: str = None     # defi, l1, l2, gaming, etc.
) -> str:
    """
    Get trending crypto narratives and projects.
    Returns: Top projects by mindshare, rising narratives, smart money discussions
    """
```

### 2. `get_ai_trends`
```python
@server.tool()
async def get_ai_trends(
    focus: str = "all",  # all, mcp, agents, vibe-coding
    timeframe: str = "daily"  # daily, weekly
) -> str:
    """
    Get trending AI/dev repositories and tools.
    Returns: Trending repos (MCP, agents, AI), new MCP servers, notable releases
    """
```

### 3. `get_daily_briefing`
```python
@server.tool()
async def get_daily_briefing() -> str:
    """
    Complete daily alpha briefing combining crypto and tech trends.
    Returns formatted report with top narratives, developments, momentum comparison
    """
```

### 4. `track_topic`
```python
@server.tool()
async def track_topic(
    topic: str,  # "berachain", "mcp", "agents", etc.
    include_history: bool = True
) -> str:
    """
    Deep dive on a specific topic across all sources.
    Shows current status + historical trend.
    """
```

---

## Implementation Plan

### Phase 1: GitHub Integration
- [ ] Project structure setup with pyproject.toml
- [ ] GitHub API client for trending repos
- [ ] Parse awesome-mcp-servers for new MCP tools
- [ ] Implement `get_ai_trends` tool
- [ ] Test with Claude Desktop or Cursor

**Key learnings**: MCP server basics, GitHub API, async Python

### Phase 2: Moni API Integration
- [ ] Moni API wrapper
- [ ] Implement `get_crypto_trends` tool
- [ ] Combine with Phase 1 for `get_daily_briefing`

### Phase 3: Memory & History
- [ ] SQLite for daily snapshots
- [ ] Track evolution (rising/falling trends)
- [ ] Implement `track_topic` with history

### Phase 4: Polish & Automation
- [ ] Cron job for daily reports
- [ ] Export format for Twitter threads
- [ ] Publish on GitHub

---

## Technical References

### MCP Server Structure (Python)
```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("daily-alpha")

@server.tool()
async def tool_name(param: str) -> str:
    """Tool description shown to the LLM."""
    # Implementation
    return result
```

### GitHub Search Syntax (useful queries)
```
topic:mcp stars:>100 pushed:>2024-12-01
topic:ai-agents language:python
topic:llm-tools created:>2024-11-01
```

### Key Repos to Reference
- https://github.com/modelcontextprotocol/servers (official MCP servers)
- https://github.com/punkpeye/awesome-mcp-servers (community list)
- https://github.com/github/github-mcp-server (GitHub's official MCP)

---

## Commands & Workflow

### Setup
```bash
# Create project with uv (recommended) or pip
uv init daily-alpha-mcp
cd daily-alpha-mcp
uv add mcp httpx sqlite-utils
```

### Run MCP Server (for testing)
```bash
# With uv
uv run python -m daily_alpha.server

# Or with mcp dev tools
mcp dev src/daily_alpha/server.py
```

### Test with Claude Desktop
Add to `~/.config/claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "daily-alpha": {
      "command": "uv",
      "args": ["run", "python", "-m", "daily_alpha.server"],
      "cwd": "/path/to/daily-alpha-mcp"
    }
  }
}
```

---

## Notes for Claude Code

When helping with this project:
1. **Explain the WHY** — User wants to learn, not just get code
2. **Use async/await** — MCP servers are async
3. **Keep it modular** — Each source in its own file
4. **Add error handling** — APIs fail, handle gracefully
5. **Type hints** — Use them everywhere for clarity
6. **French or English** — User is comfortable with both

## Current Status

**Phase 1 in progress** — Starting with project setup and GitHub integration.