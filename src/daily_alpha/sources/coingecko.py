"""
CoinGecko API client for cryptocurrency market data.

Provides access to:
- Market data (prices, market caps, volumes)
- Token information and metadata
- Historical price data
- Trending cryptocurrencies
- Developer activity metrics

CoinGecko API offers a FREE tier with 10,000 calls/month (30 calls/min).
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


class CoinGeckoAPIError(Exception):
    """Custom exception for CoinGecko API errors."""
    pass


class CoinGeckoRateLimit:
    """Rate limiting manager for CoinGecko API."""

    def __init__(self, calls_per_minute: int = 25):  # Conservative buffer
        self.calls_per_minute = calls_per_minute
        self.request_times = []

    async def wait_if_needed(self):
        """Wait if approaching rate limits."""
        now = time.time()

        # Clean old request times
        self.request_times = [t for t in self.request_times if now - t < 60]

        # Check if we need to wait
        if len(self.request_times) >= self.calls_per_minute:
            wait_time = 60 - (now - self.request_times[0]) + random.uniform(1, 3)
            logger.info(f"⏳ CoinGecko rate limiting, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        elif len(self.request_times) >= 5:  # Burst protection
            await asyncio.sleep(random.uniform(0.2, 0.8))

        self.request_times.append(now)


class CoinGeckoClient:
    """
    Client for interacting with the CoinGecko API.

    CoinGecko provides comprehensive cryptocurrency market data including
    prices, market caps, trading volumes, and metadata for 15,000+ cryptocurrencies.

    Free tier: 10,000 calls/month, 30 calls/minute rate limit.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,  # Optional for free tier
        base_url: str = "https://api.coingecko.com/api/v3",
        timeout: int = 30
    ):
        """
        Initialize CoinGecko API client.

        Args:
            api_key: Optional API key for increased limits (not required for free tier)
            base_url: Base URL for CoinGecko API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

        # Rate limiting
        self.rate_limiter = CoinGeckoRateLimit()

        # Track stats
        self.stats = {
            "requests_made": 0,
            "errors": 0,
            "rate_limit_waits": 0,
            "coins_tracked": 0
        }

        # Configure HTTP client
        headers = {
            "User-Agent": "DailyAlpha-MCP/1.3-CoinGecko",
            "Accept": "application/json"
        }

        if api_key:
            headers["x-cg-demo-api-key"] = api_key

        timeout_config = httpx.Timeout(timeout)
        limits = httpx.Limits(max_keepalive_connections=3, max_connections=5)

        self.client = httpx.AsyncClient(
            timeout=timeout_config,
            limits=limits,
            headers=headers
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to CoinGecko API with rate limiting.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            CoinGeckoAPIError: If API request fails
        """
        await self.rate_limiter.wait_if_needed()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.debug(f"Making CoinGecko request to {endpoint}")

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            self.stats["requests_made"] += 1
            return response.json()

        except httpx.TimeoutException:
            self.stats["errors"] += 1
            raise CoinGeckoAPIError("Request timed out")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.stats["rate_limit_waits"] += 1
                logger.warning("🚫 CoinGecko rate limit exceeded")
                # Wait and retry once
                await asyncio.sleep(60 + random.uniform(5, 15))
                return await self._make_request(endpoint, params)
            else:
                self.stats["errors"] += 1
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                raise CoinGeckoAPIError(error_msg)
        except Exception as e:
            self.stats["errors"] += 1
            raise CoinGeckoAPIError(f"Request failed: {str(e)}")

    async def get_trending_coins(self) -> List[Dict[str, Any]]:
        """
        Get currently trending coins on CoinGecko.

        Returns:
            List of trending coins with basic data
        """
        try:
            data = await self._make_request("/search/trending")

            trending_coins = []
            for coin_data in data.get("coins", []):
                coin = coin_data.get("item", {})

                trending_coins.append({
                    "id": coin.get("id"),
                    "name": coin.get("name"),
                    "symbol": coin.get("symbol", "").upper(),
                    "market_cap_rank": coin.get("market_cap_rank"),
                    "thumb": coin.get("thumb"),
                    "score": coin.get("score", 0),
                    "trend_rank": len(trending_coins) + 1,
                    "price_btc": coin.get("price_btc", 0)
                })

            return trending_coins

        except Exception as e:
            logger.error(f"Failed to get trending coins: {e}")
            return []

    async def get_market_data(
        self,
        coins: Optional[List[str]] = None,
        vs_currency: str = "usd",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get market data for cryptocurrencies.

        Args:
            coins: List of coin IDs (if None, gets top coins by market cap)
            vs_currency: Currency to quote prices in
            limit: Maximum coins to return

        Returns:
            List of coins with market data
        """
        try:
            params = {
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": min(limit, 250),  # API limit
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "1h,24h,7d"
            }

            if coins:
                params["ids"] = ",".join(coins[:100])  # Limit to avoid URL length issues

            data = await self._make_request("/coins/markets", params)

            # Enhance data with computed fields
            for coin in data:
                coin["market_cap_formatted"] = self._format_currency(coin.get("market_cap", 0))
                coin["volume_24h_formatted"] = self._format_currency(coin.get("total_volume", 0))
                coin["price_formatted"] = self._format_price(coin.get("current_price", 0))

                # Momentum analysis
                coin["momentum"] = self._analyze_price_momentum(
                    coin.get("price_change_percentage_1h_in_currency"),
                    coin.get("price_change_percentage_24h_in_currency"),
                    coin.get("price_change_percentage_7d_in_currency")
                )

                # Market cap tier
                coin["tier"] = self._categorize_by_market_cap(coin.get("market_cap", 0))

            self.stats["coins_tracked"] = len(data)
            return data

        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return []

    async def get_coin_info(
        self,
        coin_id: str,
        include_market_data: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific cryptocurrency.

        Args:
            coin_id: CoinGecko coin ID
            include_market_data: Whether to include current market data

        Returns:
            Detailed coin information
        """
        try:
            params = {
                "localization": False,
                "tickers": False,
                "market_data": include_market_data,
                "community_data": True,
                "developer_data": True,
                "sparkline": False
            }

            data = await self._make_request(f"/coins/{coin_id}", params)

            # Extract and format key information
            coin_info = {
                "id": data.get("id"),
                "name": data.get("name"),
                "symbol": data.get("symbol", "").upper(),
                "description": self._clean_description(data.get("description", {}).get("en", "")),
                "categories": data.get("categories", []),
                "website": data.get("links", {}).get("homepage", [""])[0],
                "twitter": data.get("links", {}).get("twitter_screen_name"),
                "github": data.get("links", {}).get("repos_url", {}).get("github", [])[:1],
                "blockchain_site": data.get("links", {}).get("blockchain_site", [""])[0],
                "genesis_date": data.get("genesis_date"),
                "hashing_algorithm": data.get("hashing_algorithm"),
                "sentiment_votes": {
                    "up": data.get("sentiment_votes_up_percentage", 0),
                    "down": data.get("sentiment_votes_down_percentage", 0)
                }
            }

            # Add market data if available
            if include_market_data and data.get("market_data"):
                market_data = data["market_data"]
                coin_info.update({
                    "current_price": market_data.get("current_price", {}).get("usd", 0),
                    "price_formatted": self._format_price(market_data.get("current_price", {}).get("usd", 0)),
                    "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                    "market_cap_formatted": self._format_currency(market_data.get("market_cap", {}).get("usd", 0)),
                    "market_cap_rank": market_data.get("market_cap_rank"),
                    "volume_24h": market_data.get("total_volume", {}).get("usd", 0),
                    "volume_24h_formatted": self._format_currency(market_data.get("total_volume", {}).get("usd", 0)),
                    "ath": market_data.get("ath", {}).get("usd", 0),
                    "ath_change_percentage": market_data.get("ath_change_percentage", {}).get("usd", 0),
                    "atl": market_data.get("atl", {}).get("usd", 0),
                    "circulating_supply": market_data.get("circulating_supply", 0),
                    "max_supply": market_data.get("max_supply"),
                    "price_change_24h": market_data.get("price_change_percentage_24h", 0),
                    "price_change_7d": market_data.get("price_change_percentage_7d", 0),
                    "price_change_30d": market_data.get("price_change_percentage_30d", 0)
                })

            # Add community data
            if data.get("community_data"):
                community = data["community_data"]
                coin_info["community"] = {
                    "twitter_followers": community.get("twitter_followers", 0),
                    "reddit_subscribers": community.get("reddit_subscribers", 0),
                    "telegram_channel_user_count": community.get("telegram_channel_user_count", 0)
                }

            # Add developer data
            if data.get("developer_data"):
                dev_data = data["developer_data"]
                coin_info["developer_activity"] = {
                    "stars": dev_data.get("stars", 0),
                    "forks": dev_data.get("forks", 0),
                    "commit_count_4_weeks": dev_data.get("commit_count_4_weeks", 0),
                    "pull_requests_merged": dev_data.get("pull_requests_merged", 0)
                }

            return coin_info

        except Exception as e:
            logger.error(f"Failed to get coin info for {coin_id}: {e}")
            return {"error": f"Failed to fetch {coin_id}: {str(e)}"}

    async def search_coins(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for cryptocurrencies by name or symbol.

        Args:
            query: Search term
            limit: Maximum results to return

        Returns:
            List of matching coins
        """
        try:
            data = await self._make_request("/search", {"query": query})

            coins = data.get("coins", [])[:limit]

            # Add additional context
            for coin in coins:
                coin["match_score"] = self._calculate_match_score(query, coin)

            # Sort by relevance
            coins.sort(key=lambda x: x["match_score"], reverse=True)

            return coins

        except Exception as e:
            logger.error(f"Failed to search coins for '{query}': {e}")
            return []

    async def get_new_listings(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recently listed cryptocurrencies.

        Args:
            days: How many days back to look for new listings
            limit: Maximum coins to return

        Returns:
            List of newly listed coins
        """
        try:
            # Get all coins and filter by addition date
            # Note: This is an approximation as CoinGecko doesn't have a direct "new listings" endpoint
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 250,
                "page": 1,
                "sparkline": False
            }

            data = await self._make_request("/coins/markets", params)

            # This is a simplified approach - in practice you'd want to track additions over time
            # For now, we'll return the smallest market cap coins as proxy for "new"
            new_coins = sorted(data, key=lambda x: x.get("market_cap", float('inf')))

            # Filter out coins without proper market data
            valid_new_coins = [
                coin for coin in new_coins
                if coin.get("market_cap") and coin.get("market_cap") > 0
            ]

            return valid_new_coins[-limit:]  # Return the "newest" (lowest market cap)

        except Exception as e:
            logger.error(f"Failed to get new listings: {e}")
            return []

    def _format_currency(self, amount: float) -> str:
        """Format currency amount with appropriate suffix."""
        if amount >= 1_000_000_000:
            return f"${amount / 1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"${amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount / 1_000:.1f}K"
        else:
            return f"${amount:.2f}"

    def _format_price(self, price: float) -> str:
        """Format price with appropriate precision."""
        if price >= 1:
            return f"${price:,.2f}"
        elif price >= 0.01:
            return f"${price:.4f}"
        else:
            return f"${price:.8f}"

    def _analyze_price_momentum(
        self,
        change_1h: Optional[float],
        change_24h: Optional[float],
        change_7d: Optional[float]
    ) -> str:
        """Analyze price momentum across timeframes."""
        try:
            if change_24h is None:
                return "❓ No data"

            if change_1h and change_1h > 5 and change_24h > 10:
                return "🚀 Strong rally"
            elif change_1h and change_1h > 2 and change_24h > 5:
                return "📈 Rising"
            elif change_1h and change_1h < -5 and change_24h < -10:
                return "📉 Sharp decline"
            elif change_1h and change_1h < -2 and change_24h < -5:
                return "🔻 Declining"
            elif abs(change_24h) < 2:
                return "➡️ Stable"
            else:
                return "🔄 Mixed"
        except:
            return "❓ Unknown"

    def _categorize_by_market_cap(self, market_cap: float) -> str:
        """Categorize coin by market cap."""
        if market_cap >= 50_000_000_000:  # $50B+
            return "🥇 Large Cap"
        elif market_cap >= 5_000_000_000:   # $5B+
            return "🥈 Mid Cap"
        elif market_cap >= 500_000_000:     # $500M+
            return "🥉 Small Cap"
        elif market_cap >= 50_000_000:      # $50M+
            return "💎 Micro Cap"
        else:
            return "🌱 Nano Cap"

    def _clean_description(self, description: str) -> str:
        """Clean HTML tags from description."""
        if not description:
            return ""

        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', description)

        # Limit length
        if len(clean_text) > 300:
            clean_text = clean_text[:300] + "..."

        return clean_text.strip()

    def _calculate_match_score(self, query: str, coin: Dict[str, Any]) -> float:
        """Calculate relevance score for search results."""
        score = 0.0
        query_lower = query.lower()

        name = coin.get("name", "").lower()
        symbol = coin.get("symbol", "").lower()

        # Exact matches get highest score
        if query_lower == symbol:
            score += 100
        elif query_lower == name:
            score += 90

        # Partial matches
        if query_lower in symbol:
            score += 50
        if query_lower in name:
            score += 30

        # Market cap rank influences score (higher rank = more relevant)
        market_cap_rank = coin.get("market_cap_rank", 10000)
        if market_cap_rank:
            score += max(0, 100 - market_cap_rank / 10)

        return score

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "requests_made": self.stats["requests_made"],
            "errors": self.stats["errors"],
            "rate_limit_waits": self.stats["rate_limit_waits"],
            "coins_tracked": self.stats["coins_tracked"],
            "success_rate": (
                (self.stats["requests_made"] - self.stats["errors"]) /
                max(1, self.stats["requests_made"])
            ),
            "api_tier": "Free" if not self.api_key else "Demo/Pro",
            "monthly_limit": "10,000 calls" if not self.api_key else "Enhanced"
        }

    async def close(self):
        """Close the HTTP client with stats summary."""
        stats = self.get_performance_stats()
        logger.info(f"🦎 CoinGecko session stats: {stats['requests_made']} requests, "
                   f"{stats['success_rate']:.1%} success rate, "
                   f"{stats['rate_limit_waits']} rate limit waits")
        await self.client.aclose()