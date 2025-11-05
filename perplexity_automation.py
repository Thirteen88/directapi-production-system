#!/usr/bin/env python3
"""
Perplexity Automation - No API Key Required!

This script automates the Perplexity app on your Android device.
It can send prompts and retrieve responses (text or images) like a human would.
"""

import subprocess
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

# Try to import OCR libraries (optional)
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️  OCR not available. Install: pip install pillow pytesseract")


class PerplexityAutomation:
    """
    Automate Perplexity app without API key by controlling it like a human.
    """

    def __init__(self, device_id: Optional[str] = None):
        """Initialize Perplexity automation"""
        self.device_id = device_id or self._get_device_id()
        self.package_name = "ai.perplexity.app.android"
        self.screenshots_dir = Path("screenshots/perplexity")
        self.responses_dir = Path("output/perplexity_responses")

        # Create directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)

        # Screen dimensions for Pixel 9 Pro XL
        self.screen_width = 1344
        self.screen_height = 2992

        # Keep screen awake during automation
        self._keep_screen_awake()

        print(f"✅ Perplexity Automation initialized for device: {self.device_id}")

    def _get_device_id(self) -> str:
        """Get connected device ID"""
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')[1:]
        for line in lines:
            if '\tdevice' in line:
                return line.split('\t')[0]
        return ""

    def _adb_cmd(self, cmd: str, timeout: int = 30) -> str:
        """Execute ADB command"""
        full_cmd = f"adb -s {self.device_id} {cmd}"
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip()

    def _tap(self, x: int, y: int):
        """Tap at coordinates"""
        self._adb_cmd(f"shell input tap {x} {y}")
        time.sleep(0.3)

    def _type_text(self, text: str):
        """Type text (replace spaces with %s)"""
        # Escape special characters
        safe_text = text.replace(" ", "%s").replace("'", "").replace('"', '')
        self._adb_cmd(f"shell input text '{safe_text}'")
        time.sleep(0.5)

    def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Swipe gesture"""
        self._adb_cmd(f"shell input swipe {x1} {y1} {x2} {y2} {duration}")
        time.sleep(0.5)

    def _press_key(self, keycode: str):
        """Press a key (ENTER, BACK, etc.)"""
        self._adb_cmd(f"shell input keyevent KEYCODE_{keycode}")
        time.sleep(0.3)

    def _keep_screen_awake(self):
        """Keep screen awake during automation"""
        self._adb_cmd("shell svc power stayon true")
        print("💡 Screen will stay awake during automation")

    def _ensure_unlocked(self):
        """Ensure device is unlocked"""
        # Wake the device
        self._adb_cmd("shell input keyevent KEYCODE_WAKEUP")
        time.sleep(0.5)

        # Swipe up to unlock (works with swipe lock)
        self._swipe(672, 2500, 672, 1000, 300)
        time.sleep(0.5)

    def take_screenshot(self, name: str = "screenshot") -> Path:
        """Take a screenshot and pull it to computer"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        device_path = f"/sdcard/{filename}"
        local_path = self.screenshots_dir / filename

        # Take screenshot
        self._adb_cmd(f"shell screencap -p {device_path}")

        # Pull to computer
        self._adb_cmd(f"pull {device_path} {local_path}")

        # Delete from device
        self._adb_cmd(f"shell rm {device_path}")

        print(f"📸 Screenshot saved: {local_path}")
        return local_path

    def extract_text_from_screenshot(self, image_path: Path) -> str:
        """Extract text from screenshot using OCR"""
        if not OCR_AVAILABLE:
            print("⚠️  OCR not available. Returning empty text.")
            return ""

        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"❌ OCR failed: {e}")
            return ""

    def open_perplexity(self):
        """Open Perplexity app"""
        print("🚀 Opening Perplexity app...")

        # Ensure device is unlocked
        self._ensure_unlocked()

        # Launch app
        self._adb_cmd(f"shell am start -n {self.package_name}/.MainActivity")
        time.sleep(3)

        # Take screenshot to see UI
        screenshot = self.take_screenshot("perplexity_opened")
        print(f"✅ Perplexity opened: {screenshot}")

        return screenshot

    def close_perplexity(self):
        """Close Perplexity app"""
        print("Closing Perplexity app...")
        self._adb_cmd(f"shell am force-stop {self.package_name}")
        time.sleep(1)

    def send_prompt(
        self,
        prompt: str,
        wait_time: int = 10,
        capture_interval: int = 2
    ) -> Dict:
        """
        Send a prompt to Perplexity and capture the response

        Args:
            prompt: The question/prompt to send
            wait_time: How long to wait for response (seconds)
            capture_interval: Take screenshots every N seconds

        Returns:
            Dictionary with response data
        """
        print(f"\n{'='*80}")
        print(f"📝 SENDING PROMPT TO PERPLEXITY")
        print(f"{'='*80}")
        print(f"Prompt: {prompt}")
        print(f"{'='*80}\n")

        response_data = {
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "screenshots": [],
            "extracted_text": "",
            "success": False
        }

        try:
            # 1. Open Perplexity
            self.open_perplexity()

            # 2. Wait for app to fully load
            time.sleep(2)

            # 3. Find and tap search/prompt field
            # Based on typical Perplexity UI, the search is usually at bottom
            # Let's tap near the bottom center where search usually is
            print("🔍 Looking for search field...")
            search_y = int(self.screen_height * 0.95)  # Near bottom
            search_x = int(self.screen_width * 0.5)    # Center
            self._tap(search_x, search_y)
            time.sleep(1)

            # Take screenshot after tapping search
            self.take_screenshot("after_tap_search")

            # 4. Type the prompt
            print(f"⌨️  Typing prompt: {prompt}")
            self._type_text(prompt)
            time.sleep(1)

            # Take screenshot after typing
            self.take_screenshot("after_typing_prompt")

            # 5. Submit (press ENTER or tap submit button)
            print("📤 Submitting prompt...")
            self._press_key("ENTER")
            time.sleep(2)

            # 6. Wait for response and capture screenshots
            print(f"⏳ Waiting for response ({wait_time} seconds)...")
            screenshots = []

            for i in range(0, wait_time, capture_interval):
                screenshot = self.take_screenshot(f"response_{i}s")
                screenshots.append(str(screenshot))
                time.sleep(capture_interval)

            response_data["screenshots"] = screenshots

            # 7. Take final screenshot
            final_screenshot = self.take_screenshot("response_final")
            screenshots.append(str(final_screenshot))

            # 8. Extract text from final screenshot
            if OCR_AVAILABLE:
                print("🔍 Extracting text from response...")
                extracted_text = self.extract_text_from_screenshot(final_screenshot)
                response_data["extracted_text"] = extracted_text
                print(f"\n📄 Extracted Text Preview:\n{extracted_text[:500]}...\n")

            response_data["success"] = True

            # 9. Save response data
            response_file = self.responses_dir / f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(response_file, 'w') as f:
                json.dump(response_data, f, indent=2)

            print(f"✅ Response saved to: {response_file}")

        except Exception as e:
            print(f"❌ Error during automation: {e}")
            response_data["error"] = str(e)

        return response_data

    def get_response_text(self, response_data: Dict) -> str:
        """Extract text from response data"""
        return response_data.get("extracted_text", "")

    def get_response_images(self, response_data: Dict) -> List[str]:
        """Get list of screenshot paths from response"""
        return response_data.get("screenshots", [])

    def interactive_mode(self):
        """Interactive mode - keep asking prompts"""
        print("\n" + "="*80)
        print("🤖 PERPLEXITY INTERACTIVE MODE")
        print("="*80)
        print("Type your prompts and get AI responses!")
        print("Commands: 'quit' to exit, 'clear' to clear screen")
        print("="*80 + "\n")

        while True:
            try:
                prompt = input("\n💭 Your prompt (or 'quit'): ").strip()

                if prompt.lower() == 'quit':
                    print("👋 Goodbye!")
                    break

                if prompt.lower() == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                    continue

                if not prompt:
                    continue

                # Send prompt and get response
                response = self.send_prompt(prompt, wait_time=15)

                if response["success"]:
                    print("\n✅ Response received!")
                    print(f"📸 Screenshots: {len(response['screenshots'])}")

                    if OCR_AVAILABLE and response.get("extracted_text"):
                        print("\n" + "="*80)
                        print("📄 EXTRACTED TEXT:")
                        print("="*80)
                        print(response["extracted_text"])
                        print("="*80)
                else:
                    print("❌ Failed to get response")

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main entry point"""
    import sys

    # Create automation instance
    perplexity = PerplexityAutomation()

    # Check if prompt provided as argument
    if len(sys.argv) > 1:
        # Single prompt mode
        prompt = " ".join(sys.argv[1:])
        response = perplexity.send_prompt(prompt, wait_time=15)

        print("\n" + "="*80)
        print("📊 RESPONSE SUMMARY")
        print("="*80)
        print(f"Success: {response['success']}")
        print(f"Screenshots: {len(response['screenshots'])}")

        if OCR_AVAILABLE and response.get("extracted_text"):
            print("\nExtracted Text:")
            print("-" * 80)
            print(response["extracted_text"])

        print("\nScreenshot locations:")
        for screenshot in response["screenshots"]:
            print(f"  - {screenshot}")

    else:
        # Interactive mode
        perplexity.interactive_mode()


if __name__ == "__main__":
    main()
