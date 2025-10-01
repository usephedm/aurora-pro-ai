"""Stealth Browser Agent for Aurora Pro - Anti-detection web automation.

This module provides advanced browser automation with anti-bot detection features
using undetected-chromedriver and selenium-stealth. All features are gated by
operator_enabled.yaml configuration.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import yaml

logger = logging.getLogger(__name__)


@dataclass
class BrowserTask:
    """Browser automation task specification."""
    task_id: str
    action: str  # navigate, click, type, extract, screenshot
    parameters: Dict
    status: str = "queued"
    created_at: float = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class StealthBrowserAgent:
    """
    Stealth browser automation agent with anti-detection capabilities.

    Features:
    - undetected-chromedriver for bypassing bot detection
    - selenium-stealth for fingerprint evasion
    - Random user agents and viewport sizes
    - Behavioral simulation (mouse movements, scrolling)
    - CAPTCHA integration
    - Operator authorization gating
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/stealth_browser.log"
    CONFIG_PATH = "/root/aurora_pro/config/operator_enabled.yaml"
    SCREENSHOT_DIR = "/root/aurora_pro/logs/browser_screenshots"

    # User agent pool for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    VIEWPORT_SIZES = [
        (1920, 1080),
        (1366, 768),
        (1440, 900),
        (1536, 864),
    ]

    def __init__(self):
        self._driver = None
        self._config: Dict = {}
        self._running = False
        self._undetected_available = False
        self._stealth_available = False
        self._lock = asyncio.Lock()

        # Create screenshot directory
        Path(self.SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Initialize stealth browser agent."""
        self._running = True
        await self._load_config()
        await self._check_dependencies()
        await self._audit_log("system", "Stealth browser agent started")

    async def stop(self):
        """Shutdown stealth browser agent."""
        self._running = False
        await self._close_driver()
        await self._audit_log("system", "Stealth browser agent stopped")

    async def _load_config(self):
        """Load operator configuration."""
        try:
            async with aiofiles.open(self.CONFIG_PATH, "r") as f:
                content = await f.read()
                self._config = yaml.safe_load(content)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {"operator_enabled": False, "features": {}}

    async def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            import undetected_chromedriver
            self._undetected_available = True
            logger.info("undetected-chromedriver available")
        except ImportError:
            logger.warning("undetected-chromedriver not available")
            self._undetected_available = False

        try:
            from selenium_stealth import stealth
            self._stealth_available = True
            logger.info("selenium-stealth available")
        except ImportError:
            logger.warning("selenium-stealth not available")
            self._stealth_available = False

    def _check_authorization(self) -> bool:
        """Check if stealth browsing is authorized."""
        operator_enabled = self._config.get("operator_enabled", False)
        feature_enabled = self._config.get("features", {}).get("stealth_browsing", False)
        return operator_enabled and feature_enabled

    async def _init_driver(self):
        """Initialize undetected Chrome driver with stealth settings."""
        if self._driver:
            return

        if not self._undetected_available:
            raise RuntimeError("undetected-chromedriver not available - install with: pip install undetected-chromedriver")

        try:
            import undetected_chromedriver as uc

            # Configure Chrome options
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Random user agent
            user_agent = random.choice(self.USER_AGENTS)
            options.add_argument(f"--user-agent={user_agent}")

            # Initialize driver
            self._driver = uc.Chrome(options=options, use_subprocess=True)

            # Random viewport size
            width, height = random.choice(self.VIEWPORT_SIZES)
            self._driver.set_window_size(width, height)

            # Apply selenium-stealth if available
            if self._stealth_available:
                from selenium_stealth import stealth
                stealth(
                    self._driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Linux",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )

            logger.info("Stealth browser driver initialized")
            await self._audit_log("system", f"Driver initialized with UA: {user_agent}")

        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

    async def _close_driver(self):
        """Close browser driver."""
        if self._driver:
            try:
                self._driver.quit()
            except:
                pass
            self._driver = None

    async def navigate(
        self,
        url: str,
        wait_time: float = 2.0,
        operator_user: Optional[str] = None,
    ) -> Dict:
        """
        Navigate to URL with anti-detection measures.

        Args:
            url: Target URL
            wait_time: Time to wait after navigation (seconds)
            operator_user: User requesting operation

        Returns:
            Result dictionary with page info
        """
        if not self._check_authorization():
            raise PermissionError("Stealth browsing not authorized - check operator_enabled.yaml")

        async with self._lock:
            try:
                # Initialize driver if needed
                await self._init_driver()

                # Navigate
                self._driver.get(url)

                # Human-like wait with randomness
                await asyncio.sleep(wait_time + random.uniform(0, 1))

                # Simulate human behavior
                await self._simulate_human_behavior()

                # Get page info
                title = self._driver.title
                current_url = self._driver.current_url

                result = {
                    "success": True,
                    "url": current_url,
                    "title": title,
                }

                await self._audit_log(
                    "navigate",
                    f"Navigated to {url}",
                    operator_user=operator_user,
                    metadata=result,
                )

                return result

            except Exception as e:
                logger.error(f"Navigation failed: {e}")
                await self._audit_log("error", f"Navigation failed: {e}")
                raise

    async def _simulate_human_behavior(self):
        """Simulate human-like behavior to avoid detection."""
        try:
            from selenium.webdriver.common.action_chains import ActionChains

            if not self._driver:
                return

            # Random mouse movements
            actions = ActionChains(self._driver)
            for _ in range(random.randint(1, 3)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                actions.move_by_offset(x_offset, y_offset)
            actions.perform()

            # Random scroll
            scroll_amount = random.randint(100, 500)
            self._driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

            # Small random delay
            await asyncio.sleep(random.uniform(0.1, 0.5))

        except Exception as e:
            logger.debug(f"Behavior simulation error: {e}")

    async def extract_content(
        self,
        selector: Optional[str] = None,
        operator_user: Optional[str] = None,
    ) -> str:
        """
        Extract content from current page.

        Args:
            selector: CSS selector (if None, extracts all text)
            operator_user: User requesting operation

        Returns:
            Extracted text content
        """
        if not self._check_authorization():
            raise PermissionError("Stealth browsing not authorized - check operator_enabled.yaml")

        async with self._lock:
            try:
                if not self._driver:
                    raise RuntimeError("Browser not initialized - call navigate() first")

                if selector:
                    element = self._driver.find_element("css selector", selector)
                    content = element.text
                else:
                    content = self._driver.find_element("tag name", "body").text

                await self._audit_log(
                    "extract_content",
                    f"Extracted {len(content)} characters",
                    operator_user=operator_user,
                    metadata={"selector": selector, "length": len(content)},
                )

                return content

            except Exception as e:
                logger.error(f"Content extraction failed: {e}")
                await self._audit_log("error", f"Content extraction failed: {e}")
                raise

    async def take_screenshot(
        self,
        filename: Optional[str] = None,
        operator_user: Optional[str] = None,
    ) -> str:
        """
        Take screenshot of current page.

        Returns path to screenshot file.
        """
        if not self._check_authorization():
            raise PermissionError("Stealth browsing not authorized - check operator_enabled.yaml")

        async with self._lock:
            try:
                if not self._driver:
                    raise RuntimeError("Browser not initialized - call navigate() first")

                # Generate filename
                if not filename:
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    task_id = str(uuid.uuid4())[:8]
                    filename = f"browser_{timestamp}_{task_id}.png"

                filepath = str(Path(self.SCREENSHOT_DIR) / filename)

                # Take screenshot
                self._driver.save_screenshot(filepath)

                await self._audit_log(
                    "screenshot",
                    f"Screenshot saved to {filepath}",
                    operator_user=operator_user,
                    metadata={"path": filepath},
                )

                return filepath

            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                await self._audit_log("error", f"Screenshot failed: {e}")
                raise

    async def click_element(
        self,
        selector: str,
        operator_user: Optional[str] = None,
    ) -> Dict:
        """
        Click element with human-like behavior.

        Args:
            selector: CSS selector for element to click
            operator_user: User requesting operation

        Returns:
            Result dictionary
        """
        if not self._check_authorization():
            raise PermissionError("Stealth browsing not authorized - check operator_enabled.yaml")

        async with self._lock:
            try:
                if not self._driver:
                    raise RuntimeError("Browser not initialized - call navigate() first")

                from selenium.webdriver.common.action_chains import ActionChains

                # Find element
                element = self._driver.find_element("css selector", selector)

                # Move to element with human-like curve
                actions = ActionChains(self._driver)
                actions.move_to_element(element)
                actions.pause(random.uniform(0.1, 0.3))
                actions.click()
                actions.perform()

                # Small delay
                await asyncio.sleep(random.uniform(0.2, 0.5))

                result = {"success": True, "selector": selector}

                await self._audit_log(
                    "click_element",
                    f"Clicked element: {selector}",
                    operator_user=operator_user,
                    metadata=result,
                )

                return result

            except Exception as e:
                logger.error(f"Click failed: {e}")
                await self._audit_log("error", f"Click failed: {e}")
                raise

    async def type_text(
        self,
        selector: str,
        text: str,
        operator_user: Optional[str] = None,
    ) -> Dict:
        """
        Type text into element with human-like timing.

        Args:
            selector: CSS selector for input element
            text: Text to type
            operator_user: User requesting operation

        Returns:
            Result dictionary
        """
        if not self._check_authorization():
            raise PermissionError("Stealth browsing not authorized - check operator_enabled.yaml")

        async with self._lock:
            try:
                if not self._driver:
                    raise RuntimeError("Browser not initialized - call navigate() first")

                # Find element
                element = self._driver.find_element("css selector", selector)

                # Click to focus
                element.click()
                await asyncio.sleep(random.uniform(0.1, 0.2))

                # Type with human-like delays
                for char in text:
                    element.send_keys(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))

                result = {"success": True, "selector": selector, "text_length": len(text)}

                await self._audit_log(
                    "type_text",
                    f"Typed {len(text)} characters into {selector}",
                    operator_user=operator_user,
                    metadata=result,
                )

                return result

            except Exception as e:
                logger.error(f"Type text failed: {e}")
                await self._audit_log("error", f"Type text failed: {e}")
                raise

    def get_status(self) -> Dict:
        """Get stealth browser status."""
        return {
            "running": self._running,
            "driver_initialized": self._driver is not None,
            "undetected_chromedriver_available": self._undetected_available,
            "selenium_stealth_available": self._stealth_available,
            "authorized": self._check_authorization(),
        }

    async def _audit_log(
        self,
        action: str,
        message: str,
        operator_user: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Write audit log entry."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

        entry = {
            "timestamp": timestamp,
            "action": action,
            "message": message,
            "operator_user": operator_user or "system",
            "metadata": metadata or {},
        }

        line = json.dumps(entry) + "\n"

        log_path = Path(self.AUDIT_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(self.AUDIT_LOG_PATH, "a") as f:
                await f.write(line)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Singleton instance
_stealth_browser_instance: Optional[StealthBrowserAgent] = None


def get_stealth_browser() -> StealthBrowserAgent:
    """Get or create stealth browser singleton."""
    global _stealth_browser_instance
    if _stealth_browser_instance is None:
        _stealth_browser_instance = StealthBrowserAgent()
    return _stealth_browser_instance


__all__ = ["StealthBrowserAgent", "get_stealth_browser", "BrowserTask"]