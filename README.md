# HondaLink Controller

A **secure** FastAPI service that interfaces with the HondaLink Android app via `uiautomator2` to provide a programmable API for your vehicle. This allows you to lock, unlock, and remote start your car using HTTP requests.

## 🔒 Security Features

This service includes comprehensive security hardening to prevent unauthorized access:

- **API Key Authentication** - Required for all endpoints
- **IP Whitelist** - Restrict access to trusted networks
- **Rate Limiting** - Prevent abuse (10 commands/min, 30 API calls/min)
- **Audit Logging** - Track all vehicle commands and security events
- **HTTPS/TLS Support** - Encrypt traffic in transit

**⚠️ IMPORTANT**: This service controls your physical vehicle. Please review the [Security Guide](SECURITY.md) before deployment.

## Prerequisites

1.  **Android Device/Emulator**:
    *   A physical Android device with USB debugging enabled.
    *   OR an emulator (e.g., Waydroid, Android Studio AVD).
    *   **HondaLink App**: Installed and logged in.
2.  **ADB (Android Debug Bridge)**:
    *   Installed and available in your PATH.
    *   Device must be authorized (`adb devices` should show the device).
3.  **Python 3.11+**:
    *   We recommend using `uv` for package management.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd hondalink-controller
    ```

2.  **Install dependencies**:
    ```bash
    uv sync
    ```

## Configuration

### Quick Setup (Secure)

1. **Generate an API key:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Create a `.env` file** with security settings:

```ini
# .env

# === Android Device Settings ===
ANDROID_DEVICE_IP=192.168.1.100  # Leave empty for USB
PIN_CODE=1234                     # Your HondaLink app PIN
HONDALINK_PACKAGE=com.honda.hondalink.connect
USE_MOCK_DRIVER=False

# === Security Settings (REQUIRED) ===
REQUIRE_AUTHENTICATION=true
API_KEYS=your-generated-key-here  # From step 1

# IP Whitelist (comma-separated, or empty to allow all)
ALLOWED_IPS=192.168.1.0/24        # Your home network

# Rate Limiting
ENABLE_RATE_LIMITING=true
API_RATE_LIMIT=30                 # Requests per minute
COMMAND_RATE_LIMIT=10             # Vehicle commands per minute

# Audit Logging
AUDIT_LOG_FILE=logs/security_audit.jsonl
```

**For complete security configuration, see [SECURITY.md](SECURITY.md)**

## Running the Server

### Standard Mode (HTTP)
```bash
uv run uvicorn src.hondalink.main:app --host 0.0.0.0 --port 8000 --reload
```

### Secure Mode (HTTPS - Recommended)

1. Generate self-signed certificate (for testing):
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes \
     -keyout key.pem -out cert.pem -days 365 \
     -subj "/CN=localhost"
   ```

2. Run with HTTPS:
   ```bash
   uv run uvicorn src.hondalink.main:app \
     --host 0.0.0.0 \
     --port 8443 \
     --ssl-keyfile=key.pem \
     --ssl-certfile=cert.pem
   ```

**For production deployment, use proper certificates from Let's Encrypt or a trusted CA.**

## Usage

**All commands require authentication (see Configuration above).**

Store your API key:
```bash
export API_KEY="your-generated-key-here"
```

### 1. Check Service Health
```bash
curl http://localhost:8000/health
```

### 2. Get Vehicle Status
Retrieves current status (Odometer, Fuel, Lock state, etc.).

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/status
```

### 3. Remote Commands
Supported commands: `start`, `stop`, `lock`, `unlock`.

**Remote Start:**
```bash
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/action/start
```

**Lock Doors:**
```bash
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/action/lock
```

**Unlock Doors:**
```bash
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/action/unlock
```

**Stop Engine:**
```bash
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/action/stop
```

### 4. Debugging
If scraping fails, dump the current UI hierarchy to inspect element attributes:

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/debug/hierarchy > dump.xml
```

### 5. Audit Logs
View security events and command history:

```bash
# Tail live logs
tail -f logs/security_audit.jsonl

# Search for vehicle commands
grep "vehicle_command" logs/security_audit.jsonl | jq .
```

## Troubleshooting

### Authentication Errors

**"Missing API key"**
- Add `X-API-Key` header to your requests
- Check that API key matches the value in `.env`

**"IP address not authorized"**
- Add your IP to `ALLOWED_IPS` in `.env`
- Check your actual IP: `curl ipinfo.io/ip`
- Temporarily disable whitelist: `ALLOWED_IPS=` (empty)

**"Rate limit exceeded"**
- Wait 60 seconds before retrying
- Check audit logs for abuse: `grep "rate_limit" logs/security_audit.jsonl`
- Increase limits in `.env` if legitimate use

### Connection Issues

*   **ADB Connection**: Ensure `adb devices` lists your device. If using Waydroid, you may need to run `adb connect <IP>:5555`.
*   **App Not Starting**: Check the logs. If the app crashes, the service tries to restart it, but persistent crashes may require manual intervention.
*   **Elements Not Found**: UI layouts can change between app versions. Use the `/debug/hierarchy` endpoint to inspect the current UI and update `src/hondalink/controller.py` with correct text or XPath selectors.

### Security

For security issues or questions, see [SECURITY.md](SECURITY.md) for:
- Emergency lockdown procedures
- API key rotation
- Audit log analysis
- Firewall configuration
- Reverse proxy setup
