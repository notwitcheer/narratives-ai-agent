#!/usr/bin/env python3
"""
Test script for enhanced crypto intelligence features.
Tests the new emerging projects detection, smart money tracking, and project health analysis.
"""

import asyncio
import os
from src.daily_alpha.sources.moni import MoniClient

async def test_enhanced_features():
    """Test all new enhanced crypto intelligence features."""

    moni_api_key = os.getenv("MONI_API_KEY")
    if not moni_api_key:
        print("❌ MONI_API_KEY not found")
        return

    print("🚀 Testing Enhanced Crypto Intelligence Features")
    print("=" * 60)

    async with MoniClient(moni_api_key) as client:

        # Test 1: Emerging Projects Detection
        print("\\n🔍 TEST 1: Emerging Projects Detection")
        print("-" * 40)
        try:
            emerging = await client.detect_emerging_projects(
                discovery_method="all",
                timeframe="7d",
                min_confidence=0.5,  # Lower threshold for testing
                limit=5
            )

            if emerging:
                print(f"✅ Found {len(emerging)} emerging projects:")
                for i, project in enumerate(emerging, 1):
                    name = project.get('name', 'Unknown')
                    confidence = project.get('confidence_score', 0)
                    signals = project.get('emergence_signals', {})
                    print(f"  {i}. {name} (Confidence: {confidence:.1%})")
                    if signals.get('smart_money_interest'):
                        print("      🧠 Smart money interest detected")
                    if signals.get('engagement_surge'):
                        print("      📈 Engagement surge detected")
            else:
                print("⚠️  No emerging projects found (confidence threshold might be too high)")

        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 2: Smart Money Tracking
        print("\\n💰 TEST 2: Smart Money Tracking")
        print("-" * 40)
        try:
            smart_moves = await client.track_smart_money_moves(
                wallet_tier="tier1",
                timeframe="24h",
                limit=3  # Limit for testing
            )

            if smart_moves:
                print(f"✅ Found {len(smart_moves)} smart money activities:")
                for i, move in enumerate(smart_moves, 1):
                    account = move.get('account_handle', 'Unknown')
                    significance = move.get('significance_score', 0)
                    moni_score = move.get('moni_score', 0)
                    print(f"  {i}. @{account} (Significance: {significance:.1%}, Influence: {moni_score:,})")
            else:
                print("⚠️  No significant smart money activity detected")

        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 3: Project Health Analysis
        print("\\n🏥 TEST 3: Project Health Analysis")
        print("-" * 40)

        test_projects = ["Ethereum", "Solana", "Arbitrum"]

        for project_name in test_projects:
            try:
                print(f"\\nAnalyzing {project_name}...")
                health = await client.analyze_project_health(
                    project_name=project_name,
                    include_fundamentals=True,
                    risk_assessment=True
                )

                if health.get("status") == "not_found":
                    print(f"  ❌ {project_name} not found in current data")
                elif health.get("status") == "error":
                    print(f"  ❌ Analysis failed: {health.get('message')}")
                else:
                    grade = health.get('health_grade', 'N/A')
                    score = health.get('overall_health_score', 0)
                    social = health.get('social_intelligence', {})
                    engagement = health.get('engagement_analysis', {})

                    print(f"  ✅ {project_name}: Health Grade {grade} ({score:.1f}/10)")
                    print(f"     • Social Health: {social.get('social_health', 'unknown').title()}")
                    print(f"     • Momentum: {engagement.get('momentum_direction', 'unknown').title()}")

                    risks = health.get('risk_factors', [])
                    opportunities = health.get('opportunities', [])

                    if risks:
                        print(f"     • Risk Factors: {len(risks)}")
                    if opportunities:
                        print(f"     • Opportunities: {len(opportunities)}")

                # Rate limiting pause
                await asyncio.sleep(1)

            except Exception as e:
                print(f"  ❌ Error analyzing {project_name}: {e}")

        print("\\n" + "=" * 60)
        print("✅ Enhanced crypto intelligence testing complete!")
        print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(test_enhanced_features())
    except KeyboardInterrupt:
        print("\\n\\nTesting interrupted by user")
    except Exception as e:
        print(f"\\n\\n❌ Testing failed: {e}")