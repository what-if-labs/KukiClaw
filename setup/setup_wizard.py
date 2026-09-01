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
            tokens = data.get("tokens", {})
            return {
                "success": True,
                "token": tokens.get("accessToken"),
                "refreshToken": tokens.get("refreshToken"),
                "expiresIn": tokens.get("expiresIn"),
                "user": data.get("user", {})
            }
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
            except (json.JSONDecodeError, ValueError):
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
    """Get API key from user or environment, and persist directly in config."""
    env_var = provider['env_var']
    existing_key = os.environ.get(env_var)

    if existing_key:
        print(f"\n✅ Found {env_var} in environment")
        use_env = get_input(f"Use existing {env_var}? (y/n)", "y")
        if use_env.lower() == 'y':
            # Store the actual key value directly in the config file,
            # not an env var reference like ${OPENAI_API_KEY}.
            print(f"   The key will be stored directly in ~/.openclaw/openclaw.json")
            return existing_key

    print(f"\n🔑 Enter your {provider['name']} API key:")
    print(f"   (This will be stored in ~/.openclaw/openclaw.json)")
    api_key = get_password(f"{env_var}")

    # Return the actual key for direct storage in config
    return api_key


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


def create_mcp_config(existing_config, url, token, refresh_token=None, telegram_config=None):
    """Create OpenClaw MCP client configuration for KūkiOS"""
    config = existing_config.copy() if existing_config else {}

    # Update meta
    config["meta"] = {
        "lastTouchedVersion": "2026.8.1"
    }

    # Add MCP configuration with actual token (not env var reference)
    mcp_server_config = {
        "url": url,
        "headers": {
            "Authorization": f"Bearer {token}"
        }
    }
    # Save refresh token for automatic token refresh
    if refresh_token:
        mcp_server_config["refreshToken"] = refresh_token

    config["mcp"] = {
        "servers": {
            "kukios-mcp": mcp_server_config
        }
    }

    # Also save token to shell profile for backward compatibility
    save_to_shell_profile("KUKIOS_TOKEN", token)

    # Add Telegram configuration if provided
    if telegram_config:
        config["channels"] = {
            "telegram": telegram_config
        }

    return config


def write_soul_file(existing_config=None):
    """Write SOUL.md to the agent workspace directory for IAQ companion personality.

    OpenClaw reads SOUL.md from the workspace directory to set the agent's voice
    and behavior. The workspace defaults to ~/.openclaw/workspace but can be
    overridden via agents.defaults.workspace in openclaw.json.
    """
    # Resolve workspace directory
    workspace = os.environ.get("OPENCLAW_WORKSPACE", "").strip()
    if not workspace:
        if existing_config:
            workspace = existing_config.get("agents", {}).get("defaults", {}).get("workspace", "").strip()
    if not workspace:
        workspace = str(Path.home() / ".openclaw" / "workspace")

    workspace = os.path.expanduser(workspace)
    workspace_path = Path(workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)

    soul_path = workspace_path / "SOUL.md"

    # Don't overwrite existing SOUL.md
    if soul_path.exists():
        print(f"\nℹ️  SOUL.md already exists at: {soul_path}")
        print("   Skipping personality setup (your existing personality is preserved)")
        return

    soul_content = """# KūkiClaw — IAQ Companion

You are KūkiClaw, an Indoor Air Quality (IAQ) companion agent.

## Role

You help users monitor and understand their IoT sensor data, air quality metrics,
and building health. You are knowledgeable about CO2, PM2.5, temperature, humidity,
TVOC, and other environmental sensors.

## Capabilities

- Check device status and retrieve real-time readings
- Analyze historical air quality trends
- Provide compliance analysis against IAQ standards (SS554, WELL, WHO, RESET, GOAQS)
- Generate IAQ health scores and reports
- Monitor alerts and recommend actions

## Tone

Be friendly, concise, and practical. Prioritize user safety and health
recommendations when air quality is poor. Use real data from the KūkiOS MCP
tools — don't guess or hallucinate readings.

## Safety

When air quality is poor (high CO2, dangerous PM2.5, etc.), clearly flag the
risk and recommend concrete actions (ventilation, evacuate, check HVAC).
Never downplay health-relevant readings.
"""

    with open(soul_path, "w") as f:
        f.write(soul_content)

    print(f"\n✅ IAQ Companion personality written to: {soul_path}")
    print("   This gives your agent a focused IAQ voice and safety awareness.")


def test_mcp_connection(url, token):
    """Test MCP connection with the provided token"""
    try:
        # Try root domain first (most common for KukiOS)
        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if response.status_code in [200, 401, 403]:
                return {"success": True, "endpoint": "/ (root)", "status": response.status_code}
        except (requests.exceptions.RequestException, ValueError):
            pass

        # Try common MCP endpoints as fallback
        endpoints = [
            "/mcp",
            "/api/mcp",
            "/mcp/v1",
            "/.well-known/mcp"
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{url}{endpoint}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                if response.status_code in [200, 401]:  # 401 means endpoint exists but needs auth
                    return {"success": True, "endpoint": endpoint, "status": response.status_code}
            except (requests.exceptions.RequestException, ValueError):
                continue

        return {"success": False, "error": "No MCP endpoint found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def refresh_token_via_api(url, refresh_token):
    """Refresh JWT token using the refresh token endpoint.

    Returns a new access/refresh token pair without requiring re-login.
    """
    try:
        response = requests.post(
            f"{url}/api/auth/refresh",
            json={"refreshToken": refresh_token},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            tokens = data.get("tokens", {})
            return {
                "success": True,
                "token": tokens.get("accessToken"),
                "refreshToken": tokens.get("refreshToken"),
                "expiresIn": tokens.get("expiresIn"),
            }
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", error_data.get("message", f"HTTP {response.status_code}"))
            except Exception:
                error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
            return {"success": False, "error": error_msg}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to server"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_mcp_protocol(url, token):
    """Test MCP connection using JSON-RPC initialize handshake.

    Sends a proper MCP protocol initialize request and verifies the
    server responds with valid protocol capabilities.
    """
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "kukiclaw-setup", "version": "1.0.0"},
        },
    }

    # Try root domain first
    endpoints_to_test = [""]
    # Then common MCP endpoints
    for ep in ["/mcp", "/api/mcp", "/mcp/v1", "/.well-known/mcp"]:
        endpoints_to_test.append(ep)

    for endpoint in endpoints_to_test:
        test_url = url + endpoint
        try:
            response = requests.post(
                test_url,
                json=initialize_request,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=10
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Check for valid JSON-RPC response
                    if "result" in data:
                        result = data["result"]
                        capabilities = result.get("capabilities", {})
                        server_info = result.get("serverInfo", {})
                        return {
                            "success": True,
                            "endpoint": endpoint if endpoint else "/ (root)",
                            "protocol_version": result.get("protocolVersion", "unknown"),
                            "capabilities": list(capabilities.keys()) if capabilities else [],
                            "server_name": server_info.get("name", "unknown"),
                            "server_version": server_info.get("version", "unknown"),
                        }
                    elif "error" in data:
                        # Got a valid JSON-RPC error — protocol is working
                        return {
                            "success": True,
                            "endpoint": endpoint if endpoint else "/ (root)",
                            "protocol_error": data["error"].get("message", "unknown"),
                            "note": "MCP protocol responded (error is expected for some methods)",
                        }
                except Exception:
                    # Got 200 but not JSON — endpoint exists but not MCP
                    continue
            elif response.status_code == 405:
                # Method not allowed — endpoint exists, try GET-based test
                continue
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue

    return {"success": False, "error": "No MCP protocol endpoint responded to initialize"}


def refresh_token(url, email, password):
    """Refresh/get a new JWT token"""
    return test_connection(url, email, password)


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
    refresh_token = result.get("refreshToken")
    expires_in = result.get("expiresIn")
    user = result.get("user", {})
    print(f"✅ Connected! Welcome, {user.get('firstName', 'User')}")
    if expires_in:
        print(f"   Token expires in {expires_in}s ({expires_in // 60} minutes)")

    # Step 3b: Test MCP Connection (HTTP reachability)
    print("\n🔗 Testing MCP Connection...")
    mcp_test = test_mcp_connection(url, token)
    if mcp_test["success"]:
        print(f"✅ MCP endpoint found: {mcp_test['endpoint']}")
    else:
        print(f"⚠️  MCP test warning: {mcp_test['error']}")
        print("   The token works for auth, but MCP endpoint may need verification.")

    # Step 3c: Test MCP Protocol (JSON-RPC initialize)
    print("\n🔗 Testing MCP Protocol (JSON-RPC handshake)...")
    protocol_test = test_mcp_protocol(url, token)
    if protocol_test["success"]:
        print(f"✅ MCP protocol OK at {protocol_test['endpoint']}")
        if protocol_test.get("server_name"):
            print(f"   Server: {protocol_test['server_name']} v{protocol_test.get('server_version', '?')}")
        if protocol_test.get("protocol_version"):
            print(f"   Protocol: {protocol_test['protocol_version']}")
        if protocol_test.get("capabilities"):
            print(f"   Capabilities: {', '.join(protocol_test['capabilities'])}")
        if protocol_test.get("note"):
            print(f"   Note: {protocol_test['note']}")
    else:
        print(f"⚠️  Protocol test warning: {protocol_test['error']}")
        print("   HTTP endpoint is reachable but JSON-RPC handshake did not respond.")

    # Step 3d: Test token refresh flow (if refresh token available)
    if refresh_token:
        print("\n🔄 Testing token refresh...")
        refresh_result = refresh_token_via_api(url, refresh_token)
        if refresh_result["success"]:
            print(f"✅ Token refresh works (new token expires in {refresh_result.get('expiresIn', '?')}s)")
        else:
            print(f"⚠️  Token refresh test: {refresh_result['error']}")
            print("   You can still re-authenticate with credentials to get a new token.")

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
    config = create_mcp_config(existing_config, url, token, refresh_token, telegram_config)

    openclaw_dir = Path.home() / ".openclaw"
    openclaw_dir.mkdir(exist_ok=True)

    config_path = openclaw_dir / "openclaw.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    os.chmod(config_path, 0o600)
    print(f"✅ Configuration saved to: {config_path}")

    # Step 5b: Write IAQ Companion Personality
    write_soul_file(existing_config)

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

🔄 Token refresh: JWT tokens expire. To refresh without re-entering credentials:
   python3 setup/refresh_token.py

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
