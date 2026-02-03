#!/usr/bin/env python3
"""
Security setup helper for HondaLink Controller.

This script helps you generate secure API keys and configure security settings.
"""

import secrets
import sys
from pathlib import Path


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


def main():
    print("=" * 70)
    print("HondaLink Controller - Security Setup Helper")
    print("=" * 70)
    print()

    print("This script will help you set up security for your HondaLink server.")
    print()

    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        print(f"⚠️  No .env file found.")
        if env_example.exists():
            print(f"   Creating .env from .env.example...")
            env_file.write_text(env_example.read_text())
            print(f"   ✓ Created .env file")
        else:
            print(f"   ✗ No .env.example found either!")
            sys.exit(1)

    print()
    print("1. GENERATE API KEY")
    print("-" * 70)
    num_keys = input("   How many API keys do you need? [1]: ").strip() or "1"

    try:
        num_keys = int(num_keys)
    except ValueError:
        print("   ✗ Invalid number")
        sys.exit(1)

    api_keys = [generate_api_key() for _ in range(num_keys)]

    print()
    print("   Generated API keys:")
    for i, key in enumerate(api_keys, 1):
        print(f"   [{i}] {key}")

    print()
    print("2. CONFIGURE IP WHITELIST")
    print("-" * 70)
    print("   Leave empty to allow all IPs (not recommended)")
    print("   Examples:")
    print("     - Single IP: 192.168.1.100")
    print("     - Multiple: 192.168.1.100,192.168.1.50")
    print("     - Network: 192.168.1.0/24")

    allowed_ips = input("   Enter allowed IPs: ").strip()

    print()
    print("3. CONFIGURE RATE LIMITS")
    print("-" * 70)
    api_rate = input("   API rate limit (requests/min) [30]: ").strip() or "30"
    cmd_rate = input("   Command rate limit (requests/min) [10]: ").strip() or "10"

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Add these to your .env file:")
    print()
    print("REQUIRE_AUTHENTICATION=true")
    print(f"API_KEYS={','.join(api_keys)}")
    print(f"ALLOWED_IPS={allowed_ips}")
    print("ENABLE_RATE_LIMITING=true")
    print(f"API_RATE_LIMIT={api_rate}")
    print(f"COMMAND_RATE_LIMIT={cmd_rate}")
    print()

    update = input("Update .env file automatically? [y/N]: ").strip().lower()

    if update == "y":
        env_content = env_file.read_text()

        replacements = {
            "API_KEYS=": f"API_KEYS={','.join(api_keys)}",
            "ALLOWED_IPS=": f"ALLOWED_IPS={allowed_ips}",
            "API_RATE_LIMIT=": f"API_RATE_LIMIT={api_rate}",
            "COMMAND_RATE_LIMIT=": f"COMMAND_RATE_LIMIT={cmd_rate}",
            "REQUIRE_AUTHENTICATION=false": "REQUIRE_AUTHENTICATION=true",
            "ENABLE_RATE_LIMITING=false": "ENABLE_RATE_LIMITING=true",
        }

        for key, value in replacements.items():
            if key in env_content:
                env_content = env_content.replace(
                    key + env_content.split(key)[1].split("\n")[0], value
                )

        env_file.write_text(env_content)
        print("✓ Updated .env file")
        print()
        print("Next steps:")
        print("1. Review .env file")
        print("2. Start server with: uv run uvicorn src.hondalink.main:app")
        print("3. Use API keys in X-API-Key header")
    else:
        print("Manual setup required - copy the settings above to your .env file")

    print()
    print("For HTTPS setup, see SECURITY.md")
    print()


if __name__ == "__main__":
    main()
