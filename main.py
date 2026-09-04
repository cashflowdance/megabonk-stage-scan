# ============================================================================
# MAIN APPLICATION - MEGABONK STAGE SCAN
# ============================================================================

import sys
import time
import traceback
from typing import Optional, Dict
from pynput import keyboard

import config
from logger_setup import setup_logging
from screen import ScreenCapture
from ocr import OCRProcessor
from logic import GameLogic
from keyboard_control import KeyboardManager
import logging

# Setup logging
logger = setup_logging(config.LOG_LEVEL, config.LOG_FILE)


class MegabonkStageScan:
    """Main application class"""
    
    def __init__(self):
        """Initialize the application"""
        logger.info("Initializing Megabonk Stage Scan...")
        
        # Validate configuration
        try:
            config.validate_config()
            logger.info("✓ Configuration validated")
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        
        # Initialize components
        self.screen_capture = ScreenCapture()
        self.ocr_processor = OCRProcessor()
        self.game_logic = GameLogic()
        self.keyboard_manager = KeyboardManager()
        
        # Application state
        self.automation_enabled = config.AUTOMATION_ENABLED_AT_START
        self.running = True
        self.frame_count = 0
        
        logger.info(f"Automation enabled at start: {self.automation_enabled}")
        logger.info("Application initialized. Ready to start.")
    
    def on_hotkey_toggle_automation(self):
        """Hotkey handler: toggle automation"""
        self.automation_enabled = not self.automation_enabled
        status = "ENABLED" if self.automation_enabled else "DISABLED"
        logger.info(f"Automation {status}")
    
    def on_hotkey_exit(self):
        """Hotkey handler: exit application"""
        logger.info("Exit hotkey pressed")
        self.running = False
    
    def setup_hotkeys(self):
        """Setup hotkey listeners"""
        try:
            listener = keyboard.Listener(
                on_press=self._on_key_press
            )
            listener.start()
            logger.info(f"Hotkeys registered")
            logger.info(f"  F8 - Toggle automation")
            logger.info(f"  ESC - Exit")
            return listener
        except Exception as e:
            logger.error(f"Failed to setup hotkeys: {e}")
            return None
    
    def _on_key_press(self, key):
        """Handle key press events"""
        try:
            if key == keyboard.Key.f8:
                self.on_hotkey_toggle_automation()
            elif key == keyboard.Key.esc:
                self.on_hotkey_exit()
        except AttributeError:
            pass  # Key doesn't have common attributes
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
    
    def process_frame(self) -> bool:
        """
        Process a single frame of game screen
        
        Returns True if processing was successful
        Returns False if an error occurred (but app continues)
        """
        self.frame_count += 1
        
        try:
            # Capture ROI for each item
            captured_data = {}
            for item_name in config.TARGETS.keys():
                roi_image = self.screen_capture.capture_roi(item_name)
                if roi_image is None:
                    logger.warning(f"Failed to capture ROI for {item_name}")
                    return False
                captured_data[item_name] = roi_image
            
            # Extract text from each ROI
            ocr_results = {}
            ocr_text = {}
            for item_name, roi_image in captured_data.items():
                text = self.ocr_processor.extract_text(roi_image)
                if text is None:
                    logger.warning(f"OCR failed for {item_name}")
                    return False
                ocr_text[item_name] = text
                ocr_results[item_name] = text
            
            # Parse OCR results
            parsed_data = self.ocr_processor.parse_menu_text(
                "\n".join([f"{name} {text}" for name, text in ocr_text.items()])
            )
            
            # Validate OCR results
            if not self.game_logic.is_valid_ocr_result(parsed_data):
                logger.debug("OCR result invalid. Waiting for next frame.")
                self.game_logic.clear_confirmation_buffer()
                
                if config.DEBUG:
                    logger.debug(self.game_logic.get_debug_info(parsed_data))
                
                return False
            
            # Add to confirmation buffer
            confirmed = self.game_logic.add_confirmation(parsed_data)
            
            if config.DEBUG:
                logger.debug(self.game_logic.get_debug_info(parsed_data))
            
            # Check if we have confirmed result
            if not confirmed:
                logger.debug(
                    f"Confirmation: {len(self.game_logic.confirmation_buffer)}/"
                    f"{config.CONFIRMATION_COUNT}"
                )
                return True
            
            # Decision point: should we press R?
            should_press = self.game_logic.should_press_r(parsed_data)
            
            logger.info(f"Confirmed result received")
            logger.info(
                f"Decision: {'PRESS R' if should_press else 'DO NOT PRESS R'}"
            )
            
            if should_press:
                # Perform action
                self.perform_press_r_action()
            
            # Clear buffer for next decision
            self.game_logic.clear_confirmation_buffer()
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            logger.debug(traceback.format_exc())
            self.game_logic.clear_confirmation_buffer()
            return False
    
    def perform_press_r_action(self):
        """Perform the R key press action"""
        # Check automation state
        if not self.automation_enabled:
            logger.info("Automation disabled. R will NOT be pressed.")
            return
        
        # Check cooldown
        if self.keyboard_manager.is_in_cooldown():
            remaining = self.keyboard_manager.get_cooldown_remaining()
            logger.info(f"In cooldown. R will NOT be pressed. ({remaining:.2f}s remaining)")
            return
        
        # Check test mode
        if config.TEST_MODE:
            logger.info("[TEST MODE] R key press simulation")
            self.keyboard_manager.test_press_r()
            return
        
        # Actually press R
        success = self.keyboard_manager.press_r()
        if success:
            logger.info("R key pressed successfully")
        else:
            logger.error("Failed to press R key")
    
    def save_debug_screenshots(self):
        """Save debug screenshots if enabled"""
        if not config.SAVE_DEBUG_SCREENSHOTS:
            return
        
        if self.frame_count % config.DEBUG_SCREENSHOT_FREQUENCY != 0:
            return
        
        try:
            full_frame = self.screen_capture.capture_screen()
            self.screen_capture.save_debug_screenshot(
                full_frame,
                f"frame_{self.frame_count}.png"
            )
        except Exception as e:
            logger.error(f"Failed to save debug screenshot: {e}")
    
    def run(self):
        """Main application loop"""
        logger.info("Starting main loop...")
        logger.info(f"TEST_MODE: {config.TEST_MODE}")
        logger.info(f"DEBUG: {config.DEBUG}")
        logger.info(f"AUTOMATION: {self.automation_enabled}")
        logger.info("")
        
        # Setup hotkeys
        hotkey_listener = self.setup_hotkeys()
        
        try:
            while self.running:
                try:
                    # Process one frame
                    self.process_frame()
                    
                    # Save debug screenshots if needed
                    if config.DEBUG:
                        self.save_debug_screenshots()
                    
                    # Sleep for specified interval
                    time.sleep(config.CHECK_INTERVAL)
                
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in main loop: {e}")
                    logger.debug(traceback.format_exc())
                    time.sleep(config.CHECK_INTERVAL)
        
        except Exception as e:
            logger.error(f"Critical error: {e}")
            logger.debug(traceback.format_exc())
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application safely"""
        logger.info("Shutting down...")
        
        # Ensure R key is released
        self.keyboard_manager.ensure_r_released()
        
        logger.info("Application stopped")
    
    def print_banner(self):
        """Print application banner"""
        print("\n" + "="*60)
        print("MEGABONK STAGE SCAN")
        print("Real-time Game Menu OCR Analysis")
        print("="*60)
        print()


def main():
    """Application entry point"""
    app = MegabonkStageScan()
    app.print_banner()
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.debug(traceback.format_exc())
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
