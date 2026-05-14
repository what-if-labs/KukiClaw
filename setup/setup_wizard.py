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

# Available model providers and their configurations
PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "env_var": "OPENAI_API_KEY",
        "models": [
            ("openai/gpt-5.5", "GPT-5.5 (Latest)"),
            ("openai/gpt-5.4", "GPT-5.4"),
            ("openai/gpt-5.4-mini", "GPT-5.4 Mini"),
        ],
        "base_url": None,
        "api": "openai",
    },
    "anthropic": {
        "name": "Anthropic",
        "env_var": "ANTHROPIC_API_KEY",
        "models": [
            ("anthropic/claude-opus-4-6", "Claude Opus 4.6"),
            ("anthropic/claude-sonnet-4-7", "Claude Sonnet 4.7"),
            ("anthropic/claude-sonnet-4-5", "Claude Sonnet 4.5"),
        ],
        "base_url": None,
        "api": "anthropic",
    },
    "openrouter": {
        "name": "OpenRouter",
        "env_var": "OPENROUTER_API_KEY",
        "models": [
            ("openrouter/anthropic/claude-opus-4", "Claude Opus 4 (via OpenRouter)"),
            ("openrouter/openai/gpt-5.5", "GPT-5.5 (via OpenRouter)"),
            ("openrouter/auto", "Auto (OpenRouter picks)"),
        ],
        "base_url": "https://openrouter.ai/api/v1",
        "api": "openai-completions",
    },
    "moonshot": {
        "name": "Moonshot AI (Kimi)",
        "env_var": "MOONSHOT_API_KEY",
        "models": [
            ("moonshot/kimi-k2.6", "Kimi K2.6"),
            ("moonshot/kimi-k2.5", "Kimi K2.5"),
            ("moonshot/kimi-k2-thinking", "Kimi K2 Thinking"),
        ],
        "base_url": "https://api.moonshot.ai/v1",
        "api": "openai-completions",
    },
    "qwen": {
        "name": "Qwen Cloud (Alibaba)",
        "env_var": "QWEN_API_KEY",
        "models": [
            ("qwen/qwen3.5-plus", "Qwen 3.5 Plus"),
            ("qwen/MiniMax-M2.5", "MiniMax M2.5"),
            ("qwen/glm-5", "GLM-5"),
            ("qwen/kimi-k2.5", "Kimi K2.5"),
        ],
        "base_url": "https://coding-intl.dashscope.aliyuncs.com/v1",
        "api": "openai-completions",
    },
    "zai": {
        "name": "Z.AI (GLM)",
        "env_var": "ZAI_API_KEY",
        "models": [
            ("zai/glm-5.1", "GLM 5.1"),
            ("zai/glm-5", "GLM 5"),
            ("zai/glm-4.7", "GLM 4.7"),
        ],
        "base_url": None,
        "api": "openai-completions",
    },
    "minimax": {
        "name": "MiniMax",
        "env_var": "MINIMAX_API_KEY",
        "models": [
            ("minimax/MiniMax-M2.7", "MiniMax M2.7"),
            ("minimax/MiniMax-M2.5", "MiniMax M2.5"),
        ],
        "base_url": None,
        "api": "openai-completions",
    },
    "google": {
        "name": "Google Gemini",
        "env_var": "GEMINI_API_KEY",
        "models": [
            ("google/gemini-3.1-pro-preview", "Gemini 3.1 Pro"),
            ("google/gemini-3-flash-preview", "Gemini 3 Flash"),
            ("google/gemini-2.5-pro-preview", "Gemini 2.5 Pro"),
        ],
        "base_url": None,
        "api": "gemini",
    },
    "xai": {
        "name": "xAI (Grok)",
        "env_var": "XAI_API_KEY",
        "models": [
            ("xai/grok-4.3", "Grok 4.3"),
            ("xai/grok-4", "Grok 4"),
            ("xai/grok-3", "Grok 3"),
        ],
        "base_url": None,
        "api": "openai-completions",
    },
    "deepseek": {
        "name": "DeepSeek",
        "env_var": "DEEPSEEK_API_KEY",
        "models": [
            ("deepseek/deepseek-v4", "DeepSeek V4"),
            ("deepseek/deepseek-v4-flash", "DeepSeek V4 Flash"),
            ("deepseek/deepseek-v3.2", "DeepSeek V3.2"),
        ],
        "base_url": None,
        "api": "openai-completions",
    },
}


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


def get_password(prompt):
    """Get password input (hidden)"""
    import getpass
    return getpass.getpass(f"{prompt}: ")


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


def select_provider():
    """Interactive provider selection"""
    print("\n🤖 Step 3: AI Model Provider")
    print("Select your AI model provider (like OpenClaw configure):\n")

    providers_list = list(PROVIDERS.keys())
    for i, provider_id in enumerate(providers_list, 1):
        provider = PROVIDERS[provider_id]
        print(f"  {i}. {provider['name']}")

    print(f"\n  0. Skip (use existing OpenClaw config)")

    while True:
        choice = get_input("\nSelect provider (number)", "1")
        try:
            idx = int(choice)
            if idx == 0:
                return None, None, None
            if 1 <= idx <= len(providers_list):
                provider_id = providers_list[idx - 1]
                return select_model(provider_id)
            print("❌ Invalid selection. Please try again.")
        except ValueError:
            print("❌ Please enter a number.")


def select_model(provider_id):
    """Interactive model selection for a provider"""
    provider = PROVIDERS[provider_id]

    print(f"\n📋 Available models for {provider['name']}:")
    for i, (model_id, model_name) in enumerate(provider['models'], 1):
        print(f"  {i}. {model_name}")
        print(f"     Ref: {model_id}")

    while True:
        choice = get_input("\nSelect model (number)", "1")
        try:
            idx = int(choice)
            if 1 <= idx <= len(provider['models']):
                model_id, model_name = provider['models'][idx - 1]
                return provider_id, model_id, provider
            print("❌ Invalid selection. Please try again.")
        except ValueError:
            print("❌ Please enter a number.")


def get_api_key(provider):
    """Get API key from user or environment, and persist to shell profile"""
    env_var = provider['env_var']
    existing_key = os.environ.get(env_var)

    if existing_key:
        print(f"\n✅ Found {env_var} in environment")
        use_env = get_input(f"Use existing {env_var}? (y/n)", "y")
        if use_env.lower() == 'y':
            return f"${{{env_var}}}"

    print(f"\n🔑 Enter your {provider['name']} API key:")
    print(f"   (This will be stored in ~/.bashrc as ${{{env_var}}})")
    api_key = get_password(f"{env_var}")

    # Set in current environment for this session
    os.environ[env_var] = api_key

    # Persist to shell profile
    save_to_shell_profile(env_var, api_key)

    return f"${{{env_var}}}"


def save_to_shell_profile(env_var, value):
    """Save environment variable to shell profile"""
    # Determine shell profile file
    home = Path.home()
    shell = os.environ.get('SHELL', '/bin/bash')

    if 'zsh' in shell:
        profile_file = home / ".zshrc"
    else:
        # Default to bash
        profile_file = home / ".bashrc"

    # Check if already in profile
    export_line = f'export {env_var}="{value}"'

    try:
        if profile_file.exists():
            with open(profile_file, 'r') as f:
                content = f.read()
                if env_var in content:
                    # Update existing line
                    lines = content.split('\n')
                    new_lines = []
                    found = False
                    for line in lines:
                        if line.startswith(f'export {env_var}='):
                            new_lines.append(export_line)
                            found = True
                        else:
                            new_lines.append(line)
                    if found:
                        with open(profile_file, 'w') as f:
                            f.write('\n'.join(new_lines))
                        print(f"   ✅ Updated {env_var} in {profile_file}")
                    else:
                        # Append if not found as export line
                        with open(profile_file, 'a') as f:
                            f.write(f"\n# KukiClaw AI Provider\n{export_line}\n")
                        print(f"   ✅ Added {env_var} to {profile_file}")
                else:
                    # Append to file
                    with open(profile_file, 'a') as f:
                        f.write(f"\n# KukiClaw AI Provider\n{export_line}\n")
                    print(f"   ✅ Added {env_var} to {profile_file}")
        else:
            # Create new profile file
            with open(profile_file, 'w') as f:
                f.write(f"# KukiClaw AI Provider\n{export_line}\n")
            print(f"   ✅ Created {profile_file} with {env_var}")
    except Exception as e:
        print(f"   ⚠️  Could not save to {profile_file}: {e}")
        print(f"   Please manually add: export {env_var}='your-api-key'")


def create_provider_config(provider_id, model_id, provider, api_key_ref):
    """Create provider configuration"""
    config = {
        "agents": {
            "defaults": {
                "model": {
                    "primary": model_id,
                    "fallbacks": []
                },
                "models": {
                    model_id: {}
                }
            }
        },
        "models": {
            "mode": "merge",
            "providers": {
                provider_id: {
                    "apiKey": api_key_ref,
                    "api": provider['api'],
                    "models": []
                }
            }
        },
        "auth": {
            "profiles": {
                f"{provider_id}:default": {
                    "provider": provider_id,
                    "mode": "api_key"
                }
            }
        }
    }

    # Add base URL if specified
    if provider.get('base_url'):
        config["models"]["providers"][provider_id]["baseUrl"] = provider['base_url']

    # Add all models from this provider
    for mid, name in provider['models']:
        model_config = {
            "id": mid.split('/')[-1],
            "name": name,
            "reasoning": False,
            "input": ["text", "image"] if "image" in name.lower() or "vision" in name.lower() else ["text"],
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
            "contextWindow": 128000,
            "maxTokens": 8192
        }
        config["models"]["providers"][provider_id]["models"].append(model_config)

        # Add to fallbacks (except the primary)
        if mid != model_id:
            config["agents"]["defaults"]["model"]["fallbacks"].append(mid)
            config["agents"]["defaults"]["models"][mid] = {}

    return config


def load_existing_config():
    """Load existing OpenClaw config if it exists"""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def merge_configs(existing, new):
    """Deep merge new config into existing"""
    result = existing.copy() if existing else {}

    for key, value in new.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def create_mcp_config(existing_config, url, token, telegram_config=None):
    """Create OpenClaw MCP client configuration for KūkiOS"""
    config = existing_config.copy() if existing_config else {}

    # Update meta
    config["meta"] = {
        "lastTouchedVersion": "2026.4.22"
    }

    # Add MCP configuration
    config["mcp"] = {
        "servers": {
            "kukios-mcp": {
                "url": url,
                "headers": {
                    "Authorization": f"Bearer {token}"
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
    print("You'll need your KūkiOS credentials and an AI model provider.\n")

    # Step 1: Get KūkiOS MCP Server URL
    print("🌐 Step 1: KūkiOS MCP Server")
    url = get_input("KūkiOS MCP Server URL", "https://dashbeta.what-if.sg")

    # Step 2: Get Credentials
    print("\n🔐 Step 2: Your KūkiOS Credentials")
    email = get_input("Email address")
    password = get_password("Password")

    # Step 3: Test Connection
    print("\n🔗 Testing KūkiOS Connection...")
    result = test_connection(url, email, password)

    if not result["success"]:
        print(f"❌ {result['error']}")
        print("\nPlease check your credentials and try again.")
        print("\nTroubleshooting:")
        print(f"  1. Test manually: curl -X POST {url}/api/auth/login \\")
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"email":"your-email","password":"your-password"}\'')
        sys.exit(1)

    token = result["token"]
    user = result.get("user", {})
    print(f"✅ Connected! Welcome, {user.get('firstName', 'User')}")

    # Load existing config
    existing_config = load_existing_config()
    if existing_config:
        print("\n📂 Found existing OpenClaw configuration")

    # Step 3: Model Provider Selection
    provider_id, model_id, provider = select_provider()

    model_config = {}
    if provider_id and provider:
        print(f"\n✅ Selected: {provider['name']} with {model_id}")

        # Get API key
        api_key_ref = get_api_key(provider)

        # Create provider configuration
        model_config = create_provider_config(provider_id, model_id, provider, api_key_ref)

        print(f"\n📝 Model Configuration:")
        print(f"   Provider: {provider['name']}")
        print(f"   Model: {model_id}")
        print(f"   API Key: {api_key_ref}")
    else:
        print("\n⏭️  Skipping model setup (using existing OpenClaw config)")
        if not existing_config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary"):
            print("\n⚠️  Warning: No existing model configuration found!")
            print("   You may need to run 'openclaw configure' after setup.")

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

    # Merge model config with existing
    if model_config:
        existing_config = merge_configs(existing_config, model_config)

    # Add MCP and Telegram
    config = create_mcp_config(existing_config, url, token, telegram_config)

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
  • User: {email}"""

    if provider_id and provider:
        summary += f"""
  • AI Provider: {provider['name']}
  • Model: {model_id}"""
    else:
        summary += """
  • AI Provider: (using existing config)"""

    summary += f"""
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
