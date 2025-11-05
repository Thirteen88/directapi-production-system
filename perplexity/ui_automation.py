"""
Perplexity UI Automation via Termux/ADB

Provides UI automation fallback for Perplexity app when API is unavailable.
Uses ADB commands, clipboard monitoring, and screenshot OCR for interaction.

Usage:
    from ui_automation import PerplexityUIAutomation

    automator = PerplexityUIAutomation()
    response = automator.send_query("What is quantum computing?")
    print(response)
"""

import os
import time
import json
import logging
import subprocess
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from pathlib import Path


class ADBError(Exception):
    """ADB command execution error"""
    pass


class UIAutomationError(Exception):
    """UI automation specific error"""
    pass


class PerplexityUIAutomation:
    """
    Perplexity app UI automation using ADB commands.

    Features:
    - App launching via intents
    - Text input via ADB input commands
    - Clipboard monitoring for responses
    - Screenshot OCR fallback
    - Notification content parsing
    - Error recovery and retry logic
    - Session management

    Example:
        automator = PerplexityUIAutomation()

        # Simple query
        response = automator.send_query("What is AI?")
        print(response)

        # With retry
        response = automator.send_query_with_retry(
            "Complex question",
            max_retries=3
        )
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize UI automation.

        Args:
            config_path: Path to config.json file
            logger: Custom logger instance
        """
        self.logger = logger or self._setup_logger()
        self.config = self._load_config(config_path)
        self.ui_config = self.config["ui_automation"]

        # Check ADB availability
        if not self._check_adb():
            raise RuntimeError("ADB not available. Install android-tools in Termux.")

        self.logger.info("Perplexity UI Automation initialized")

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger("PerplexityUI")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from JSON file"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "config.json"
            )

        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}")
            raise

    def _check_adb(self) -> bool:
        """Check if ADB is available"""
        try:
            result = subprocess.run(
                ["which", "adb"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_adb_command(
        self,
        command: List[str],
        timeout: int = 30,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run ADB command and return result.

        Args:
            command: ADB command as list of strings
            timeout: Command timeout in seconds
            check: Whether to raise exception on non-zero exit

        Returns:
            CompletedProcess object

        Raises:
            ADBError: If command fails and check=True
        """
        full_command = ["adb"] + command
        self.logger.debug(f"Running ADB command: {' '.join(full_command)}")

        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ADB command failed: {e.stderr}")
            raise ADBError(f"ADB command failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            self.logger.error(f"ADB command timed out after {timeout}s")
            raise ADBError(f"ADB command timed out")

    def launch_app(self) -> bool:
        """
        Launch Perplexity app via intent.

        Returns:
            True if successful, False otherwise
        """
        app_config = self.ui_config["app"]
        package = app_config["package"]
        activity = app_config["activity"]
        timeout = app_config["launch_timeout"]

        self.logger.info(f"Launching Perplexity app: {package}")

        try:
            # Launch app
            self._run_adb_command([
                "shell", "am", "start",
                "-n", f"{package}/{activity}",
                "-a", "android.intent.action.MAIN",
                "-c", "android.intent.category.LAUNCHER"
            ])

            # Wait for app to load
            time.sleep(timeout)

            # Verify app is running
            result = self._run_adb_command([
                "shell", "pidof", package
            ], check=False)

            if result.returncode == 0 and result.stdout.strip():
                self.logger.info("App launched successfully")
                return True
            else:
                self.logger.warning("App may not have launched properly")
                return False

        except ADBError as e:
            self.logger.error(f"Failed to launch app: {str(e)}")
            return False

    def close_app(self) -> bool:
        """
        Force stop Perplexity app.

        Returns:
            True if successful
        """
        package = self.ui_config["app"]["package"]
        self.logger.info(f"Closing app: {package}")

        try:
            self._run_adb_command([
                "shell", "am", "force-stop", package
            ])
            time.sleep(1)
            return True
        except ADBError:
            return False

    def restart_app(self) -> bool:
        """
        Restart Perplexity app.

        Returns:
            True if successful
        """
        self.logger.info("Restarting app...")
        self.close_app()
        time.sleep(2)
        return self.launch_app()

    def tap_screen(self, x: int, y: int):
        """
        Tap screen at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.logger.debug(f"Tapping at ({x}, {y})")
        self._run_adb_command([
            "shell", "input", "tap", str(x), str(y)
        ])
        time.sleep(0.5)

    def input_text(self, text: str):
        """
        Input text via ADB. Handles special characters.

        Args:
            text: Text to input
        """
        self.logger.debug(f"Inputting text: {text[:50]}...")

        # Escape special characters for shell
        # Replace spaces with %s for ADB input
        escaped_text = text.replace(" ", "%s")
        escaped_text = escaped_text.replace("'", "'\\''")
        escaped_text = escaped_text.replace('"', '\\"')

        try:
            self._run_adb_command([
                "shell", "input", "text", escaped_text
            ])
            time.sleep(self.ui_config["interaction"]["delay_after_input"])
        except ADBError:
            # Fallback: Use clipboard method
            self.logger.warning("Direct input failed, using clipboard method")
            self._input_via_clipboard(text)

    def _input_via_clipboard(self, text: str):
        """
        Input text via clipboard as fallback.

        Args:
            text: Text to input
        """
        # Set clipboard content
        self._run_adb_command([
            "shell", "am", "broadcast",
            "-a", "clipper.set",
            "-e", "text", text
        ])
        time.sleep(0.5)

        # Simulate paste (Ctrl+V)
        self._run_adb_command([
            "shell", "input", "keyevent", "279"  # KEYCODE_PASTE
        ])

    def send_button_press(self):
        """Trigger send button via tap or keypress"""
        send_config = self.ui_config["interaction"]["send_button_tap"]

        # Try tapping send button
        self.tap_screen(send_config["x"], send_config["y"])

        # Alternatively, press Enter
        # self._run_adb_command(["shell", "input", "keyevent", "66"])

        time.sleep(self.ui_config["interaction"]["delay_after_send"])

    def get_clipboard_content(self) -> Optional[str]:
        """
        Get current clipboard content.

        Returns:
            Clipboard text or None if unavailable
        """
        try:
            # Try Termux clipboard API first
            result = subprocess.run(
                ["termux-clipboard-get"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                content = result.stdout.strip()
                if content:
                    return content
        except Exception:
            pass

        # Fallback to ADB
        try:
            result = self._run_adb_command([
                "shell", "am", "broadcast",
                "-a", "clipper.get"
            ], check=False)

            # Parse clipboard from output
            if "text=" in result.stdout:
                match = re.search(r'text=([^\n]+)', result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass

        return None

    def monitor_clipboard_for_response(
        self,
        timeout: int = 60,
        check_interval: float = 0.5
    ) -> Optional[str]:
        """
        Monitor clipboard for response content.

        Args:
            timeout: Maximum wait time in seconds
            check_interval: Check interval in seconds

        Returns:
            Response text or None if timeout
        """
        self.logger.info("Monitoring clipboard for response...")

        # Get initial clipboard content to detect changes
        initial_content = self.get_clipboard_content()
        start_time = time.time()

        while time.time() - start_time < timeout:
            current_content = self.get_clipboard_content()

            if current_content and current_content != initial_content:
                # Check if content looks like a response (not the query)
                if len(current_content) > 50:  # Arbitrary threshold
                    self.logger.info("Response detected in clipboard")
                    return current_content

            time.sleep(check_interval)

        self.logger.warning("Clipboard monitoring timed out")
        return None

    def get_screen_text_via_ocr(self) -> Optional[str]:
        """
        Capture screenshot and extract text via OCR.

        Returns:
            Extracted text or None if OCR unavailable
        """
        if not self.ui_config["screenshot"]["enabled"]:
            return None

        self.logger.info("Capturing screenshot for OCR...")

        try:
            # Take screenshot
            screenshot_path = "/sdcard/perplexity_screenshot.png"
            self._run_adb_command([
                "shell", "screencap", "-p", screenshot_path
            ])

            # Pull screenshot to local
            local_path = "/tmp/perplexity_screenshot.png"
            self._run_adb_command([
                "pull", screenshot_path, local_path
            ])

            # Check if tesseract is available
            try:
                subprocess.run(
                    ["which", "tesseract"],
                    capture_output=True,
                    check=True
                )

                # Run OCR
                result = subprocess.run(
                    ["tesseract", local_path, "stdout"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    text = result.stdout.strip()
                    self.logger.info("OCR extraction successful")
                    return text

            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.warning("Tesseract not available for OCR")

        except Exception as e:
            self.logger.error(f"Screenshot OCR failed: {str(e)}")

        return None

    def parse_notification_content(self) -> Optional[str]:
        """
        Parse notification content for responses.

        Returns:
            Notification text or None
        """
        self.logger.debug("Parsing notifications...")

        try:
            # Dump notification content
            result = self._run_adb_command([
                "shell", "dumpsys", "notification"
            ], timeout=10, check=False)

            if result.returncode != 0:
                return None

            output = result.stdout
            keywords = self.ui_config["response_detection"]["notification_keywords"]

            # Look for Perplexity notifications
            for keyword in keywords:
                if keyword.lower() in output.lower():
                    # Extract text after keyword
                    lines = output.split('\n')
                    for i, line in enumerate(lines):
                        if keyword.lower() in line.lower():
                            # Look for text in next few lines
                            for j in range(i+1, min(i+10, len(lines))):
                                if "text=" in lines[j]:
                                    match = re.search(r'text=([^\n]+)', lines[j])
                                    if match:
                                        return match.group(1)

        except Exception as e:
            self.logger.error(f"Notification parsing failed: {str(e)}")

        return None

    def detect_response(self, timeout: int = 60) -> Optional[str]:
        """
        Detect response using multiple methods.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            Response text or None
        """
        methods = self.ui_config["response_detection"]["methods"]
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Try clipboard first (most reliable)
            if "clipboard" in methods:
                response = self.monitor_clipboard_for_response(
                    timeout=5,
                    check_interval=0.5
                )
                if response:
                    return response

            # Try notifications
            if "notification" in methods:
                response = self.parse_notification_content()
                if response:
                    return response

            # Try screenshot OCR as last resort
            if "screenshot" in methods:
                response = self.get_screen_text_via_ocr()
                if response and len(response) > 50:
                    return response

            time.sleep(1)

        return None

    def send_query(
        self,
        query: str,
        auto_launch: bool = True
    ) -> Optional[str]:
        """
        Send query to Perplexity app and get response.

        Args:
            query: User query/question
            auto_launch: Automatically launch app if needed

        Returns:
            Response text or None if failed
        """
        self.logger.info(f"Sending query: {query[:50]}...")

        try:
            # Launch app if needed
            if auto_launch:
                if not self.launch_app():
                    self.logger.error("Failed to launch app")
                    return None

            # Tap text input field
            input_config = self.ui_config["interaction"]["text_field_tap"]
            self.tap_screen(input_config["x"], input_config["y"])
            time.sleep(0.5)

            # Clear existing text
            self._run_adb_command([
                "shell", "input", "keyevent", "123"  # KEYCODE_CTRL_LEFT
            ])
            self._run_adb_command([
                "shell", "input", "keyevent", "29"  # KEYCODE_A
            ])
            self._run_adb_command([
                "shell", "input", "keyevent", "112"  # KEYCODE_DEL
            ])
            time.sleep(0.3)

            # Input query
            self.input_text(query)

            # Send query
            self.send_button_press()

            # Wait for and detect response
            max_wait = self.ui_config["response_detection"]["max_wait_time"]
            response = self.detect_response(timeout=max_wait)

            if response:
                self.logger.info("Query completed successfully")
                return response
            else:
                self.logger.warning("No response detected")
                return None

        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            return None

    def send_query_with_retry(
        self,
        query: str,
        max_retries: Optional[int] = None
    ) -> Optional[str]:
        """
        Send query with automatic retry on failure.

        Args:
            query: User query/question
            max_retries: Maximum retry attempts (from config if None)

        Returns:
            Response text or None if all retries failed
        """
        if max_retries is None:
            max_retries = self.ui_config["error_recovery"]["max_retries"]

        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.logger.info(f"Retry attempt {attempt}/{max_retries}")

                # Restart app on retry
                if self.ui_config["error_recovery"]["restart_app_on_failure"]:
                    self.restart_app()

            response = self.send_query(query, auto_launch=(attempt == 0))

            if response:
                return response

        self.logger.error(f"All {max_retries + 1} attempts failed")
        return None

    def clear_app_data(self):
        """Clear app data (use with caution)"""
        package = self.ui_config["app"]["package"]
        self.logger.warning(f"Clearing app data for {package}")

        try:
            self._run_adb_command([
                "shell", "pm", "clear", package
            ])
            self.logger.info("App data cleared")
        except ADBError as e:
            self.logger.error(f"Failed to clear app data: {str(e)}")


if __name__ == "__main__":
    # Example usage
    try:
        automator = PerplexityUIAutomation()

        print("Testing app launch...")
        if automator.launch_app():
            print("App launched successfully")

            print("\nSending test query...")
            response = automator.send_query_with_retry(
                "What is the capital of France?",
                max_retries=2
            )

            if response:
                print(f"\nResponse received:\n{response}")
            else:
                print("Failed to get response")

            automator.close_app()
        else:
            print("Failed to launch app")

    except Exception as e:
        print(f"Error: {str(e)}")
