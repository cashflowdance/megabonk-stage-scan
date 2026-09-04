# ============================================================================
# KEYBOARD CONTROL MODULE
# ============================================================================

import time
from typing import Optional
import pynput
from pynput.keyboard import Controller, Key
import config
import logging

logger = logging.getLogger('megabonk_scan')

keyboard = Controller()


class KeyboardManager:
    """Manages keyboard input and R key pressing"""
    
    def __init__(self):
        """Initialize keyboard manager"""
        self.r_pressed = False
        self.last_r_press_time = 0
        self.in_cooldown = False
    
    def is_in_cooldown(self) -> bool:
        """Check if currently in cooldown period"""
        if not self.in_cooldown:
            return False
        
        elapsed = time.time() - self.last_r_press_time
        if elapsed >= config.R_COOLDOWN:
            self.in_cooldown = False
            logger.info("Cooldown period ended")
            return False
        
        return True
    
    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in seconds"""
        if not self.in_cooldown:
            return 0
        
        elapsed = time.time() - self.last_r_press_time
        remaining = config.R_COOLDOWN - elapsed
        return max(0, remaining)
    
    def press_r(self) -> bool:
        """
        Press and hold R key for specified duration
        
        Returns True if R was successfully pressed
        Returns False if in cooldown or other error
        """
        if self.is_in_cooldown():
            remaining = self.get_cooldown_remaining()
            logger.warning(f"Cannot press R: cooldown active ({remaining:.2f}s remaining)")
            return False
        
        try:
            logger.info(f"Pressing R for {config.R_HOLD_DURATION} seconds...")
            
            # Press R
            keyboard.press('r')
            self.r_pressed = True
            logger.debug("R key pressed down")
            
            # Hold for specified duration
            time.sleep(config.R_HOLD_DURATION)
            
            # Release R
            keyboard.release('r')
            self.r_pressed = False
            logger.debug("R key released")
            
            # Record time and start cooldown
            self.last_r_press_time = time.time()
            self.in_cooldown = True
            logger.info(f"Starting {config.R_COOLDOWN}s cooldown period")
            
            return True
        
        except Exception as e:
            logger.error(f"Error while pressing R: {e}")
            # Ensure R is released even if error occurs
            try:
                keyboard.release('r')
                self.r_pressed = False
            except:
                pass
            return False
    
    def ensure_r_released(self):
        """Ensure R key is released (for emergency shutdown)"""
        if self.r_pressed:
            try:
                keyboard.release('r')
                self.r_pressed = False
                logger.info("R key released (emergency)")
            except Exception as e:
                logger.error(f"Failed to release R key: {e}")
    
    def test_press_r(self):
        """
        Test mode: simulate R press without actually pressing
        """
        logger.info(f"[TEST MODE] Would press R for {config.R_HOLD_DURATION} seconds")
        # Update cooldown state anyway
        self.last_r_press_time = time.time()
        self.in_cooldown = True
        logger.info(f"[TEST MODE] Starting {config.R_COOLDOWN}s cooldown period")
