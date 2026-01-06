"""
Moni API client for crypto mindshare and social intelligence data.

Provides access to:
- Projects mindshare tracking
- Smart accounts activity
- Narrative trends and sentiment
- Category-level insights
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import quote

import httpx

# Configure logging
logger = logging.getLogger(__name__)


class MoniAPIError(Exception):
    """Custom exception for Moni API errors."""
    pass


def sanitize_username(username: str) -> str:
    """
    Sanitize username input to prevent injection attacks.

    Args:
        username: Raw username input

    Returns:
        Sanitized username safe for API calls

    Raises:
        ValueError: If username contains invalid characters
    """
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")

    # Remove leading/trailing whitespace and @
    username = username.strip().lstrip('@')

    # Check for valid characters only (alphanumeric, dots, underscores, hyphens)
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        raise ValueError(f"Username contains invalid characters: {username}")

    # Limit length to prevent excessive requests
    if len(username) > 100:
        raise ValueError("Username too long")

    return username


def sanitize_project_id(project_id: str) -> str:
    """
    Sanitize project ID input.

    Args:
        project_id: Raw project ID

    Returns:
        Sanitized project ID

    Raises:
        ValueError: If project ID is invalid
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("Project ID must be a non-empty string")

    project_id = project_id.strip()

    # Allow alphanumeric, dots, underscores, hyphens
    if not re.match(r'^[a-zA-Z0-9._-]+$', project_id):
        raise ValueError(f"Project ID contains invalid characters: {project_id}")

    if len(project_id) > 100:
        raise ValueError("Project ID too long")

    return project_id


def validate_timeframe(timeframe: str) -> str:
    """
    Validate and sanitize timeframe parameter.

    Args:
        timeframe: Timeframe string

    Returns:
        Validated timeframe

    Raises:
        ValueError: If timeframe is invalid
    """
    valid_timeframes = ["1h", "24h", "7d", "30d", "daily", "weekly"]

    if timeframe not in valid_timeframes:
        raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}")

    return timeframe


class MoniClient:
    """
    Async client for Moni API - Social Intelligence Layer for Web3.

    Provides access to mindshare data, smart accounts tracking,
    and narrative trends in the crypto space.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.discover.getmoni.io/api/v3"):
        """
        Initialize Moni API client.

        Args:
            api_key: API key from Moni (contact @moni_api_support)
            base_url: Base URL for Moni API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

        # HTTP client with timeout and retry logic
        timeout = httpx.Timeout(30.0, connect=10.0)
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)

        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "DailyAlpha-MCP/1.0",
                "Accept": "application/json"
            }
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Moni API with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data

        Returns:
            JSON response data

        Raises:
            MoniAPIError: If API request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.debug(f"Making {method} request to {url}")

            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data
            )

            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise MoniAPIError(
                    f"Rate limited. Retry after {retry_after} seconds"
                )

            # Raise for HTTP errors
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException:
            raise MoniAPIError("Request timed out")
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "message" in error_data:
                    error_msg += f": {error_data['message']}"
            except (ValueError, AttributeError):
                error_msg += f": {e.response.text}"
            raise MoniAPIError(error_msg)
        except Exception as e:
            raise MoniAPIError(f"Request failed: {str(e)}")

    async def get_account_info(
        self,
        username: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific account.

        Args:
            username: Account username or handle

        Returns:
            Account information and metrics
        """
        try:
            # Sanitize input to prevent injection
            safe_username = sanitize_username(username)
            safe_username = quote(safe_username, safe='')

            data = await self._make_request("GET", f"/accounts/{safe_username}/info/full")
            return data
        except ValueError as e:
            logger.error(f"Invalid username '{username}': {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to get account info for {username}: {e}")
            return {}

    async def get_account_smarts(
        self,
        username: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get smart mentions for a specific account.

        Args:
            username: Account username
            limit: Number of mentions to return (max 100)

        Returns:
            List of smart mentions
        """
        try:
            # Sanitize inputs
            safe_username = sanitize_username(username)
            safe_username = quote(safe_username, safe='')

            # Validate limit parameter
            if not isinstance(limit, int) or limit < 1:
                limit = 20
            elif limit > 100:  # API limit
                limit = 100

            params = {"limit": limit}
            data = await self._make_request("GET", f"/accounts/{safe_username}/smarts/full", params=params)
            return data.get("smarts", [])
        except ValueError as e:
            logger.error(f"Invalid username '{username}': {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get smarts for {username}: {e}")
            return []

    async def get_projects_mindshare(
        self,
        timeframe: str = "24h",
        limit: int = 20,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get trending projects by querying known influential accounts.

        NOTE: This is a workaround since Moni API is account-based.
        We query popular crypto accounts and aggregate their mentions.

        Args:
            timeframe: Time period (24h, 7d, 30d)
            limit: Number of projects to return
            category: Filter by category (defi, l1, l2, gaming, etc.)

        Returns:
            List of projects with mindshare metrics
        """
        try:
            # Validate inputs
            safe_timeframe = validate_timeframe(timeframe)

            if not isinstance(limit, int) or limit < 1:
                limit = 20
            elif limit > 100:
                limit = 100

            if category and not re.match(r'^[a-zA-Z0-9_-]+$', category):
                logger.warning(f"Invalid category format: {category}")
                category = None

            # Popular crypto accounts to check for trending mentions
            influential_accounts = [
                "vitalik",
                "satoshiNakamoto",
                "elonmusk",
                "cz_binance",
                "naval",
                "balajis",
                "AndreCronjeTech",
                "RyanSAdams"
            ]

            all_mentions = []
            for account in influential_accounts[:3]:  # Limit to avoid rate limits
                try:
                    smarts = await self.get_account_smarts(account, limit=10)
                    all_mentions.extend(smarts)
                except Exception as e:
                    logger.debug(f"Skipping {account}: {e}")
                    continue

            # For now, return a structured response indicating the limitation
            return [{
                "note": "Moni API is account-based. This method queries influential accounts.",
                "data_source": "Limited sample from influential accounts",
                "mentions_found": len(all_mentions),
                "timeframe": safe_timeframe,
                "category": category
            }]
        except ValueError as e:
            logger.error(f"Invalid parameters: {e}")
            return []

    async def get_category_mindshare(
        self,
        timeframe: str = "24h"
    ) -> List[Dict[str, Any]]:
        """
        Get mindshare data by category through account analysis.

        NOTE: Moni API is account-based. This queries different account types.

        Args:
            timeframe: Time period (24h, 7d, 30d)

        Returns:
            List of categories with mindshare metrics
        """
        try:
            # Validate timeframe
            safe_timeframe = validate_timeframe(timeframe)

            # Sample accounts from different categories
            category_accounts = {
                "defi": ["AaveAave", "Uniswap", "MakerDAO"],
                "l1": ["ethereum", "solana", "avax"],
                "l2": ["arbitrum", "Optimism", "0xPolygon"],
                "gaming": ["axieinfinity", "TheSandboxGame"],
                "ai": ["FetchAI", "SingularityNET"]
            }

            results = []
            for category, accounts in category_accounts.items():
                total_activity = 0
                for account in accounts[:1]:  # Limit to 1 per category to avoid rate limits
                    try:
                        info = await self.get_account_info(account)
                        if info:
                            total_activity += 1
                    except Exception:
                        continue

                results.append({
                    "name": category,
                    "mindshare_score": total_activity * 10,  # Placeholder calculation
                    "change_24h": 0,
                    "timeframe": safe_timeframe
                })

            return results
        except ValueError as e:
            logger.error(f"Invalid timeframe: {e}")
            return []

    async def get_chains_mindshare(
        self,
        timeframe: str = "24h"
    ) -> List[Dict[str, Any]]:
        """
        Get mindshare data by blockchain through ecosystem accounts.

        NOTE: Moni API is account-based. This queries chain ecosystem accounts.

        Args:
            timeframe: Time period (24h, 7d, 30d)

        Returns:
            List of chains with mindshare metrics
        """
        chain_accounts = {
            "Ethereum": ["ethereum", "VitalikButerin"],
            "Solana": ["solana", "toly"],
            "Avalanche": ["avalancheavax"],
            "Polygon": ["0xPolygon"],
            "Arbitrum": ["arbitrum"]
        }

        results = []
        for chain, accounts in chain_accounts.items():
            activity_score = 0
            for account in accounts[:1]:  # Limit queries
                try:
                    info = await self.get_account_info(account)
                    if info:
                        activity_score += 1
                except Exception:
                    continue

            results.append({
                "name": chain,
                "mindshare_score": activity_score * 15,  # Placeholder calculation
                "change_24h": 0,
                "timeframe": timeframe
            })

        return results

    async def get_smart_mentions_feed(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        timeframe: str = "24h"
    ) -> List[Dict[str, Any]]:
        """
        Get recent smart mentions from influential accounts.

        Args:
            limit: Number of mentions to return
            category: Filter by category
            timeframe: Time period to fetch

        Returns:
            List of smart mentions with metadata
        """
        params = {
            "limit": limit,
            "timeframe": timeframe
        }

        if category:
            params["category"] = category

        try:
            data = await self._make_request("GET", "/feed/smart-mentions", params=params)
            return data.get("mentions", [])
        except Exception as e:
            logger.error(f"Failed to get smart mentions: {e}")
            return []

    async def get_account_info(
        self,
        account_address: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific account.

        Args:
            account_address: Account address or handle

        Returns:
            Account information and metrics
        """
        try:
            data = await self._make_request("GET", f"/accounts/{account_address}")
            return data.get("account", {})
        except Exception as e:
            logger.error(f"Failed to get account info for {account_address}: {e}")
            return {}

    async def get_smart_engagement(
        self,
        project_id: str,
        timeframe: str = "7d"
    ) -> Dict[str, Any]:
        """
        Get smart engagement metrics for a project.

        Args:
            project_id: Project identifier
            timeframe: Time period (24h, 7d, 30d)

        Returns:
            Engagement metrics from smart accounts
        """
        params = {"timeframe": timeframe}

        try:
            data = await self._make_request(
                "GET",
                f"/projects/{project_id}/smart-engagement",
                params=params
            )
            return data.get("engagement", {})
        except Exception as e:
            logger.error(f"Failed to get smart engagement for {project_id}: {e}")
            return {}

    async def search_projects(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for projects by name or symbol.

        Args:
            query: Search term
            limit: Number of results

        Returns:
            List of matching projects
        """
        try:
            # Sanitize search query
            if not query or not isinstance(query, str):
                raise ValueError("Query must be a non-empty string")

            query = query.strip()
            if len(query) > 200:
                raise ValueError("Query too long")

            # Basic sanitization - allow alphanumeric, spaces, dots, hyphens
            if not re.match(r'^[a-zA-Z0-9 ._-]+$', query):
                raise ValueError("Query contains invalid characters")

            # Validate limit
            if not isinstance(limit, int) or limit < 1:
                limit = 10
            elif limit > 100:
                limit = 100

            params = {
                "q": query,
                "limit": limit
            }

            data = await self._make_request("GET", "/search/projects", params=params)
            return data.get("results", [])
        except ValueError as e:
            logger.error(f"Invalid search parameters: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to search projects for '{query}': {e}")
            return []

    async def get_trending_narratives(
        self,
        timeframe: str = "24h",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get currently trending narratives and themes.

        Args:
            timeframe: Time period (24h, 7d)
            limit: Number of narratives to return

        Returns:
            List of trending narratives with momentum data
        """
        params = {
            "timeframe": timeframe,
            "limit": limit
        }

        try:
            data = await self._make_request("GET", "/narratives/trending", params=params)
            return data.get("narratives", [])
        except Exception as e:
            logger.error(f"Failed to get trending narratives: {e}")
            return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Utility functions for data formatting

def format_mindshare_data(projects: List[Dict[str, Any]]) -> str:
    """
    Format mindshare data into readable text.

    Args:
        projects: List of projects with mindshare data

    Returns:
        Formatted string representation
    """
    if not projects:
        return "No mindshare data available."

    lines = ["🚀 **Top Projects by Mindshare**\n"]

    for i, project in enumerate(projects[:10], 1):
        name = project.get("name", "Unknown")
        symbol = project.get("symbol", "")
        mindshare = project.get("mindshare_score", 0)
        change = project.get("change_24h", 0)
        category = project.get("category", "")

        change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        change_text = f"{change:+.1f}%" if change != 0 else "0%"

        line = f"{i}. **{name}"
        if symbol:
            line += f" ({symbol})"
        line += f"**"

        if category:
            line += f" • {category}"

        line += f"\n   Mindshare: {mindshare:.1f} {change_emoji} {change_text}\n"

        lines.append(line)

    return "\n".join(lines)


def format_smart_mentions(mentions: List[Dict[str, Any]]) -> str:
    """
    Format smart mentions into readable text.

    Args:
        mentions: List of smart mentions

    Returns:
        Formatted string representation
    """
    if not mentions:
        return "No smart mentions available."

    lines = ["🧠 **Smart Mentions Feed**\n"]

    for mention in mentions[:5]:
        author = mention.get("author", {})
        content = mention.get("content", "")
        timestamp = mention.get("timestamp", "")
        project = mention.get("project", {})

        author_name = author.get("name", "Anonymous")
        author_followers = author.get("followers", 0)
        project_name = project.get("name", "Unknown Project")

        lines.append(f"**@{author_name}** ({author_followers:,} followers)")
        lines.append(f"💬 {content[:200]}{'...' if len(content) > 200 else ''}")
        lines.append(f"🎯 About: {project_name}")
        lines.append(f"⏰ {timestamp}\n")

    return "\n".join(lines)


def format_category_trends(categories: List[Dict[str, Any]]) -> str:
    """
    Format category mindshare data into readable text.

    Args:
        categories: List of categories with mindshare data

    Returns:
        Formatted string representation
    """
    if not categories:
        return "No category data available."

    lines = ["📊 **Mindshare by Category**\n"]

    for category in categories:
        name = category.get("name", "Unknown")
        mindshare = category.get("mindshare_score", 0)
        change = category.get("change_24h", 0)
        top_projects = category.get("top_projects", [])

        change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        change_text = f"{change:+.1f}%" if change != 0 else "0%"

        lines.append(f"**{name}**: {mindshare:.1f} {change_emoji} {change_text}")

        if top_projects:
            project_names = [p.get("name", "") for p in top_projects[:3]]
            lines.append(f"   Top: {', '.join(project_names)}")

        lines.append("")

    return "\n".join(lines)