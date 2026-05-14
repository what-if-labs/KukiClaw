# KūkiClaw Installation Guide

**Quick Setup for Your IAQ Companion**

---

## What is KūkiClaw?

KūkiClaw is your personal AI assistant for monitoring indoor air quality (IAQ). It connects to your KūkiOS sensors and lets you ask questions like:
- "What's the CO2 level in the meeting room?"
- "Which sensors have poor air quality?"
- "Show me temperature trends for the past week"

You can chat with it via Telegram or your terminal.

---

## What You'll Need

Before starting, gather these items:

- ✅ A Linux computer (Ubuntu, Debian, or similar)
- ✅ Internet connection
- ✅ Your KūkiOS account (email and password)
- ✅ An AI provider API key (we'll guide you through this)
- ✅ (Optional) A Telegram Bot Token if you want to chat via Telegram

**Time needed:** About 10-15 minutes

---

## Step-by-Step Installation

### Step 1: Open Your Terminal

Open the terminal application on your Linux computer. It looks like a black window where you can type commands.

![Terminal icon]

### Step 2: Run the One-Line Installer

Copy and paste this single line into your terminal, then press Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/install.sh | bash
```

**What this does:**
- Installs required software (Node.js, Python, OpenClaw)
- Downloads the setup wizard
- Guides you through configuration

The installer will ask for your password if it needs to install system packages.

### Step 3: Enter Your KūkiOS Credentials

The setup wizard will start and ask for:

**KūkiOS Server URL:**
- Press Enter to accept the default (`https://dashbeta.what-if.sg`)
- Or type your custom server URL if different

**Email Address:**
- Enter the email you use to log in to KūkiOS

**Password:**
- Enter your KūkiOS password
- The password won't show on screen as you type (this is normal for security)

The wizard will test the connection and welcome you if successful.

### Step 4: Choose Your AI Provider

KūkiClaw needs an AI model to understand your questions. Choose from popular providers:

| Provider | What You Need | Example Models |
|----------|---------------|----------------|
| OpenAI | OpenAI API key | GPT-5.5, GPT-5.4 |
| Anthropic | Anthropic API key | Claude Opus, Claude Sonnet |
| OpenRouter | OpenRouter API key | Any model via OpenRouter |
| Qwen | Qwen API key | Qwen 3.5 Plus, MiniMax |
| Google Gemini | Google API key | Gemini 3.1 Pro, Gemini 3 Flash |
| Other | Various | Moonshot, Z.AI, MiniMax, DeepSeek, xAI |

**Steps:**
1. Type the number for your preferred provider (e.g., `1` for OpenAI)
2. Choose a model from the list
3. Enter your API key when prompted

**Don't have an API key yet?**
- Visit the provider's website to create an account and get a key
- Most providers offer free credits to start
- You can come back and re-run the setup wizard later

### Step 5: Set Up Telegram (Optional)

If you want to chat with KūkiClaw on Telegram:

1. Say `y` when asked "Set up Telegram?"
2. Create a Telegram bot:
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` to BotFather
   - Follow the prompts to name your bot
   - Copy the bot token (looks like `123456:ABC-DEF...`)
3. Paste the bot token when the wizard asks for it
4. Choose a DM policy:
   - `pairing` (recommended) - You approve each user manually
   - `allowlist` - Only specific users can chat
   - `open` - Anyone can chat (not recommended)

If you skip this step, you can still use KūkiClaw from the terminal.

### Step 6: Start KūkiClaw

After setup completes, the wizard will ask:

```
🚀 Would you like to start KūkiClaw now? (y/n) [y]:
```

Type `y` and press Enter to start immediately, or `n` to start later.

**To start later:**
```bash
cd ~
source ~/.bashrc
openclaw gateway start
```

---

## What Happens Next?

Once KūkiClaw is running, you can:

### In Your Terminal
The terminal will show a prompt where you can type questions directly.

### On Telegram (if configured)
1. Open Telegram and find your bot
2. Send a message to start chatting
3. If using `pairing` policy, you'll need to approve the connection first:
   ```bash
   openclaw pairing list telegram
   openclaw pairing approve telegram <CODE>
   ```

### Example Questions to Try
- "What devices do I have?"
- "Show me the latest sensor readings"
- "What's the air quality like?"
- "List any active alerts"

---

## Troubleshooting

### "command not found" Error
If you see `openclaw: command not found`:
```bash
source ~/.bashrc
```
Or use the full path:
```bash
~/.npm-global/bin/openclaw gateway start
```

### Missing API Key Error
If you see `missing env var "XXX_API_KEY"`:
1. Check that you entered the API key correctly during setup
2. Re-run the setup wizard to update your configuration:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/install.sh | bash
   ```

### Token Expired Error
If you see `INVALID_TOKEN` or authentication errors:
- Your KūkiOS token has expired
- Re-run the setup wizard to get a fresh token

### MCP Connection Failed
If the MCP test fails during setup:
- Check that your KūkiOS server URL is correct
- Verify your internet connection
- Contact your KūkiOS administrator

---

## Configuration Files

Your KūkiClaw configuration is stored in:
```
~/.openclaw/openclaw.json
```

This file contains:
- Your KūkiOS server and token
- Your AI provider settings
- Telegram configuration (if set up)
- Personality and display settings

⚠️ **Keep this file secure** - it contains sensitive information.

---

## Updating KūkiClaw

To update to the latest version:
```bash
cd ~
npm update -g openclaw
```

---

## Uninstalling

To remove KūkiClaw:
```bash
npm uninstall -g openclaw
rm -rf ~/.openclaw
```

---

## Getting Help

- **Documentation:** https://github.com/what-if-labs/KukiClaw
- **Support:** Contact your system administrator or What If Labs

---

## Quick Reference Card

**Start KūkiClaw:**
```bash
openclaw gateway start
```

**Check Status:**
```bash
openclaw logs
```

**List Pairings (Telegram):**
```bash
openclaw pairing list telegram
```

**Re-run Setup:**
```bash
curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/install.sh | bash
```

---

*Last updated: May 2026*
