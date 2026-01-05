"""Aggregator for AI/tech trends combining GitHub and MCP ecosystem data."""

from typing import Dict, List, Optional
from ..sources.github_trending import GitHubClient
from ..sources.awesome_mcp import AwesomeMCPParser, get_mcp_servers_summary


class TechTrendsAggregator:
    """Combines GitHub trending repos and MCP ecosystem data into actionable insights."""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize aggregator with optional GitHub token.

        Args:
            github_token: GitHub API token for higher rate limits

        WHY optional token: The aggregator works without a token (60 req/hour)
        but performs better with one (5000 req/hour).
        """
        self.github_client = GitHubClient(token=github_token)
        self.mcp_parser = AwesomeMCPParser()

    async def get_trending_summary(
        self,
        focus: str = "all",
        timeframe: str = "daily",
    ) -> str:
        """
        Generate a formatted summary of tech/AI trends.

        Args:
            focus: "all", "mcp", "agents", or "llm"
            timeframe: "daily" (7 days) or "weekly" (30 days)

        Returns:
            Formatted markdown report

        WHY this structure: The report is designed to be read by humans OR by
        an LLM. Markdown formatting makes it easy to parse and display.
        """
        days = 7 if timeframe == "daily" else 30

        sections = []
        sections.append(f"# AI/Tech Trends - {timeframe.title()} Update\n")
        sections.append(f"*Data from last {days} days*\n")

        # Get GitHub trending data based on focus
        if focus in ["all", "mcp"]:
            sections.append(await self._get_mcp_section(days))

        if focus in ["all", "agents"]:
            sections.append(await self._get_agents_section(days))

        if focus in ["all", "llm"]:
            sections.append(await self._get_llm_section(days))

        # Add MCP ecosystem overview
        if focus in ["all", "mcp"]:
            sections.append("\n---\n")
            sections.append(await get_mcp_servers_summary())

        return "\n".join(sections)

    async def _get_mcp_section(self, days: int) -> str:
        """Get trending MCP repositories and servers."""
        lines = ["\n## 🔌 MCP (Model Context Protocol)\n"]

        # Search for MCP-related repos
        mcp_topics = ["mcp", "mcp-server", "model-context-protocol"]
        repos = []

        for topic in mcp_topics:
            topic_repos = await self.github_client.get_trending_repos(
                topic=topic,
                days=days,
                min_stars=10,  # Lower threshold for MCP (newer ecosystem)
                limit=5,
            )
            repos.extend(topic_repos)

        # Deduplicate by full_name
        seen = set()
        unique_repos = []
        for repo in repos:
            if repo["full_name"] not in seen:
                seen.add(repo["full_name"])
                unique_repos.append(repo)

        if unique_repos:
            lines.append("### Trending Repositories\n")
            for repo in unique_repos[:5]:  # Top 5
                lines.append(f"**{repo['full_name']}** ⭐ {repo['stars']:,}")
                if repo['description']:
                    lines.append(f"  {repo['description']}")
                lines.append(f"  {repo['url']}\n")
        else:
            lines.append("*No significant activity in the last period*\n")

        return "\n".join(lines)

    async def _get_agents_section(self, days: int) -> str:
        """Get trending AI agent frameworks and tools."""
        lines = ["\n## 🤖 AI Agents\n"]

        repos = await self.github_client.get_trending_repos(
            topic="ai-agents",
            days=days,
            min_stars=50,
            limit=5,
        )

        if repos:
            lines.append("### Trending Agent Frameworks\n")
            for repo in repos:
                lines.append(f"**{repo['full_name']}** ⭐ {repo['stars']:,}")
                if repo['description']:
                    lines.append(f"  {repo['description']}")
                if repo['language']:
                    lines.append(f"  Language: {repo['language']}")
                lines.append(f"  {repo['url']}\n")
        else:
            lines.append("*No significant activity in the last period*\n")

        return "\n".join(lines)

    async def _get_llm_section(self, days: int) -> str:
        """Get trending LLM tools and frameworks."""
        lines = ["\n## 🧠 LLM Tools & Frameworks\n"]

        # Combine multiple relevant topics
        topics = ["llm-tools", "llm", "large-language-models"]
        repos = []

        for topic in topics:
            topic_repos = await self.github_client.get_trending_repos(
                topic=topic,
                days=days,
                min_stars=100,  # Higher threshold (more mature ecosystem)
                limit=3,
            )
            repos.extend(topic_repos)

        # Deduplicate
        seen = set()
        unique_repos = []
        for repo in repos:
            if repo["full_name"] not in seen:
                seen.add(repo["full_name"])
                unique_repos.append(repo)

        # Sort by stars
        unique_repos.sort(key=lambda x: x['stars'], reverse=True)

        if unique_repos:
            lines.append("### Trending Tools\n")
            for repo in unique_repos[:5]:  # Top 5
                lines.append(f"**{repo['full_name']}** ⭐ {repo['stars']:,}")
                if repo['description']:
                    lines.append(f"  {repo['description']}")
                lines.append(f"  {repo['url']}\n")
        else:
            lines.append("*No significant activity in the last period*\n")

        return "\n".join(lines)

    async def search_tech_topic(self, topic: str, days: int = 7) -> str:
        """
        Search for a specific tech topic across GitHub.

        Args:
            topic: Search term (e.g., "langchain", "autogen", "mcp")
            days: Lookback period

        Returns:
            Formatted report on the topic

        WHY this is useful: For deep dives on specific tools or frameworks.
        Example: "What's happening with LangChain this week?"
        """
        lines = [f"# Deep Dive: {topic.title()}\n"]

        # Try as a topic first
        repos = await self.github_client.get_trending_repos(
            topic=topic,
            days=days,
            min_stars=10,
            limit=10,
        )

        # If no results as topic, try as keyword search
        if not repos:
            repos = await self.github_client.search_repositories(
                query=f"{topic} stars:>10 pushed:>2024-01-01",
                per_page=10,
            )

        if repos:
            lines.append(f"\n### Found {len(repos)} relevant repositories\n")
            for repo in repos:
                lines.append(f"**{repo['full_name']}** ⭐ {repo['stars']:,}")
                if repo['description']:
                    lines.append(f"  {repo['description']}")
                lines.append(f"  Last updated: {repo['updated_at'][:10]}")
                lines.append(f"  {repo['url']}\n")
        else:
            lines.append(f"\n*No significant activity found for '{topic}'*\n")

        # Check MCP ecosystem
        mcp_matches = await self.mcp_parser.get_servers_by_keyword(topic)
        if mcp_matches:
            lines.append(f"\n### Related MCP Servers ({len(mcp_matches)})\n")
            for server in mcp_matches[:3]:
                lines.append(f"- **{server['name']}**: {server['description']}")
                lines.append(f"  {server['url']}\n")

        return "\n".join(lines)

    async def get_new_releases(self, days: int = 7) -> str:
        """
        Get newly released projects across AI/tech categories.

        Args:
            days: Look at projects created in last N days

        Returns:
            Formatted report of new projects

        WHY this matters: New projects = emerging trends. Early alpha!
        """
        lines = [f"# 🆕 New Releases (Last {days} Days)\n"]

        topics = ["mcp", "ai-agents", "llm-tools"]

        for topic in topics:
            new_repos = await self.github_client.get_new_repos(
                topic=topic,
                days=days,
                limit=3,
            )

            if new_repos:
                lines.append(f"\n## {topic.replace('-', ' ').title()}\n")
                for repo in new_repos:
                    lines.append(f"**{repo['full_name']}** ⭐ {repo['stars']}")
                    if repo['description']:
                        lines.append(f"  {repo['description']}")
                    lines.append(f"  Created: {repo['created_at'][:10]}")
                    lines.append(f"  {repo['url']}\n")

        return "\n".join(lines)


# Helper function for the MCP tool
async def get_ai_trends_report(
    focus: str = "all",
    timeframe: str = "daily",
    github_token: Optional[str] = None,
) -> str:
    """
    Main entry point for getting AI/tech trends.

    Args:
        focus: "all", "mcp", "agents", or "llm"
        timeframe: "daily" or "weekly"
        github_token: Optional GitHub token

    Returns:
        Formatted markdown report

    WHY this wrapper: This is the function that the MCP server will call.
    It provides a simple interface with sensible defaults.
    """
    aggregator = TechTrendsAggregator(github_token=github_token)
    return await aggregator.get_trending_summary(focus=focus, timeframe=timeframe)
