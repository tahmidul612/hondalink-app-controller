# HONDALINK CONTROLLER PROJECT

**Generated:** 2026-02-03 13:20  
**Commit:** 9be6e61  
**Branch:** feat/hondalink-controller-12529357378338011672

## OVERVIEW

FastAPI service controlling HondaLink Android app via uiautomator2. Provides REST API for remote vehicle operations (lock/unlock/start). Python 3.11+, uses `uv` package manager.

## STRUCTURE

```text
.
├── src/hondalink/       # Main package (519 lines)
│   ├── main.py          # FastAPI app + lifespan
│   ├── controller.py    # Business logic (203 lines)
│   ├── driver.py        # ABC for Android automation
│   ├── driver_impl.py   # Real uiautomator2 wrapper
│   ├── driver_mock.py   # Test mock (stateful)
│   ├── config.py        # Pydantic settings (.env)
│   └── models.py        # CommandType, VehicleStatus
├── tests/               # Pytest tests (166 lines)
│   ├── test_api.py      # FastAPI endpoint tests
│   ├── test_controller.py
│   └── test_controller_pin.py
├── pyproject.toml       # Dependencies + config
└── uv.lock              # Locked dependencies
```

## WHERE TO LOOK

| Task | Location | Notes |
| ------ | ---------- | ------- |
| Add/fix API endpoint | `main.py` | All routes in single file, no routers |
| Fix UI element selector | `controller.py` | Text/XPath selectors, see BRITTLE PATTERNS |
| Mock Android device | `driver_mock.py` | Register elements with `.register_element()` |
| Add vehicle command | `models.py` + `controller.py` | Add enum + handler |
| Monitor remote start | `controller.get_remote_start_status()` | Returns timer + cabin temp during active session |
| Change env config | `config.py` | Pydantic settings from `.env` |
| Debug UI hierarchy | `/debug/hierarchy` endpoint | Dumps XML when selectors fail |

## ARCHITECTURE DEVIATIONS

This project deviates from standard FastAPI patterns due to Android automation constraints:

### 1. **Global Controller + Async Lock** (Not Idiomatic)

- Controller instantiated globally in lifespan, protected by `asyncio.Lock()`
- **Why**: Android device connection is stateful, cannot use typical dependency injection
- **Location**: `main.py:16-47`

### 2. **Sync Business Logic in Async Endpoints** (Hybrid)

- All controller methods are blocking, wrapped with `asyncio.to_thread()`
- **Why**: `uiautomator2` is synchronous, cannot be made async
- **Location**: All endpoints use `await asyncio.to_thread(controller.method)`

### 3. **Retry at Business Layer** (Non-Standard)

- `@retry` decorator on `execute_remote_command()` method
- **Why**: UI automation is flaky, needs retry at operation level not HTTP level
- **Location**: `controller.py:153`

### 4. **Driver Abstraction with Protocol** (Unusual)

- ABC + two implementations (real + mock)
- **Why**: Testing without real Android device requires full driver mock
- **Pattern**: Protocol-based (`UIElement`) + ABC (`AndroidDriver`)

## BRITTLE PATTERNS

### Text-Based UI Selectors (HIGH RISK)

**Problem**: HondaLink app UI changes break text selectors  
**Location**: `controller.py:130-151`  
**Pattern**:

```python
# BRITTLE: Breaks when app updates change text
self.driver.find_by_text("Start").click()
```

**Fix**: Use `/debug/hierarchy` to get resource IDs, prefer XPath with attributes  
**Example**:

```python
# BETTER: Use resource ID
self.driver.find_by_resource_id("com.honda.auto:id/btn_start")
```

### Speculative PIN Logic

**Problem**: PIN entry assumes UI structure without verification  
**Location**: `controller.py:43-66`  
**Action Required**: Verify against actual app before deploying

### No Relative Lookups

**Problem**: Cannot find "value near label" easily  
**Workaround**: Use XPath sibling selectors

```python
# Find odometer value near "Odometer" label
self.driver.find_by_xpath("//*[@text='Odometer']/following-sibling::*[@text]")
```

### Remote Start Extend Logic

**Behavior**: When remote start is active, "Start" button becomes "Extend" button  
**Location**: `controller.py:execute_remote_command()`  
**Implementation**: Checks for "Extend" button first when START command is issued

```python
# Automatically uses Extend button if remote start is already active
if command == CommandType.START:
    extend_btn = self.driver.find_by_text("Extend")
    if extend_btn.exists():
        btn = extend_btn  # Use Extend instead of Start
```

**Resource IDs for Remote Start Status**:
- Timer: `com.honda.hondalink.connect:id/text_success_timer` (format: "MM:SS")
- Cabin Temp: `com.honda.hondalink.connect:id/remote_command_inside_temp` (format: "XX °C")

## CODE CONVENTIONS

### Ruff Linting (Strict)

```toml
select = ["E", "W", "F", "I", "B", "C4", "UP"]
line-length = 88
```

- **Import sorting**: Enforced by isort (I)
- **Bugbear checks**: Enabled (B)
- **No type checking**: mypy/pyright NOT configured

### Testing

- **Framework**: pytest 9.0+
- **Fixture Pattern**: `mock_driver` → `controller` (dependency injection)
- **MockDriver**: Register elements with state

  ```python
  mock_driver.register_element("text=Start", exists=True)
  start_btn.clicked  # Assert interaction
  ```

- **Coverage**: Auto-runs with `pytest` (configured in pyproject.toml)
- **Settings Override**: Tests set `settings.use_mock_driver = True`

### Environment Variables (.env)

```ini
ANDROID_DEVICE_IP=192.168.1.100  # Optional, defaults to USB
PIN_CODE=1234                     # Required if app needs PIN
HONDALINK_PACKAGE=com.honda.auto  # Default package name
USE_MOCK_DRIVER=False             # True for testing
```

**NEVER commit `.env`** - create locally

## COMMANDS

```bash
# Setup
uv sync                          # Install deps + dev tools

# Development
uv run uvicorn src.hondalink.main:app --host 0.0.0.0 --port 8000 --reload

# Testing
uv run pytest                    # Runs with coverage
USE_MOCK_DRIVER=True uv run pytest  # Force mock mode

# Linting
uv run ruff check src/ tests/
uv run ruff format src/ tests/   # Auto-format

# Debugging
curl http://localhost:8000/debug/hierarchy > ui.xml
# Inspect ui.xml to find correct selectors when elements fail
```

## API ENDPOINTS

### GET /health
Health check endpoint (no authentication required)

### GET /status
Get vehicle status (odometer, fuel, lock state, etc.)

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

### GET /remote-start/status
Get active remote start session status (timer and cabin temperature)

**Response when active:**
```json
{
  "is_active": true,
  "remaining_time": "09:58",
  "cabin_temperature": "-2 °C"
}
```

**Response when inactive:**
```json
{
  "is_active": false,
  "remaining_time": "Unknown",
  "cabin_temperature": "Unknown"
}
```

**Note**: This endpoint checks for remote start UI elements without disrupting the active session.

### POST /action/{command}
Execute vehicle command: `start`, `stop`, `lock`, `unlock`

**Special behavior for START command:**
- If remote start is already active, automatically uses "Extend" button instead
- Extends the current remote start session by 10 minutes

**Response:**
```json
{
  "status": "success",
  "message": "Command start executed successfully"
}
```

### GET /debug/hierarchy
Dump current UI hierarchy as XML (useful for debugging selectors)

## MAINTENANCE REQUIREMENTS

### When HondaLink App Updates

1. Run `/debug/hierarchy` endpoint
2. Inspect XML for changed text/IDs
3. Update selectors in `controller.py`
4. Re-run tests

### Adding New Commands

1. Add enum to `models.CommandType`
2. Add button mapping in `controller.execute_remote_command()`
3. Add test in `tests/test_controller.py`
4. Update README usage section

### Known Issues

- **Coverage plugin**: `pytest-cov` may not be installed despite being in pyproject.toml
- **Pre-commit hook**: References missing `.pre-commit-config.yaml`
- **Python version**: `.python-version` says 3.14 but project requires 3.11+

## NOTES

- **No CI/CD**: No GitHub Actions configured (manual testing only)
- **No Makefile**: Use `uv run` prefix for all commands
- **Android device required**: Or set `USE_MOCK_DRIVER=True` for API testing
- **Stateful API**: Concurrent requests blocked by asyncio.Lock (one operation at a time)
- **Retry logic**: Commands retry 3x with 2s delay on failure
