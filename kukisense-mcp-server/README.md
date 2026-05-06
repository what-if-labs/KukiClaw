# KūkiOS MCP Server

MCP (Model Context Protocol) server for KūkiOS Pro Platform integration.

## Features

- **Connection Pooling**: Reuses TCP connections for better performance
- **Multi-Tier Caching**: Different cache TTLs for different data types
- **Batch Operations**: Fetch multiple devices/readings in one call
- **Retry Logic**: Automatic retry with exponential backoff
- **Thread-Safe**: Safe for concurrent access

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export IAQ_TOKEN="your-jwt-token"
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"
```

### Optional Performance Tuning

```bash
export CACHE_TTL=300          # Cache duration (seconds)
export POOL_CONNECTIONS=10    # Connection pool size
export POOL_MAXSIZE=20        # Max pool size
export MAX_RETRIES=3          # Retry attempts
export REQUEST_TIMEOUT=30     # Request timeout (seconds)
```

## Usage

### Quick Start

```bash
# 1. Set environment variables
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"

# 2. Login with your credentials (get JWT token)
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" \
  password="your-password"

# 3. Get all devices
mcporter call --stdio "python3 server.py" list_devices

# 4. Get readings for a device
mcporter call --stdio "python3 server.py" get_latest_readings \
  device_id="your-device-id"
```

### Getting a JWT Token

**Option 1: Login via MCP (recommended)**
```bash
# Login returns token automatically - no manual copy needed
mcporter call --stdio "python3 server.py" auth_login \
  email="your-email" \
  password="your-password"
```

**Option 2: Manual API call**
```bash
curl -X POST https://dashbeta.what-if.sg/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email","password":"your-password"}'

# Copy the accessToken from response
export IAQ_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Option 3: Set in environment**
```bash
# Add to ~/.bashrc or ~/.zshrc
export IAQ_TOKEN="your-jwt-token"
export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"
```

### Multiple Setup Options

See **[SETUP.md](SETUP.md)** for detailed instructions on:
- **mcporter** (CLI)
- **Claude Desktop** (AI assistant)
- **Cursor IDE** (Development)
- **Direct Python Import** (Scripts)
- **HTTP Mode** (Web apps)
- **Custom Scripts** (Automation)

### Common Operations

```bash
# Authentication
mcporter call kukios auth_login email="your-email" password="your-password"
mcporter call kukios get_current_user

# Buildings & Devices
mcporter call kukios list_buildings
mcporter call kukios list_devices
mcporter call kukios get_device device_id="uuid"

# Sensor Readings
mcporter call kukios get_latest_readings device_id="uuid"
mcporter call kukios get_historical_readings \
  device_id="uuid" start_date="2026-05-01" end_date="2026-05-05"

# Batch Operations (faster for multiple devices)
mcporter call kukios batch_get_latest_readings \
  device_ids='["id1", "id2", "id3"]'

# Alerts & Monitoring
mcporter call kukios list_alerts status="active"
mcporter call kukios get_realtime_status
mcporter call kukios acknowledge_alert alert_id="uuid"

# Compliance
mcporter call kukios list_standards
mcporter call kukios calculate_compliance \
  device_id="uuid" standard_id="uuid" start_date="2026-05-01" end_date="2026-05-05"

# Cache Management
mcporter call kukios cache_stats
mcporter call kukios cache_clear
```

## Available Tools

| Tool | Description |
|------|-------------|
| `auth_login` | Authenticate and get token |
| `get_current_user` | Get user profile (cached) |
| `list_buildings` | List buildings (cached) |
| `get_building` | Get building details (cached) |
| `list_devices` | List devices (cached) |
| `get_device` | Get device details (cached) |
| `batch_get_devices` | Get multiple devices at once |
| `get_latest_readings` | Get latest sensor data (cached) |
| `get_historical_readings` | Get historical data (cached) |
| `batch_get_latest_readings` | Get readings for multiple devices |
| `list_alerts` | List IAQ alerts (real-time) |
| `acknowledge_alert` | Acknowledge alert |
| `resolve_alert` | Resolve alert |
| `list_standards` | List compliance standards (cached) |
| `calculate_compliance` | Calculate compliance grade |
| `list_reports` | List reports |
| `generate_report_pdf` | Generate PDF report |
| `get_realtime_status` | Get system status (real-time) |
| `get_sensor_history` | Get device status history |
| `cache_stats` | Get cache statistics |
| `cache_clear` | Clear caches |

## Cache Configuration

| Cache | TTL | Use Case |
|-------|-----|----------|
| Buildings | 5 min | Building structure |
| Standards | 30 min | Compliance standards |
| Devices | 1 min | Device list |
| Readings | 30 sec | Sensor data |
| User | 5 min | User profile |

## Performance

- **Cached reads**: 10-50x faster than direct API calls
- **Connection reuse**: ~80% latency reduction
- **Batch operations**: N API calls → 1 call
- **Overall throughput**: 5-10x improvement

## Testing

```bash
# Test basic connectivity
mcporter call --stdio "python3 server.py" \
  kukios-optimized.get_realtime_status

# Test cache performance
mcporter call --stdio "python3 server.py" \
  kukios-optimized.cache_stats
```

## License

Private - What If Labs
