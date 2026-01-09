#!/usr/bin/env python3
"""
Exploration script to discover additional Moni API capabilities.
This script tests various endpoint patterns to understand what advanced features are available.
"""

import asyncio
import os
from src.daily_alpha.sources.moni import MoniClient

async def explore_moni_endpoints():
    """Systematically explore Moni API endpoints to discover new capabilities."""

    moni_api_key = os.getenv("MONI_API_KEY")
    if not moni_api_key:
        print("❌ MONI_API_KEY not found")
        return

    print("🔍 Exploring Moni API Advanced Capabilities")
    print("=" * 60)

    async with MoniClient(moni_api_key) as client:

        # Test various endpoint patterns
        potential_endpoints = [
            # Feed and discovery endpoints
            "/feed/trending",
            "/feed/smart-mentions",
            "/feed/narratives",
            "/discovery/emerging",
            "/discovery/projects",
            "/discovery/early",

            # Analytics and insights
            "/analytics/trends",
            "/analytics/momentum",
            "/analytics/sentiment",
            "/insights/narratives",
            "/insights/smart-activity",

            # Market intelligence
            "/market/emerging",
            "/market/trending-projects",
            "/market/smart-signals",
            "/intelligence/early-projects",
            "/intelligence/momentum",

            # Social and engagement
            "/social/trending",
            "/social/emerging-topics",
            "/engagement/surge",
            "/engagement/trending",

            # Projects and tokens
            "/projects/trending",
            "/projects/emerging",
            "/projects/by-category",
            "/tokens/trending",
            "/tokens/early",

            # Search capabilities
            "/search/projects",
            "/search/trending",
            "/search/narratives",
        ]

        working_endpoints = []
        failed_endpoints = []

        for endpoint in potential_endpoints:
            try:
                print(f"Testing {endpoint}...", end=" ")

                # Try to make a request
                data = await client._make_request("GET", endpoint, params={"limit": 5})

                if data and len(str(data)) > 50:  # Check if we got meaningful data
                    print("✅ WORKING!")
                    working_endpoints.append(endpoint)
                    print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Non-dict response'}")
                else:
                    print("⚠️  Empty/minimal response")

            except Exception as e:
                print(f"❌ {type(e).__name__}: {str(e)[:100]}")
                failed_endpoints.append((endpoint, str(e)))

        print("\n" + "=" * 60)
        print(f"📊 RESULTS: {len(working_endpoints)} working, {len(failed_endpoints)} failed")
        print("=" * 60)

        if working_endpoints:
            print("\n✅ Working Endpoints:")
            for endpoint in working_endpoints:
                print(f"   {endpoint}")

        print(f"\n❌ Failed Endpoints ({len(failed_endpoints)}):")
        for endpoint, error in failed_endpoints[:5]:  # Show first 5 failures
            print(f"   {endpoint}: {error[:80]}...")

        # Test account-based discovery with known working accounts
        print("\n🔍 Testing Account-Based Discovery:")
        print("-" * 40)

        test_accounts = ["echo_0x", "VitalikButerin", "cz_binance"]

        for account in test_accounts:
            try:
                print(f"\nTesting {account}:")
                info = await client.get_account_info(account)
                if info:
                    print(f"   ✅ Account found - Keys: {list(info.keys())}")

                    # Look for interesting data patterns
                    if "smartEngagement" in info:
                        engagement = info["smartEngagement"]
                        print(f"   📊 Smart Engagement: {engagement}")

                    if "projects" in info:
                        print(f"   📂 Projects mentioned: {len(info['projects'])}")

                else:
                    print(f"   ❌ No data")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        # Test time-based queries for trend detection
        print("\n⏰ Testing Time-Based Trend Detection:")
        print("-" * 40)

        timeframes = ["1h", "6h", "24h", "7d", "30d"]

        for timeframe in timeframes:
            try:
                projects = await client.get_projects_mindshare(timeframe=timeframe, limit=3)
                if projects and len(projects) > 0:
                    print(f"✅ {timeframe}: Found {len(projects)} projects")
                    top_project = projects[0]
                    score = top_project.get("mindshare_score", 0)
                    change = top_project.get("change_24h", 0)
                    print(f"   Top: {top_project.get('name')} (score: {score}, change: {change}%)")
                else:
                    print(f"⚠️  {timeframe}: No projects found")

            except Exception as e:
                print(f"❌ {timeframe}: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(explore_moni_endpoints())
    except KeyboardInterrupt:
        print("\n\nExploration interrupted by user")
    except Exception as e:
        print(f"\n❌ Exploration failed: {e}")