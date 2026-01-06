"""
Crypto trends aggregator using Moni API data.

Combines mindshare data, smart mentions, and narrative trends
to provide comprehensive crypto market insights.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..sources.moni import MoniClient, format_mindshare_data, format_smart_mentions, format_category_trends

# Configure logging
logger = logging.getLogger(__name__)


class CryptoTrendsAggregator:
    """
    Aggregates crypto trend data from Moni API.

    Provides high-level insights by combining:
    - Project mindshare rankings
    - Category trends
    - Smart account activity
    - Trending narratives
    """

    def __init__(self, moni_client: MoniClient):
        """
        Initialize crypto trends aggregator.

        Args:
            moni_client: Authenticated Moni API client
        """
        self.moni_client = moni_client

    async def get_trending_projects(
        self,
        timeframe: str = "24h",
        category: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get trending crypto projects by mindshare.

        Args:
            timeframe: Time period (24h, 7d, 30d)
            category: Filter by category (defi, l1, l2, gaming, etc.)
            limit: Number of projects to return

        Returns:
            Dictionary with trending projects data
        """
        try:
            logger.info(f"Fetching trending projects for {timeframe}")

            # Get projects mindshare data
            projects = await self.moni_client.get_projects_mindshare(
                timeframe=timeframe,
                limit=limit,
                category=category
            )

            # Get category overview for context
            categories = await self.moni_client.get_category_mindshare(
                timeframe=timeframe
            )

            return {
                "timeframe": timeframe,
                "category_filter": category,
                "total_projects": len(projects),
                "projects": projects,
                "categories": categories,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get trending projects: {e}")
            return {
                "error": str(e),
                "timeframe": timeframe,
                "projects": [],
                "categories": []
            }

    async def get_smart_activity(
        self,
        timeframe: str = "24h",
        category: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get smart account activity and mentions.

        Args:
            timeframe: Time period (24h, 7d)
            category: Filter by category
            limit: Number of mentions to return

        Returns:
            Dictionary with smart activity data
        """
        try:
            logger.info(f"Fetching smart activity for {timeframe}")

            # Get smart mentions feed
            mentions = await self.moni_client.get_smart_mentions_feed(
                limit=limit,
                category=category,
                timeframe=timeframe
            )

            # Extract mentioned projects
            mentioned_projects = []
            for mention in mentions:
                if "project" in mention:
                    project = mention["project"]
                    if project not in mentioned_projects:
                        mentioned_projects.append(project)

            return {
                "timeframe": timeframe,
                "category_filter": category,
                "total_mentions": len(mentions),
                "mentions": mentions,
                "mentioned_projects": mentioned_projects,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get smart activity: {e}")
            return {
                "error": str(e),
                "timeframe": timeframe,
                "mentions": [],
                "mentioned_projects": []
            }

    async def get_narrative_trends(
        self,
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """
        Get trending crypto narratives and themes.

        Args:
            timeframe: Time period (24h, 7d)

        Returns:
            Dictionary with narrative trends data
        """
        try:
            logger.info(f"Fetching narrative trends for {timeframe}")

            # Get trending narratives
            narratives = await self.moni_client.get_trending_narratives(
                timeframe=timeframe,
                limit=15
            )

            # Get category mindshare for context
            categories = await self.moni_client.get_category_mindshare(
                timeframe=timeframe
            )

            return {
                "timeframe": timeframe,
                "total_narratives": len(narratives),
                "narratives": narratives,
                "category_context": categories,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get narrative trends: {e}")
            return {
                "error": str(e),
                "timeframe": timeframe,
                "narratives": []
            }

    async def get_comprehensive_overview(
        self,
        timeframe: str = "24h",
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive crypto trends overview.

        Combines all available data sources for a complete picture.

        Args:
            timeframe: Time period (24h, 7d, 30d)
            category: Optional category filter

        Returns:
            Dictionary with comprehensive trends data
        """
        try:
            logger.info(f"Generating comprehensive overview for {timeframe}")

            # Fetch all data concurrently for speed
            tasks = [
                self.get_trending_projects(timeframe, category, 15),
                self.get_smart_activity(timeframe, category, 30),
                self.get_narrative_trends(timeframe)
            ]

            # Get chain mindshare data too
            chains_task = self.moni_client.get_chains_mindshare(timeframe)
            tasks.append(chains_task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            trending_projects = results[0] if len(results) > 0 else {}
            smart_activity = results[1] if len(results) > 1 else {}
            narratives = results[2] if len(results) > 2 else {}
            chains = results[3] if len(results) > 3 else []

            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {i} failed: {result}")

            return {
                "timeframe": timeframe,
                "category_filter": category,
                "overview": {
                    "trending_projects": trending_projects,
                    "smart_activity": smart_activity,
                    "narratives": narratives,
                    "chains": chains if not isinstance(chains, Exception) else []
                },
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate comprehensive overview: {e}")
            return {
                "error": str(e),
                "timeframe": timeframe,
                "overview": {}
            }

    def format_crypto_report(
        self,
        data: Dict[str, Any],
        include_details: bool = True
    ) -> str:
        """
        Format crypto trends data into a readable report.

        Args:
            data: Crypto trends data from get_comprehensive_overview()
            include_details: Whether to include detailed breakdowns

        Returns:
            Formatted markdown report
        """
        if "error" in data:
            return f"❌ **Error generating crypto report**: {data['error']}"

        timeframe = data.get("timeframe", "24h")
        category = data.get("category_filter")
        overview = data.get("overview", {})

        lines = [
            f"# 💰 Crypto Trends Report - {timeframe.upper()}\n",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
        ]

        if category:
            lines.append(f"Category Filter: **{category.upper()}**")

        lines.append("")

        # Trending Projects Section
        trending = overview.get("trending_projects", {})
        if trending.get("projects"):
            lines.append("## 🚀 Top Projects by Mindshare\n")
            formatted_projects = format_mindshare_data(trending["projects"])
            lines.append(formatted_projects)
            lines.append("")

        # Category Trends
        if trending.get("categories"):
            lines.append("## 📊 Category Overview\n")
            formatted_categories = format_category_trends(trending["categories"])
            lines.append(formatted_categories)
            lines.append("")

        # Smart Activity Section
        smart_data = overview.get("smart_activity", {})
        if smart_data.get("mentions") and include_details:
            lines.append("## 🧠 Smart Money Activity\n")
            formatted_mentions = format_smart_mentions(smart_data["mentions"])
            lines.append(formatted_mentions)
            lines.append("")

        # Narratives Section
        narratives_data = overview.get("narratives", {})
        if narratives_data.get("narratives"):
            lines.append("## 📈 Trending Narratives\n")
            for i, narrative in enumerate(narratives_data["narratives"][:5], 1):
                name = narrative.get("name", "Unknown")
                momentum = narrative.get("momentum", 0)
                projects_count = len(narrative.get("projects", []))

                momentum_emoji = "🔥" if momentum > 50 else "⚡" if momentum > 25 else "💫"
                lines.append(f"{i}. **{name}** {momentum_emoji}")
                lines.append(f"   Momentum: {momentum:.1f} • {projects_count} projects\n")

        # Chains Section
        chains = overview.get("chains", [])
        if chains and include_details:
            lines.append("## ⛓️ Chain Activity\n")
            for chain in chains[:5]:
                name = chain.get("name", "Unknown")
                mindshare = chain.get("mindshare_score", 0)
                change = chain.get("change_24h", 0)

                change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                change_text = f"{change:+.1f}%" if change != 0 else "0%"

                lines.append(f"**{name}**: {mindshare:.1f} {change_emoji} {change_text}")

            lines.append("")

        # Summary
        lines.append("---")
        lines.append("*Powered by Moni Social Intelligence*")

        return "\n".join(lines)


# Utility functions for specific analysis

async def analyze_category_momentum(
    moni_client: MoniClient,
    category: str,
    timeframes: List[str] = ["24h", "7d"]
) -> Dict[str, Any]:
    """
    Analyze momentum for a specific category across timeframes.

    Args:
        moni_client: Moni API client
        category: Category to analyze (defi, l1, l2, etc.)
        timeframes: List of timeframes to compare

    Returns:
        Category momentum analysis
    """
    try:
        aggregator = CryptoTrendsAggregator(moni_client)

        momentum_data = {}
        for timeframe in timeframes:
            data = await aggregator.get_trending_projects(
                timeframe=timeframe,
                category=category,
                limit=10
            )
            momentum_data[timeframe] = data

        return {
            "category": category,
            "timeframes": timeframes,
            "momentum_data": momentum_data,
            "analysis": "Category momentum analysis complete"
        }

    except Exception as e:
        return {"error": f"Failed to analyze category momentum: {e}"}


async def find_emerging_projects(
    moni_client: MoniClient,
    min_momentum_change: float = 20.0,
    timeframe: str = "24h"
) -> List[Dict[str, Any]]:
    """
    Find projects with significant momentum increases.

    Args:
        moni_client: Moni API client
        min_momentum_change: Minimum momentum change percentage
        timeframe: Timeframe to analyze

    Returns:
        List of emerging projects
    """
    try:
        aggregator = CryptoTrendsAggregator(moni_client)

        trends_data = await aggregator.get_trending_projects(
            timeframe=timeframe,
            limit=50
        )

        emerging = []
        for project in trends_data.get("projects", []):
            change = project.get("change_24h", 0)
            if change >= min_momentum_change:
                emerging.append({
                    "project": project,
                    "momentum_change": change,
                    "reason": "High momentum increase"
                })

        return sorted(emerging, key=lambda x: x["momentum_change"], reverse=True)

    except Exception as e:
        logger.error(f"Failed to find emerging projects: {e}")
        return []