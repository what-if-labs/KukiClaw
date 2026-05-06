# KūkiOS MCP - Detailed Usage Guide

## Table of Contents
- [Setup](#setup)
- [Authentication](#authentication)
- [Daily Monitoring](#daily-monitoring)
- [Alert Management](#alert-management)
- [Batch Operations](#batch-operations)
- [Troubleshooting](#troubleshooting)

## Setup

### Install
```bash
git clone https://github.com/what-if21/kukios-mcp.git
cd kukios-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment
```bash
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"
# Optional performance tuning:
export CACHE_TTL=300
export POOL_CONNECTIONS=10
```

## Authentication

### Login
```bash
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" \
  password="your-password"
```

Returns:
```json
{
  "success": true,
  "user": { "id", "email", "firstName", "lastName", "role" },
  "tokens": { "accessToken", "refreshToken", "expiresIn": 900 }
}
```

**Note:** Token expires in 15 minutes. Re-run auth_login when needed.

### Get Current User
```bash
mcporter call --stdio "python3 server.py" get_current_user
```

## Daily Monitoring

### Check All Sensors (Quick)
```bash
# 1. Login
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" password="your-password"

# 2. Get devices
DEVICES=$(mcporter call --stdio "python3 server.py" list_devices --output json)

# 3. Check each device
echo $DEVICES | jq -r '.[].id' | while read id; do
  echo "Device: $id"
  mcporter call --stdio "python3 server.py" get_latest_readings device_id="$id"
done
```

### Office Environment Check
```bash
# Get readings for specific device
mcporter call --stdio "python3 server.py" get_latest_readings \
  device_id="84a1fa53-2780-4448-adbd-bfe7ea348061"
```

Expected office ranges:
- Temperature: 23-26°C
- Humidity: 40-60%
- CO2: <600 ppm (good), <800 ppm (acceptable)
- PM2.5: <15 µg/m³
- TVOC: <500 µg/m³

### Real-Time Status
```bash
mcporter call --stdio "python3 server.py" get_realtime_status
```

## Alert Management

### List Active Alerts
```bash
mcporter call --stdio "python3 server.py" list_alerts status="active"
```

### Acknowledge Alert
```bash
mcporter call --stdio "python3 server.py" acknowledge_alert \
  alert_id="alert-uuid" \
  notes="Checking with facilities team"
```

### Resolve Alert
```bash
mcporter call --stdio "python3 server.py" resolve_alert \
  alert_id="alert-uuid" \
  notes="Ventilation increased, CO2 normalized"
```

## Batch Operations

### Get All Device Readings at Once
```bash
mcporter call --stdio "python3 server.py" batch_get_latest_readings \
  device_ids='["84a1fa53-...", "8819b16e-...", "c5f96497-..."]'
```

### Get Multiple Device Details
```bash
mcporter call --stdio "python3 server.py" batch_get_devices \
  device_ids='["84a1fa53-...", "8819b16e-..."]'
```

## Compliance Reporting

### List Standards
```bash
mcporter call --stdio "python3 server.py" list_standards
```

### Calculate Compliance
```bash
mcporter call --stdio "python3 server.py" calculate_compliance \
  device_id="84a1fa53-2780-4448-adbd-bfe7ea348061" \
  standard_id="standard-uuid" \
  start_date="2026-05-01" \
  end_date="2026-05-05"
```

## Troubleshooting

### Check Cache Stats
```bash
mcporter call --stdio "python3 server.py" cache_stats
```

### Clear Cache
```bash
mcporter call --stdio "python3 server.py" cache_clear
```

### Token Expired?
```bash
# Re-login
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" password="your-password"
```

### Connection Issues?
```bash
# Test basic connectivity
mcporter call --stdio "python3 server.py" get_realtime_status

# Check if API is reachable
curl https://dashbeta.what-if.sg/health
```

## Tips

1. **Use config mode for convenience:**
   ```bash
   mcporter config add kukios --command "python3 server.py"
   mcporter call kukios list_devices
   ```

2. **Batch operations are faster:**
   - `batch_get_devices` vs multiple `get_device` calls
   - `batch_get_latest_readings` vs multiple `get_latest_readings`

3. **Cache helps performance:**
   - Buildings cached 5 min
   - Devices cached 1 min
   - Readings cached 30 sec

4. **For scripts, use JSON output:**
   ```bash
   mcporter call kukios list_devices --output json | jq '.[0].name'
   ```
