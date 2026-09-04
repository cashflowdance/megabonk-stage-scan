# ============================================================================
# ROI SELECTOR TOOL
# ============================================================================

import cv2
import mss
import numpy as np
from typing import Optional, Dict
import json
from pathlib import Path


class ROISelector:
    """Interactive tool for selecting and configuring ROI regions"""
    
    def __init__(self):
        """Initialize ROI selector"""
        self.roi_dict = {}
        self.selecting = False
        self.start_point = None
        self.end_point = None
        self.current_item_name = None
        self.screenshot = None
        self.display_image = None
    
    def mouse_callback(self, event, x, y, flags, param):
        """Mouse callback for selecting ROI"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start_point = (x, y)
            self.selecting = True
            print(f"Selection started at ({x}, {y})")
        
        elif event == cv2.EVENT_MOUSEMOVE and self.selecting:
            self.end_point = (x, y)
            # Update display with rectangle preview
            self._update_display()
        
        elif event == cv2.EVENT_LBUTTONUP:
            self.end_point = (x, y)
            self.selecting = False
            self._update_display()
            self._process_selection()
    
    def _update_display(self):
        """Update display with current selection"""
        self.display_image = self.screenshot.copy()
        
        if self.start_point and self.end_point:
            cv2.rectangle(
                self.display_image,
                self.start_point,
                self.end_point,
                (0, 255, 0),
                2
            )
            
            # Draw info
            x1, y1 = self.start_point
            x2, y2 = self.end_point
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            text = f"({min(x1,x2)}, {min(y1,y2)}) - {width}x{height}"
            cv2.putText(
                self.display_image,
                text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        
        cv2.imshow("ROI Selector", self.display_image)
    
    def _process_selection(self):
        """Process the selected ROI"""
        if not self.start_point or not self.end_point:
            return
        
        x1, y1 = self.start_point
        x2, y2 = self.end_point
        
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        if width > 0 and height > 0:
            roi = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
            
            self.roi_dict[self.current_item_name] = roi
            print(f"\nROI for '{self.current_item_name}' saved:")
            print(f"  left: {left}")
            print(f"  top: {top}")
            print(f"  width: {width}")
            print(f"  height: {height}")
            print()
    
    def capture_screen(self) -> np.ndarray:
        """Capture full screen"""
        with mss.mss() as mss_obj:
            monitor = mss_obj.monitors[1]  # Primary monitor
            screenshot = mss_obj.grab(monitor)
            frame = np.array(screenshot)
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    
    def select_roi_for_item(self, item_name: str):
        """Interactive ROI selection for a specific item"""
        self.current_item_name = item_name
        self.start_point = None
        self.end_point = None
        
        print(f"\n{'='*60}")
        print(f"Selecting ROI for: {item_name}")
        print(f"{'='*60}")
        print("Instructions:")
        print("  1. Click and drag to select ROI")
        print("  2. Release to confirm")
        print("  3. Press 'ESC' to skip")
        print("  4. Press 'C' to confirm and continue")
        print()
        
        self.screenshot = self.capture_screen()
        self.display_image = self.screenshot.copy()
        
        cv2.namedWindow("ROI Selector")
        cv2.setMouseCallback("ROI Selector", self.mouse_callback)
        cv2.imshow("ROI Selector", self.display_image)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):  # Continue
                break
            elif key == 27:  # ESC - skip
                print(f"Skipped ROI selection for {item_name}")
                break
        
        cv2.destroyAllWindows()
    
    def interactive_setup(self, items: list):
        """Interactively setup ROIs for multiple items"""
        print("\n" + "="*60)
        print("MEGABONK STAGE SCAN - ROI SETUP TOOL")
        print("="*60)
        print()
        
        for item_name in items:
            self.select_roi_for_item(item_name)
        
        if self.roi_dict:
            self._save_roi_config()
            return self.roi_dict
        else:
            print("No ROIs were configured.")
            return None
    
    def _save_roi_config(self):
        """Save ROI configuration to file"""
        config_text = "ROW_ROIS = {\n"
        
        for item_name, roi in self.roi_dict.items():
            config_text += f'    "{item_name}": {{\n'
            config_text += f'        "left": {roi["left"]},\n'
            config_text += f'        "top": {roi["top"]},\n'
            config_text += f'        "width": {roi["width"]},\n'
            config_text += f'        "height": {roi["height"]}\n'
            config_text += '    },\n'
        
        config_text += "}"
        
        # Save to file
        output_file = Path("roi_config_generated.py")
        with open(output_file, "w") as f:
            f.write(config_text)
        
        print(f"\nROI configuration saved to: {output_file}")
        print("\nYou can copy the configuration to config.py")
        print()


if __name__ == "__main__":
    import config
    
    selector = ROISelector()
    items = list(config.TARGETS.keys())
    selector.interactive_setup(items)
