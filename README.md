# KukiClaw

**OpenClaw + Kukisense IAQ MCP - Messaging-only IoT monitoring**

A pre-configured OpenClaw installation with the Kukisense IAQ Reporter MCP server for natural language IoT device monitoring and control.

---

## What You'll Get

After this installation, you'll have:
- ✅ OpenClaw AI assistant running locally
- ✅ Kukisense IAQ MCP server prebuilt and ready
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
# Install OpenClaw globally
npm install -g openclaw

# Verify installation
openclaw --version
```

### 3. Setup Kukisense MCP Server

```bash
cd kukisense-mcp

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure OpenClaw

Create or update your OpenClaw configuration:

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
        "command": "/absolute/path/to/kukiclaw/kukisense-mcp/venv/bin/python3",
        "args": ["/absolute/path/to/kukiclaw/kukisense-mcp/server.py"],
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

### 5. Start OpenClaw

```bash
# Start OpenClaw with the Kukisense MCP
openclaw start

# Or run in interactive mode
openclaw chat
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IAQ_REPORTER_URL` | Yes | - | IAQ Reporter API URL |
| `IAQ_TOKEN` | No | - | Pre-authenticated JWT token |
| `CACHE_TTL` | No | 300 | Cache duration (seconds) |
| `POOL_CONNECTIONS` | No | 10 | Connection pool size |
| `POOL_MAXSIZE` | No | 20 | Max pool size |
| `MAX_RETRIES` | No | 3 | Retry attempts |
| `REQUEST_TIMEOUT` | No | 30 | Request timeout (seconds) |

### Getting a JWT Token

**Option 1: Login via MCP (recommended)**
```bash
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" \
  password="your-password"
```

**Option 2: Manual API call**
```bash
curl -X POST https://dashbeta.what-if.sg/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email","password":"your-password"}'
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

### Connection Issues

```bash
# Test IAQ Reporter connection
curl https://dashbeta.what-if.sg/health

# Check MCP server logs
openclaw logs
```

### MCP Server Not Starting

```bash
# Verify MCP server is installed
cd kukisense-mcp
source venv/bin/activate
python3 server.py
```

### Authentication Failed

- Verify your IAQ Reporter credentials
- Check if your account has tenant access
- Ensure IAQ Reporter server is running

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

# Remove MCP server
rm -rf kukisense-mcp

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
