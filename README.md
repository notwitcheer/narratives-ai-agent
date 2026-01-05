# Daily Alpha MCP

A Model Context Protocol (MCP) server that aggregates trends from crypto and AI/tech worlds to provide daily briefings.

**Phase 1 Status**: ✅ GitHub integration complete - Get AI/tech trends from GitHub and the MCP ecosystem

## What is This?

Daily Alpha MCP is an MCP server that helps you track:
- 🔌 **MCP ecosystem**: New Model Context Protocol servers and tools
- 🤖 **AI Agents**: Trending agent frameworks and implementations
- 🧠 **LLM Tools**: Developer tools for working with large language models
- 📈 **Crypto trends**: (Phase 2 - coming soon)

It surfaces this information through tools that Claude Desktop (or any MCP client) can use.

## Features (Phase 1)

### Tools Available

1. **get_ai_trends** - Get trending repos and tools
   - Focus: `all`, `mcp`, `agents`, or `llm`
   - Timeframe: `daily` (7 days) or `weekly` (30 days)

2. **search_tech_topic** - Deep dive on a specific topic
   - Search GitHub repos and MCP servers by keyword
   - Example: "langchain", "autogen", "cursor"

3. **get_new_releases** - Discover newly created projects
   - See what launched in the last N days
   - Early alpha before things trend!

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- GitHub token (optional, but recommended for higher rate limits)

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd narratives-ai-agent
   ```

2. **Install dependencies**
   ```bash
   # With uv (recommended)
   uv sync

   # Or with pip
   pip install -e .
   ```

3. **Get a GitHub token (optional but recommended)**
   - Go to https://github.com/settings/tokens
   - Generate a new token (classic)
   - Select scope: `public_repo` (read access to public repos)
   - Copy the token

4. **Set environment variable**
   ```bash
   # Add to your .bashrc, .zshrc, or .env
   export GITHUB_TOKEN="your_token_here"
   ```

   **WHY you need this**: Without a token, GitHub API limits you to 60 requests/hour. With a token, you get 5,000/hour. The token is free and only needs read access.

## Usage

### Option 1: With Claude Desktop (Recommended)

1. **Add to Claude Desktop config**

   Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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
           "GITHUB_TOKEN": "your_token_here"
         }
       }
     }
   }
   ```

   **Important**: Replace `/absolute/path/to/narratives-ai-agent` with your actual path!

2. **Restart Claude Desktop**

3. **Try it out**

   In Claude Desktop, ask:
   - "What are the trending MCP servers this week?"
   - "Show me new AI agent frameworks from the last 7 days"
   - "Search for repos related to langchain"

### Option 2: Test Directly

You can test the server without Claude Desktop:

```bash
# Run the server (it will wait for input on stdin)
uv run python -m daily_alpha.server

# Or if using pip
python -m daily_alpha.server
```

**Note**: Direct testing requires understanding the MCP protocol. It's easier to test through Claude Desktop or using MCP Inspector.

### Option 3: MCP Inspector (For Development)

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run with inspector
mcp-inspector uv --directory /path/to/narratives-ai-agent run python -m daily_alpha.server
```

This opens a web UI where you can test the tools interactively.

## Project Structure

```
narratives-ai-agent/
├── src/
│   └── daily_alpha/
│       ├── __init__.py
│       ├── server.py              # MCP server entry point
│       │
│       ├── sources/               # Data source modules
│       │   ├── github_trending.py # GitHub API client
│       │   └── awesome_mcp.py     # Parse awesome-mcp-servers
│       │
│       ├── aggregators/           # Data processing
│       │   └── tech_trends.py     # Combine and format data
│       │
│       └── storage/               # (Phase 3 - history tracking)
│
├── pyproject.toml                 # Project config and dependencies
├── README.md
└── CLAUDE.md                      # Project plan and architecture
```

## How It Works

### Architecture Overview

1. **Data Sources** (`sources/`)
   - `github_trending.py`: Fetches trending repos using GitHub API
   - `awesome_mcp.py`: Parses the awesome-mcp-servers community list

2. **Aggregators** (`aggregators/`)
   - `tech_trends.py`: Combines data from sources into formatted reports
   - Handles categorization, deduplication, and formatting

3. **MCP Server** (`server.py`)
   - Exposes tools that LLMs can call
   - Handles tool invocation and returns formatted text

### Example Flow

```
User in Claude Desktop: "What's trending in MCP?"
    ↓
Claude calls: get_ai_trends(focus="mcp", timeframe="daily")
    ↓
MCP Server → TechTrendsAggregator → GitHubClient + AwesomeMCPParser
    ↓
Fetch data from GitHub API + awesome-mcp-servers
    ↓
Format as markdown report
    ↓
Return to Claude → User sees formatted trends
```

## Development

### Running Tests

```bash
# With uv
uv run pytest

# Or with pip
pytest
```

### Code Quality

```bash
# Format and lint
uv run ruff check .
uv run ruff format .
```

### Adding New Features

1. **New data source**: Add module in `sources/`
2. **New aggregation logic**: Add module in `aggregators/`
3. **New MCP tool**: Add to `server.py` in `list_tools()` and `call_tool()`

## Roadmap

### ✅ Phase 1: GitHub Integration (Complete)
- [x] Project structure
- [x] GitHub API client
- [x] awesome-mcp-servers parser
- [x] `get_ai_trends` tool
- [x] Basic testing

### 🚧 Phase 2: Crypto Integration (Next)
- [ ] Moni API wrapper
- [ ] `get_crypto_trends` tool
- [ ] `get_daily_briefing` combining both sides

### 📋 Phase 3: Memory & History
- [ ] SQLite for daily snapshots
- [ ] Track evolution (rising/falling trends)
- [ ] `track_topic` with historical data

### 🚀 Phase 4: Polish & Automation
- [ ] Scheduled daily reports
- [ ] Export to Twitter thread format
- [ ] Publish to GitHub

## Troubleshooting

### "Command not found: uv"
Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### "API rate limit exceeded"
Add a GitHub token (see Setup step 3)

### "Module not found: mcp"
Install dependencies: `uv sync` or `pip install -e .`

### Claude Desktop doesn't see the server
1. Check config file path is correct
2. Ensure absolute paths (no `~` or relative paths)
3. Restart Claude Desktop
4. Check logs: `~/Library/Logs/Claude/mcp*.log` (macOS)

## Contributing

This is a learning project! Contributions are welcome:
- Report bugs or suggest features via issues
- Submit pull requests with improvements
- Share your own MCP server ideas

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
- [GitHub API Docs](https://docs.github.com/en/rest)

## License

MIT License - see LICENSE file

---

Built with ❤️ to learn MCP development and track the bleeding edge of crypto & AI/tech
