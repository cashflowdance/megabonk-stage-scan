# ============================================================================
# SCREEN CAPTURE AND ROI MANAGEMENT MODULE
# ============================================================================

import mss
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import config
import logging

logger = logging.getLogger('megabonk_scan')


class ScreenCapture:
    """Handles screen capture and ROI extraction"""
    
    def __init__(self):
        """Initialize screen capture"""
        self.mss = mss.mss()
        self.current_screen_width = None
        self.current_screen_height = None
        self._update_screen_dimensions()
        self.scaled_rois = self._compute_scaled_rois()
    
    def _update_screen_dimensions(self):
        """Update current screen dimensions"""
        primary_monitor = self.mss.monitors[1]
        self.current_screen_width = primary_monitor["width"]
        self.current_screen_height = primary_monitor["height"]
    
    def _compute_scaled_rois(self) -> Dict[str, Dict[str, int]]:
        """Compute ROI coordinates scaled to current screen resolution"""
        if not config.USE_ROI_SCALING:
            return config.ROW_ROIS.copy()
        
        scale_x = self.current_screen_width / config.BASE_SCREEN_WIDTH
        scale_y = self.current_screen_height / config.BASE_SCREEN_HEIGHT
        
        scaled_rois = {}
        for item_name, roi in config.ROW_ROIS.items():
            scaled_rois[item_name] = {
                "left": int(roi["left"] * scale_x),
                "top": int(roi["top"] * scale_y),
                "width": int(roi["width"] * scale_x),
                "height": int(roi["height"] * scale_y)
            }
        
        return scaled_rois
    
    def capture_screen(self) -> np.ndarray:
        """Capture entire screen"""
        screenshot = self.mss.grab(self.mss.monitors[0])
        frame = np.array(screenshot)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    
    def capture_roi(self, item_name: str) -> Optional[np.ndarray]:
        """Capture specific ROI for an item"""
        if item_name not in self.scaled_rois:
            logger.warning(f"Item '{item_name}' not found in ROI configuration")
            return None
        
        roi = self.scaled_rois[item_name]
        monitor = {
            "left": roi["left"],
            "top": roi["top"],
            "width": roi["width"],
            "height": roi["height"]
        }
        
        try:
            screenshot = self.mss.grab(monitor)
            frame = np.array(screenshot)
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            logger.error(f"Failed to capture ROI for '{item_name}': {e}")
            return None
    
    def save_debug_screenshot(self, frame: np.ndarray, filename: str):
        """Save screenshot for debugging"""
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        
        filepath = debug_dir / filename
        cv2.imwrite(str(filepath), frame)
        logger.debug(f"Saved debug screenshot: {filepath}")
    
    def save_roi_screenshots(self, full_frame: np.ndarray, frame_number: int):
        """Save individual ROI screenshots for debugging"""
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        
        for item_name in config.TARGETS.keys():
            roi = self.scaled_rois[item_name]
            roi_frame = full_frame[
                roi["top"]:roi["top"] + roi["height"],
                roi["left"]:roi["left"] + roi["width"]
            ]
            
            filepath = debug_dir / f"{item_name}.png"
            cv2.imwrite(str(filepath), roi_frame)
