"""Parser for awesome-mcp-servers repository to track new MCP tools."""

import httpx
import re
from typing import List, Dict


class AwesomeMCPParser:
    """Parser for the awesome-mcp-servers community list."""

    REPO_URL = "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md"

    async def fetch_readme(self) -> str:
        """
        Fetch the README.md file from awesome-mcp-servers.

        Returns:
            Raw markdown content

        WHY we use raw.githubusercontent.com: This gives us the raw file content
        without needing authentication. Perfect for simple parsing.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(self.REPO_URL, timeout=30.0)
            response.raise_for_status()
            return response.text

    def parse_servers(self, markdown: str) -> List[Dict]:
        """
        Parse MCP servers from the awesome list markdown.

        Args:
            markdown: Raw README.md content

        Returns:
            List of MCP servers with name, description, and URL

        WHY this parsing approach: The awesome list follows a standard format:
        - [Server Name](url) - Description
        We use regex to extract these structured entries.
        """
        servers = []

        # Match pattern: - [Name](url) - Description
        # or: - [Name](url): Description
        pattern = r'-\s+\[([^\]]+)\]\(([^)]+)\)\s*[-:]\s*(.+?)(?:\n|$)'

        matches = re.finditer(pattern, markdown, re.MULTILINE)

        for match in matches:
            name = match.group(1).strip()
            url = match.group(2).strip()
            description = match.group(3).strip()

            # Filter out non-server entries (like headers, badges, etc.)
            if url.startswith('http'):
                servers.append({
                    "name": name,
                    "url": url,
                    "description": description,
                    "source": "awesome-mcp-servers",
                })

        return servers

    def categorize_servers(self, servers: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize MCP servers by type based on name/description.

        Args:
            servers: List of parsed servers

        Returns:
            Dictionary mapping category -> servers

        WHY categorization matters: Instead of a flat list, grouping by purpose
        (databases, APIs, dev tools, etc.) makes the data more actionable.
        """
        categories = {
            "databases": [],
            "apis": [],
            "dev_tools": [],
            "file_systems": [],
            "web": [],
            "ai_ml": [],
            "other": [],
        }

        # Keywords for categorization
        category_keywords = {
            "databases": ["postgres", "sqlite", "database", "db", "sql", "mongo"],
            "apis": ["api", "rest", "graphql", "http"],
            "dev_tools": ["git", "github", "docker", "kubernetes", "ci", "cd"],
            "file_systems": ["file", "filesystem", "fs", "directory", "storage"],
            "web": ["browser", "web", "html", "puppeteer", "selenium"],
            "ai_ml": ["llm", "ai", "ml", "model", "openai", "anthropic"],
        }

        for server in servers:
            text = f"{server['name']} {server['description']}".lower()
            categorized = False

            for category, keywords in category_keywords.items():
                if any(keyword in text for keyword in keywords):
                    categories[category].append(server)
                    categorized = True
                    break

            if not categorized:
                categories["other"].append(server)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    async def get_all_servers(self, categorize: bool = True) -> Dict | List[Dict]:
        """
        Fetch and parse all MCP servers from the awesome list.

        Args:
            categorize: If True, return categorized dict; if False, return flat list

        Returns:
            Either categorized servers or flat list

        WHY async: Even though parsing is synchronous, the fetch is async.
        This keeps the entire MCP server async-compatible.
        """
        markdown = await self.fetch_readme()
        servers = self.parse_servers(markdown)

        if categorize:
            return self.categorize_servers(servers)
        return servers

    async def get_servers_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Search for MCP servers matching a keyword.

        Args:
            keyword: Search term (e.g., "github", "database", "filesystem")

        Returns:
            Matching servers

        WHY this is useful: When tracking a specific topic (e.g., "github"),
        you can quickly find all related MCP servers.
        """
        servers = await self.get_all_servers(categorize=False)
        keyword_lower = keyword.lower()

        return [
            server for server in servers
            if keyword_lower in server['name'].lower()
            or keyword_lower in server['description'].lower()
        ]


# Helper function for common use cases
async def get_latest_mcp_servers(limit: int = 10) -> List[Dict]:
    """
    Get the latest MCP servers from awesome list.

    Args:
        limit: Max number to return

    Returns:
        List of recent MCP servers

    NOTE: Since we're parsing a static list, we can't get "true" chronological order.
    In Phase 3, we'll add history tracking to detect newly added servers.

    For now, we return the full list and rely on the user to compare with previous runs.
    """
    parser = AwesomeMCPParser()
    servers = await parser.get_all_servers(categorize=False)
    return servers[:limit]


async def get_mcp_servers_summary() -> str:
    """
    Get a formatted summary of MCP servers by category.

    Returns:
        Formatted string with server counts and highlights

    WHY this format: Returns a human-readable summary that can be directly
    included in the daily briefing.
    """
    parser = AwesomeMCPParser()
    categorized = await parser.get_all_servers(categorize=True)

    summary_lines = ["## MCP Servers Ecosystem\n"]

    total = sum(len(servers) for servers in categorized.values())
    summary_lines.append(f"**Total servers tracked**: {total}\n")

    for category, servers in categorized.items():
        summary_lines.append(f"\n### {category.replace('_', ' ').title()} ({len(servers)})")

        # Show top 3 in each category
        for server in servers[:3]:
            summary_lines.append(f"- **{server['name']}**: {server['description']}")
            summary_lines.append(f"  {server['url']}")

        if len(servers) > 3:
            summary_lines.append(f"  ... and {len(servers) - 3} more")

    return "\n".join(summary_lines)
