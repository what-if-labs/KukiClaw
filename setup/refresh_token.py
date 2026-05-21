#!/usr/bin/env python3
"""
KukiClaw Token Refresh Utility

Refreshes expired JWT tokens without requiring re-authentication with credentials.
Reads the refresh token from ~/.openclaw/openclaw.json, exchanges it for a new
access/refresh token pair via the /api/auth/refresh endpoint, and updates the config.

Usage:
    python3 setup/refresh_token.py
"""

import json
import sys
import requests
from pathlib import Path


CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"


def load_config():
    """Load OpenClaw configuration."""
    if not CONFIG_PATH.exists():
        print(f"Error: Configuration not found at {CONFIG_PATH}")
        print("Run the setup wizard first: curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/setup/setup_wizard.py | python3")
        sys.exit(1)

    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Failed to read configuration: {e}")
        sys.exit(1)


def get_mcp_server_config(config):
    """Extract KukiOS MCP server config from OpenClaw config."""
    mcp_servers = config.get("mcp", {}).get("servers", {})
    kukios = mcp_servers.get("kukios-mcp", {})
    if not kukios:
        print("Error: No kukios-mcp server found in configuration.")
        print("Run the setup wizard first to configure the MCP connection.")
        sys.exit(1)
    return kukios


def refresh_token(url, refresh_token):
    """Exchange a refresh token for a new access/refresh token pair."""
    try:
        response = requests.post(
            f"{url}/api/auth/refresh",
            json={"refreshToken": refresh_token},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            tokens = data.get("tokens", {})
            return {
                "success": True,
                "accessToken": tokens.get("accessToken"),
                "refreshToken": tokens.get("refreshToken"),
                "expiresIn": tokens.get("expiresIn"),
            }
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", error_data.get("message", f"HTTP {response.status_code}"))
            except Exception:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            return {"success": False, "error": error_msg}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": f"Cannot connect to {url}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": f"Connection to {url} timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_config(config, new_access_token, new_refresh_token):
    """Update the config file with new tokens."""
    mcp_server = config["mcp"]["servers"]["kukios-mcp"]

    # Update Authorization header with new access token
    auth_header = mcp_server.get("headers", {}).get("Authorization", "")
    if auth_header.startswith("Bearer "):
        mcp_server["headers"]["Authorization"] = f"Bearer {new_access_token}"
    else:
        mcp_server["headers"]["Authorization"] = f"Bearer {new_access_token}"

    # Update refresh token if we got a new one
    if new_refresh_token:
        mcp_server["refreshToken"] = new_refresh_token

    # Write config back
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    CONFIG_PATH.chmod(0o600)


def main():
    print("=" * 60)
    print("  KukiClaw Token Refresh")
    print("=" * 60)
    print()

    # Load config
    print(f"Loading configuration from {CONFIG_PATH}...")
    config = load_config()

    # Get MCP server config
    mcp_server = get_mcp_server_config(config)
    url = mcp_server.get("url", "").rstrip("/")
    refresh_token_value = mcp_server.get("refreshToken", "")

    if not url:
        print("Error: No KukiOS server URL found in configuration.")
        sys.exit(1)

    if not refresh_token_value:
        print(f"Error: No refresh token found in configuration for {url}")
        print()
        print("The refresh token was not saved during initial setup.")
        print("Please re-run the setup wizard to re-authenticate:")
        print(f"  curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/setup/setup_wizard.py | python3")
        sys.exit(1)

    print(f"KukiOS server: {url}")
    print()

    # Refresh token
    print("Refreshing token...")
    result = refresh_token(url, refresh_token_value)

    if not result["success"]:
        print(f"\nError: {result['error']}")
        print()
        if "INVALID_REFRESH_TOKEN" in result.get("error", "") or "expired" in result.get("error", "").lower():
            print("Your refresh token has expired. Re-authenticate with credentials:")
            print(f"  curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/setup/setup_wizard.py | python3")
        else:
            print("If this persists, re-run the setup wizard to re-authenticate.")
        sys.exit(1)

    new_access = result["accessToken"]
    new_refresh = result["refreshToken"]
    expires_in = result.get("expiresIn")

    if not new_access:
        print("Error: Server did not return a new access token.")
        sys.exit(1)

    # Update config
    update_config(config, new_access, new_refresh)

    print(f"Token refreshed successfully!")
    if expires_in:
        print(f"New token expires in {expires_in}s ({expires_in // 60} minutes)")
    print()
    print(f"Configuration updated: {CONFIG_PATH}")
    print()

    # Quick verification test
    print("Verifying connection...")
    try:
        test = requests.get(
            url,
            headers={"Authorization": f"Bearer {new_access}"},
            timeout=5
        )
        if test.status_code in [200, 401, 403]:
            print(f"Connection verified (HTTP {test.status_code})")
        else:
            print(f"Server responded with HTTP {test.status_code}")
    except Exception as e:
        print(f"Verification request failed: {e}")
        print("(Token was still saved — test manually if needed)")

    print()
    print("Done. Restart OpenClaw to use the new token:")
    print("  openclaw gateway stop && openclaw gateway start")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nToken refresh cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
