#!/usr/bin/env python3
"""
Example script demonstrating direct usage of the Daily Alpha components.

This shows how to use the library without MCP, useful for:
- Testing during development
- Understanding how the components work
- Creating custom scripts

Run with: uv run python example.py
"""

import asyncio
import os
from src.daily_alpha.aggregators.tech_trends import get_ai_trends_report, TechTrendsAggregator
from src.daily_alpha.aggregators.daily_briefing import generate_daily_briefing
from src.daily_alpha.sources.moni import MoniClient
from src.daily_alpha.aggregators.crypto_trends import CryptoTrendsAggregator


async def main():
    """Demonstrate different ways to use the Daily Alpha library."""

    # Get API keys from environment
    github_token = os.getenv("GITHUB_TOKEN")
    moni_api_key = os.getenv("MONI_API_KEY")

    print("=" * 80)
    print("Daily Alpha Example - Direct Library Usage")
    print("=" * 80)
    print(f"🔑 GitHub Token: {'✅ Available' if github_token else '❌ Not found'}")
    print(f"🔑 Moni API Key: {'✅ Available' if moni_api_key else '❌ Not found'}")
    print()

    # TECH TRENDS EXAMPLES
    print("🤖 TECH & AI TRENDS")
    print("=" * 80)

    # Example 1: Get AI trends with default settings
    print("📊 Example 1: Get all AI trends (daily)")
    print("-" * 80)
    report = await get_ai_trends_report(focus="all", timeframe="daily", github_token=github_token)
    print(report[:1000] + "..." if len(report) > 1000 else report)
    print()

    # Example 2: Focus on MCP ecosystem
    print("\n" + "=" * 40)
    print("🔌 Example 2: Focus on MCP ecosystem (weekly)")
    print("-" * 40)
    report = await get_ai_trends_report(focus="mcp", timeframe="weekly", github_token=github_token)
    print(report[:800] + "..." if len(report) > 800 else report)
    print()

    # CRYPTO TRENDS EXAMPLES (if Moni API key available)
    if moni_api_key:
        print("\n" + "💰 CRYPTO TRENDS")
        print("=" * 80)

        # Example 3: Get crypto trends
        print("📊 Example 3: Get crypto trends (24h)")
        print("-" * 80)
        try:
            async with MoniClient(moni_api_key) as moni_client:
                aggregator = CryptoTrendsAggregator(moni_client)
                crypto_data = await aggregator.get_comprehensive_overview(timeframe="24h")
                report = aggregator.format_crypto_report(crypto_data, include_details=False)
                print(report[:1000] + "..." if len(report) > 1000 else report)
                print()
        except Exception as e:
            print(f"❌ Error getting crypto trends: {e}")
            print("This might be due to API key issues or network problems.")

        # Example 4: DeFi specific trends
        print("\n" + "=" * 40)
        print("🏦 Example 4: DeFi category trends")
        print("-" * 40)
        try:
            async with MoniClient(moni_api_key) as moni_client:
                aggregator = CryptoTrendsAggregator(moni_client)
                crypto_data = await aggregator.get_comprehensive_overview(
                    timeframe="24h",
                    category="defi"
                )
                report = aggregator.format_crypto_report(crypto_data, include_details=False)
                print(report[:800] + "..." if len(report) > 800 else report)
                print()
        except Exception as e:
            print(f"❌ Error getting DeFi trends: {e}")

    else:
        print("\n" + "💰 CRYPTO TRENDS")
        print("=" * 80)
        print("❌ Moni API key not found - skipping crypto examples")
        print("To test crypto features:")
        print("1. Contact @moni_api_support on Telegram to get an API key")
        print("2. Set: export MONI_API_KEY='your_key_here'")
        print()

    # DAILY BRIEFING EXAMPLE
    print("\n" + "🚀 DAILY BRIEFING")
    print("=" * 80)

    print("📋 Example 5: Complete daily briefing")
    print("-" * 80)
    try:
        briefing = await generate_daily_briefing(
            github_token=github_token,
            moni_api_key=moni_api_key,
            timeframe="daily",
            focus_areas=["mcp", "ai"] if moni_api_key else ["mcp"]
        )
        print(briefing[:1500] + "..." if len(briefing) > 1500 else briefing)
    except Exception as e:
        print(f"❌ Error generating briefing: {e}")

    print("\n" + "=" * 80)
    print("✅ Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    print("""
    NOTE: This example makes real API calls to GitHub and Moni.

    🤖 GITHUB API:
    - Without GITHUB_TOKEN: 60 requests/hour limit
    - With GITHUB_TOKEN: 5,000 requests/hour limit
    - Set token: export GITHUB_TOKEN="your_token_here"

    💰 MONI API:
    - Requires API key from @moni_api_support on Telegram
    - Set key: export MONI_API_KEY="your_key_here"
    - Without key: crypto features will be skipped

    🚀 MCP Server Testing:
    - Phase 1 (GitHub): ✅ Complete and ready
    - Phase 2 (Moni): ✅ Complete - needs API key for testing
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nCommon issues:")
        print("- Rate limit exceeded: Get a GitHub token")
        print("- Moni API error: Check API key or contact support")
        print("- Network error: Check your internet connection")
        print("- Import error: Run 'uv sync' to install dependencies")
