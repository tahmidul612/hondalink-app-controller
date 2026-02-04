# Remote Command Processing - Testing Guide

## Overview

This guide helps you verify the new 30-second remote command processing logic with your actual Android device and HondaLink app.

## What Changed

### Before
- Command execution waited only 8 seconds
- No detection of processing UI or command completion
- Assumed success if no error popup appeared
- Could return success while command was still processing

### After
- Waits up to 30 seconds for command to complete
- Detects processing UI ("Sending command…", "Contacting server…")
- Detects failure dialogs ("Remote Command Failed")
- Verifies success state (for remote start: checks timer/temperature)
- Returns descriptive error messages on failure

## Test Scenarios

### Test 1: Successful Remote Start

**Setup:**
- Car is OFF and parked
- HondaLink app is logged in
- Remote start has NOT been used twice consecutively

**Steps:**
1. Start the server: `uv run uvicorn src.hondalink.main:app --host 0.0.0.0 --port 8000`
2. Execute command: `curl -X POST http://localhost:8000/action/start`
3. **Watch the phone screen** - you should see:
   - Processing UI with "Sending command…" or "Contacting server…"
   - Processing may take 10-25 seconds (this is normal)
4. Wait for response

**Expected Result:**
```json
{
  "status": "success",
  "message": "Remote start successful"
}
```

**Log Output:**
```
INFO:hondalink.controller:Clicking command button: Start
INFO:hondalink.controller:Waiting for command start to complete (timeout: 30.0s)
DEBUG:hondalink.controller:Still processing: Sending command… (2.3s elapsed)
DEBUG:hondalink.controller:Still processing: Contacting server… (5.7s elapsed)
INFO:hondalink.controller:Remote start confirmed active
INFO:hondalink.controller:Command start executed: Remote start successful
```

**Verification:**
- Car engine should start
- Check `/remote-start/status` endpoint shows active session with timer

### Test 2: Failed Remote Start (Max Attempts)

**Setup:**
- Car is already remote started
- Extend remote start once (2nd consecutive start)
- Try to start/extend a 3rd time (should fail)

**Steps:**
1. Start car remotely twice (start → extend)
2. Try 3rd remote start: `curl -X POST http://localhost:8000/action/start`
3. **Watch the phone screen** - you should see:
   - Processing UI briefly
   - Then "Remote Command Failed" dialog with message

**Expected Result:**
```json
{
  "status": "error",
  "message": "Command failed: Maximum start requests reached. Please reset by turning the car ON then OFF. Remote Engine Start not executed."
}
```

**Log Output:**
```
INFO:hondalink.controller:Clicking command button: Start
INFO:hondalink.controller:Waiting for command start to complete (timeout: 30.0s)
DEBUG:hondalink.controller:Still processing: Sending command… (1.2s elapsed)
ERROR:hondalink.controller:Command failed: Maximum start requests reached...
ERROR:hondalink.controller:Execution failed: Command failed: Maximum start requests...
```

**Verification:**
- Car does NOT start
- Error message explains why (max attempts)
- OK button was clicked automatically to dismiss dialog

### Test 3: Timeout Scenario

**Setup:**
- Poor network connection OR server issues

**Steps:**
1. Turn off WiFi or use airplane mode
2. Try remote command: `curl -X POST http://localhost:8000/action/lock`
3. Processing should hang

**Expected Result (after 30 seconds):**
```json
{
  "status": "error",
  "message": "Command timeout after 30 seconds"
}
```

**Log Output:**
```
INFO:hondalink.controller:Waiting for command lock to complete (timeout: 30.0s)
DEBUG:hondalink.controller:Still processing: Contacting server… (15.3s elapsed)
DEBUG:hondalink.controller:Still processing: Contacting server… (28.9s elapsed)
WARNING:hondalink.controller:Command processing timeout after 30s
```

### Test 4: Quick Success (Lock/Unlock)

**Setup:**
- Good network connection
- Car is unlocked

**Steps:**
1. Execute lock: `curl -X POST http://localhost:8000/action/lock`
2. Should complete quickly (2-5 seconds)

**Expected Result:**
```json
{
  "status": "success",
  "message": "Command lock executed successfully"
}
```

**Notes:**
- Lock/Unlock commands typically complete faster than remote start
- Processing UI may appear briefly or not at all

## Debugging Failed Tests

### If processing never completes:

1. **Check network connection**
   - Ensure phone has stable WiFi/cellular
   - Try `/status` endpoint to verify app communication

2. **Check app state**
   - Use `/debug/hierarchy` to see current UI
   - Look for stuck dialogs or unexpected screens

3. **Check logs**
   - Enable debug logging: `export LOG_LEVEL=DEBUG`
   - Look for "Still processing" messages

### If wrong elements detected:

1. **Dump UI hierarchy during processing**
   - Run command, quickly call `/debug/hierarchy`
   - Compare resource IDs with expected values:
     - Processing: `com.honda.hondalink.connect:id/remote_command_progress_message`
     - Failure: `com.honda.hondalink.connect:id/alertTitle`
     - Success (START): `com.honda.hondalink.connect:id/text_success_timer`

2. **Update resource IDs if changed**
   - If app version updated and IDs changed, modify `controller.py`
   - Search for resource ID strings and update accordingly

### If timeout too short/long:

**Adjust timeout in `controller.py`:**
```python
success, message = self._wait_for_command_completion(command, timeout=45.0)  # Increase to 45s
```

## Performance Benchmarks

Expected processing times (real device):

| Command | Typical | Maximum |
|---------|---------|---------|
| Lock | 2-5s | 10s |
| Unlock | 2-5s | 10s |
| Remote Start | 10-20s | 30s |
| Stop Engine | 3-8s | 15s |

## Common Issues

### Issue: "Processing completed, no failure detected" but car didn't start

**Cause:** Success detection failed (timer/temp elements not found)

**Solution:**
1. Check if resource IDs changed: `/debug/hierarchy` after command
2. Verify car is eligible for remote start (not already running, etc.)
3. Check HondaLink app manually - did it show success?

### Issue: Commands always timeout at 30 seconds

**Cause:** Processing UI never disappears OR success indicators not detected

**Solutions:**
1. Check if `remote_command_progress_message` ID still valid
2. Ensure app is on main dashboard (not stuck in menu)
3. Verify network connectivity

### Issue: Failure dialogs not detected

**Cause:** Dialog resource IDs changed or different error format

**Solution:**
1. Capture hierarchy when error appears: `/debug/hierarchy`
2. Look for dialog title element
3. Update `_check_command_failure_dialog()` with correct IDs

## Manual Verification Steps

### 1. Verify Processing Detection
```bash
# Start command
curl -X POST http://localhost:8000/action/start &

# Immediately dump hierarchy (within 1-2 seconds)
sleep 1 && curl http://localhost:8000/debug/hierarchy > processing.xml

# Check for processing UI
grep "remote_command_progress_message" processing.xml
```

### 2. Verify Success Detection
```bash
# After command completes successfully
curl http://localhost:8000/remote-start/status

# Should show active with timer if remote start
```

### 3. Verify Failure Detection
```bash
# Trigger max attempts error (3rd consecutive start)
curl -X POST http://localhost:8000/action/start  # 1st
curl -X POST http://localhost:8000/action/start  # 2nd (extend)
curl -X POST http://localhost:8000/action/start  # 3rd (should fail)

# Should return error with descriptive message
```

## Adjusting for Your Environment

### Faster Network
If your commands complete quickly (< 5 seconds consistently):
- Reduce `poll_interval` in `_wait_for_command_completion()` from 0.5s to 0.2s

### Slower Network
If commands often take 25-30 seconds:
- Increase timeout from 30s to 45s
- Reduce `poll_interval` to save log spam

### Different App Version
If HondaLink app updated and resource IDs changed:
1. Capture hierarchy during each phase (processing/success/failure)
2. Update resource IDs in `controller.py`:
   - Line ~167: `remote_command_progress_message`
   - Line ~143: `alertTitle`
   - Line ~297-298: `text_success_timer`, `remote_command_inside_temp`

## Success Criteria

✅ All test scenarios pass
✅ Processing time logged accurately
✅ Failure messages are descriptive
✅ No false positives (success when actually failed)
✅ No false negatives (failure when actually succeeded)
✅ Timeout works correctly (30s max)
✅ Retry mechanism still functions (3 attempts on failure)

## Reporting Issues

If you find issues during testing, provide:
1. Log output (with DEBUG level enabled)
2. UI hierarchy dump at time of issue
3. Expected vs actual behavior
4. HondaLink app version
5. Network conditions (WiFi/LTE, signal strength)
