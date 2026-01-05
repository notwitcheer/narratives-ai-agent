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
from src.daily_alpha.aggregators.tech_trends import get_ai_trends_report, TechTrendsAggregator


async def main():
    """Demonstrate different ways to use the Daily Alpha library."""

    print("=" * 80)
    print("Daily Alpha Example - Direct Library Usage")
    print("=" * 80)
    print()

    # Example 1: Get AI trends with default settings
    print("📊 Example 1: Get all AI trends (daily)")
    print("-" * 80)
    report = await get_ai_trends_report(focus="all", timeframe="daily")
    print(report)
    print()

    # Example 2: Focus on MCP ecosystem
    print("\n" + "=" * 80)
    print("🔌 Example 2: Focus on MCP ecosystem (weekly)")
    print("-" * 80)
    report = await get_ai_trends_report(focus="mcp", timeframe="weekly")
    print(report)
    print()

    # Example 3: Search for a specific topic
    print("\n" + "=" * 80)
    print("🔍 Example 3: Search for 'langchain'")
    print("-" * 80)
    aggregator = TechTrendsAggregator()
    report = await aggregator.search_tech_topic(topic="langchain", days=30)
    print(report)
    print()

    # Example 4: Get new releases
    print("\n" + "=" * 80)
    print("🆕 Example 4: New releases in last 7 days")
    print("-" * 80)
    report = await aggregator.get_new_releases(days=7)
    print(report)
    print()

    print("=" * 80)
    print("✅ Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    print("""
    NOTE: This example makes real API calls to GitHub.

    - Without GITHUB_TOKEN: 60 requests/hour limit
    - With GITHUB_TOKEN: 5,000 requests/hour limit

    Set token: export GITHUB_TOKEN="your_token_here"
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nCommon issues:")
        print("- Rate limit exceeded: Get a GitHub token")
        print("- Network error: Check your internet connection")
        print("- Import error: Run 'uv sync' to install dependencies")
