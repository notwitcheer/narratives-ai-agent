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
        Tool(
            name="detect_emerging_projects",
            description=(
                "Detect emerging crypto projects using multi-signal analysis. Combines social "
                "intelligence, smart money activity, and momentum indicators to identify projects "
                "gaining traction before they trend mainstream. Perfect for early alpha detection."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "discovery_method": {
                        "type": "string",
                        "enum": ["all", "smart_money", "social_surge"],
                        "description": (
                            "Detection strategy: 'all' for comprehensive analysis, 'smart_money' "
                            "for smart money signals, 'social_surge' for social momentum"
                        ),
                        "default": "all",
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["24h", "7d", "30d"],
                        "description": "Analysis window for trend detection",
                        "default": "7d",
                    },
                    "min_confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Minimum confidence score for emerging projects (0.0 to 1.0)",
                        "default": 0.7,
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of projects to return",
                        "default": 20,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="track_smart_money_moves",
            description=(
                "Track smart money movements and emerging positions from influential crypto "
                "accounts. Monitors what key players, institutions, and successful traders are "
                "discussing and engaging with to identify early trend signals."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "wallet_tier": {
                        "type": "string",
                        "enum": ["tier1", "institutional", "whale"],
                        "description": (
                            "Type of smart money to track: 'tier1' for top influencers, "
                            "'institutional' for funds/VCs, 'whale' for large traders"
                        ),
                        "default": "tier1",
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["24h", "7d"],
                        "description": "Activity monitoring window",
                        "default": "24h",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum moves to track",
                        "default": 20,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="analyze_project_health",
            description=(
                "Comprehensive health analysis of a specific crypto project. Evaluates social "
                "intelligence, engagement patterns, momentum indicators, and risk factors to "
                "provide a holistic view of project sustainability and investment potential."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name or symbol of the project to analyze",
                    },
                    "include_fundamentals": {
                        "type": "boolean",
                        "description": "Include fundamental analysis metrics",
                        "default": True,
                    },
                    "risk_assessment": {
                        "type": "boolean",
                        "description": "Include detailed risk factor analysis",
                        "default": True,
                    },
                },
                "required": ["project_name"],
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

        elif name == "detect_emerging_projects":
            discovery_method = arguments.get("discovery_method", "all")
            timeframe = arguments.get("timeframe", "7d")
            min_confidence = arguments.get("min_confidence", 0.7)
            limit = arguments.get("limit", 20)

            # Check if Moni API key is available
            if not MONI_API_KEY:
                return [TextContent(
                    type="text",
                    text=(
                        "❌ **Moni API Error**: MONI_API_KEY not found.\\n\\n"
                        "This tool requires Moni API access for crypto intelligence.\\n"
                        "Contact @moni_api_support on Telegram to get an API key."
                    )
                )]

            # Detect emerging projects
            async with MoniClient(MONI_API_KEY) as moni_client:
                emerging_projects = await moni_client.detect_emerging_projects(
                    discovery_method=discovery_method,
                    timeframe=timeframe,
                    min_confidence=min_confidence,
                    limit=limit
                )

                # Format the report
                if not emerging_projects:
                    report = (
                        f"🔍 **No Emerging Projects Found**\\n\\n"
                        f"**Search Parameters:**\\n"
                        f"- Method: {discovery_method}\\n"
                        f"- Timeframe: {timeframe}\\n"
                        f"- Confidence: {min_confidence:.1%}\\n\\n"
                        f"Try lowering the confidence threshold or different timeframe."
                    )
                else:
                    report = f"🚀 **Emerging Projects Detected ({len(emerging_projects)} found)**\\n\\n"

                    for i, project in enumerate(emerging_projects[:10], 1):
                        name = project.get('name', 'Unknown')
                        confidence = project.get('confidence_score', 0)
                        category = project.get('category', 'unknown')
                        mindshare = project.get('mindshare_score', 0)
                        change = project.get('change_24h', 0)

                        signals = project.get('emergence_signals', {})
                        smart_money = "🧠" if signals.get('smart_money_interest') else ""
                        surge = "📈" if signals.get('engagement_surge') else ""

                        report += (
                            f"**{i}. {name}** {smart_money} {surge}\\n"
                            f"   • Confidence: {confidence:.1%}\\n"
                            f"   • Category: {category}\\n"
                            f"   • Mindshare: {mindshare:,} (24h: {change:+.1f}%)\\n"
                            f"   • Momentum: {signals.get('momentum_score', 0):.1f}/1.0\\n\\n"
                        )

                    report += f"\\n*Method: {discovery_method} | Window: {timeframe}*"

            return [TextContent(type="text", text=report)]

        elif name == "track_smart_money_moves":
            wallet_tier = arguments.get("wallet_tier", "tier1")
            timeframe = arguments.get("timeframe", "24h")
            limit = arguments.get("limit", 20)

            # Check if Moni API key is available
            if not MONI_API_KEY:
                return [TextContent(
                    type="text",
                    text=(
                        "❌ **Moni API Error**: MONI_API_KEY not found.\\n\\n"
                        "This tool requires Moni API access for smart money tracking.\\n"
                        "Contact @moni_api_support on Telegram to get an API key."
                    )
                )]

            # Track smart money moves
            async with MoniClient(MONI_API_KEY) as moni_client:
                smart_moves = await moni_client.track_smart_money_moves(
                    wallet_tier=wallet_tier,
                    timeframe=timeframe,
                    limit=limit
                )

                # Format the report
                if not smart_moves:
                    report = (
                        f"🔍 **No Significant Smart Money Activity**\\n\\n"
                        f"**Search Parameters:**\\n"
                        f"- Wallet Tier: {wallet_tier}\\n"
                        f"- Timeframe: {timeframe}\\n\\n"
                        f"This could indicate a quiet period or rate limiting. Try again later."
                    )
                else:
                    report = f"💰 **Smart Money Activity ({wallet_tier} tier)**\\n\\n"

                    for i, move in enumerate(smart_moves[:8], 1):
                        account = move.get('account_handle', 'Unknown')
                        significance = move.get('significance_score', 0)
                        moni_score = move.get('moni_score', 0)
                        smart_mentions = move.get('smart_mentions', 0)
                        keywords = move.get('narrative_keywords', [])[:3]

                        significance_emoji = "🔥" if significance > 0.8 else "⚡" if significance > 0.6 else "📊"

                        report += (
                            f"**{i}. @{account}** {significance_emoji}\\n"
                            f"   • Significance: {significance:.1%}\\n"
                            f"   • Influence: {moni_score:,} Moni Score\\n"
                            f"   • Activity: {smart_mentions} smart mentions\\n"
                        )

                        if keywords:
                            report += f"   • Keywords: {', '.join(keywords)}\\n"

                        report += "\\n"

                    report += f"\\n*Tracking {wallet_tier} accounts over {timeframe}*"

            return [TextContent(type="text", text=report)]

        elif name == "analyze_project_health":
            project_name = arguments.get("project_name")
            include_fundamentals = arguments.get("include_fundamentals", True)
            risk_assessment = arguments.get("risk_assessment", True)

            if not project_name:
                return [TextContent(
                    type="text",
                    text="Error: 'project_name' parameter is required"
                )]

            # Check if Moni API key is available
            if not MONI_API_KEY:
                return [TextContent(
                    type="text",
                    text=(
                        "❌ **Moni API Error**: MONI_API_KEY not found.\\n\\n"
                        "This tool requires Moni API access for project health analysis.\\n"
                        "Contact @moni_api_support on Telegram to get an API key."
                    )
                )]

            # Analyze project health
            async with MoniClient(MONI_API_KEY) as moni_client:
                health_report = await moni_client.analyze_project_health(
                    project_name=project_name,
                    include_fundamentals=include_fundamentals,
                    risk_assessment=risk_assessment
                )

                # Format the report
                if health_report.get("status") == "not_found":
                    report = (
                        f"❌ **Project Not Found: {project_name}**\\n\\n"
                        f"{health_report.get('message')}\\n\\n"
                        f"**Suggestions:**\\n"
                    )
                    for suggestion in health_report.get("suggestions", []):
                        report += f"• {suggestion}\\n"
                elif health_report.get("status") == "error":
                    report = (
                        f"❌ **Analysis Failed for {project_name}**\\n\\n"
                        f"{health_report.get('message')}"
                    )
                else:
                    # Format comprehensive health report
                    name = health_report.get('project_name', project_name)
                    grade = health_report.get('health_grade', 'N/A')
                    score = health_report.get('overall_health_score', 0)

                    social = health_report.get('social_intelligence', {})
                    engagement = health_report.get('engagement_analysis', {})
                    momentum = health_report.get('momentum_indicators', {})
                    risks = health_report.get('risk_factors', [])
                    opportunities = health_report.get('opportunities', [])
                    recommendation = health_report.get('recommendation', '')

                    grade_emoji = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⚫"}.get(grade, "❓")

                    report = (
                        f"{grade_emoji} **{name} Health Analysis**\\n\\n"
                        f"**Overall Health:** {grade} ({score:.1f}/10.0)\\n\\n"

                        f"**📊 Social Intelligence**\\n"
                        f"• Mindshare Score: {social.get('mindshare_score', 0):,}\\n"
                        f"• Smart Mentions: {social.get('smart_mentions', 0)}\\n"
                        f"• Social Health: {social.get('social_health', 'unknown').title()}\\n"
                        f"• Influence Level: {social.get('influence_level', 'unknown').title()}\\n\\n"

                        f"**📈 Engagement Analysis**\\n"
                        f"• 24h Change: {engagement.get('recent_change_24h', 0):+.1f}%\\n"
                        f"• Momentum: {engagement.get('momentum_direction', 'unknown').title()}\\n"
                        f"• Velocity: {engagement.get('engagement_velocity', 'unknown').title()}\\n"
                        f"• Sustainability: {engagement.get('sustainability_score', 0):.1%}\\n\\n"

                        f"**⚡ Momentum Indicators**\\n"
                        f"• Trend Strength: {momentum.get('trend_strength', 0):.1f}/10\\n"
                        f"• Quality: {momentum.get('momentum_quality', 'unknown').replace('_', ' ').title()}\\n"
                        f"• Breakout Potential: {momentum.get('breakout_potential', 0):.1%}\\n\\n"
                    )

                    if risks:
                        report += f"**⚠️ Risk Factors ({len(risks)})**\\n"
                        for risk in risks:
                            report += f"• {risk}\\n"
                        report += "\\n"

                    if opportunities:
                        report += f"**💡 Opportunities ({len(opportunities)})**\\n"
                        for opp in opportunities:
                            report += f"• {opp}\\n"
                        report += "\\n"

                    report += f"**🎯 Recommendation**\\n{recommendation}"

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
