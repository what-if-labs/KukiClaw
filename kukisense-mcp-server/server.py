#!/usr/bin/env python3
"""
KūkiOS Pro MCP Server - Optimized for High Concurrency
Features: Connection pooling, caching, batch ops, retry logic

Usage:
  export IAQ_TOKEN="your-jwt-token"
  export IAQ_REPORTER_URL="https://dashbeta.what-if.sg"
  python3 server.py
"""
from mcp.server.fastmcp import FastMCP
import requests
import os
import time
import threading
from typing import Optional, List, Dict, Any
from functools import wraps
from collections import OrderedDict

mcp = FastMCP("kukios")
BASE_URL = os.getenv("IAQ_REPORTER_URL", "https://dashbeta.what-if.sg")

# ============================================================================
# CONFIGURATION
# ============================================================================

CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "100"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))
POOL_CONNECTIONS = int(os.getenv("POOL_CONNECTIONS", "10"))
POOL_MAXSIZE = int(os.getenv("POOL_MAXSIZE", "20"))

# ============================================================================
# THREAD-SAFE CACHE WITH TTL
# ============================================================================

class TTLCache:
    """Thread-safe LRU cache with TTL expiration"""
    
    def __init__(self, maxsize: int = 100, ttl: int = 300):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = threading.RLock()
    
    def _is_expired(self, key: str) -> bool:
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > self.ttl
    
    def get(self, key: str) -> Any:
        with self._lock:
            if key in self._cache and not self._is_expired(key):
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                return self._cache[key]
            # Expired or missing - clean up
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            return None
    
    def set(self, key: str, value: Any):
        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self.maxsize:
                oldest = next(iter(self._cache))
                self._cache.pop(oldest)
                self._timestamps.pop(oldest, None)
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._cache.move_to_end(key)
    
    def invalidate(self, pattern: str = None):
        with self._lock:
            if pattern:
                keys_to_remove = [k for k in self._cache if pattern in k]
                for k in keys_to_remove:
                    self._cache.pop(k, None)
                    self._timestamps.pop(k, None)
            else:
                self._cache.clear()
                self._timestamps.clear()
    
    def stats(self) -> dict:
        with self._lock:
            expired = sum(1 for k in self._timestamps if self._is_expired(k))
            return {
                "size": len(self._cache),
                "max_size": self.maxsize,
                "ttl": self.ttl,
                "expired_entries": expired
            }

# Initialize caches
cache_buildings = TTLCache(maxsize=50, ttl=CACHE_TTL)
cache_standards = TTLCache(maxsize=20, ttl=CACHE_TTL * 6)  # 30 min - rarely change
cache_devices = TTLCache(maxsize=200, ttl=60)  # 1 min - change more often
cache_readings = TTLCache(maxsize=500, ttl=30)  # 30 sec - very dynamic
cache_user = TTLCache(maxsize=10, ttl=300)

# ============================================================================
# CONNECTION POOL + RETRY LOGIC
# ============================================================================

class APIClient:
    """Thread-safe API client with connection pooling and retry logic"""
    
    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=POOL_CONNECTIONS,
            pool_maxsize=POOL_MAXSIZE,
            max_retries=requests.adapters.Retry(
                total=MAX_RETRIES,
                backoff_factor=RETRY_DELAY,
                status_forcelist=[429, 500, 502, 503, 504]
            )
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self._token = os.getenv("IAQ_TOKEN", "")
        self._token_lock = threading.Lock()
        self._request_count = 0
        self._request_lock = threading.Lock()
    
    @property
    def token(self) -> str:
        with self._token_lock:
            return self._token
    
    @token.setter
    def token(self, value: str):
        with self._token_lock:
            self._token = value
    
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get(self, path: str, params: dict = None, use_cache: bool = False, cache_key: str = None, cache_store: TTLCache = None) -> dict:
        """GET with optional caching"""
        # Check cache first
        if use_cache and cache_store and cache_key:
            cached = cache_store.get(cache_key)
            if cached is not None:
                return cached
        
        url = f"{BASE_URL}{path}"
        
        with self._request_lock:
            self._request_count += 1
        
        resp = self.session.get(
            url,
            headers=self.headers(),
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Store in cache
        if use_cache and cache_store and cache_key:
            cache_store.set(cache_key, data)
        
        return data
    
    def post(self, path: str, json_data: dict = None) -> dict:
        """POST with retry logic"""
        url = f"{BASE_URL}{path}"
        
        with self._request_lock:
            self._request_count += 1
        
        resp = self.session.post(
            url,
            headers=self.headers(),
            json=json_data,
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    
    def put(self, path: str, json_data: dict = None) -> dict:
        """PUT with retry logic"""
        url = f"{BASE_URL}{path}"
        
        with self._request_lock:
            self._request_count += 1
        
        resp = self.session.put(
            url,
            headers=self.headers(),
            json=json_data,
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    
    def delete(self, path: str) -> dict:
        """DELETE with retry logic"""
        url = f"{BASE_URL}{path}"
        
        with self._request_lock:
            self._request_count += 1
        
        resp = self.session.delete(
            url,
            headers=self.headers(),
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return {"success": True}
    
    def get_stats(self) -> dict:
        with self._request_lock:
            return {"total_requests": self._request_count}

# Global client instance
client = APIClient()

# ============================================================================
# CACHE MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def cache_stats() -> dict:
    """
    Get cache statistics for performance monitoring
    
    Returns:
        Cache hit rates and sizes for all cache tiers
    """
    return {
        "buildings": cache_buildings.stats(),
        "standards": cache_standards.stats(),
        "devices": cache_devices.stats(),
        "readings": cache_readings.stats(),
        "user": cache_user.stats(),
        "api_requests": client.get_stats()
    }

@mcp.tool()
def cache_clear(pattern: str = None) -> dict:
    """
    Clear caches (useful after data updates)
    
    Args:
        pattern: Optional pattern to match cache keys (e.g., "building")
        
    Returns:
        Status of cache clear operation
    """
    cache_buildings.invalidate(pattern)
    cache_standards.invalidate(pattern)
    cache_devices.invalidate(pattern)
    cache_readings.invalidate(pattern)
    cache_user.invalidate(pattern)
    return {"success": True, "cleared_pattern": pattern}

# ============================================================================
# AUTHENTICATION
# ============================================================================

@mcp.tool()
def auth_login(email: str, password: str) -> dict:
    """
    Authenticate and cache token for subsequent requests
    
    Args:
        email: User email
        password: User password
        
    Returns:
        {"token": "...", "refreshToken": "...", "user": {...}}
    """
    data = client.post("/api/auth/login", {"email": email, "password": password})
    if data.get("success") and data.get("tokens"):
        client.token = data["tokens"]["accessToken"]
        # Cache user info
        if "user" in data:
            cache_user.set("current_user", data["user"])
    return data

@mcp.tool()
def auth_refresh(refresh_token: str) -> dict:
    """
    Refresh JWT token using refresh token
    
    Args:
        refresh_token: Refresh token from login
        
    Returns:
        {"success": true, "tokens": {"accessToken": "...", "refreshToken": "...", "expiresIn": 900}}
    """
    data = client.post("/api/auth/refresh", {"refreshToken": refresh_token})
    if data.get("success") and data.get("tokens"):
        client.token = data["tokens"]["accessToken"]
        cache_user.invalidate()  # Clear user cache on refresh
    return data

@mcp.tool()
def get_current_user(use_cache: bool = True) -> dict:
    """
    Get current user from /api/auth/me endpoint
    
    Args:
        use_cache: Use cached data if available (default true)
        
    Returns:
        User object with id, email, firstName, lastName, role
    """
    if use_cache:
        cached = cache_user.get("current_user")
        if cached:
            return cached
    
    data = client.get("/api/auth/me")
    cache_user.set("current_user", data)
    return data

# ============================================================================
# BUILDINGS (CACHED)
# ============================================================================

@mcp.tool()
def list_buildings(page: int = 0, page_size: int = 100, use_cache: bool = True) -> dict:
    """
    List buildings with caching
    
    Args:
        page: Page number
        page_size: Items per page
        use_cache: Use cache if available (default true)
        
    Returns:
        Buildings list
    """
    cache_key = f"buildings_{page}_{page_size}"
    return client.get(
        "/api/buildings",
        params={"page": page, "page_size": page_size},
        use_cache=use_cache,
        cache_key=cache_key,
        cache_store=cache_buildings
    )

@mcp.tool()
def get_building(building_id: str, use_cache: bool = True) -> dict:
    """
    Get building details (cached)
    
    Args:
        building_id: Building UUID
        use_cache: Use cache if available
        
    Returns:
        Building object with levels
    """
    cache_key = f"building_{building_id}"
    return client.get(
        f"/api/buildings/{building_id}",
        use_cache=use_cache,
        cache_key=cache_key,
        cache_store=cache_buildings
    )

# ============================================================================
# DEVICES (CACHED)
# ============================================================================

@mcp.tool()
def list_devices(
    building_id: str = None,
    level_id: str = None,
    zone_id: str = None,
    status: str = None,
    provider: str = None,
    page: int = 0,
    page_size: int = 100,
    use_cache: bool = True
) -> dict:
    """
    List devices with caching
    
    Args:
        building_id: Filter by building
        level_id: Filter by level
        zone_id: Filter by zone
        status: online|offline|error|maintenance
        provider: kukisense|manual
        page: Page number
        page_size: Items per page
        use_cache: Use cache (default true)
        
    Returns:
        Devices list
    """
    params = {"page": page, "page_size": page_size}
    if building_id:
        params["building_id"] = building_id
    if level_id:
        params["level_id"] = level_id
    if zone_id:
        params["zone_id"] = zone_id
    if status:
        params["status"] = status
    if provider:
        params["provider"] = provider
    
    cache_key = f"devices_{hash(str(sorted(params.items())))}"
    return client.get(
        "/api/devices",
        params=params,
        use_cache=use_cache,
        cache_key=cache_key,
        cache_store=cache_devices
    )

@mcp.tool()
def get_device(device_id: str, use_cache: bool = True) -> dict:
    """
    Get device details (cached)
    
    Args:
        device_id: Device UUID
        use_cache: Use cache if available
        
    Returns:
        Device object
    """
    cache_key = f"device_{device_id}"
    return client.get(
        f"/api/devices/{device_id}",
        use_cache=use_cache,
        cache_key=cache_key,
        cache_store=cache_devices
    )

# ============================================================================
# BATCH OPERATIONS (Optimized)
# ============================================================================

@mcp.tool()
def batch_get_devices(device_ids: List[str]) -> dict:
    """
    Get multiple devices in one batch (reduces API calls)
    
    Args:
        device_ids: List of device UUIDs
        
    Returns:
        {"data": [...], "errors": [...]}
    """
    results = []
    errors = []
    
    for device_id in device_ids:
        try:
            device = get_device(device_id, use_cache=True)
            results.append(device)
        except Exception as e:
            errors.append({"device_id": device_id, "error": str(e)})
    
    return {"data": results, "errors": errors, "total": len(results)}

@mcp.tool()
def batch_get_latest_readings(device_ids: List[str]) -> dict:
    """
    Get latest readings for multiple devices (batch operation)
    
    Args:
        device_ids: List of device UUIDs
        
    Returns:
        {"data": [...], "errors": [...]}
    """
    results = []
    errors = []
    
    for device_id in device_ids:
        try:
            cache_key = f"readings_{device_id}"
            cached = cache_readings.get(cache_key)
            
            if cached:
                results.append(cached)
                continue
            
            data = client.get(f"/api/readings/{device_id}")
            cache_readings.set(cache_key, data)
            results.append(data)
        except Exception as e:
            errors.append({"device_id": device_id, "error": str(e)})
    
    return {"data": results, "errors": errors, "total": len(results)}

# ============================================================================
# READINGS (CACHED)
# ============================================================================

@mcp.tool()
def get_latest_readings(device_id: str, use_cache: bool = True) -> dict:
    """
    Get latest sensor readings with short cache
    
    Args:
        device_id: Device UUID
        use_cache: Use cache (default true, 30s TTL)
        
    Returns:
        Latest readings
    """
    cache_key = f"readings_{device_id}"
    cached = cache_readings.get(cache_key)
    if use_cache and cached:
        return cached
    
    data = client.get(f"/api/readings/{device_id}")
    cache_readings.set(cache_key, data)
    return data

@mcp.tool()
def get_historical_readings(
    device_id: str,
    start_date: str,
    end_date: str,
    aggregate: str = None,
    use_cache: bool = True
) -> dict:
    """
    Get historical readings with caching
    
    Args:
        device_id: Device UUID
        start_date: Start date (ISO)
        end_date: End date (ISO)
        aggregate: Aggregation level
        use_cache: Use cache (default true)
        
    Returns:
        Historical data
    """
    params = {"start": start_date, "end": end_date}
    if aggregate:
        params["aggregate"] = aggregate
    
    cache_key = f"hist_{device_id}_{start_date}_{end_date}_{aggregate}"
    cached = cache_readings.get(cache_key)
    if use_cache and cached:
        return cached
    
    data = client.get(
        f"/api/readings/{device_id}/historical",
        params=params
    )
    cache_readings.set(cache_key, data)
    return data

# ============================================================================
# ALERTS
# ============================================================================

@mcp.tool()
def list_alerts(
    status: str = None,
    severity: str = None,
    device_id: str = None,
    building_id: str = None,
    page: int = 0,
    page_size: int = 100
) -> dict:
    """List IAQ alerts (no cache - real-time data)"""
    params = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if severity:
        params["severity"] = severity
    if device_id:
        params["device_id"] = device_id
    if building_id:
        params["building_id"] = building_id
    
    return client.get("/api/operations/alerts", params=params)

@mcp.tool()
def acknowledge_alert(alert_id: str, notes: str = "") -> dict:
    """Acknowledge alert (invalidates alert cache)"""
    data = client.post(
        f"/api/operations/alerts/{alert_id}/acknowledge",
        {"notes": notes} if notes else {}
    )
    # Invalidate alert cache
    cache_readings.invalidate("alerts")
    return data

@mcp.tool()
def resolve_alert(alert_id: str, notes: str = "") -> dict:
    """Resolve alert (invalidates alert cache)"""
    data = client.post(
        f"/api/operations/alerts/{alert_id}/resolve",
        {"notes": notes} if notes else {}
    )
    cache_readings.invalidate("alerts")
    return data

# ============================================================================
# COMPLIANCE (CACHED)
# ============================================================================

@mcp.tool()
def list_standards(use_cache: bool = True) -> dict:
    """
    List compliance standards (cached, rarely change)
    
    Args:
        use_cache: Use cache (default true, 30min TTL)
        
    Returns:
        Standards list
    """
    cache_key = "all_standards"
    return client.get(
        "/api/standards",
        use_cache=use_cache,
        cache_key=cache_key,
        cache_store=cache_standards
    )

@mcp.tool()
def calculate_compliance(
    device_id: str,
    standard_id: str,
    start_date: str,
    end_date: str
) -> dict:
    """Calculate compliance (no cache - expensive computation)"""
    return client.post("/api/compliance/calculate", {
        "device_id": device_id,
        "standard_id": standard_id,
        "start_date": start_date,
        "end_date": end_date
    })

# ============================================================================
# REPORTS
# ============================================================================

@mcp.tool()
def list_reports(
    building_id: str = None,
    report_type: str = None,
    start_date: str = None,
    end_date: str = None,
    page: int = 0,
    page_size: int = 100
) -> dict:
    """List reports"""
    params = {"page": page, "page_size": page_size}
    if building_id:
        params["building_id"] = building_id
    if report_type:
        params["report_type"] = report_type
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    return client.get("/api/reports", params=params)

@mcp.tool()
def generate_report_pdf(report_id: str) -> dict:
    """Generate PDF report"""
    return client.post(f"/api/reports/{report_id}/pdf")

# ============================================================================
# IAQ ANALYSIS & RECOMMENDATIONS
# ============================================================================

# IAQ Standards thresholds
IAQ_THRESHOLDS = {
    "temperature": {"good": (23, 26), "warning": (26, 28), "critical": (28, 35), "unit": "°C"},
    "humidity": {"good": (40, 60), "warning": (30, 70), "critical": (0, 100), "unit": "%"},
    "pm25": {"good": 15, "warning": 35, "critical": 55, "unit": "µg/m³"},
    "pm10": {"good": 45, "warning": 65, "critical": 100, "unit": "µg/m³"},
    "co2": {"good": 600, "warning": 800, "critical": 1000, "unit": "ppm"},
    "tvoc": {"good": 500, "warning": 1000, "critical": 2000, "unit": "µg/m³"},
    "formaldehyde": {"good": 80, "warning": 120, "critical": 200, "unit": "µg/m³"}
}

RECOMMENDATIONS = {
    "temperature": {
        "high": "Lower AC setpoint to 23-24°C. Check AC filter and thermostat calibration.",
        "low": "Increase heating. Check insulation and drafts."
    },
    "humidity": {
        "high": "Use dehumidifier or increase AC cooling. Check for water leaks.",
        "low": "Use humidifier. Check for dry air sources."
    },
    "pm25": {
        "high": "Check/replace HVAC filters. Increase air filtration. Check for indoor sources (cooking, smoking)."
    },
    "pm10": {
        "high": "Check HVAC filters. Reduce dust sources. Increase cleaning frequency."
    },
    "co2": {
        "high": "Increase ventilation. Open windows or increase fresh air intake. Check occupancy levels."
    },
    "tvoc": {
        "high": "Identify VOC source immediately. Check for new furniture, cleaning products, paint, or solvents. Increase ventilation."
    },
    "formaldehyde": {
        "high": "Check for formaldehyde sources (pressed wood, adhesives). Increase ventilation. Consider air purifier with activated carbon."
    }
}

@mcp.tool()
def analyze_iaq_quality(device_id: str) -> dict:
    """
    Analyze IAQ readings and provide actionable recommendations
    
    Args:
        device_id: Device UUID
        
    Returns:
        Analysis with overall grade, issues, and prioritized actions
    """
    # Get device info from list
    devices = list_devices()
    device = None
    for d in devices:
        if d['id'] == device_id:
            device = d
            break
    
    if not device:
        return {"error": f"Device not found: {device_id}"}
    
    # Get latest readings
    readings = get_latest_readings(device_id)
    
    if not readings.get('readings'):
        return {"error": "No readings available"}
    
    latest = readings['readings'][0]
    
    issues = []
    actions = []
    
    # Analyze each parameter
    for param, thresholds in IAQ_THRESHOLDS.items():
        value = latest.get(param)
        if value is None:
            continue
        
        severity = None
        
        if isinstance(thresholds.get("good"), tuple):
            # Range-based (temperature, humidity)
            good_min, good_max = thresholds["good"]
            warn_min, warn_max = thresholds["warning"]
            crit_min, crit_max = thresholds["critical"]
            
            if good_min <= value <= good_max:
                severity = "good"
            elif warn_min <= value <= warn_max or crit_min <= value <= crit_max:
                severity = "warning" if value <= warn_max else "critical"
            else:
                severity = "warning"  # Outside all ranges
        else:
            # Threshold-based (pm25, co2, tvoc, etc.)
            if value <= thresholds["good"]:
                severity = "good"
            elif value <= thresholds["warning"]:
                severity = "warning"
            elif value <= thresholds["critical"]:
                severity = "critical"
            else:
                severity = "critical"
        
        if severity in ["warning", "critical"]:
            unit = thresholds.get("unit", "")
            direction = "high"
            
            issue = {
                "parameter": param,
                "value": value,
                "unit": unit,
                "severity": severity,
                "status": "⚠️" if severity == "warning" else "🔴"
            }
            
            if isinstance(thresholds.get("good"), tuple):
                issue["acceptable_range"] = f"{thresholds['good'][0]}-{thresholds['good'][1]}{unit}"
            else:
                issue["acceptable_limit"] = f"<={thresholds['good']}{unit}"
            
            # Add recommendation
            if param in RECOMMENDATIONS:
                rec = RECOMMENDATIONS[param].get(direction, RECOMMENDATIONS[param].get("high", ""))
                issue["recommendation"] = rec
                actions.append(f"{severity.upper()}: {param} at {value}{unit} - {rec}")
            
            issues.append(issue)
    
    # Calculate overall grade
    if any(i["severity"] == "critical" for i in issues):
        grade = "D"
    elif len(issues) >= 2:
        grade = "C"
    elif len(issues) == 1:
        grade = "B"
    else:
        grade = "A"
    
    return {
        "device": device.get("name", "Unknown"),
        "timestamp": latest.get("time"),
        "overall_grade": grade,
        "issues_count": len(issues),
        "issues": issues,
        "prioritized_actions": actions[:5]  # Top 5 actions
    }

@mcp.tool()
def get_iaq_recommendations(building_id: str = None) -> dict:
    """
    Get prioritized IAQ recommendations for all sensors
    
    Args:
        building_id: Optional building UUID to filter by
        
    Returns:
        Building-wide IAQ analysis with prioritized actions
    """
    # Get devices
    params = {}
    if building_id:
        params["building_id"] = building_id
    
    devices_data = client.get("/api/devices", params=params)
    devices = devices_data if isinstance(devices_data, list) else devices_data.get("data", [])
    
    all_issues = []
    all_actions = []
    device_analyses = []
    
    for device in devices:
        analysis = analyze_iaq_quality(device["id"])
        device_analyses.append(analysis)
        
        for issue in analysis.get("issues", []):
            issue["device"] = device["name"]
            all_issues.append(issue)
        
        all_actions.extend(analysis.get("prioritized_actions", []))
    
    # Sort by severity
    severity_order = {"critical": 0, "warning": 1, "good": 2}
    all_issues.sort(key=lambda x: severity_order.get(x["severity"], 3))
    
    return {
        "devices_analyzed": len(devices),
        "total_issues": len(all_issues),
        "critical_issues": len([i for i in all_issues if i["severity"] == "critical"]),
        "warning_issues": len([i for i in all_issues if i["severity"] == "warning"]),
        "issues": all_issues,
        "prioritized_actions": all_actions[:10]  # Top 10 actions
    }

@mcp.tool()
def compare_to_standards(device_id: str, standard: str = "SS554") -> dict:
    """
    Compare readings against specific IAQ standard
    
    Args:
        device_id: Device UUID
        standard: Standard to compare against (SS554, RESET, WELL, GOAQS, WHO)
        
    Returns:
        Compliance analysis with recommendations
    """
    # Standard thresholds (good/bad limits)
    standards = {
        "SS554": {
            "pm25": 35, "co2": 1000, "tvoc": 1000, "formaldehyde": 120,
            "temperature": (23, 26), "humidity": (40, 70)
        },
        "RESET": {
            "pm25": 15, "co2": 600, "tvoc": 500, "formaldehyde": 80,
            "temperature": (20, 26), "humidity": (30, 60)
        },
        "WELL": {
            "pm25": 15, "co2": 400, "tvoc": 500, "formaldehyde": 80,
            "temperature": (20, 26), "humidity": (30, 60)
        },
        "GOAQS": {
            "pm25": 15, "co2": 600, "tvoc": 500, "formaldehyde": 80,
            "temperature": (20, 26), "humidity": (30, 60)
        },
        "WHO": {
            "pm25": 15, "co2": 1000, "tvoc": 500, "formaldehyde": 100,
            "temperature": (18, 24), "humidity": (40, 60)
        }
    }
    
    if standard not in standards:
        return {"error": f"Unknown standard: {standard}. Use: {', '.join(standards.keys())}"}
    
    std_thresholds = standards[standard]
    readings = get_latest_readings(device_id)
    
    if not readings.get('readings'):
        return {"error": "No readings available"}
    
    latest = readings['readings'][0]
    compliance = []
    
    for param, limit in std_thresholds.items():
        value = latest.get(param)
        if value is None:
            continue
        
        if isinstance(limit, tuple):
            compliant = limit[0] <= value <= limit[1]
            limit_str = f"{limit[0]}-{limit[1]}"
        else:
            compliant = value <= limit
            limit_str = f"<={limit}"
        
        unit = IAQ_THRESHOLDS.get(param, {}).get("unit", "")
        compliance.append({
            "parameter": param,
            "value": value,
            "unit": unit,
            "standard_limit": limit_str,
            "compliant": compliant,
            "status": "✅" if compliant else "❌"
        })
    
    compliant_count = len([c for c in compliance if c["compliant"]])
    total_count = len(compliance)
    
    return {
        "device": device.get("name", "Unknown") if device else "Unknown",
        "standard": standard,
        "compliance_rate": f"{compliant_count}/{total_count}",
        "compliant": compliant_count == total_count,
        "details": compliance
    }

# ============================================================================
# LEAD GENERATION & RECOMMENDATIONS WITH CTA
# ============================================================================

# What If Labs contact info
COMPANY_INFO = {
    "name": "What If Labs",
    "tagline": "Engineering the Internet of Everything",
    "website": "https://what-if.sg",
    "contact_page": "https://what-if.sg/contact",
    "email": "hello@what-if.sg",
    "services": [
        "IAQ Sensor Installation & Monitoring",
        "Indoor Air Quality Assessment",
        "HVAC Optimization Consulting",
        "Compliance Reporting (SS554, RESET, WELL)",
        "Custom IoT Solutions",
        "Smart Building Integration"
    ],
    "value_proposition": "Professional IAQ monitoring and optimization for offices, commercial spaces, and industrial facilities in Singapore and Southeast Asia."
}

@mcp.tool()
def get_iaq_recommendations_with_cta(device_id: str) -> dict:
    """
    Analyze IAQ readings and provide recommendations with contact CTA
    
    This tool generates professional IAQ recommendations that include
    a call-to-action to contact What If Labs for further assistance.
    
    Args:
        device_id: Device UUID
        
    Returns:
        Analysis with recommendations and lead generation CTA
    """
    # Get device info from list
    devices = list_devices()
    device = None
    for d in devices:
        if d['id'] == device_id:
            device = d
            break
    
    if not device:
        return {"error": f"Device not found: {device_id}"}
    
    # Get latest readings
    readings = get_latest_readings(device_id)
    
    if not readings.get('readings'):
        return {"error": "No readings available"}
    
    latest = readings['readings'][0]
    
    issues = []
    actions = []
    severity_counts = {"critical": 0, "warning": 0, "good": 0}
    
    # Analyze each parameter
    for param, thresholds in IAQ_THRESHOLDS.items():
        value = latest.get(param)
        if value is None:
            continue
        
        severity = None
        
        if isinstance(thresholds.get("good"), tuple):
            good_min, good_max = thresholds["good"]
            warn_min, warn_max = thresholds["warning"]
            crit_min, crit_max = thresholds["critical"]
            
            if good_min <= value <= good_max:
                severity = "good"
            elif warn_min <= value <= warn_max or crit_min <= value <= crit_max:
                severity = "warning" if value <= warn_max else "critical"
            else:
                severity = "warning"
        else:
            if value <= thresholds["good"]:
                severity = "good"
            elif value <= thresholds["warning"]:
                severity = "warning"
            elif value <= thresholds["critical"]:
                severity = "critical"
            else:
                severity = "critical"
        
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity in ["warning", "critical"]:
            unit = thresholds.get("unit", "")
            direction = "high"
            
            issue = {
                "parameter": param,
                "value": value,
                "unit": unit,
                "severity": severity,
                "status": "⚠️" if severity == "warning" else "🔴"
            }
            
            if isinstance(thresholds.get("good"), tuple):
                issue["acceptable_range"] = f"{thresholds['good'][0]}-{thresholds['good'][1]}{unit}"
            else:
                issue["acceptable_limit"] = f"<={thresholds['good']}{unit}"
            
            if param in RECOMMENDATIONS:
                rec = RECOMMENDATIONS[param].get(direction, RECOMMENDATIONS[param].get("high", ""))
                issue["recommendation"] = rec
                actions.append(f"{severity.upper()}: {param} at {value}{unit} - {rec}")
            
            issues.append(issue)
    
    # Calculate overall grade
    if severity_counts["critical"] > 0:
        grade = "D"
    elif severity_counts["warning"] >= 2:
        grade = "C"
    elif severity_counts["warning"] == 1:
        grade = "B"
    else:
        grade = "A"
    
    # Generate lead generation CTA
    urgency_level = "critical" if severity_counts["critical"] > 0 else "warning" if severity_counts["warning"] > 0 else "routine"
    
    cta_messages = {
        "critical": {
            "headline": "🚨 URGENT: Your office air quality requires immediate attention",
            "message": f"We found {severity_counts['critical']} critical issue(s) in your IAQ readings. Professional assessment recommended.",
            "service": "Emergency IAQ Assessment & Resolution"
        },
        "warning": {
            "headline": "⚠️ Your office air quality needs improvement",
            "message": f"We found {severity_counts['warning']} warning issue(s). Our team can help optimize your indoor environment.",
            "service": "Professional IAQ Assessment & Optimization"
        },
        "routine": {
            "headline": "✅ Your office air quality is good",
            "message": "Maintain optimal air quality with our monitoring solutions.",
            "service": "Ongoing IAQ Monitoring Package"
        }
    }
    
    cta = cta_messages[urgency_level]
    
    return {
        "device": device.get("name", "Unknown"),
        "timestamp": latest.get("time"),
        "overall_grade": grade,
        "issues_count": len(issues),
        "issues": issues,
        "prioritized_actions": actions[:5],
        "lead_generation": {
            "urgency": urgency_level,
            "cta_headline": cta["headline"],
            "cta_message": cta["message"],
            "recommended_service": cta["service"],
            "contact_options": [
                {"type": "website", "label": "🌐 Visit What If Labs", "url": COMPANY_INFO["website"]},
                {"type": "contact", "label": "📧 Contact Us", "url": COMPANY_INFO["contact_page"]},
                {"type": "email", "label": "✉️ Email", "value": COMPANY_INFO["email"]}
            ],
            "value_proposition": COMPANY_INFO["value_proposition"],
            "services_offered": COMPANY_INFO["services"]
        }
    }

@mcp.tool()
def generate_iaq_report_for_client(building_id: str = None) -> dict:
    """
    Generate a client-facing IAQ report with lead generation CTA
    
    This creates a professional report that can be shared with building
    managers, facility operators, or potential clients.
    
    Args:
        building_id: Optional building UUID to filter by
        
    Returns:
        Professional IAQ report with recommendations and CTA
    """
    # Get devices
    params = {}
    if building_id:
        params["building_id"] = building_id
    
    devices_data = client.get("/api/devices", params=params)
    devices = devices_data if isinstance(devices_data, list) else devices_data.get("data", [])
    
    all_issues = []
    all_actions = []
    device_summaries = []
    severity_counts = {"critical": 0, "warning": 0, "good": 0}
    
    for device in devices:
        # Get latest readings
        readings = get_latest_readings(device["id"])
        if not readings.get('readings'):
            continue
        
        latest = readings['readings'][0]
        device_issues = []
        
        for param, thresholds in IAQ_THRESHOLDS.items():
            value = latest.get(param)
            if value is None:
                continue
            
            severity = None
            if isinstance(thresholds.get("good"), tuple):
                good_min, good_max = thresholds["good"]
                warn_min, warn_max = thresholds["warning"]
                
                if good_min <= value <= good_max:
                    severity = "good"
                elif warn_min <= value <= warn_max:
                    severity = "warning"
                else:
                    severity = "critical"
            else:
                if value <= thresholds["good"]:
                    severity = "good"
                elif value <= thresholds["warning"]:
                    severity = "warning"
                else:
                    severity = "critical"
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            if severity in ["warning", "critical"]:
                unit = thresholds.get("unit", "")
                issue = {
                    "parameter": param,
                    "value": value,
                    "unit": unit,
                    "severity": severity,
                    "device": device["name"]
                }
                if param in RECOMMENDATIONS:
                    issue["recommendation"] = RECOMMENDATIONS[param].get("high", "")
                device_issues.append(issue)
                all_issues.append(issue)
        
        device_summaries.append({
            "device": device["name"],
            "issues_count": len(device_issues),
            "status": "🔴 Critical" if any(i["severity"] == "critical" for i in device_issues) else "⚠️ Warning" if device_issues else "✅ Good"
        })
    
    # Calculate overall grade
    if severity_counts["critical"] > 0:
        grade = "D"
    elif severity_counts["warning"] >= 3:
        grade = "C"
    elif severity_counts["warning"] > 0:
        grade = "B"
    else:
        grade = "A"
    
    return {
        "report_title": "IAQ Health Check Report",
        "generated_by": COMPANY_INFO["name"],
        "date": latest.get("time", "")[:10] if latest else "",
        "devices_analyzed": len(devices),
        "overall_grade": grade,
        "summary": {
            "critical_issues": severity_counts["critical"],
            "warning_issues": severity_counts["warning"],
            "total_issues": severity_counts["critical"] + severity_counts["warning"]
        },
        "device_summaries": device_summaries,
        "issues": all_issues,
        "next_steps": [
            "1. Address critical IAQ issues immediately",
            "2. Schedule professional IAQ assessment",
            "3. Implement ongoing monitoring solution"
        ],
        "contact_us": {
            "headline": "🔍 Need a comprehensive IAQ assessment?",
            "message": f"{COMPANY_INFO['name']} provides professional IAQ monitoring and optimization services.",
            "cta_button": "Contact What If Labs",
            "cta_url": COMPANY_INFO["contact_page"],
            "services": COMPANY_INFO["services"],
            "website": COMPANY_INFO["website"]
        }
    }

@mcp.tool()
def get_iaq_health_score(device_id: str) -> dict:
    """
    Get an IAQ health score (0-100) with CTA
    
    Args:
        device_id: Device UUID
        
    Returns:
        IAQ health score with breakdown and contact CTA
    """
    devices = list_devices()
    device = None
    for d in devices:
        if d['id'] == device_id:
            device = d
            break
    
    if not device:
        return {"error": f"Device not found: {device_id}"}
    
    readings = get_latest_readings(device_id)
    if not readings.get('readings'):
        return {"error": "No readings available"}
    
    latest = readings['readings'][0]
    
    # Calculate score for each parameter
    param_scores = {}
    total_score = 0
    param_count = 0
    
    for param, thresholds in IAQ_THRESHOLDS.items():
        value = latest.get(param)
        if value is None:
            continue
        
        score = 100  # Default perfect score
        
        if isinstance(thresholds.get("good"), tuple):
            good_min, good_max = thresholds["good"]
            warn_min, warn_max = thresholds["warning"]
            
            if good_min <= value <= good_max:
                score = 100
            elif warn_min <= value <= warn_max:
                # Linear scale from good to warning
                if value > good_max:
                    range_size = warn_max - good_max
                    distance = value - good_max
                else:
                    range_size = good_min - warn_min
                    distance = good_min - value
                score = max(50, 100 - (distance / range_size) * 50)
            else:
                score = 25
        else:
            if value <= thresholds["good"]:
                score = 100
            elif value <= thresholds["warning"]:
                range_size = thresholds["warning"] - thresholds["good"]
                distance = value - thresholds["good"]
                score = max(50, 100 - (distance / range_size) * 50)
            elif value <= thresholds["critical"]:
                range_size = thresholds["critical"] - thresholds["warning"]
                distance = value - thresholds["warning"]
                score = max(25, 50 - (distance / range_size) * 25)
            else:
                score = 0
        
        unit = thresholds.get("unit", "")
        status = "✅ Good" if score >= 80 else "⚠️ Warning" if score >= 50 else "🔴 Critical"
        
        param_scores[param] = {
            "score": round(score),
            "value": value,
            "unit": unit,
            "status": status
        }
        
        total_score += score
        param_count += 1
    
    overall_score = round(total_score / param_count) if param_count > 0 else 0
    
    if overall_score >= 90:
        grade = "A"
        message = "✅ Excellent air quality!"
    elif overall_score >= 75:
        grade = "B"
        message = "⚠️ Good, but some areas need improvement"
    elif overall_score >= 50:
        grade = "C"
        message = "⚠️ Fair - Several issues need attention"
    elif overall_score >= 25:
        grade = "D"
        message = "🔴 Poor - Immediate action required"
    else:
        grade = "F"
        message = "🚨 Critical - Urgent intervention needed"
    
    return {
        "device": device.get("name", "Unknown"),
        "health_score": overall_score,
        "grade": grade,
        "message": message,
        "parameter_scores": param_scores,
        "lead_generation": {
            "cta_headline": f"📊 Your IAQ Health Score: {overall_score}/100 (Grade: {grade})",
            "cta_message": message,
            "contact_options": [
                {"type": "website", "label": "🌐 Visit What If Labs", "url": COMPANY_INFO["website"]},
                {"type": "contact", "label": "📧 Free IAQ Assessment", "url": COMPANY_INFO["contact_page"]}
            ],
            "services": COMPANY_INFO["services"][:3],
            "value_proposition": COMPANY_INFO["value_proposition"]
        }
    }

# ============================================================================
# OPERATIONS
# ============================================================================

@mcp.tool()
def get_realtime_status() -> dict:
    """Get real-time system status (no cache)"""
    return client.get("/api/operations/realtime")

@mcp.tool()
def get_sensor_history(device_id: str, hours: int = 24) -> dict:
    """Get sensor history"""
    return client.get(
        f"/api/operations/sensors/{device_id}/history",
        params={"hours": hours}
    )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    mcp.run(transport='stdio')
