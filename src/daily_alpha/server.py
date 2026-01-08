"""Daily Alpha MCP Server - Main entry point."""

import asyncio
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .config import GITHUB_TOKEN, MONI_API_KEY
from .aggregators.tech_trends import get_ai_trends_report, TechTrendsAggregator
from .sources.moni import MoniClient
from .aggregators.crypto_trends import CryptoTrendsAggregator
from .aggregators.daily_briefing import generate_daily_briefing


# Initialize the MCP server
server = Server("daily-alpha")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools for the MCP client.

    WHY this is needed: MCP clients (like Claude Desktop) call this to discover
    what tools are available. Each tool needs a name, description, and parameters.
    """
    return [
        Tool(
            name="get_ai_trends",
            description=(
                "Get trending AI/tech repositories and tools from GitHub and the MCP ecosystem. "
                "Returns a formatted report with trending repos, new MCP servers, and notable "
                "developments in the AI/dev space."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "focus": {
                        "type": "string",
                        "enum": ["all", "mcp", "agents", "llm"],
                        "description": (
                            "Focus area: 'all' for everything, 'mcp' for Model Context Protocol, "
                            "'agents' for AI agent frameworks, 'llm' for general LLM tools"
                        ),
                        "default": "all",
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["daily", "weekly"],
                        "description": (
                            "'daily' looks at last 7 days, 'weekly' looks at last 30 days"
                        ),
                        "default": "daily",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="search_tech_topic",
            description=(
                "Deep dive into a specific tech topic or framework. Searches GitHub repositories "
                "and MCP servers matching the topic. Useful for tracking specific tools like "
                "'langchain', 'autogen', 'cursor', etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to search for (e.g., 'langchain', 'mcp', 'autogen')",
                    },
                    "days": {
                        "type": "number",
                        "description": "Lookback period in days",
                        "default": 7,
                    },
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="get_new_releases",
            description=(
                "Get newly created projects in AI/tech space. Shows projects created in the "
                "last N days across MCP, AI agents, and LLM tools categories. Perfect for "
                "discovering emerging tools before they trend."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "number",
                        "description": "Look at projects created in last N days",
                        "default": 7,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_crypto_trends",
            description=(
                "Get trending crypto projects, mindshare data, and smart money activity. "
                "Provides insights into crypto narratives, rising projects, and influential "
                "account mentions using Moni's social intelligence platform."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "enum": ["24h", "7d", "30d"],
                        "description": (
                            "Time period for analysis: '24h' for daily trends, '7d' for weekly, "
                            "'30d' for monthly perspective"
                        ),
                        "default": "24h",
                    },
                    "category": {
                        "type": "string",
                        "description": (
                            "Optional category filter: 'defi', 'l1', 'l2', 'gaming', 'ai', 'meme', etc. "
                            "Leave empty for all categories"
                        ),
                    },
                    "include_smart_activity": {
                        "type": "boolean",
                        "description": "Include smart money mentions and activity in the report",
                        "default": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_daily_briefing",
            description=(
                "Generate a comprehensive daily alpha briefing combining crypto trends (Moni) "
                "and tech/AI developments (GitHub). Provides cross-sector insights and identifies "
                "opportunities spanning both crypto and tech innovation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "enum": ["daily", "weekly"],
                        "description": (
                            "'daily' covers last 24 hours, 'weekly' covers last 7 days. "
                            "Daily gives fresh developments, weekly shows bigger trends."
                        ),
                        "default": "daily",
                    },
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional focus areas: 'mcp', 'agents', 'defi', 'l1', 'l2', 'ai', 'gaming'. "
                            "Multiple areas can be specified for targeted briefing."
                        ),
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool calls from the MCP client.

    WHY this structure: When an LLM calls a tool, this function receives the
    tool name and arguments, executes the appropriate code, and returns the result.

    Args:
        name: Tool name (e.g., "get_ai_trends")
        arguments: Dictionary of arguments passed by the LLM

    Returns:
        List of TextContent with the tool's response
    """
    # Use GitHub token from config (loaded from .env or environment)
    github_token = GITHUB_TOKEN

    try:
        if name == "get_ai_trends":
            focus = arguments.get("focus", "all")
            timeframe = arguments.get("timeframe", "daily")

            report = await get_ai_trends_report(
                focus=focus,
                timeframe=timeframe,
                github_token=github_token,
            )

            return [TextContent(type="text", text=report)]

        elif name == "search_tech_topic":
            topic = arguments.get("topic")
            days = arguments.get("days", 7)

            if not topic:
                return [TextContent(
                    type="text",
                    text="Error: 'topic' parameter is required"
                )]

            aggregator = TechTrendsAggregator(github_token=github_token)
            report = await aggregator.search_tech_topic(topic=topic, days=days)

            return [TextContent(type="text", text=report)]

        elif name == "get_new_releases":
            days = arguments.get("days", 7)

            aggregator = TechTrendsAggregator(github_token=github_token)
            report = await aggregator.get_new_releases(days=days)

            return [TextContent(type="text", text=report)]

        elif name == "get_crypto_trends":
            timeframe = arguments.get("timeframe", "24h")
            category = arguments.get("category")
            include_smart_activity = arguments.get("include_smart_activity", True)

            # Check if Moni API key is available
            if not MONI_API_KEY:
                return [TextContent(
                    type="text",
                    text=(
                        "❌ **Moni API Error (401)**: Request failed with status code 401\n\n"
                        "**Invalid API key. Please check your MONI_API_KEY.**\n\n"
                        "Troubleshooting:\n"
                        "1. **Claude Desktop**: Add MCP server to claude_desktop_config.json with correct cwd path\n"
                        "2. **API Key**: Verify MONI_API_KEY in your .env file: `MONI_API_KEY=your_key_here`\n"
                        "3. **Support**: Contact @moni_api_support on Telegram for a valid API key\n\n"
                        "Current working directory needs access to your .env file."
                    )
                )]

            # Create Moni client and aggregator
            async with MoniClient(MONI_API_KEY) as moni_client:
                aggregator = CryptoTrendsAggregator(moni_client)

                # Get comprehensive crypto trends
                crypto_data = await aggregator.get_comprehensive_overview(
                    timeframe=timeframe,
                    category=category
                )

                # Format the report
                report = aggregator.format_crypto_report(
                    crypto_data,
                    include_details=include_smart_activity
                )

            return [TextContent(type="text", text=report)]

        elif name == "get_daily_briefing":
            timeframe = arguments.get("timeframe", "daily")
            focus_areas = arguments.get("focus_areas")

            # Generate comprehensive briefing
            report = await generate_daily_briefing(
                github_token=GITHUB_TOKEN,
                moni_api_key=MONI_API_KEY,
                timeframe=timeframe,
                focus_areas=focus_areas
            )

            return [TextContent(type="text", text=report)]

        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]

    except Exception as e:
        # Return error as text instead of raising
        # WHY: MCP clients handle text errors better than exceptions
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def main():
    """
    Main entry point for the MCP server.

    WHY stdio_server: MCP servers communicate over stdin/stdout. This is how
    Claude Desktop and other clients connect to the server.
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    """
    Run the server when executed directly.

    Usage:
        python -m daily_alpha.server
        # or with uv:
        uv run python -m daily_alpha.server
    """
    asyncio.run(main())
