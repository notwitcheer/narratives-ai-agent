"""Configuration management for Daily Alpha MCP."""

import os
from pathlib import Path


def load_env():
    """
    Load environment variables from .env file if it exists.

    This is a simple .env loader that reads KEY=VALUE pairs.
    For production, consider using python-dotenv package.
    """
    env_file = Path(__file__).parent.parent.parent / ".env"

    if not env_file.exists():
        return

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Set environment variable (don't override existing ones)
                if key and not os.getenv(key):
                    os.environ[key] = value


# Auto-load on import
load_env()


# Export commonly used config values
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
