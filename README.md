# KukiClaw

**OpenClaw + Kukisense IAQ Companion Agent - Messaging-only IoT monitoring**

A pre-configured OpenClaw installation that connects to the remote Kukisense IAQ MCP server. On first install, the bot asks for your credentials and starts operating as your IAQ companion agent.

---

## What You'll Get

After setup, you'll have:
- ✅ OpenClaw AI assistant running locally
- ✅ MCP client configured to connect to remote Kukisense IAQ MCP server
- ✅ Natural language queries for your IoT devices
- ✅ Real-time sensor data, historical analysis, and device control
- ✅ Messaging integration (Telegram, Discord, etc.)

**Example queries:**
- *"What's the CO2 level in the meeting room?"*
- *"Show me all sensors with poor air quality"*
- *"Which devices are offline?"*

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/what-if21/kukiclaw.git
cd kukiclaw
```

### 2. Install OpenClaw

```bash
npm install -g openclaw
```

### 3. Run Setup Wizard

```bash
cd setup
python3 setup_wizard.py
```

The wizard will:
1. Ask for your IAQ Reporter URL
2. Ask for your email and password
3. Test the connection
4. Ask for the Kukisense MCP Server URL
5. Configure OpenClaw with MCP client
6. Start your IAQ companion agent

### 4. Start KukiClaw

```bash
openclaw start
```

---

## How It Works

```
User → OpenClaw (MCP Client) → Remote Kukisense IAQ MCP Server → IAQ Reporter Platform
```

### First Install Flow

1. **Clone & Install** - Get KukiClaw and OpenClaw
2. **Run Wizard** - Answer a few questions about your IAQ Reporter
3. **Auto-Configure** - MCP client is fixed to your instance
4. **Start Chatting** - Your IAQ companion agent is ready!

### Credential Storage

- Credentials are stored in `~/.openclaw/openclaw.json`
- File permissions are set to `600` (owner only)
- JWT tokens are auto-refreshed by the MCP server

---

## Configuration

### Environment Variables (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IAQ_REPORTER_URL` | Yes | - | IAQ Reporter API URL |
| `IAQ_TOKEN` | No | - | Pre-authenticated JWT token |
| `CACHE_TTL` | No | 300 | Cache duration (seconds) |
| `POOL_CONNECTIONS` | No | 10 | Connection pool size |
| `POOL_MAXSIZE` | No | 20 | Max pool size |
| `MAX_RETRIES` | No | 3 | Retry attempts |
| `REQUEST_TIMEOUT` | No | 30 | Request timeout (seconds) |

### Manual Configuration

If you prefer to configure manually:

```bash
mkdir -p ~/.openclaw

cat > ~/.openclaw/openclaw.json << 'EOF'
{
  "meta": {
    "lastTouchedVersion": "2026.4.22"
  },
  "mcp": {
    "servers": {
      "kukisense-iaq": {
        "command": "python3",
        "args": ["https://kukisense-mcp.what-if.sg"],
        "env": {
          "IAQ_REPORTER_URL": "https://dashbeta.what-if.sg",
          "IAQ_TOKEN": "your-jwt-token-here",
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
EOF

chmod 600 ~/.openclaw/openclaw.json
```

---

## Available MCP Tools

### Device Management

| Tool | Description |
|------|-------------|
| `list_devices` | List all devices |
| `get_device` | Get device details |
| `batch_get_devices` | Get multiple devices at once |

### Telemetry & Data

| Tool | Description |
|------|-------------|
| `get_latest_readings` | Get latest sensor data |
| `get_historical_readings` | Get historical data |
| `batch_get_latest_readings` | Get readings for multiple devices |

### Alerts & Monitoring

| Tool | Description |
|------|-------------|
| `list_alerts` | List IAQ alerts |
| `acknowledge_alert` | Acknowledge alert |
| `resolve_alert` | Resolve alert |
| `get_realtime_status` | Get system status |

### Compliance

| Tool | Description |
|------|-------------|
| `list_standards` | List compliance standards |
| `calculate_compliance` | Calculate compliance grade |

### Reports

| Tool | Description |
|------|-------------|
| `list_reports` | List reports |
| `generate_report_pdf` | Generate PDF report |

### Cache Management

| Tool | Description |
|------|-------------|
| `cache_stats` | Get cache statistics |
| `cache_clear` | Clear caches |

---

## Example Queries

### Device Queries
```
"List all my IoT devices"
"Get details for device 'Sensor-01'"
"Which devices are offline?"
```

### Telemetry Queries
```
"Show me the temperature and humidity from Sensor-01"
"What's the CO2 level in the meeting room?"
"Get PM2.5 readings for all devices"
```

### Historical Data
```
"Get CO2 history for Sensor-01 for the past 24 hours"
"Show me temperature trends for the last 7 days"
```

### Alerts & Monitoring
```
"List active alerts"
"Acknowledge alert 'alert-uuid'"
"Get real-time system status"
```

---

## Troubleshooting

### Setup Wizard Fails

```bash
# Test connection manually
curl -X POST https://dashbeta.what-if.sg/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email","password":"your-password"}'
```

### MCP Client Not Starting

```bash
# Check MCP server is accessible
curl https://kukisense-mcp.what-if.sg/health

# Check OpenClaw logs
openclaw logs
```

### Connection Issues

```bash
# Test IAQ Reporter connection
curl https://dashbeta.what-if.sg/health

# Check OpenClaw logs
openclaw logs
```

---

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Set file permissions** on config files (`chmod 600`)
4. **Use HTTPS** in production environments
5. **Rotate passwords** regularly

---

## Uninstallation

```bash
# Remove OpenClaw
npm uninstall -g openclaw

# Remove KukiClaw
rm -rf /path/to/kukiclaw

# Remove configuration
rm -rf ~/.openclaw
```

---

## Support

- **Documentation:** [OpenClaw Docs](https://docs.openclaw.ai)
- **Community:** [Discord](https://discord.com/invite/clawd)
- **GitHub:** [what-if21/kukiclaw](https://github.com/what-if21/kukiclaw)

---

## License

Private - What If Labs
