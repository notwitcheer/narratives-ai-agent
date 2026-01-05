#!/usr/bin/env python3
"""
Quick setup verification script.

Run this to verify your environment is configured correctly
before trying to run the MCP server or examples.

Usage: uv run python test_setup.py
"""

import sys
import os


def test_python_version():
    """Check Python version is 3.10+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version: {version.major}.{version.minor}.{version.micro}")
        print("   Required: Python 3.10 or higher")
        return False


def test_imports():
    """Check all required modules can be imported"""
    required_modules = [
        ("httpx", "httpx"),
        ("mcp.server", "mcp"),
        ("mcp.types", "mcp"),
    ]

    all_good = True
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {package_name} is installed")
        except ImportError:
            print(f"❌ {package_name} is NOT installed")
            print(f"   Run: uv sync")
            all_good = False

    return all_good


def test_project_structure():
    """Check project files exist"""
    required_files = [
        "src/daily_alpha/__init__.py",
        "src/daily_alpha/server.py",
        "src/daily_alpha/sources/github_trending.py",
        "src/daily_alpha/sources/awesome_mcp.py",
        "src/daily_alpha/aggregators/tech_trends.py",
    ]

    all_good = True
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"✅ {filepath}")
        else:
            print(f"❌ {filepath} NOT FOUND")
            all_good = False

    return all_good


def test_github_token():
    """Check if GitHub token is configured"""
    # Import config to load .env file
    try:
        from src.daily_alpha.config import GITHUB_TOKEN as token
    except ImportError:
        token = os.getenv("GITHUB_TOKEN")

    if token:
        # Don't print the actual token, just check it's there
        print(f"✅ GITHUB_TOKEN is set ({len(token)} chars)")
        if token.startswith("ghp_"):
            print("   Token format looks correct (ghp_...)")
        else:
            print("   ⚠️  Token doesn't start with 'ghp_' - is it correct?")
        return True
    else:
        print("⚠️  GITHUB_TOKEN not set (optional but recommended)")
        print("   Without token: 60 requests/hour")
        print("   With token: 5,000 requests/hour")
        print("   Set it: export GITHUB_TOKEN='your_token'")
        return None  # Warning, not error


def test_can_import_daily_alpha():
    """Check if our package can be imported"""
    try:
        from src.daily_alpha import __version__
        print(f"✅ daily_alpha package can be imported (v{__version__})")
        return True
    except ImportError as e:
        print(f"❌ Cannot import daily_alpha package")
        print(f"   Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("Daily Alpha MCP - Setup Verification")
    print("=" * 70)
    print()

    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_imports),
        ("Project Structure", test_project_structure),
        ("Package Import", test_can_import_daily_alpha),
        ("GitHub Token", test_github_token),
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 70)
        results[test_name] = test_func()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v is True)
    warnings = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)

    print(f"✅ Passed: {passed}")
    if warnings:
        print(f"⚠️  Warnings: {warnings}")
    if failed:
        print(f"❌ Failed: {failed}")

    print()

    if failed == 0:
        print("🎉 All critical tests passed! Ready to run.")
        print()
        print("Next steps:")
        print("1. Run example: uv run python example.py")
        print("2. Set up Claude Desktop: see QUICKSTART.md")
        if warnings:
            print("3. (Optional) Set GITHUB_TOKEN for higher rate limits")
        return 0
    else:
        print("❌ Some tests failed. Fix the issues above before proceeding.")
        print()
        print("Common fixes:")
        print("- Install dependencies: uv sync")
        print("- Check Python version: python --version")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
