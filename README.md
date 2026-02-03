# HondaLink Controller

A FastAPI service that interfaces with the HondaLink Android app via `uiautomator2` to provide a programmable API for your vehicle. This allows you to lock, unlock, and remote start your car using HTTP requests.

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

Create a `.env` file in the root directory (copy from example below):

```ini
# .env

# IP address of your Android device (if connecting wirelessly or via Waydroid)
# Leave empty to connect to the first USB device found.
ANDROID_DEVICE_IP=192.168.1.100

# PIN for the HondaLink app (if required)
PIN_CODE=1234

# Package name (default is com.honda.auto, usually doesn't need changing)
HONDALINK_PACKAGE=com.honda.auto

# Set to True to use the Mock driver for testing without a real device
USE_MOCK_DRIVER=False
```

## Running the Server

Start the FastAPI server:

```bash
uv run uvicorn src.hondalink.main:app --host 0.0.0.0 --port 8000 --reload
```

## Usage

### 1. Check Service Health
```bash
curl http://localhost:8000/health
```

### 2. Get Vehicle Status
Retrieves current status (Odometer, Fuel, Lock state, etc.).
*Note: Ensure the app is running. The service will attempt to launch it if not.*

```bash
curl http://localhost:8000/status
```

### 3. Remote Commands
Supported commands: `start`, `stop`, `lock`, `unlock`.

**Remote Start:**
```bash
curl -X POST http://localhost:8000/action/start
```

**Lock Doors:**
```bash
curl -X POST http://localhost:8000/action/lock
```

### 4. Debugging
If scraping fails, you can dump the current UI hierarchy to inspect element attributes:

```bash
curl http://localhost:8000/debug/hierarchy > dump.xml
```

## Troubleshooting

*   **ADB Connection**: Ensure `adb devices` lists your device. If using Waydroid, you may need to run `adb connect <IP>:5555`.
*   **App Not Starting**: Check the logs. If the app crashes, the service tries to restart it, but persistent crashes may require manual intervention.
*   **Elements Not Found**: UI layouts can change between app versions. Use the `/debug/hierarchy` endpoint to inspect the current UI and update `src/hondalink/controller.py` with correct text or XPath selectors.
