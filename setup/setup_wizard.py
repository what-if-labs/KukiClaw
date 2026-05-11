#!/usr/bin/env python3
"""
KukiClaw Setup Wizard
Interactive setup for KūkiOS MCP client configuration.
Connects to the cloud-hosted KūkiOS MCP server at dashbeta.what-if.sg
"""

import os
import sys
import json
import requests
from pathlib import Path

def print_header():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🤖  KūkiClaw Setup Wizard                              ║
║   OpenClaw + KūkiOS MCP Client                           ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")

def get_input(prompt, default=None):
    """Get user input from terminal (works even when stdin is piped)"""
    try:
        # Open terminal directly for input
        with open('/dev/tty', 'r') as tty:
            if default:
                sys.stdout.write(f"{prompt} [{default}]: ")
            else:
                sys.stdout.write(f"{prompt}: ")
            sys.stdout.flush()
            value = tty.readline().strip()
    except:
        # Fallback to stdin if /dev/tty not available
        if default:
            value = input(f"{prompt} [{default}]: ").strip()
        else:
            value = input(f"{prompt}: ").strip()
    
    if default and not value:
        return default
    return value

def test_connection(url, email, password):
    """Test connection to KūkiOS and get JWT token"""
    try:
        response = requests.post(
            f"{url}/api/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "token": data.get("tokens", {}).get("accessToken"),
                "user": data.get("user", {})
            }
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
            except:
                error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
            return {
                "success": False,
                "error": error_msg
            }
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to server. Check URL."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_mcp_config(url, token):
    """Create OpenClaw MCP client configuration for KūkiOS"""
    config = {
        "meta": {
            "lastTouchedVersion": "2026.4.22"
        },
        "mcp": {
            "servers": {
                "kukios-mcp": {
                    "url": url,
                    "headers": {
                        "Authorization": f"Bearer {token}"
                    }
                }
            }
        }
    }
    return config

def main():
    print_header()
    
    print("This wizard will set up KūkiClaw connected to KūkiOS MCP.")
    print("You'll need your KūkiOS credentials.\n")
    
    # Step 1: Get KūkiOS MCP Server URL
    print("🌐 Step 1: KūkiOS MCP Server")
    url = get_input("KūkiOS MCP Server URL", "https://dashbeta.what-if.sg")
    
    # Step 2: Get Credentials
    print("\n🔐 Step 2: Your Credentials")
    email = get_input("Email address")
    password = get_input("Password")
    
    # Step 3: Test Connection
    print("\n🔗 Step 3: Testing Connection...")
    result = test_connection(url, email, password)
    
    if not result["success"]:
        print(f"❌ {result['error']}")
        print("\nPlease check your credentials and try again.")
        print("\nTroubleshooting:")
        print("  1. Verify your email and password are correct")
        print(f"  2. Test manually: curl -X POST {url}/api/auth/login \\")
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"email":"your-email","password":"your-password"}\'')
        sys.exit(1)
    
    token = result["token"]
    user = result.get("user", {})
    print(f"✅ Connected! Welcome, {user.get('firstName', 'User')}")
    
    # Step 4: Create OpenClaw Config
    print("\n⚙️  Step 4: Creating OpenClaw Configuration...")
    config = create_mcp_config(url, token)
    
    openclaw_dir = Path.home() / ".openclaw"
    openclaw_dir.mkdir(exist_ok=True)
    
    config_path = openclaw_dir / "openclaw.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    os.chmod(config_path, 0o600)
    print(f"✅ Configuration saved to: {config_path}")
    
    # Step 5: Summary
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print(f"""
Your KūkiClaw bot is now configured with:
  • KūkiOS MCP: {url}
  • User: {email}
  • Config: {config_path}

KūkiOS MCP is cloud-hosted - no local server required!

To start your IAQ companion agent:
  1. openclaw start

Example queries:
  • "What's the CO2 level in the meeting room?"
  • "Show me all sensors with poor air quality"
  • "Which devices are offline?"
  • "Get IAQ health score for device X"
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
