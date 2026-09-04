# ============================================================================
# OCR AND TEXT PARSING MODULE
# ============================================================================

import cv2
import numpy as np
import pytesseract
import re
from typing import Dict, Optional, Tuple
from pathlib import Path
import config
import logging

logger = logging.getLogger('megabonk_scan')

# Configure Tesseract path if specified
if config.TESSERACT_PATH:
    pytesseract.pytesseract.pytesseract_cmd = config.TESSERACT_PATH


class OCRProcessor:
    """Handles OCR preprocessing and text extraction"""
    
    def __init__(self):
        """Initialize OCR processor"""
        self.frame_count = 0
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Apply preprocessing pipeline to improve OCR accuracy"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Upscale image
        scaled = cv2.resize(gray, None, fx=config.OCR_SCALE, fy=config.OCR_SCALE, 
                           interpolation=cv2.INTER_CUBIC)
        
        if config.PREPROCESSING_MODE == "aggressive":
            # Aggressive preprocessing
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(scaled)
            
            # Apply bilateral filter to reduce noise while keeping edges
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # Apply adaptive threshold
            binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            return binary
        
        elif config.PREPROCESSING_MODE == "gentle":
            # Gentle preprocessing
            # Simple threshold
            _, binary = cv2.threshold(scaled, 150, 255, cv2.THRESH_BINARY)
            return binary
        
        else:  # default
            # Balanced preprocessing
            # Denoise
            denoised = cv2.fastNlMeansDenoising(scaled, None, h=10)
            
            # Apply adaptive threshold
            binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
            
            return binary
    
    def extract_text(self, image: np.ndarray) -> Optional[str]:
        """Extract text from image using Tesseract"""
        try:
            preprocessed = self.preprocess_image(image)
            text = pytesseract.image_to_string(preprocessed)
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return None
    
    def parse_menu_text(self, text: str) -> Dict[str, Dict[str, Optional[int]]]:
        """
        Parse OCR text to extract item names and values
        
        Expected format:
        Microwaves 0/1
        Moais 0/2
        Shady Guy 0/5
        
        Returns:
        {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": 0, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
        """
        result = {}
        
        for item_name in config.TARGETS.keys():
            result[item_name] = {"current": None, "max": None}
        
        # Clean text: remove extra whitespace, convert to standard format
        text = text.strip()
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to match each item
            for item_name in config.TARGETS.keys():
                if item_name.lower() in line.lower():
                    # Extract numbers from line
                    # Pattern: "CURRENT / MAX" or "CURRENT/MAX"
                    match = re.search(r'(\d+)\s*\/\s*(\d+)', line)
                    if match:
                        try:
                            current = int(match.group(1))
                            max_val = int(match.group(2))
                            result[item_name]["current"] = current
                            result[item_name]["max"] = max_val
                        except ValueError:
                            logger.warning(f"Failed to parse numbers from line: {line}")
                    break
        
        return result


def parse_menu(text: str) -> Dict[str, Dict[str, Optional[int]]]:
    """Convenience function to parse menu text"""
    processor = OCRProcessor()
    return processor.parse_menu_text(text)
