"""
DeFiLlama API client for TVL and protocol analytics.

Provides access to:
- Protocol TVL tracking across chains
- Yield farming and pool data
- Protocol revenue and fees
- Historical TVL data
- Cross-chain analytics

DeFiLlama API is completely FREE with no authentication required.
"""

import asyncio
import logging
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

import httpx

# Configure logging
logger = logging.getLogger(__name__)


class DeFiLlamaAPIError(Exception):
    """Custom exception for DeFiLlama API errors."""
    pass


class DeFiLlamaClient:
    """
    Client for interacting with the DeFiLlama API.

    DeFiLlama provides comprehensive DeFi analytics including TVL tracking,
    protocol data, yield farming information, and cross-chain metrics.

    The API is completely free and requires no authentication.
    """

    def __init__(
        self,
        base_url: str = "https://api.llama.fi",
        timeout: int = 30,
        requests_per_minute: int = 120  # Conservative rate limiting
    ):
        """
        Initialize DeFiLlama API client.

        Args:
            base_url: Base URL for DeFiLlama API
            timeout: Request timeout in seconds
            requests_per_minute: Conservative rate limit
        """
        self.base_url = base_url.rstrip('/')

        # Simple rate limiting
        self.request_times = []
        self.requests_per_minute = requests_per_minute

        # Track stats
        self.stats = {
            "requests_made": 0,
            "errors": 0,
            "total_protocols_tracked": 0
        }

        # Configure HTTP client
        timeout_config = httpx.Timeout(timeout)
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        self.client = httpx.AsyncClient(
            timeout=timeout_config,
            limits=limits,
            headers={
                "User-Agent": "DailyAlpha-MCP/1.3-DeFiLlama",
                "Accept": "application/json"
            }
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def _rate_limit_wait(self):
        """Simple rate limiting to be respectful of free API."""
        now = time.time()

        # Clean old request times (older than 1 minute)
        self.request_times = [t for t in self.request_times if now - t < 60]

        # Check if we need to wait
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0]) + random.uniform(0.5, 2.0)
            logger.info(f"⏳ DeFiLlama rate limiting, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        elif len(self.request_times) >= 10:  # Burst protection
            await asyncio.sleep(random.uniform(0.1, 0.5))

        self.request_times.append(now)

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to DeFiLlama API.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            DeFiLlamaAPIError: If API request fails
        """
        await self._rate_limit_wait()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.debug(f"Making DeFiLlama request to {endpoint}")

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            self.stats["requests_made"] += 1
            return response.json()

        except httpx.TimeoutException:
            self.stats["errors"] += 1
            raise DeFiLlamaAPIError("Request timed out")
        except httpx.HTTPStatusError as e:
            self.stats["errors"] += 1
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            raise DeFiLlamaAPIError(error_msg)
        except Exception as e:
            self.stats["errors"] += 1
            raise DeFiLlamaAPIError(f"Request failed: {str(e)}")

    async def get_protocols(
        self,
        min_tvl: int = 1000000,  # $1M minimum TVL
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all DeFi protocols with their current TVL.

        Args:
            min_tvl: Minimum TVL in USD to include
            limit: Maximum protocols to return

        Returns:
            List of protocols with TVL data
        """
        try:
            data = await self._make_request("/protocols")

            # Filter by minimum TVL and sort by TVL descending
            filtered_protocols = [
                protocol for protocol in data
                if protocol.get("tvl") is not None and protocol.get("tvl", 0) >= min_tvl
            ]

            # Sort by TVL descending
            filtered_protocols.sort(key=lambda x: x.get("tvl", 0), reverse=True)

            # Add some computed fields
            for protocol in filtered_protocols[:limit]:
                protocol["tvl_formatted"] = f"${protocol.get('tvl', 0):,.0f}"
                protocol["category_clean"] = protocol.get("category", "Unknown").title()

                # Calculate TVL change if available
                tvl_1h = protocol.get("change_1h")
                tvl_1d = protocol.get("change_1d")
                tvl_7d = protocol.get("change_7d")

                protocol["momentum_score"] = self._calculate_tvl_momentum(tvl_1h, tvl_1d, tvl_7d)

            self.stats["total_protocols_tracked"] = len(data)
            return filtered_protocols[:limit]

        except Exception as e:
            logger.error(f"Failed to get protocols: {e}")
            return []

    def _calculate_tvl_momentum(
        self,
        change_1h: Optional[float],
        change_1d: Optional[float],
        change_7d: Optional[float]
    ) -> str:
        """
        Calculate TVL momentum based on timeframe changes.

        Args:
            change_1h: 1-hour TVL change percentage
            change_1d: 1-day TVL change percentage
            change_7d: 7-day TVL change percentage

        Returns:
            Momentum description
        """
        try:
            # Weight recent changes more heavily
            if change_1h is not None and change_1d is not None:
                if change_1h > 2 and change_1d > 5:
                    return "🚀 Accelerating"
                elif change_1h > 0 and change_1d > 2:
                    return "📈 Growing"
                elif change_1h < -2 and change_1d < -5:
                    return "📉 Declining"
                elif abs(change_1d or 0) < 1:
                    return "➡️ Stable"
                else:
                    return "🔄 Mixed"
            elif change_1d is not None:
                if change_1d > 5:
                    return "📈 Growing"
                elif change_1d < -5:
                    return "📉 Declining"
                else:
                    return "➡️ Stable"
            else:
                return "❓ Unknown"
        except:
            return "❓ Unknown"

    async def get_protocol_tvl(
        self,
        protocol_name: str
    ) -> Dict[str, Any]:
        """
        Get detailed TVL data for a specific protocol.

        Args:
            protocol_name: Name or slug of the protocol

        Returns:
            Detailed TVL data including historical data
        """
        try:
            # First get the protocol slug from the protocols list
            all_protocols = await self._make_request("/protocols")

            # Find matching protocol (case-insensitive)
            protocol_slug = None
            protocol_info = None

            for protocol in all_protocols:
                if (protocol_name.lower() in protocol.get("name", "").lower() or
                    protocol_name.lower() in protocol.get("slug", "").lower()):
                    protocol_slug = protocol.get("slug")
                    protocol_info = protocol
                    break

            if not protocol_slug:
                return {
                    "error": f"Protocol '{protocol_name}' not found",
                    "suggestions": [
                        p.get("name") for p in all_protocols[:5]
                        if protocol_name.lower()[0] in p.get("name", "").lower()
                    ]
                }

            # Get detailed TVL data
            tvl_data = await self._make_request(f"/protocol/{protocol_slug}")

            # Combine basic info with detailed TVL
            result = {
                "name": protocol_info.get("name"),
                "slug": protocol_slug,
                "category": protocol_info.get("category"),
                "current_tvl": protocol_info.get("tvl"),
                "tvl_formatted": f"${protocol_info.get('tvl', 0):,.0f}",
                "change_1h": protocol_info.get("change_1h"),
                "change_1d": protocol_info.get("change_1d"),
                "change_7d": protocol_info.get("change_7d"),
                "momentum": self._calculate_tvl_momentum(
                    protocol_info.get("change_1h"),
                    protocol_info.get("change_1d"),
                    protocol_info.get("change_7d")
                ),
                "chains": tvl_data.get("chainTvls", {}),
                "symbol": tvl_data.get("symbol"),
                "description": tvl_data.get("description", "")[:200] + "..." if len(tvl_data.get("description", "")) > 200 else tvl_data.get("description", ""),
                "total_data_points": len(tvl_data.get("tvl", [])),
                "website": tvl_data.get("url"),
                "twitter": tvl_data.get("twitter")
            }

            return result

        except Exception as e:
            logger.error(f"Failed to get protocol TVL for {protocol_name}: {e}")
            return {"error": f"Failed to fetch data: {str(e)}"}

    async def get_chains_tvl(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get TVL data for all blockchain networks.

        Args:
            limit: Maximum chains to return

        Returns:
            List of chains with TVL data
        """
        try:
            data = await self._make_request("/chains")

            # Sort by TVL descending
            chains = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)

            # Enhance with computed fields
            for chain in chains[:limit]:
                chain["tvl_formatted"] = f"${chain.get('tvl', 0):,.0f}"
                chain["dominance"] = (chain.get("tvl", 0) / sum(c.get("tvl", 0) for c in chains[:10])) * 100
                chain["momentum"] = self._calculate_tvl_momentum(
                    None,  # No 1h data for chains
                    chain.get("change_1d"),
                    chain.get("change_7d")
                )

            return chains[:limit]

        except Exception as e:
            logger.error(f"Failed to get chains TVL: {e}")
            return []

    async def get_trending_protocols(
        self,
        timeframe: str = "1d",  # 1h, 1d, 7d
        direction: str = "up",  # up, down
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending protocols based on TVL changes.

        Args:
            timeframe: Time period for trend analysis
            direction: Direction of trend (up/down)
            limit: Maximum protocols to return

        Returns:
            List of trending protocols
        """
        try:
            protocols = await self.get_protocols(min_tvl=100000, limit=200)  # Get more for analysis

            # Choose the change field based on timeframe
            change_field = f"change_{timeframe}"

            # Filter protocols with valid change data
            valid_protocols = [
                p for p in protocols
                if p.get(change_field) is not None and p.get("tvl", 0) > 0
            ]

            # Sort by change percentage
            if direction == "up":
                trending = sorted(valid_protocols, key=lambda x: x.get(change_field, 0), reverse=True)
            else:
                trending = sorted(valid_protocols, key=lambda x: x.get(change_field, 0))

            # Enhance with additional context
            for protocol in trending[:limit]:
                change_value = protocol.get(change_field, 0)
                protocol["trend_strength"] = "🔥 Strong" if abs(change_value) > 10 else "📊 Moderate" if abs(change_value) > 5 else "🔄 Mild"
                protocol["trend_direction"] = "📈" if change_value > 0 else "📉"
                protocol["change_formatted"] = f"{change_value:+.1f}%"

            return trending[:limit]

        except Exception as e:
            logger.error(f"Failed to get trending protocols: {e}")
            return []

    async def analyze_defi_market(
        self,
        focus_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze overall DeFi market trends and insights.

        Args:
            focus_categories: Specific categories to focus on

        Returns:
            Market analysis with key insights
        """
        try:
            # Get protocols and chains data
            protocols = await self.get_protocols(min_tvl=1000000, limit=100)
            chains = await self.get_chains_tvl(limit=15)

            if not protocols or not chains:
                return {"error": "Failed to fetch market data"}

            # Calculate market metrics
            total_tvl = sum(p.get("tvl", 0) for p in protocols)

            # Category analysis
            category_tvl = {}
            for protocol in protocols:
                category = protocol.get("category", "Unknown")
                category_tvl[category] = category_tvl.get(category, 0) + protocol.get("tvl", 0)

            # Top categories
            top_categories = sorted(category_tvl.items(), key=lambda x: x[1], reverse=True)[:5]

            # Chain dominance
            eth_tvl = next((c.get("tvl", 0) for c in chains if c.get("name", "").lower() == "ethereum"), 0)
            eth_dominance = (eth_tvl / total_tvl * 100) if total_tvl > 0 else 0

            # Growth trends
            growing_protocols = [p for p in protocols if p.get("change_1d", 0) > 5]
            declining_protocols = [p for p in protocols if p.get("change_1d", 0) < -5]

            analysis = {
                "market_overview": {
                    "total_tvl": total_tvl,
                    "total_tvl_formatted": f"${total_tvl:,.0f}",
                    "total_protocols": len(protocols),
                    "total_chains": len(chains),
                    "eth_dominance": f"{eth_dominance:.1f}%"
                },
                "top_categories": [
                    {
                        "category": cat,
                        "tvl": tvl,
                        "tvl_formatted": f"${tvl:,.0f}",
                        "dominance": f"{(tvl/total_tvl*100):.1f}%"
                    }
                    for cat, tvl in top_categories
                ],
                "top_protocols": protocols[:5],
                "top_chains": chains[:5],
                "market_trends": {
                    "growing_count": len(growing_protocols),
                    "declining_count": len(declining_protocols),
                    "stable_count": len(protocols) - len(growing_protocols) - len(declining_protocols),
                    "top_grower": growing_protocols[0] if growing_protocols else None,
                    "biggest_decline": declining_protocols[0] if declining_protocols else None
                },
                "analysis_timestamp": datetime.now().isoformat(),
                "data_freshness": "Real-time"
            }

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze DeFi market: {e}")
            return {"error": f"Market analysis failed: {str(e)}"}

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "requests_made": self.stats["requests_made"],
            "errors": self.stats["errors"],
            "total_protocols_tracked": self.stats["total_protocols_tracked"],
            "success_rate": (
                (self.stats["requests_made"] - self.stats["errors"]) /
                max(1, self.stats["requests_made"])
            ),
            "data_source": "DeFiLlama (Free API)"
        }

    async def close(self):
        """Close the HTTP client with stats summary."""
        stats = self.get_performance_stats()
        logger.info(f"🦙 DeFiLlama session stats: {stats['requests_made']} requests, "
                   f"{stats['success_rate']:.1%} success rate")
        await self.client.aclose()


# Utility functions for DeFi data analysis

def format_tvl_change(change: Optional[float]) -> str:
    """Format TVL change percentage with emoji indicators."""
    if change is None:
        return "❓ No data"

    emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
    return f"{emoji} {change:+.1f}%"

def categorize_protocol_by_tvl(tvl: float) -> str:
    """Categorize protocol by TVL size."""
    if tvl >= 1_000_000_000:  # $1B+
        return "🏦 Blue Chip"
    elif tvl >= 100_000_000:  # $100M+
        return "🏢 Major"
    elif tvl >= 10_000_000:   # $10M+
        return "🏪 Established"
    elif tvl >= 1_000_000:    # $1M+
        return "🏠 Emerging"
    else:
        return "🌱 Early"