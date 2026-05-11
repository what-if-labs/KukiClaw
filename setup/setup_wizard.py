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
    """Get user input from terminal"""
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    else:
        while True:
            value = input(f"{prompt}: ").strip()
            if value:
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

def create_mcp_config(url, token, telegram_config=None):
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
    
    # Add Telegram configuration if provided
    if telegram_config:
        config["channels"] = {
            "telegram": telegram_config
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
    
    # Step 4: Telegram Configuration
    print("\n💬 Step 4: Telegram Configuration (Optional)")
    print("Configure Telegram to chat with your IAQ companion agent.")
    
    setup_telegram = get_input("Set up Telegram? (y/n)", "n")
    
    telegram_config = None
    if setup_telegram.lower() == 'y':
        print("\n📱 Telegram Setup Instructions:")
        print("  1. Open Telegram and chat with @BotFather")
        print("  2. Run /newbot and follow prompts")
        print("  3. Save the bot token")
        print()
        
        bot_token = get_input("Telegram Bot Token")
        
        print("\n🔐 DM Policy Options:")
        print("  - pairing (default): Approve each user manually")
        print("  - allowlist: Only specific user IDs can DM")
        print("  - open: Anyone can DM (not recommended)")
        
        dm_policy = get_input("DM Policy", "pairing")
        
        telegram_config = {
            "enabled": True,
            "botToken": bot_token,
            "dmPolicy": dm_policy,
            "groups": {"*": {"requireMention": True}}
        }
        
        if dm_policy == "allowlist":
            print("\n📝 Enter your Telegram user ID (one per line, empty to finish):")
            print("   To find your ID: DM your bot, then run 'openclaw logs --follow'")
            allow_from = []
            while True:
                user_id = input("   User ID (or press Enter to finish): ").strip()
                if not user_id:
                    break
                allow_from.append(user_id)
            if allow_from:
                telegram_config["allowFrom"] = allow_from
    
    # Step 5: Create OpenClaw Config
    print("\n⚙️  Step 5: Creating OpenClaw Configuration...")
    config = create_mcp_config(url, token, telegram_config)
    
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
    
    summary = f"""
Your KūkiClaw bot is now configured with:
  • KūkiOS MCP: {url}
  • User: {email}
  • Config: {config_path}"""
    
    if telegram_config:
        summary += f"""
  • Telegram: ✅ Configured (DM Policy: {telegram_config.get('dmPolicy', 'pairing')})"""
    
    summary += f"""

KūkiOS MCP is cloud-hosted - no local server required!

🚀 To start your IAQ companion agent:
  1. Open a NEW terminal (or run: source ~/.bashrc)
  2. Run: openclaw start

   Or use full path immediately:
   ~/.npm-global/bin/openclaw start"""
    
    if telegram_config:
        summary += f"""

💬 To test Telegram:
  1. Start OpenClaw: openclaw start
  2. DM your bot on Telegram
  3. If using 'pairing' policy:
     - Run: openclaw pairing list telegram
     - Run: openclaw pairing approve telegram <CODE>"""
    
    summary += f"""

📝 Example queries:
  • "What's the CO2 level in the meeting room?"
  • "Show me all sensors with poor air quality"
  • "Which devices are offline?"
  • "Get IAQ health score for device X"
"""
    
    print(summary)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
