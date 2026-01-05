"""GitHub API client for fetching trending repositories and topics."""

import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..config import GITHUB_TOKEN as DEFAULT_GITHUB_TOKEN


class GitHubClient:
    """Client for interacting with GitHub API to fetch trending repos and search."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token. If not provided, will try to read
                   from GITHUB_TOKEN environment variable. Anonymous requests have
                   lower rate limits (60/hour vs 5000/hour with auth).

        WHY we need this: GitHub API has rate limits. With a token, you get 5000
        requests per hour instead of just 60. The token is free to create.
        """
        self.token = token or DEFAULT_GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 10,
    ) -> List[Dict]:
        """
        Search GitHub repositories with custom query.

        Args:
            query: GitHub search query (e.g., "topic:mcp stars:>100")
            sort: Sort by 'stars', 'forks', 'updated'
            order: 'asc' or 'desc'
            per_page: Number of results (max 100)

        Returns:
            List of repository objects with name, description, stars, etc.

        WHY this structure: GitHub's search API is powerful but returns a lot of data.
        We extract only what we need for trending analysis.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/repositories",
                headers=self.headers,
                params={
                    "q": query,
                    "sort": sort,
                    "order": order,
                    "per_page": per_page,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Extract relevant fields
            repos = []
            for item in data.get("items", []):
                repos.append({
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "description": item.get("description", ""),
                    "url": item["html_url"],
                    "stars": item["stargazers_count"],
                    "forks": item["forks_count"],
                    "language": item.get("language"),
                    "topics": item.get("topics", []),
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "pushed_at": item["pushed_at"],
                })

            return repos

    async def get_trending_repos(
        self,
        topic: str,
        days: int = 7,
        min_stars: int = 50,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get trending repositories for a specific topic.

        Args:
            topic: GitHub topic (e.g., "mcp", "ai-agents", "llm")
            days: Look at repos pushed in last N days
            min_stars: Minimum star count
            limit: Max number of results

        Returns:
            List of trending repositories

        WHY we filter by push date: A repo with recent commits is actively developed,
        which is more valuable for "trending" than just high star count.
        """
        # Calculate date threshold
        date_threshold = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Build search query
        query = f"topic:{topic} stars:>{min_stars} pushed:>{date_threshold}"

        return await self.search_repositories(
            query=query,
            sort="stars",
            order="desc",
            per_page=limit,
        )

    async def get_new_repos(
        self,
        topic: str,
        days: int = 7,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get newly created repositories for a topic.

        Args:
            topic: GitHub topic
            days: Created in last N days
            limit: Max results

        Returns:
            List of new repositories

        WHY this matters: New repos show emerging tools and trends before they
        become popular. Early alpha!
        """
        date_threshold = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = f"topic:{topic} created:>{date_threshold}"

        return await self.search_repositories(
            query=query,
            sort="stars",
            order="desc",
            per_page=limit,
        )

    async def get_multi_topic_trends(
        self,
        topics: List[str],
        days: int = 7,
        limit_per_topic: int = 5,
    ) -> Dict[str, List[Dict]]:
        """
        Get trending repos for multiple topics at once.

        Args:
            topics: List of topics to search
            days: Lookback period
            limit_per_topic: Max repos per topic

        Returns:
            Dictionary mapping topic -> list of repos

        WHY this is useful: Instead of making separate calls for "mcp", "ai-agents",
        "llm-tools", we can batch them. More efficient.
        """
        results = {}
        for topic in topics:
            try:
                repos = await self.get_trending_repos(
                    topic=topic,
                    days=days,
                    limit=limit_per_topic,
                )
                results[topic] = repos
            except Exception as e:
                # Don't let one topic failure break everything
                print(f"Error fetching {topic}: {e}")
                results[topic] = []

        return results
