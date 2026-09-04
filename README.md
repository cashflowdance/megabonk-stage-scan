# Megabonk Stage Scan

Real-time game menu OCR analysis with automated keyboard control. This application analyzes a game's menu display in real-time, extracts item counts using OCR, and automatically presses the R key based on configurable target values.

## Features

✓ Real-time OCR screen analysis
✓ Configurable target ranges and exact values
✓ Multiple OCR preprocessing modes for accuracy
✓ Confirmation-based decision making (prevents false triggers)
✓ MAX value validation for OCR error detection
✓ Cooldown system to prevent key spam
✓ Test mode for safe configuration
✓ Debug mode with detailed logging
✓ Interactive ROI setup tool
✓ Hotkey controls (F8 to toggle, ESC to exit)
✓ Comprehensive error handling

## System Requirements

- **OS**: Windows (10 or later) - Mac/Linux may work with modifications
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum
- **Dependencies**: See `requirements.txt`

## Installation

### 1. Install Python

Download and install Python 3.8+ from [python.org](https://www.python.org/downloads/)

Make sure to check "Add Python to PATH" during installation.

### 2. Install Tesseract OCR

**Windows:**

1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run `tesseract-ocr-w64-setup-v5.x.exe`
3. Use default installation path: `C:\Program Files\Tesseract-OCR`
4. Complete the installation

**Verify Tesseract installation:**

```bash
tesseract --version
```

If this doesn't work, add Tesseract to PATH or specify path in `config.py`:

```python
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### 3. Clone/Download this Repository

```bash
git clone <repository-url>
cd megabonk-stage-scan
```

### 4. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

All configuration is in `config.py`. Key settings:

### Target Values

Define what "correct" values are:

```python
TARGETS = {
    "Microwaves": {"min": 0, "max": 1},
    "Moais": {"min": 0, "max": 2},
    "Shady Guy": {"min": 0, "max": 5}
}
```

Or use exact values:

```python
TARGETS = {
    "Microwaves": {"exact": 1},
    "Moais": {"min": 0, "max": 2},
    "Shady Guy": {"exact": 5}
}
```

### Expected MAX Values

For validation (to catch OCR errors):

```python
EXPECTED_MAX = {
    "Microwaves": 1,
    "Moais": 2,
    "Shady Guy": 5
}

VALIDATE_MAX = True  # Enable validation
```

### Timing Settings

```python
CHECK_INTERVAL = 0.2        # Check every 200ms
CONFIRMATION_COUNT = 3      # Require 3 identical confirmations
R_HOLD_DURATION = 0.3       # Hold R for 300ms
R_COOLDOWN = 1.5            # Wait 1.5s before pressing R again
```

### R Key Settings

```python
R_HOLD_DURATION = 0.3       # Duration to hold R key (seconds)
R_COOLDOWN = 1.5            # Cooldown after R release (seconds)
```

### Modes

```python
DEBUG = True                 # Detailed console output
TEST_MODE = True             # Don't actually press R (recommended at first!)
AUTOMATION_ENABLED_AT_START = False  # Start with automation disabled
```

## ROI (Region of Interest) Setup

Before running the app, you need to define where on the screen to look for menu items.

### Option 1: Interactive ROI Selector (Easiest)

```bash
python roi_selector.py
```

Instructions:
1. A screenshot will appear
2. Click and drag to select the menu area for each item
3. Press 'C' to confirm and move to next item
4. Configuration will be saved to `roi_config_generated.py`
5. Copy the output to `config.py`'s `ROW_ROIS` section

### Option 2: Manual Configuration

Edit `config.py` and update `ROW_ROIS`:

```python
ROW_ROIS = {
    "Microwaves": {
        "left": 1500,
        "top": 280,
        "width": 350,
        "height": 50
    },
    "Moais": {
        "left": 1500,
        "top": 340,
        "width": 350,
        "height": 50
    },
    "Shady Guy": {
        "left": 1500,
        "top": 400,
        "width": 350,
        "height": 50
    }
}
```

**Finding coordinates:**
- Use Windows Snipping Tool or similar to take screenshot
- Measure pixel coordinates from top-left corner
- Make sure ROI includes the text but minimizes background noise

### ROI Scaling

If running on different screen resolutions:

```python
BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080
USE_ROI_SCALING = True  # Automatically scale ROIs
```

## Running the Application

### Step 1: Verify Setup

```bash
python -c "import config; config.validate_config(); print('Config OK')"
```

### Step 2: Start in TEST_MODE

Always start with TEST_MODE enabled:

```python
TEST_MODE = True
DEBUG = True
```

Run:

```bash
python main.py
```

You should see:
- OCR results being extracted
- Target validation
- "[TEST MODE] Would press R for..." messages

### Step 3: Verify Accuracy

1. Watch the debug output
2. Confirm OCR is recognizing items correctly
3. Confirm decision logic is working as expected
4. Check that values match what's on screen

### Step 4: Enable Live Mode

Once satisfied, set:

```python
TEST_MODE = False
DEBUG = False  # Optional: reduce verbosity
```

Run again:

```bash
python main.py
```

### Step 5: Control During Runtime

- **F8**: Toggle automation ON/OFF
- **ESC**: Exit program

## Debug Output

When `DEBUG = True`, you'll see:

```
[INFO] | 14:32:15 | OCR Results
Microwaves: 0/1
Modais: 0/2
Shady Guy: 0/5

[DEBUG] | 14:32:15 | Target Checks
✓ Microwaves: 0 (range: 0..1)
✓ Moais: 0 (range: 0..2)
✓ Shady Guy: 0 (range: 0..5)

[INFO] | 14:32:15 | Decision: DO NOT PRESS R
```

## Troubleshooting

### "No module named 'tesseract'"

Tesseract is not installed. Follow the Installation section above.

### "Tesseract is not installed or cannot be found"

Add path to `config.py`:

```python
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### OCR Results are Inaccurate

1. Check ROI is correctly positioned
2. Try different `PREPROCESSING_MODE`:
   - `"default"` - balanced
   - `"aggressive"` - for low contrast
   - `"gentle"` - for high contrast

3. Increase `OCR_SCALE`:
   ```python
   OCR_SCALE = 4  # Try 4x or 5x scaling
   ```

4. Enable debug screenshots to see what's being OCR'd:
   ```python
   SAVE_DEBUG_SCREENSHOTS = True
   ```
   Check `debug/` folder for screenshots

### R Key Not Pressing

1. Check `AUTOMATION_ENABLED_AT_START = True` or press F8
2. Verify `TEST_MODE = False`
3. Ensure program window has focus
4. Check cooldown isn't active (shown in debug output)

### Program Crashes

1. Check Python version: `python --version` (should be 3.8+)
2. Verify all dependencies: `pip install -r requirements.txt`
3. Run with error details:
   ```bash
   python main.py 2>&1 | tee output.log
   ```

## Testing

Run unit tests:

```bash
python -m pytest tests/
```

Or:

```bash
python tests/test_logic.py
```

Tests include:
- OCR text parsing
- Target validation logic
- Confirmation buffer behavior
- MAX value validation
- Decision making (press vs don't press)

## Project Structure

```
megabonk-stage-scan/
├── main.py                 # Main application
├── config.py               # All configuration
├── logger_setup.py         # Logging configuration
├── screen.py               # Screen capture & ROI handling
├── ocr.py                  # OCR & text parsing
├── logic.py                # Decision making
├── keyboard_control.py     # R key control
├── roi_selector.py         # Interactive ROI setup tool
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── tests/
│   └── test_logic.py       # Unit tests
├── logs/                   # Log files (created automatically)
└── debug/                  # Debug screenshots (created automatically)
```

## Safety Guarantees

The application is designed with safety as the highest priority:

- ✓ R key only pressed if ALL conditions are met:
  - Valid OCR result
  - All 3 rows detected
  - MAX validation passed (if enabled)
  - 3 identical confirmations
  - Automation enabled
  - Not in cooldown
  - Test mode disabled

- ✓ Any doubt → Do nothing (conservative approach)
- ✓ R key always released, even on crash
- ✓ Emergency shutdown with ESC key
- ✓ Cooldown prevents key spam

## Performance Notes

- **CPU**: ~5-10% usage (depends on OCR_SCALE)
- **RAM**: ~150-250MB
- **Latency**: ~500-1000ms (3 confirmations × 200ms check interval)

## Advanced Configuration

### Exact Value Matching

```python
TARGETS = {
    "Microwaves": {"exact": 1},      # Must be exactly 1
    "Moais": {"min": 0, "max": 2},   # Range
    "Shady Guy": {"exact": 5}        # Must be exactly 5
}
```

### Custom Preprocessing

Edit `config.py`:

```python
PREPROCESSING_MODE = "aggressive"  # Better for low contrast
OCR_SCALE = 4                       # Larger scale = more accuracy
```

### Logging to File

```python
LOG_FILE = "logs/megabonk_scan.log"
LOG_LEVEL = "DEBUG"
```

## Common Scenarios

### Scenario 1: Press R when ANY item exceeds target

```python
TARGETS = {
    "Microwaves": {"max": 1},
    "Moais": {"max": 2},
    "Shady Guy": {"max": 5}
}
# If any current > max → Press R
```

### Scenario 2: Press R when all items reach exact values

```python
TARGETS = {
    "Microwaves": {"exact": 1},
    "Moais": {"exact": 2},
    "Shady Guy": {"exact": 5}
}
# All must match exactly → Press R
```

### Scenario 3: Mixed strategy

```python
TARGETS = {
    "Microwaves": {"exact": 1},      # Exact
    "Moais": {"min": 1, "max": 2},    # Range
    "Shady Guy": {"min": 0, "max": 5} # Range
}
```

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions:

1. Check the Troubleshooting section above
2. Enable `DEBUG = True` for detailed output
3. Check log files in `logs/` directory
4. Verify configuration with: `python config.py`

---

**Remember**: Always test with `TEST_MODE = True` first!
