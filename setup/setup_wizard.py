#!/usr/bin/env python3
"""
KukiClaw Setup Wizard
Interactive setup for Kukisense IAQ MCP client configuration.
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path

def print_header():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🤖  KukiClaw Setup Wizard                              ║
║   OpenClaw + Kukisense IAQ Companion Agent               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")

def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    else:
        while True:
            value = input(f"{prompt}: ").strip()
            if value:
                return value

def test_connection(url, email, password):
    """Test connection to IAQ Reporter and get JWT token"""
    try:
        response = requests.post(
            f"{url}/api/auth/login",
            json={"email": email, "password": password},
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
            return {
                "success": False,
                "error": f"Authentication failed: {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to server. Check URL."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_mcp_config(url, token, mcp_server_path):
    """Create OpenClaw MCP client configuration"""
    config = {
        "meta": {
            "lastTouchedVersion": "2026.4.22"
        },
        "mcp": {
            "servers": {
                "kukisense-iaq": {
                    "command": f"{mcp_server_path}/venv/bin/python3",
                    "args": [f"{mcp_server_path}/server.py"],
                    "env": {
                        "IAQ_REPORTER_URL": url,
                        "IAQ_TOKEN": token,
                        "CACHE_TTL": "300",
                        "POOL_CONNECTIONS": "10",
                        "POOL_MAXSIZE": "20",
                        "MAX_RETRIES": "3",
                        "REQUEST_TIMEOUT": "30"
                    }
                }
            }
        }
    }
    return config

def setup_mcp_server():
    """Setup Kukisense IAQ MCP Server"""
    print("\n📦 Setting up Kukisense IAQ MCP Server...")
    
    mcp_dir = Path("kukisense-mcp-server")
    
    if not mcp_dir.exists():
        print("Cloning MCP server repository...")
        subprocess.run([
            "git", "clone", 
            "https://github.com/what-if21/iaq-reporter-mcp.git",
            str(mcp_dir)
        ], check=True)
    
    os.chdir(mcp_dir)
    
    if not Path("venv").exists():
        print("Creating Python virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    print("Installing dependencies...")
    pip_path = "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip"
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    
    os.chdir("..")
    return str(mcp_dir.absolute())

def main():
    print_header()
    
    print("This wizard will set up KukiClaw as your IAQ companion agent.")
    print("You'll need your Kukisense IAQ Reporter credentials.\n")
    
    # Step 1: Get IAQ Reporter URL
    print("🌐 Step 1: IAQ Reporter Server")
    url = get_input("IAQ Reporter URL", "https://dashbeta.what-if.sg")
    
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
        sys.exit(1)
    
    token = result["token"]
    user = result.get("user", {})
    print(f"✅ Connected! Welcome, {user.get('firstName', 'User')}")
    
    # Step 4: Setup MCP Server
    print("\n📦 Step 4: Setting up MCP Server...")
    mcp_path = setup_mcp_server()
    print(f"✅ MCP Server ready at: {mcp_path}")
    
    # Step 5: Create OpenClaw Config
    print("\n⚙️  Step 5: Creating OpenClaw Configuration...")
    config = create_mcp_config(url, token, mcp_path)
    
    openclaw_dir = Path.home() / ".openclaw"
    openclaw_dir.mkdir(exist_ok=True)
    
    config_path = openclaw_dir / "openclaw.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    os.chmod(config_path, 0o600)
    print(f"✅ Configuration saved to: {config_path}")
    
    # Step 6: Summary
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print(f"""
Your KukiClaw bot is now configured with:
  • Server: {url}
  • User: {email}
  • MCP Server: {mcp_path}
  • Config: {config_path}

To start your IAQ companion agent:
  1. cd {Path(__file__).parent.parent}
  2. openclaw start

Example queries:
  • "What's the CO2 level in the meeting room?"
  • "Show me all sensors with poor air quality"
  • "Which devices are offline?"
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
