<div align="center">

# HondaLink Controller

**A secure REST API for controlling your Honda vehicle remotely**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![uv](https://img.shields.io/badge/managed_by-uv-blueviolet.svg?style=for-the-badge)](https://github.com/astral-sh/uv)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Security](#-security-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
  - [Native Installation](#native-installation)
  - [Docker Deployment](#-docker-deployment-recommended)
- [Configuration](#-configuration)
- [Running the Server](#-running-the-server)
- [API Usage](#-api-usage)
- [Architecture](#-architecture)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🚗 Overview

HondaLink Controller is a FastAPI-based service that interfaces with the HondaLink Android app via `uiautomator2` to provide a programmable REST API for your vehicle. Control your Honda remotely using simple HTTP requests—lock doors, unlock doors, start the engine, and monitor vehicle status—all from the comfort of your home automation system, smartphone, or any HTTP client.

## ✨ Features

- **🔐 Complete Vehicle Control**: Lock, unlock, remote start, and stop your vehicle
- **📊 Status Monitoring**: Check odometer, fuel level, door locks, and more
- **🕐 Remote Start Monitoring**: View active remote start sessions with timer and cabin temperature
- **🔄 Automatic Retry Logic**: Built-in retry mechanism for flaky UI automation
- **🧪 Mock Driver**: Full test mode without requiring a physical Android device
- **⚡ FastAPI Performance**: Asynchronous architecture with OpenAPI/Swagger documentation
- **🐳 Docker Ready**: Production-ready containerized deployment with security hardening
- **🐛 Debug Tools**: UI hierarchy dump endpoint for troubleshooting element selectors

## 🔒 Security Features

This service includes comprehensive security hardening to prevent unauthorized access:

- **🔑 API Key Authentication** - Required for all endpoints with secure token validation
- **🌐 IP Whitelist** - Restrict access to trusted networks using CIDR notation
- **⏱️ Rate Limiting** - Two-tier protection (10 commands/min, 30 API calls/min)
- **📝 Audit Logging** - Complete audit trail in JSONL format for all vehicle commands
- **🔒 HTTPS/TLS Support** - Encrypt traffic in transit with SSL/TLS certificates

**⚠️ IMPORTANT**: This service controls your physical vehicle. Please review the [Security Guide](SECURITY.md) before deployment.

## 📋 Prerequisites

### Required Components

1. **Android Device or Emulator**:
   - Physical Android device with USB debugging enabled
   - OR Android emulator (Waydroid, Android Studio AVD, etc.)
   - **HondaLink App**: Must be installed and logged into your Honda account

2. **ADB (Android Debug Bridge)**:
   - Installed and accessible in your system PATH
   - Device must be authorized (`adb devices` should list your device)
   - For wireless connection: `adb connect <device-ip>:5555`

3. **Python 3.11+**:
   - Python 3.11 or higher required
   - [uv](https://github.com/astral-sh/uv) package manager recommended for fast dependency management

### System Requirements

- **OS**: Linux, macOS, or Windows (with WSL recommended)
- **RAM**: Minimum 2GB available
- **Network**: Local network access to Android device (if using wireless ADB)
- **Storage**: ~500MB for dependencies

## 🚀 Installation

Choose your preferred deployment method:

### 🐳 Docker Deployment (Recommended)

Docker provides the easiest and most reliable deployment with all dependencies pre-configured.

1. **Prerequisites**: Install [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

2. **Clone the repository**:
   ```bash
   git clone https://github.com/tahmidul612/hondalink-app-controller.git
   cd hondalink-app-controller
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings (Android device IP, PIN, API keys)
   ```

4. **Start with Docker Compose**:
   ```bash
   docker compose up -d
   ```

5. **Verify deployment**:
   ```bash
   curl http://localhost:8000/health
   ```

**Using Makefile** (recommended for easier management):
```bash
make build    # Build Docker image
make up       # Start services
make logs     # View logs
make health   # Check service status
make down     # Stop services
```

📖 **For detailed Docker configuration, networking modes, and troubleshooting**, see [Docker Deployment Guide](docs/DOCKER.md)

### Native Installation

For development or if you prefer running without Docker:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tahmidul612/hondalink-app-controller.git
   cd hondalink-app-controller
   ```

2. **Install uv** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

#### Alternative: pip Installation

If you prefer using pip:
```bash
pip install -e .
```

#### Verify Installation

Check that ADB can see your device:
```bash
adb devices
# Should output:
# List of devices attached
# <device-id>    device
```

## ⚙️ Configuration

### Quick Setup (Recommended)

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Generate a secure API key**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Edit `.env` with your settings**:

```ini
# .env

# === Android Device Settings ===
ANDROID_DEVICE_IP=192.168.1.100  # Optional: Leave empty for USB, or use IP:PORT for wireless
PIN_CODE=1234                     # Your HondaLink app PIN (if required)
HONDALINK_PACKAGE=com.honda.hondalink.connect
USE_MOCK_DRIVER=False             # Set to True for testing without real device

# === Security Settings (REQUIRED for production) ===
REQUIRE_AUTHENTICATION=true
API_KEYS=your-generated-key-here  # Paste the key from step 2

# IP Whitelist (comma-separated, or empty to allow all)
ALLOWED_IPS=192.168.1.0/24        # Example: Your home network

# Rate Limiting
ENABLE_RATE_LIMITING=true
API_RATE_LIMIT=30                 # General requests per minute
COMMAND_RATE_LIMIT=10             # Vehicle commands per minute

# Audit Logging
AUDIT_LOG_FILE=logs/security_audit.jsonl
```

### Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANDROID_DEVICE_IP` | Android device IP address (wireless ADB) | _(USB)_ | No |
| `PIN_CODE` | HondaLink app PIN code (4 digits) | _(none)_ | If app requires |
| `REQUIRE_AUTHENTICATION` | Enable API key authentication | `true` | Yes |
| `API_KEYS` | Comma-separated list of valid API keys | _(none)_ | If auth enabled |
| `ALLOWED_IPS` | Whitelist of IP addresses/CIDR ranges | _(all)_ | No |
| `ENABLE_RATE_LIMITING` | Enable request rate limiting | `true` | Recommended |
| `API_RATE_LIMIT` | Max API requests per minute | `30` | No |
| `COMMAND_RATE_LIMIT` | Max vehicle commands per minute | `10` | No |
| `AUDIT_LOG_FILE` | Path to security audit log | `logs/security_audit.jsonl` | No |

**For complete security configuration including HTTPS/TLS, see [Security Guide](docs/SECURITY.md)**

## 🏃 Running the Server

### 🐳 Docker (Recommended)

The easiest way to run the service with all dependencies configured:

```bash
# Start service in background
docker compose up -d

# View logs
docker compose logs -f

# Check status
docker compose ps

# Stop service
docker compose down
```

**Using Makefile commands**:
```bash
make up        # Start service
make logs      # View logs
make health    # Check service status
make restart   # Restart service
make down      # Stop service
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

📖 **For Docker configuration, networking, and production deployment**, see [Docker Deployment Guide](docs/DOCKER.md)

### Native Development Mode (HTTP)

Start the server with hot reload for development:

```bash
uv run uvicorn src.hondalink.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Native Production Mode (HTTPS)

1. **Generate SSL certificate** (self-signed for testing):
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes \
     -keyout key.pem -out cert.pem -days 365 \
     -subj "/CN=localhost"
   ```

2. **Run with HTTPS**:
   ```bash
   uv run uvicorn src.hondalink.main:app \
     --host 0.0.0.0 \
     --port 8443 \
     --ssl-keyfile=key.pem \
     --ssl-certfile=cert.pem
   ```

   Access at: https://localhost:8443

**For production deployment**, use proper certificates from Let's Encrypt:
```bash
certbot certonly --standalone -d yourdomain.com
```

## 📡 API Usage

All API endpoints (except `/health`) require authentication. Export your API key for convenience:

```bash
export API_KEY="your-generated-key-here"
```

### Quick Start Example

```bash
# 1. Check health (no auth required)
curl http://localhost:8000/health

# 2. Get vehicle status
curl -H "X-API-Key: $API_KEY" http://localhost:8000/status

# 3. Lock doors
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/action/lock

# 4. Remote start
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/action/start

# 5. Check remote start status
curl -H "X-API-Key: $API_KEY" http://localhost:8000/remote-start/status
```

### Endpoints

#### `GET /health`
Health check endpoint. No authentication required.

**Response:**
```json
{
  "status": "ok"
}
```

#### `GET /status`
Get current vehicle status including odometer, fuel level, lock state, and more.

**Response:**
```json
{
  "odometer": "173,305 km",
  "fuel_level": "56.0%",
  "range_remaining": "327 km",
  "oil_life": "5 %",
  "is_locked": true,
  "last_updated": "Last updated at 05:33 p.m."
}
```

#### `GET /remote-start/status`
Check if remote start is active and get remaining time and cabin temperature.

**Response (Active):**
```json
{
  "is_active": true,
  "remaining_time": "09:58",
  "cabin_temperature": "-2 °C"
}
```

**Response (Inactive):**
```json
{
  "is_active": false,
  "remaining_time": "Unknown",
  "cabin_temperature": "Unknown"
}
```

#### `POST /action/{command}`
Execute a vehicle command. Available commands: `start`, `stop`, `lock`, `unlock`

**Special Behavior:**
- **START command**: Automatically extends if remote start is already active
- **Commands include retry logic**: Automatically retries up to 3 times on failure

**Example - Remote Start:**
```bash
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8000/action/start
```

**Response:**
```json
{
  "status": "success",
  "message": "Command start executed successfully"
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Maximum start requests reached. Please reset by turning the car ON then OFF."
}
```

#### `GET /debug/hierarchy`
Dump the current UI hierarchy as XML for debugging element selectors.

**Usage:**
```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/debug/hierarchy > ui.xml
```

Use this when UI automation fails to identify correct element selectors.

### Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Test all endpoints directly from your browser
- View request/response schemas
- See authentication requirements
- Download OpenAPI specification

### Integration Examples

<details>
<summary><b>Home Assistant</b></summary>

```yaml
# configuration.yaml
rest_command:
  honda_lock:
    url: "http://your-server:8000/action/lock"
    method: POST
    headers:
      X-API-Key: "your-api-key-here"
  
  honda_unlock:
    url: "http://your-server:8000/action/unlock"
    method: POST
    headers:
      X-API-Key: "your-api-key-here"
  
  honda_start:
    url: "http://your-server:8000/action/start"
    method: POST
    headers:
      X-API-Key: "your-api-key-here"

sensor:
  - platform: rest
    name: "Honda Status"
    resource: "http://your-server:8000/status"
    headers:
      X-API-Key: "your-api-key-here"
    json_attributes:
      - odometer
      - fuel_level
      - range_remaining
    value_template: "{{ value_json.is_locked }}"
```
</details>

<details>
<summary><b>Python Client</b></summary>

```python
import requests

class HondaLinkClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def get_status(self):
        response = requests.get(f"{self.base_url}/status", headers=self.headers)
        return response.json()
    
    def lock(self):
        response = requests.post(f"{self.base_url}/action/lock", headers=self.headers)
        return response.json()
    
    def unlock(self):
        response = requests.post(f"{self.base_url}/action/unlock", headers=self.headers)
        return response.json()
    
    def remote_start(self):
        response = requests.post(f"{self.base_url}/action/start", headers=self.headers)
        return response.json()

# Usage
client = HondaLinkClient("http://localhost:8000", "your-api-key")
status = client.get_status()
print(f"Fuel: {status['fuel_level']}, Locked: {status['is_locked']}")
```
</details>

<details>
<summary><b>Node.js/JavaScript</b></summary>

```javascript
const axios = require('axios');

class HondaLinkClient {
  constructor(baseUrl, apiKey) {
    this.client = axios.create({
      baseURL: baseUrl,
      headers: { 'X-API-Key': apiKey }
    });
  }

  async getStatus() {
    const response = await this.client.get('/status');
    return response.data;
  }

  async lock() {
    const response = await this.client.post('/action/lock');
    return response.data;
  }

  async unlock() {
    const response = await this.client.post('/action/unlock');
    return response.data;
  }

  async remoteStart() {
    const response = await this.client.post('/action/start');
    return response.data;
  }
}

// Usage
const client = new HondaLinkClient('http://localhost:8000', 'your-api-key');
const status = await client.getStatus();
console.log(`Fuel: ${status.fuel_level}, Locked: ${status.is_locked}`);
```
</details>

### Audit Logs

All security events and vehicle commands are logged to `logs/security_audit.jsonl`:

```bash
# Tail live logs
tail -f logs/security_audit.jsonl

# Search for vehicle commands
grep "vehicle_command" logs/security_audit.jsonl | jq .

# Find security issues
grep -E "blocked|failed|exceeded" logs/security_audit.jsonl | jq .
```

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   HTTP Client   │────────▶│  FastAPI Server  │────────▶│ Android Device  │
│  (curl, app,    │◀────────│  (Python 3.11+)  │◀────────│  (HondaLink)    │
│   Home Assist.) │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │                             │
                                     │                             │
                                     ▼                             ▼
                            ┌─────────────────┐         ┌─────────────────┐
                            │  Security Layer │         │  UI Automation  │
                            │  • API Keys     │         │  (uiautomator2) │
                            │  • Rate Limit   │         │                 │
                            │  • IP Whitelist │         │                 │
                            │  • Audit Log    │         │                 │
                            └─────────────────┘         └─────────────────┘
```

### Component Architecture

**FastAPI Application** (`src/hondalink/main.py`)
- Asynchronous HTTP server
- OpenAPI/Swagger documentation
- Lifespan management for driver connection
- Global controller with asyncio lock for thread safety

**HondaLinkController** (`src/hondalink/controller.py`)
- Business logic for vehicle operations
- Retry mechanism with exponential backoff
- UI element detection and interaction
- Command completion verification

**Driver Abstraction** (`src/hondalink/driver*.py`)
- `AndroidDriver`: Abstract base class
- `UiautomatorDriver`: Real Android device integration via uiautomator2
- `MockDriver`: In-memory mock for testing

**Security Module** (`src/hondalink/security.py`)
- API key authentication with secure token validation
- IP whitelist with CIDR notation support
- Two-tier rate limiting (API + Commands)
- Comprehensive audit logging in JSONL format

**Configuration** (`src/hondalink/config.py`)
- Pydantic settings from environment variables
- Type-safe configuration management
- Support for `.env` files

### Data Flow

1. **Request Arrives** → Security middleware validates API key and IP
2. **Rate Limit Check** → Appropriate tier checked (API vs Command)
3. **Audit Log Entry** → Request logged with timestamp and client info
4. **Controller Execution** → Business logic executed with async-to-sync wrapper
5. **UI Automation** → uiautomator2 interacts with HondaLink app
6. **Retry Logic** → Up to 3 retries on failure with 2s delay
7. **Response** → Success/failure returned to client
8. **Audit Log Entry** → Result logged

### Key Design Patterns

**Global Controller with Lock**
- Controller instantiated once during lifespan
- Protected by `asyncio.Lock()` to prevent concurrent operations
- Necessary due to stateful Android device connection

**Sync-in-Async Execution**
- Controller methods are synchronous (uiautomator2 limitation)
- Wrapped with `asyncio.to_thread()` in endpoints
- Allows FastAPI to remain fully asynchronous

**Protocol-Based Driver Abstraction**
- ABC pattern enables testing without real hardware
- MockDriver provides stateful simulation
- Easy to add new driver implementations

**Retry at Business Layer**
- `@retry` decorator on command execution
- Handles flaky UI automation
- Operates below HTTP layer for better control

## 🐛 Troubleshooting

### Docker Issues

**Container won't start**
- Check Docker logs: `docker compose logs`
- Verify .env configuration: `docker compose config`
- Ensure ports aren't already in use: `docker ps`
- Check Docker daemon is running: `docker info`

**ADB connection from container**
- For USB devices: Ensure `devices:` section is uncommented in docker-compose.yml
- For network devices: Use `network_mode: host` or specify device IP
- Test from container: `docker compose exec hondalink-controller adb devices`
- Connect to device: `docker compose exec hondalink-controller adb connect <IP>:5555`

**Permission issues with logs**
- Ensure logs directory exists: `mkdir -p logs`
- Set permissions: `chmod 777 logs` (or `chown 1000:1000 logs`)

**High memory usage**
- Reduce resource limits in docker-compose.yml
- Check `docker stats hondalink-controller`
- See [Docker Guide](docs/DOCKER.md) for optimization tips

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

**ADB Connection Problems**
- Ensure `adb devices` lists your device as "device" (not "unauthorized")
- For Waydroid/emulator: `adb connect <IP>:5555`
- USB connection issues: Try different USB cable or port
- Restart ADB: `adb kill-server && adb start-server`

**App Not Starting**
- Check logs for crash details
- Ensure HondaLink app is installed and logged in
- Manually start app once to complete initial setup
- Clear app data if login session expired

**Elements Not Found**
- HondaLink app UI may have changed in an update
- Use `/debug/hierarchy` endpoint to inspect current UI
- Update selectors in `src/hondalink/controller.py`
- Check if app is on correct screen (should be on Remote Commands)

### Command Failures

**"Maximum start requests reached"**
- Turn car ON then OFF to reset remote start counter
- This is a Honda limitation, not a bug

**Commands Timeout**
- Check network connectivity to Android device
- Ensure device screen is unlocked
- HondaLink may be communicating with vehicle (wait 30s)
- Check audit logs for detailed error messages

**"Processing UI never appeared"**
- App may not have loaded properly
- Restart the service to reconnect
- Check if app is logged in

### Development & Testing

**Running Tests**
```bash
# Native (with uv)
uv run pytest

# Docker
make test
# or
docker compose exec hondalink-controller pytest

# Run specific test file
uv run pytest tests/test_controller.py

# Run with verbose output
uv run pytest -v

# Run in mock mode (no device needed)
USE_MOCK_DRIVER=True uv run pytest
```

**Linting & Formatting**
```bash
# Native (with uv)
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Docker
make lint
make format
```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/tahmidul612/hondalink-app-controller/issues)
- **Security**: See [Security Guide](docs/SECURITY.md) for reporting security vulnerabilities
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- **Docker**: See [Docker Guide](docs/DOCKER.md) for container deployment
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development environment setup
- Code style guidelines
- Testing requirements
- Pull request process
- Commit conventions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This project is not affiliated with, endorsed by, or connected to Honda Motor Company or HondaLink. Use at your own risk. The authors are not responsible for any damage to your vehicle or violation of terms of service.

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework for building APIs
- **uiautomator2** - Android automation library
- **uv** - Fast Python package manager
- **Honda** - For creating the HondaLink app (even though we have to automate it)

---

<div align="center">

**[⬆ back to top](#hondalink-controller)**

Made with ❤️ for the Honda community

</div>
