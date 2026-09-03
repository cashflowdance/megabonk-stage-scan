# ============================================================================
# CONFIGURATION FILE FOR MEGABONK STAGE SCAN
# ============================================================================

# ============================================================================
# 1. TARGET VALUES CONFIGURATION
# ============================================================================

# Define target ranges for each item
# Use "min" and "max" for range validation, or "exact" for strict value
# If both "exact" and "min"/"max" are specified, "exact" takes priority
TARGETS = {
    "Microwaves": {"min": 0, "max": 1},
    "Moais": {"min": 0, "max": 2},
    "Shady Guy": {"min": 0, "max": 5}
}

# Expected MAX values for validation
# If OCR detects a MAX value that doesn't match, it's considered invalid
EXPECTED_MAX = {
    "Microwaves": 1,
    "Moais": 2,
    "Shady Guy": 5
}

# Enable/disable MAX value validation
VALIDATE_MAX = True

# ============================================================================
# 2. REGION OF INTEREST (ROI) CONFIGURATION
# ============================================================================

# Individual ROI for each menu item (for better OCR accuracy)
# Coordinates are in pixels: left, top, width, height
# You can use roi_selector.py to determine these values
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

# Optional: overall menu ROI for debugging
# Leave as None to use individual ROIs
MENU_ROI = None  # {"left": 1450, "top": 260, "width": 400, "height": 200}

# Base screen resolution for scaling
BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080

# Enable ROI scaling based on current screen resolution
USE_ROI_SCALING = True

# ============================================================================
# 3. OCR CONFIGURATION
# ============================================================================

# OCR scaling factor (1x = original size, 2x = 2x upscaling, etc.)
OCR_SCALE = 3

# Preprocessing pipeline mode
# Options: "default", "aggressive", "gentle"
PREPROCESSING_MODE = "default"

# Path to Tesseract executable (if not in system PATH)
# Examples:
# - Windows: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# - Linux: "/usr/bin/tesseract"
# - macOS: "/usr/local/bin/tesseract"
TESSERACT_PATH = None  # Set to None to use system PATH

# ============================================================================
# 4. TIMING CONFIGURATION
# ============================================================================

# Interval between OCR checks (in seconds)
CHECK_INTERVAL = 0.2

# Number of consecutive identical valid results required before acting
CONFIRMATION_COUNT = 3

# Duration to hold R key (in seconds)
# Valid range: > 0
R_HOLD_DURATION = 0.3

# Cooldown duration after R is released (in seconds)
# During cooldown, no new R presses are allowed
R_COOLDOWN = 1.5

# ============================================================================
# 5. AUTOMATION CONTROL
# ============================================================================

# Start with automation enabled or disabled
AUTOMATION_ENABLED_AT_START = False

# ============================================================================
# 6. DEBUG & TEST MODES
# ============================================================================

# Enable debug mode for detailed console output
DEBUG = True

# Enable test mode (R key is never actually pressed)
TEST_MODE = True

# Save debug screenshots to debug/ folder
SAVE_DEBUG_SCREENSHOTS = True

# Frequency of saving debug screenshots (every N frames)
DEBUG_SCREENSHOT_FREQUENCY = 10

# ============================================================================
# 7. LOGGING CONFIGURATION
# ============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "DEBUG"

# Log file path (set to None to disable file logging)
LOG_FILE = "logs/megabonk_scan.log"

# ============================================================================
# 8. HOTKEYS
# ============================================================================

# Hotkey to toggle automation on/off
HOTKEY_TOGGLE_AUTOMATION = "f8"

# Hotkey to exit the program
HOTKEY_EXIT = "esc"

# ============================================================================
# 9. VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration values at startup"""
    errors = []
    
    # Validate R_HOLD_DURATION
    if R_HOLD_DURATION <= 0:
        errors.append("R_HOLD_DURATION must be > 0")
    
    # Validate R_COOLDOWN
    if R_COOLDOWN < 0:
        errors.append("R_COOLDOWN must be >= 0")
    
    # Validate CHECK_INTERVAL
    if CHECK_INTERVAL <= 0:
        errors.append("CHECK_INTERVAL must be > 0")
    
    # Validate CONFIRMATION_COUNT
    if CONFIRMATION_COUNT < 1:
        errors.append("CONFIRMATION_COUNT must be >= 1")
    
    # Validate TARGETS
    for item_name, target_config in TARGETS.items():
        if "exact" in target_config and ("min" in target_config or "max" in target_config):
            errors.append(
                f'TARGETS["{item_name}"]: Cannot specify both "exact" and "min"/"max"'
            )
        
        if "exact" not in target_config:
            if "min" not in target_config or "max" not in target_config:
                errors.append(
                    f'TARGETS["{item_name}"]: Must specify either "exact" or both "min" and "max"'
                )
            elif target_config.get("min", 0) > target_config.get("max", 0):
                errors.append(
                    f'TARGETS["{item_name}"]: min > max is invalid'
                )
    
    # Validate EXPECTED_MAX
    if VALIDATE_MAX:
        if not EXPECTED_MAX:
            errors.append("VALIDATE_MAX is True but EXPECTED_MAX is empty")
        for item_name in TARGETS:
            if item_name not in EXPECTED_MAX:
                errors.append(
                    f'EXPECTED_MAX missing entry for "{item_name}"'
                )
    
    # Validate ROI
    if not ROW_ROIS:
        errors.append("ROW_ROIS is empty")
    for item_name in TARGETS:
        if item_name not in ROW_ROIS:
            errors.append(f'ROW_ROIS missing entry for "{item_name}"')
        else:
            roi = ROW_ROIS[item_name]
            if not all(k in roi for k in ["left", "top", "width", "height"]):
                errors.append(
                    f'ROW_ROIS["{item_name}"]: missing required keys (left, top, width, height)'
                )
    
    if errors:
        error_message = "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_message)
    
    return True


if __name__ == "__main__":
    validate_config()
    print("✓ Configuration is valid!")
