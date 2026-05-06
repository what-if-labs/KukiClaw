# Setup Guide - Multiple Ways to Use KūkiOS MCP

This guide covers all the ways to connect to and use the KūkiOS MCP server.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Method 1: mcporter (CLI)](#method-1-mcporter-cli)
- [Method 2: Claude Desktop](#method-2-claude-desktop)
- [Method 3: Cursor IDE](#method-3-cursor-ide)
- [Method 4: Direct Python Import](#method-4-direct-python-import)
- [Method 5: HTTP Mode](#method-5-http-mode)
- [Method 6: Custom Script](#method-6-custom-script)
- [Environment Variables](#environment-variables)

---

## Prerequisites

```bash
# Clone repo
git clone https://github.com/what-if21/kukios-mcp.git
cd kukios-mcp

# Setup Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Method 1: mcporter (CLI)

**Best for:** Command-line usage, scripting

### Install mcporter
```bash
npm install -g mcporter
```

### Option A: Direct stdio (no config)
```bash
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"

mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" password="your-password"

mcporter call --stdio "python3 server.py" list_devices
```

### Option B: Add to mcporter config (recommended)
```bash
# Add once
mcporter config add kukios \
  --command "python3 /path/to/kukios-mcp/server.py"

# Use anytime
mcporter call kukios list_devices
mcporter call kukios get_latest_readings device_id="..."
```

### Option C: JSON output for scripting
```bash
mcporter call kukios list_devices --output json | jq '.[].name'
```

---

## Method 2: Claude Desktop

**Best for:** AI assistant integration

### macOS
```bash
# Edit config
cat > ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "kukios": {
      "command": "/path/to/kukios-mcp/venv/bin/python3",
      "args": ["/path/to/kukios-mcp/server.py"],
      "env": {
        "IAQ_REPORTER_URL": "https://dashbeta.what-if.sg"
      }
    }
  }
}
EOF
```

### Windows
```powershell
# Edit config at:
# %APPDATA%\Claude\claude_desktop_config.json

{
  "mcpServers": {
    "kukios": {
      "command": "C:\\path\\to\\kukios-mcp\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\kukios-mcp\\server.py"],
      "env": {
        "IAQ_REPORTER_URL": "https://dashbeta.what-if.sg"
      }
    }
  }
}
```

### Linux
```bash
# Edit config at:
# ~/.config/Claude/claude_desktop_config.json

{
  "mcpServers": {
    "kukios": {
      "command": "/path/to/kukios-mcp/venv/bin/python3",
      "args": ["/path/to/kukios-mcp/server.py"],
      "env": {
        "IAQ_REPORTER_URL": "https://dashbeta.what-if.sg"
      }
    }
  }
}
```

### Using in Claude
After setup, restart Claude Desktop. You can ask:
- "Show me all IAQ devices"
- "Get the latest readings from sensor X"
- "List any active alerts"

---

## Method 3: Cursor IDE

**Best for:** Development environment

### Setup
1. Open Cursor IDE
2. Go to Settings → AI → MCP Servers
3. Add new server:
   ```json
   {
     "mcpServers": {
       "kukios": {
         "command": "python3",
         "args": ["/path/to/kukios-mcp/server.py"],
         "env": {
           "IAQ_REPORTER_URL": "https://dashbeta.what-if.sg"
         }
       }
     }
   }
   ```

### Using in Cursor
Ask the AI assistant:
- "What devices are connected?"
- "Check the air quality readings"
- "Are there any alerts?"

---

## Method 4: Direct Python Import

**Best for:** Custom scripts, automation

### Basic Usage
```python
import sys
sys.path.insert(0, '/path/to/kukios-mcp')

from server import (
    auth_login,
    list_devices,
    get_latest_readings,
    get_current_user
)
import os

# Set environment
os.environ['IAQ_REPORTER_URL'] = 'https://dashbeta.what-if.sg'

# Login
result = auth_login('your-email', 'your-password')
token = result['tokens']['accessToken']

# Use token for subsequent calls
os.environ['IAQ_TOKEN'] = token

# Get devices
devices = list_devices()
print(f"Found {len(devices.get('data', []))} devices")

# Get readings for first device
if devices.get('data'):
    device_id = devices['data'][0]['id']
    readings = get_latest_readings(device_id)
    print(f"Latest: {readings}")
```

### Async Usage
```python
import asyncio
from server import client

async def monitor_devices():
    # Login
    login_result = client.post("/api/auth/login", {
        "email": "your-email",
        "password": "your-password"
    })
    client.token = login_result['tokens']['accessToken']
    
    # Get all devices
    devices = client.get("/api/devices")
    
    # Fetch readings for all
    for device in devices.get('data', []):
        readings = client.get(f"/api/readings/{device['id']}")
        print(f"{device['name']}: {readings}")

asyncio.run(monitor_devices())
```

---

## Method 5: HTTP Mode

**Best for:** Web applications, REST API consumers

### Start HTTP Server
```bash
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"
python3 server.py --transport http --port 8080
```

### Use with curl
```bash
# List tools
curl http://localhost:8080/tools/list

# Call tool
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "auth_login",
    "arguments": {
      "email": "your-email",
      "password": "your-password"
    }
  }'
```

### Use with Python requests
```python
import requests

# Call tool via HTTP
response = requests.post('http://localhost:8080/tools/call', json={
    'name': 'list_devices',
    'arguments': {}
})
data = response.json()
print(data)
```

---

## Method 6: Custom Script

**Best for:** Integration with existing systems

### Bash Script
```bash
#!/bin/bash
# iaq-monitor.sh

SERVER_DIR="/path/to/kukios-mcp"
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"

# Function to call MCP tool
call_mcp() {
    local tool=$1
    shift
    mcporter call --stdio "python3 $SERVER_DIR/server.py" "$tool" "$@"
}

# Login
call_mcp auth_login email="your-email" password="your-password"

# Get devices
echo "=== Devices ==="
call_mcp list_devices

# Check alerts
echo "=== Alerts ==="
call_mcp list_alerts status="active"
```

### Node.js Script
```javascript
const { spawn } = require('child_process');

function callMCPTool(tool, args = {}) {
  return new Promise((resolve, reject) => {
    const argsList = Object.entries(args).flatMap(([k, v]) => [`${k}=${v}`]);
    const proc = spawn('mcporter', [
      'call', '--stdio', 'python3 server.py',
      tool, ...argsList
    ], { cwd: '/path/to/kukios-mcp' });
    
    let output = '';
    proc.stdout.on('data', (data) => output += data);
    proc.on('close', () => resolve(JSON.parse(output)));
    proc.on('error', reject);
  });
}

// Usage
async function main() {
  await callMCPTool('auth_login', { 
    email: 'your-email', 
    password: 'your-password' 
  });
  
  const devices = await callMCPTool('list_devices');
  console.log(devices);
}

main();
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IAQ_REPORTER_URL` | Yes | - | KūkiOS API URL |
| `IAQ_TOKEN` | No | - | Pre-authenticated JWT token |
| `CACHE_TTL` | No | 300 | Cache duration (seconds) |
| `POOL_CONNECTIONS` | No | 10 | Connection pool size |
| `POOL_MAXSIZE` | No | 20 | Max pool size |
| `MAX_RETRIES` | No | 3 | Retry attempts |
| `REQUEST_TIMEOUT` | No | 30 | Request timeout (seconds) |

---

## Troubleshooting

### "Module not found"
```bash
# Ensure venv is activated
source venv/bin/activate
pip install -r requirements.txt
```

### "Authentication failed"
```bash
# Check credentials
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" password="your-password"

# Check URL
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"
```

### "Connection refused"
```bash
# Test API reachability
curl https://dashbeta.what-if.sg/health

# Check firewall/proxy
export HTTP_PROXY=""
export HTTPS_PROXY=""
```

### Token expired
```bash
# Re-login (token expires every 15 minutes)
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" password="your-password"
```

---

## Quick Reference

```bash
# 1. Setup
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"
cd kukios-mcp && source venv/bin/activate

# 2. Login
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" password="your-password"

# 3. Use any tool
mcporter call --stdio "python3 server.py" list_devices
mcporter call --stdio "python3 server.py" get_latest_readings \
  device_id="84a1fa53-2780-4448-adbd-bfe7ea348061"
```
