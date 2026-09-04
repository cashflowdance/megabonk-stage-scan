# ============================================================================
# GAME LOGIC AND DECISION MAKING MODULE
# ============================================================================

from typing import Dict, Optional, Tuple
import config
import logging

logger = logging.getLogger('megabonk_scan')


class GameLogic:
    """Handles validation and decision making logic"""
    
    def __init__(self):
        """Initialize game logic"""
        self.last_confirmed_result = None
        self.confirmation_buffer = []
    
    def is_valid_ocr_result(self, parsed_data: Dict[str, Dict[str, Optional[int]]]) -> bool:
        """
        Validate OCR results
        
        Returns False if:
        - Any item is missing
        - Any current or max value is None
        - MAX validation fails (if enabled)
        """
        for item_name in config.TARGETS.keys():
            if item_name not in parsed_data:
                logger.warning(f"Item '{item_name}' missing from OCR result")
                return False
            
            item_data = parsed_data[item_name]
            
            # Check if values are present
            if item_data["current"] is None or item_data["max"] is None:
                logger.warning(f"Item '{item_name}' has None values: {item_data}")
                return False
            
            # Check if values are non-negative
            if item_data["current"] < 0 or item_data["max"] < 0:
                logger.warning(f"Item '{item_name}' has negative values: {item_data}")
                return False
            
            # Sanity check: current should not exceed max
            if item_data["current"] > item_data["max"]:
                logger.warning(
                    f"Item '{item_name}': current ({item_data['current']}) > "
                    f"max ({item_data['max']})"
                )
                return False
        
        # Validate MAX values if enabled
        if config.VALIDATE_MAX:
            for item_name in config.TARGETS.keys():
                expected_max = config.EXPECTED_MAX.get(item_name)
                actual_max = parsed_data[item_name]["max"]
                
                if expected_max is not None and actual_max != expected_max:
                    logger.warning(
                        f"Item '{item_name}' MAX mismatch: expected {expected_max}, "
                        f"got {actual_max}"
                    )
                    return False
        
        return True
    
    def check_target_value(self, item_name: str, current_value: int) -> bool:
        """
        Check if a current value matches the target configuration
        
        Returns True if value is WITHIN allowed range/exact value
        Returns False if value is OUTSIDE allowed range/exact value
        """
        target_config = config.TARGETS.get(item_name)
        if not target_config:
            logger.error(f"No target configuration for '{item_name}'")
            return True  # Default to not pressing R
        
        # Check for exact value requirement
        if "exact" in target_config:
            exact_value = target_config["exact"]
            return current_value == exact_value
        
        # Check for range requirement
        if "min" in target_config and "max" in target_config:
            min_val = target_config["min"]
            max_val = target_config["max"]
            return min_val <= current_value <= max_val
        
        # Default: no constraint
        return True
    
    def should_press_r(self, parsed_data: Dict[str, Dict[str, Optional[int]]]) -> bool:
        """
        Determine if R key should be pressed based on current values
        
        Returns True if AT LEAST ONE item is outside allowed range
        Returns False if ALL items are within allowed range
        """
        for item_name in config.TARGETS.keys():
            current_value = parsed_data[item_name]["current"]
            
            if not self.check_target_value(item_name, current_value):
                logger.info(
                    f"Item '{item_name}' outside target range. "
                    f"Current: {current_value}"
                )
                return True
        
        return False
    
    def add_confirmation(self, parsed_data: Dict[str, Dict[str, Optional[int]]]) -> bool:
        """
        Add result to confirmation buffer
        
        Returns True if confirmation buffer is full and all results are identical
        Returns False otherwise
        """
        # Convert parsed_data to tuple for comparison
        data_tuple = self._data_to_tuple(parsed_data)
        self.confirmation_buffer.append(data_tuple)
        
        # Keep buffer size limited
        if len(self.confirmation_buffer) > config.CONFIRMATION_COUNT:
            self.confirmation_buffer.pop(0)
        
        # Check if buffer is full
        if len(self.confirmation_buffer) < config.CONFIRMATION_COUNT:
            return False
        
        # Check if all results are identical
        first_result = self.confirmation_buffer[0]
        all_identical = all(result == first_result for result in self.confirmation_buffer)
        
        if not all_identical:
            logger.debug("Confirmation buffer contains different results. Resetting...")
            self.confirmation_buffer = [data_tuple]  # Keep current result
            return False
        
        return True
    
    def clear_confirmation_buffer(self):
        """Clear confirmation buffer"""
        self.confirmation_buffer = []
    
    def _data_to_tuple(self, parsed_data: Dict[str, Dict[str, Optional[int]]]) -> tuple:
        """Convert parsed data dictionary to hashable tuple for comparison"""
        items = []
        for item_name in sorted(config.TARGETS.keys()):
            current = parsed_data[item_name]["current"]
            max_val = parsed_data[item_name]["max"]
            items.append((item_name, current, max_val))
        return tuple(items)
    
    def get_debug_info(self, parsed_data: Dict[str, Dict[str, Optional[int]]]) -> str:
        """
        Generate detailed debug information
        """
        lines = []
        lines.append("\n=== OCR RESULTS ===")
        
        for item_name in config.TARGETS.keys():
            current = parsed_data[item_name]["current"]
            max_val = parsed_data[item_name]["max"]
            lines.append(f"{item_name}: {current}/{max_val}")
        
        lines.append("\n=== VALIDATION ===")
        
        if not self.is_valid_ocr_result(parsed_data):
            lines.append("OCR Result: INVALID")
            return "\n".join(lines)
        
        lines.append("OCR Result: VALID")
        
        lines.append("\n=== TARGET CHECKS ===")
        for item_name in config.TARGETS.keys():
            current = parsed_data[item_name]["current"]
            target_config = config.TARGETS[item_name]
            
            if "exact" in target_config:
                exact = target_config["exact"]
                matches = current == exact
                status = "✓" if matches else "✗"
                lines.append(f"{status} {item_name}: {current} (exact: {exact})")
            else:
                min_val = target_config["min"]
                max_val = target_config["max"]
                matches = min_val <= current <= max_val
                status = "✓" if matches else "✗"
                lines.append(f"{status} {item_name}: {current} (range: {min_val}..{max_val})")
        
        lines.append("\n=== CONFIRMATION ===")
        lines.append(f"Buffer: {len(self.confirmation_buffer)}/{config.CONFIRMATION_COUNT}")
        
        if len(self.confirmation_buffer) == config.CONFIRMATION_COUNT:
            if self.should_press_r(parsed_data):
                lines.append("Decision: PRESS R")
            else:
                lines.append("Decision: DO NOT PRESS R")
        else:
            lines.append("Decision: WAITING FOR CONFIRMATION")
        
        return "\n".join(lines)
