#!/usr/bin/env python3
'''
EMERGENCY FIX: Make vision_agent and input agents work headless
Also patches main.py to skip failed agent startups gracefully
'''
import re

# Fix vision_agent.py - wrap mss in try/except with graceful degradation
vision_fix = '''
    async def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            import mss
            import os
            # Only initialize if DISPLAY is available
            if os.environ.get('DISPLAY'):
                self._mss_instance = mss.mss()
                logger.info("mss available for screen capture")
            else:
                logger.warning("No DISPLAY - screen capture disabled (headless mode)")
                self._mss_instance = None
        except Exception as e:
            logger.warning(f"mss not available: {e} - screen capture disabled")
            self._mss_instance = None

        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._pytesseract_available = True
            logger.info("pytesseract available for OCR")
        except:
            logger.warning("pytesseract not available - OCR disabled")
            self._pytesseract_available = False
'''

with open('/root/aurora_pro/vision_agent.py', 'r') as f:
    content = f.read()

# Replace the _check_dependencies method
pattern = r'async def _check_dependencies\(self\):.*?self\._pytesseract_available = False'
content = re.sub(pattern, vision_fix.strip(), content, flags=re.DOTALL)

with open('/root/aurora_pro/vision_agent.py', 'w') as f:
    f.write(content)

print("✓ Fixed vision_agent.py for headless operation")

# Fix mouse_keyboard_agent.py - same approach
with open('/root/aurora_pro/mouse_keyboard_agent.py', 'r') as f:
    mk_content = f.read()

# Find and replace _check_dependencies in mouse_keyboard_agent
mk_pattern = r'async def _check_dependencies\(self\):.*?self\._pyautogui_available = False'
mk_fix = '''
    async def _check_dependencies(self):
        """Check if PyAutoGUI is available and working."""
        try:
            import pyautogui
            import os
            # Only initialize if DISPLAY is available
            if os.environ.get('DISPLAY'):
                pyautogui.FAILSAFE = True
                self._pyautogui_available = True
                logger.info("PyAutoGUI available for input control")
            else:
                logger.warning("No DISPLAY - input control disabled (headless mode)")
                self._pyautogui_available = False
        except Exception as e:
            logger.warning(f"PyAutoGUI not available: {e} - input control disabled")
            self._pyautogui_available = False
'''

mk_content = re.sub(mk_pattern, mk_fix.strip(), mk_content, flags=re.DOTALL)

with open('/root/aurora_pro/mouse_keyboard_agent.py', 'w') as f:
    f.write(mk_content)

print("✓ Fixed mouse_keyboard_agent.py for headless operation")

# Fix main.py - wrap agent starts in try/except
with open('/root/aurora_pro/main.py', 'r') as f:
    main_content = f.read()

# Replace vision_agent start
main_content = main_content.replace(
    'vision_agent = get_vision_agent()\n    await vision_agent.start()',
    '''try:
        vision_agent = get_vision_agent()
        await vision_agent.start()
    except Exception as e:
        logger.warning(f"Vision agent failed to start: {e} - continuing without it")
        vision_agent = None'''
)

# Replace input_agent start
main_content = main_content.replace(
    'input_agent = get_input_agent()\n        await input_agent.start()',
    '''try:
            input_agent = get_input_agent()
            await input_agent.start()
        except Exception as e:
            logger.warning(f"Input agent failed to start: {e} - continuing without it")
            input_agent = None'''
)

with open('/root/aurora_pro/main.py', 'w') as f:
    f.write(main_content)

print("✓ Fixed main.py for graceful agent startup failures")
print("\n🎉 ALL FIXES APPLIED - Aurora Pro should now start headless!")
