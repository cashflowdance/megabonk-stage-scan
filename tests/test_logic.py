# ============================================================================
# UNIT TESTS FOR MEGABONK STAGE SCAN
# ============================================================================

import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from logic import GameLogic
from ocr import OCRProcessor


class TestParseMenu(unittest.TestCase):
    """Test cases for menu text parsing"""
    
    def setUp(self):
        self.processor = OCRProcessor()
    
    def test_parse_simple_format(self):
        """Test parsing simple format: '0/1'"""
        text = "Microwaves 0/1\nMoais 0/2\nShady Guy 0/5"
        result = self.processor.parse_menu_text(text)
        
        self.assertEqual(result["Microwaves"]["current"], 0)
        self.assertEqual(result["Microwaves"]["max"], 1)
        self.assertEqual(result["Moais"]["current"], 0)
        self.assertEqual(result["Moais"]["max"], 2)
        self.assertEqual(result["Shady Guy"]["current"], 0)
        self.assertEqual(result["Shady Guy"]["max"], 5)
    
    def test_parse_with_spaces(self):
        """Test parsing with spaces: '0 / 1'"""
        text = "Microwaves 0 / 1\nMoais 1 / 2\nShady Guy 3 / 5"
        result = self.processor.parse_menu_text(text)
        
        self.assertEqual(result["Microwaves"]["current"], 0)
        self.assertEqual(result["Microwaves"]["max"], 1)
        self.assertEqual(result["Moais"]["current"], 1)
        self.assertEqual(result["Moais"]["max"], 2)
    
    def test_parse_incomplete_data(self):
        """Test parsing with missing data"""
        text = "Microwaves 0/1\nMoais invalid\nShady Guy 0/5"
        result = self.processor.parse_menu_text(text)
        
        self.assertEqual(result["Microwaves"]["current"], 0)
        self.assertIsNone(result["Moais"]["current"])
        self.assertEqual(result["Shady Guy"]["current"], 0)


class TestGameLogic(unittest.TestCase):
    """Test cases for game logic"""
    
    def setUp(self):
        self.logic = GameLogic()
        # Create valid parsed data
        self.valid_data = {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": 0, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
    
    def test_valid_ocr_result(self):
        """Test validation of valid OCR result"""
        self.assertTrue(self.logic.is_valid_ocr_result(self.valid_data))
    
    def test_invalid_ocr_missing_item(self):
        """Test validation fails when item is missing"""
        invalid_data = {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": 0, "max": 2}
        }
        self.assertFalse(self.logic.is_valid_ocr_result(invalid_data))
    
    def test_invalid_ocr_none_values(self):
        """Test validation fails when values are None"""
        invalid_data = {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": None, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
        self.assertFalse(self.logic.is_valid_ocr_result(invalid_data))
    
    def test_invalid_ocr_current_exceeds_max(self):
        """Test validation fails when current > max"""
        invalid_data = {
            "Microwaves": {"current": 2, "max": 1},
            "Moais": {"current": 0, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
        self.assertFalse(self.logic.is_valid_ocr_result(invalid_data))
    
    def test_check_target_range_valid(self):
        """Test target check with valid range"""
        # Microwaves: 0..1
        self.assertTrue(self.logic.check_target_value("Microwaves", 0))
        self.assertTrue(self.logic.check_target_value("Microwaves", 1))
        self.assertFalse(self.logic.check_target_value("Microwaves", 2))
    
    def test_check_target_exact(self):
        """Test target check with exact value"""
        # Create config with exact value
        original_targets = config.TARGETS.copy()
        config.TARGETS["Microwaves"] = {"exact": 1}
        
        self.assertTrue(self.logic.check_target_value("Microwaves", 1))
        self.assertFalse(self.logic.check_target_value("Microwaves", 0))
        self.assertFalse(self.logic.check_target_value("Microwaves", 2))
        
        # Restore original
        config.TARGETS = original_targets
    
    def test_should_press_r_all_valid(self):
        """Test decision: all values valid -> NO PRESS"""
        data = {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": 1, "max": 2},
            "Shady Guy": {"current": 3, "max": 5}
        }
        self.assertFalse(self.logic.should_press_r(data))
    
    def test_should_press_r_one_invalid(self):
        """Test decision: one value invalid -> PRESS"""
        data = {
            "Microwaves": {"current": 2, "max": 1},  # Outside range
            "Moais": {"current": 1, "max": 2},
            "Shady Guy": {"current": 3, "max": 5}
        }
        self.assertTrue(self.logic.should_press_r(data))
    
    def test_should_press_r_multiple_invalid(self):
        """Test decision: multiple values invalid -> PRESS"""
        data = {
            "Microwaves": {"current": 2, "max": 1},  # Outside
            "Moais": {"current": 3, "max": 2},      # Outside
            "Shady Guy": {"current": 3, "max": 5}
        }
        self.assertTrue(self.logic.should_press_r(data))
    
    def test_confirmation_buffer_identical(self):
        """Test confirmation with identical results"""
        data = {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": 0, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
        
        # Add same data three times
        self.assertFalse(self.logic.add_confirmation(data))
        self.assertFalse(self.logic.add_confirmation(data))
        self.assertTrue(self.logic.add_confirmation(data))  # Third time -> confirmed
    
    def test_confirmation_buffer_different(self):
        """Test confirmation with different results"""
        data1 = {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": 0, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
        
        data2 = {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": 1, "max": 2},  # Different
            "Shady Guy": {"current": 0, "max": 5}
        }
        
        self.assertFalse(self.logic.add_confirmation(data1))
        self.assertFalse(self.logic.add_confirmation(data2))  # Different -> reset
        self.assertFalse(self.logic.add_confirmation(data1))
    
    def test_confirmation_buffer_clear(self):
        """Test clearing confirmation buffer"""
        data = {
            "Microwaves": {"current": 0, "max": 1},
            "Moais": {"current": 0, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
        
        self.logic.add_confirmation(data)
        self.logic.add_confirmation(data)
        self.assertEqual(len(self.logic.confirmation_buffer), 2)
        
        self.logic.clear_confirmation_buffer()
        self.assertEqual(len(self.logic.confirmation_buffer), 0)
    
    def test_max_validation_disabled(self):
        """Test that MAX validation can be disabled"""
        original_validate = config.VALIDATE_MAX
        config.VALIDATE_MAX = False
        
        # Data with wrong MAX should still be valid
        data = {
            "Microwaves": {"current": 0, "max": 999},  # Wrong MAX
            "Moais": {"current": 0, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
        
        self.assertTrue(self.logic.is_valid_ocr_result(data))
        config.VALIDATE_MAX = original_validate
    
    def test_max_validation_enabled(self):
        """Test that MAX validation works when enabled"""
        original_validate = config.VALIDATE_MAX
        config.VALIDATE_MAX = True
        
        # Data with wrong MAX should be invalid
        data = {
            "Microwaves": {"current": 0, "max": 999},  # Wrong MAX
            "Moais": {"current": 0, "max": 2},
            "Shady Guy": {"current": 0, "max": 5}
        }
        
        self.assertFalse(self.logic.is_valid_ocr_result(data))
        config.VALIDATE_MAX = original_validate


if __name__ == "__main__":
    unittest.main()
