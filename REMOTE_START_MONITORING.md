# Remote Start Monitoring

## Overview

The `/remote-start/status` endpoint provides real-time monitoring of active remote start sessions without disrupting them. This allows you to check remaining time and cabin temperature while the engine is running.

**✅ Status**: Fully working and tested (2026-02-03)

## Endpoint

### GET `/remote-start/status`

**Authentication:** Requires `X-API-Key` header

**Response when remote start is ACTIVE:**
```json
{
  "is_active": true,
  "remaining_time": "09:55",
  "cabin_temperature": "5 °C"
}
```

**Response when remote start is INACTIVE:**
```json
{
  "is_active": false,
  "remaining_time": "Unknown",
  "cabin_temperature": "Unknown"
}
```

## How It Works

The endpoint checks for two specific UI elements that only appear during an active remote start session:

1. **Timer Element** (`text_success_timer`): Shows remaining time in "MM:SS" format
2. **Temperature Element** (`remote_command_inside_temp`): Shows cabin temperature in "XX °C" format

Both elements must be present for the remote start to be considered active.

## Captured UI Hierarchy

A reference UI hierarchy from an active remote start session has been saved to:
- **File**: `hierarchy_remote_start_active.xml`
- **Captured**: 2026-02-03 17:53
- **Status at capture**: 
  - Timer: 01:36 remaining  
  - Cabin Temp: 6 °C
  - Extend button visible
  - "Engine On" status displayed

This file can be used for debugging when UI selectors break after app updates.

### Technical Fix Applied

**Problem**: Endpoint returned `is_active: false` even when remote start was active.

**Root Cause**: `uiautomator2` library's `.exists` property returns an `Exists` object (not a plain Python boolean), which Pydantic validation rejected with error:
```
Input should be a valid boolean [type=bool_type, input_value=True, input_type=Exists]
```

**Solution**: Explicitly convert to bool in `controller.py`:
```python
timer_exists = bool(timer_elem.exists())
temp_exists = bool(temp_elem.exists())
is_active = bool(timer_exists and temp_exists)
```

## Usage Example

### Monitor Active Remote Start

```bash
# Start remote start
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8002/action/start

# Poll status every 30 seconds
while true; do
  curl -H "X-API-Key: $API_KEY" http://localhost:8002/remote-start/status | jq .
  sleep 30
done
```

### Extend Active Session

When remote start is already active, calling `/action/start` will automatically use the "Extend" button instead:

```bash
# This will extend the session by 10 minutes if already running
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:8002/action/start
```

## Technical Details

### Resource IDs

```xml
<!-- Timer Display -->
<node text="09:55" 
      resource-id="com.honda.hondalink.connect:id/text_success_timer" 
      class="android.widget.TextView" />

<!-- Cabin Temperature -->
<node text="5 °C" 
      resource-id="com.honda.hondalink.connect:id/remote_command_inside_temp" 
      class="android.widget.TextView" />

<!-- Extend Button (visible during active session) -->
<node text="Extend" 
      resource-id="com.honda.hondalink.connect:id/text_remote_command_extend" 
      class="android.widget.TextView" 
      clickable="true" />
```

### Implementation

The status check is non-intrusive:
- Does NOT expand/collapse UI panels
- Does NOT trigger any vehicle commands
- Simply queries element existence
- Fast response time (< 1 second)

## Troubleshooting

### Status shows inactive but car is running

1. Check the UI hierarchy:
   ```bash
   curl -H "X-API-Key: $API_KEY" http://localhost:8002/debug/hierarchy > current.xml
   ```

2. Search for timer/temperature elements:
   ```bash
   grep "text_success_timer\|remote_command_inside_temp" current.xml
   ```

3. If elements are present but not detected:
   - Check resource IDs haven't changed in app update
   - Verify app is in foreground
   - Check logs for connection issues

### Elements not found after app update

Compare your current hierarchy with the reference file:

```bash
diff -u hierarchy_remote_start_active.xml current.xml
```

Update resource IDs in `controller.py` if they've changed.

## Rate Limiting

This endpoint is subject to API rate limiting (30 requests/minute by default). For continuous monitoring, poll no more than once every 30 seconds.

## Security Notes

Remote start status can reveal:
- Whether vehicle is currently running
- Current cabin temperature
- Approximate time engine has been running

Ensure API keys are kept secure and IP whitelist is properly configured.
