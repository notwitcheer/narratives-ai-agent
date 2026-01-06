"""
Daily briefing aggregator that combines crypto and tech trends.

Provides comprehensive alpha reports by combining:
- Crypto trends from Moni API (mindshare, smart accounts)
- Tech/AI trends from GitHub (trending repos, new MCP servers)
- Cross-sector insights and correlations
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .tech_trends import TechTrendsAggregator
from .crypto_trends import CryptoTrendsAggregator
from ..sources.moni import MoniClient

# Configure logging
logger = logging.getLogger(__name__)


class DailyBriefingAggregator:
    """
    Combines crypto and tech trends for comprehensive daily alpha reports.

    Provides unified insights across:
    - Crypto narratives and projects (via Moni)
    - AI/tech developments (via GitHub)
    - Cross-sector opportunities and themes
    """

    def __init__(self, github_token: Optional[str] = None, moni_client: Optional[MoniClient] = None):
        """
        Initialize daily briefing aggregator.

        Args:
            github_token: GitHub API token for tech trends
            moni_client: Authenticated Moni client for crypto trends
        """
        self.github_token = github_token
        self.moni_client = moni_client

        # Initialize sub-aggregators
        self.tech_aggregator = TechTrendsAggregator(github_token=github_token)

        if moni_client:
            self.crypto_aggregator = CryptoTrendsAggregator(moni_client)
        else:
            self.crypto_aggregator = None

    async def get_daily_briefing(
        self,
        timeframe: str = "daily",
        include_crypto: bool = True,
        include_tech: bool = True,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive daily briefing combining crypto and tech trends.

        Args:
            timeframe: "daily" (24h) or "weekly" (7d)
            include_crypto: Include crypto trends section
            include_tech: Include tech/AI trends section
            focus_areas: Optional list of focus areas ["mcp", "agents", "defi", "l1", etc.]

        Returns:
            Dictionary with combined briefing data
        """
        try:
            logger.info(f"Generating daily briefing for {timeframe}")

            # Convert timeframe for different APIs
            crypto_timeframe = "24h" if timeframe == "daily" else "7d"

            # Collect tasks for parallel execution
            tasks = []

            # Tech trends tasks
            if include_tech and self.github_token:
                # AI trends overview
                tasks.append(
                    self._get_tech_overview(timeframe, focus_areas)
                )

                # New releases
                days = 7 if timeframe == "daily" else 30
                tasks.append(
                    self.tech_aggregator.get_new_releases(days=days)
                )

            # Crypto trends tasks
            if include_crypto and self.crypto_aggregator:
                # Crypto overview
                crypto_category = None
                if focus_areas:
                    # Map focus areas to crypto categories
                    crypto_categories = {"defi", "l1", "l2", "gaming", "ai", "meme"}
                    matching_categories = [f for f in focus_areas if f in crypto_categories]
                    if matching_categories:
                        crypto_category = matching_categories[0]

                tasks.append(
                    self.crypto_aggregator.get_comprehensive_overview(
                        timeframe=crypto_timeframe,
                        category=crypto_category
                    )
                )

            # Execute all tasks concurrently
            if not tasks:
                return {
                    "error": "No data sources available. Check GitHub token and Moni API key.",
                    "timeframe": timeframe
                }

            logger.info(f"Executing {len(tasks)} data collection tasks")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            briefing_data = {
                "timeframe": timeframe,
                "focus_areas": focus_areas,
                "generated_at": datetime.now().isoformat(),
                "sections": {}
            }

            result_idx = 0

            # Process tech results
            if include_tech and self.github_token:
                tech_overview = results[result_idx] if result_idx < len(results) else None
                result_idx += 1

                new_releases = results[result_idx] if result_idx < len(results) else None
                result_idx += 1

                briefing_data["sections"]["tech"] = {
                    "overview": tech_overview if not isinstance(tech_overview, Exception) else None,
                    "new_releases": new_releases if not isinstance(new_releases, Exception) else None
                }

            # Process crypto results
            if include_crypto and self.crypto_aggregator:
                crypto_overview = results[result_idx] if result_idx < len(results) else None

                briefing_data["sections"]["crypto"] = {
                    "overview": crypto_overview if not isinstance(crypto_overview, Exception) else None
                }

            return briefing_data

        except Exception as e:
            logger.error(f"Failed to generate daily briefing: {e}")
            return {
                "error": str(e),
                "timeframe": timeframe,
                "sections": {}
            }

    async def _get_tech_overview(self, timeframe: str, focus_areas: Optional[List[str]] = None) -> str:
        """Get tech trends overview based on focus areas."""
        try:
            # Determine focus for tech aggregator
            if focus_areas:
                if "mcp" in focus_areas:
                    focus = "mcp"
                elif "agents" in focus_areas:
                    focus = "agents"
                else:
                    focus = "all"
            else:
                focus = "all"

            # Get AI trends report
            from .tech_trends import get_ai_trends_report
            return await get_ai_trends_report(
                focus=focus,
                timeframe=timeframe,
                github_token=self.github_token
            )

        except Exception as e:
            logger.error(f"Failed to get tech overview: {e}")
            return f"Error getting tech trends: {e}"

    def format_daily_briefing(
        self,
        briefing_data: Dict[str, Any],
        detailed: bool = True
    ) -> str:
        """
        Format daily briefing data into a comprehensive report.

        Args:
            briefing_data: Briefing data from get_daily_briefing()
            detailed: Whether to include detailed sections

        Returns:
            Formatted markdown report
        """
        if "error" in briefing_data:
            return f"❌ **Error generating daily briefing**: {briefing_data['error']}"

        timeframe = briefing_data.get("timeframe", "daily")
        focus_areas = briefing_data.get("focus_areas", [])
        sections = briefing_data.get("sections", {})

        # Header
        lines = [
            f"# 🚀 Daily Alpha Briefing - {timeframe.title()}\n",
            f"📅 **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
        ]

        if focus_areas:
            lines.append(f"🎯 **Focus Areas**: {', '.join(focus_areas)}")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive Summary
        lines.append("## 📊 Executive Summary\n")

        summary_points = []

        # Tech summary
        if "tech" in sections:
            tech_data = sections["tech"]
            if tech_data.get("overview"):
                summary_points.append("🤖 **AI/Tech**: New developments in MCP ecosystem and AI agent frameworks")
            if tech_data.get("new_releases"):
                summary_points.append("🆕 **New Tools**: Fresh releases in AI development space")

        # Crypto summary
        if "crypto" in sections:
            crypto_data = sections["crypto"]
            if crypto_data.get("overview"):
                summary_points.append("💰 **Crypto**: Rising mindshare and smart money movements tracked")

        if summary_points:
            lines.extend(summary_points)
        else:
            lines.append("No significant developments tracked in this timeframe.")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Detailed Sections
        if detailed:
            # Tech Section
            if "tech" in sections:
                tech_data = sections["tech"]

                if tech_data.get("overview"):
                    lines.append("# 🤖 Tech & AI Trends\n")
                    lines.append(tech_data["overview"])
                    lines.append("")
                    lines.append("---")
                    lines.append("")

                if tech_data.get("new_releases"):
                    lines.append("## 🆕 New Releases\n")
                    lines.append(tech_data["new_releases"])
                    lines.append("")
                    lines.append("---")
                    lines.append("")

            # Crypto Section
            if "crypto" in sections:
                crypto_data = sections["crypto"]

                if crypto_data.get("overview"):
                    lines.append("# 💰 Crypto Trends\n")

                    # Format crypto overview using the aggregator
                    if self.crypto_aggregator:
                        crypto_report = self.crypto_aggregator.format_crypto_report(
                            crypto_data["overview"],
                            include_details=True
                        )
                        lines.append(crypto_report)
                    else:
                        lines.append(str(crypto_data["overview"]))

                    lines.append("")

        # Cross-Sector Insights
        lines.append("---")
        lines.append("")
        lines.append("## 🔍 Cross-Sector Insights\n")

        insights = self._generate_cross_sector_insights(sections)
        lines.extend(insights)

        # Footer
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Daily Alpha MCP - Combining crypto and tech intelligence*")
        lines.append("*Tech data via GitHub • Crypto data via Moni*")

        return "\n".join(lines)

    def _generate_cross_sector_insights(self, sections: Dict[str, Any]) -> List[str]:
        """
        Generate insights that span both crypto and tech sectors.

        Args:
            sections: Briefing sections data

        Returns:
            List of insight strings
        """
        insights = []

        tech_data = sections.get("tech", {})
        crypto_data = sections.get("crypto", {})

        # AI + Crypto intersection
        if tech_data.get("overview") and crypto_data.get("overview"):
            # Look for AI-related crypto projects
            crypto_overview = crypto_data.get("overview", {})
            if isinstance(crypto_overview, dict):
                trending_projects = crypto_overview.get("overview", {}).get("trending_projects", {})
                projects = trending_projects.get("projects", [])

                ai_projects = [
                    p for p in projects
                    if p.get("category", "").lower() in ["ai", "artificial-intelligence", "ml"]
                ]

                if ai_projects:
                    insights.append("🤖💰 **AI x Crypto Convergence**: AI-focused crypto projects gaining mindshare")
                    for project in ai_projects[:3]:
                        name = project.get("name", "Unknown")
                        mindshare = project.get("mindshare_score", 0)
                        insights.append(f"   • **{name}**: {mindshare:.1f} mindshare")

        # MCP + Crypto opportunities
        if "mcp" in tech_data.get("overview", "").lower():
            insights.append("🔗 **MCP Opportunity**: Model Context Protocol growth could enable crypto data integration")

        # Agent frameworks + DeFi
        if "agent" in tech_data.get("overview", "").lower():
            insights.append("🤖 **Agent x DeFi**: AI agent frameworks increasingly relevant for automated DeFi strategies")

        # Default insights if no specific connections found
        if not insights:
            insights.extend([
                "📈 **Multi-Sector Alpha**: Monitor both tech innovation and crypto narratives for complete market picture",
                "🔄 **Cross-Pollination**: Technologies often migrate between sectors - early tech trends may predict crypto developments"
            ])

        return insights


# Utility function for external use
async def generate_daily_briefing(
    github_token: Optional[str] = None,
    moni_api_key: Optional[str] = None,
    timeframe: str = "daily",
    focus_areas: Optional[List[str]] = None
) -> str:
    """
    Generate a complete daily briefing report.

    Args:
        github_token: GitHub API token
        moni_api_key: Moni API key
        timeframe: "daily" or "weekly"
        focus_areas: List of focus areas

    Returns:
        Formatted daily briefing report
    """
    try:
        # Initialize Moni client if API key provided
        moni_client = None
        if moni_api_key:
            moni_client = MoniClient(moni_api_key)

        # Create aggregator
        aggregator = DailyBriefingAggregator(
            github_token=github_token,
            moni_client=moni_client
        )

        # Determine what to include based on available credentials
        include_crypto = moni_client is not None
        include_tech = github_token is not None

        if moni_client:
            async with moni_client:
                # Generate briefing
                briefing_data = await aggregator.get_daily_briefing(
                    timeframe=timeframe,
                    include_crypto=include_crypto,
                    include_tech=include_tech,
                    focus_areas=focus_areas
                )

                # Format report
                return aggregator.format_daily_briefing(briefing_data, detailed=True)
        else:
            # Generate briefing without crypto data
            briefing_data = await aggregator.get_daily_briefing(
                timeframe=timeframe,
                include_crypto=include_crypto,
                include_tech=include_tech,
                focus_areas=focus_areas
            )

            # Format report
            return aggregator.format_daily_briefing(briefing_data, detailed=True)

    except Exception as e:
        logger.error(f"Failed to generate daily briefing: {e}")
        return f"Error generating daily briefing: {e}"