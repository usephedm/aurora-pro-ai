"""Selenium powered browser automation engine with workspace management."""
import asyncio
import contextlib
import dataclasses
import io
import json
import logging
import pathlib
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from ssrf_protection import SSRFProtection

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BrowserTab:
    """Represents a browser tab and its metadata."""

    handle: str
    url: str = "about:blank"
    title: str = ""
    created_at: float = dataclasses.field(default_factory=time.time)


@dataclasses.dataclass
class BrowserWorkspace:
    """Logical grouping of browser tabs for task isolation."""

    name: str
    tabs: Dict[str, BrowserTab] = dataclasses.field(default_factory=dict)
    active_tab: Optional[str] = None

    def snapshot(self) -> Dict[str, dict]:
        return {
            "name": self.name,
            "active_tab": self.active_tab,
            "tabs": {key: dataclasses.asdict(tab) for key, tab in self.tabs.items()},
        }


class BrowserAgent:
    """High-level browser automation wrapper with async helpers."""

    def __init__(self, enable_ssrf_protection: bool = True) -> None:
        self._driver: Optional[WebDriver] = None
        self._driver_lock = asyncio.Lock()
        self._workspaces: Dict[str, BrowserWorkspace] = {}
        self._active_workspace: Optional[str] = None
        self._ssrf_protection = SSRFProtection() if enable_ssrf_protection else None

    def _validate_url(self, url: str) -> None:
        """Validate URL against SSRF protection if enabled."""
        if not self._ssrf_protection:
            return

        is_valid, error = self._ssrf_protection.validate_url(url)
        if not is_valid:
            raise ValueError(f"URL blocked by SSRF protection: {error}")

    async def ensure_driver(self, browser: str = "chrome", headless: bool = True) -> WebDriver:
        """Create a Selenium WebDriver if one is not already active."""
        if self._driver:
            return self._driver

        async with self._driver_lock:
            if self._driver:
                return self._driver

            def _build_driver() -> WebDriver:
                if browser == "firefox":
                    options = webdriver.FirefoxOptions()
                    options.headless = headless
                    driver_path = None
                    try:
                        driver_path = GeckoDriverManager().install()
                    except Exception:  # noqa: BLE001
                        logger.warning("Falling back to system geckodriver")
                    service = FirefoxService(executable_path=driver_path) if driver_path else FirefoxService()
                    return webdriver.Firefox(options=options, service=service)

                options = ChromeOptions()
                if headless:
                    options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                driver_path = None
                try:
                    driver_path = ChromeDriverManager().install()
                except Exception:  # noqa: BLE001
                    logger.warning("Falling back to system chromedriver")
                service = ChromeService(executable_path=driver_path) if driver_path else ChromeService()
                return webdriver.Chrome(options=options, service=service)

            try:
                self._driver = await asyncio.to_thread(_build_driver)
            except WebDriverException as exc:
                logger.exception("Failed to start WebDriver: %s", exc)
                raise

            self._initialize_workspace("default")
            return self._driver

    def _initialize_workspace(self, name: str) -> None:
        if name in self._workspaces:
            return
        self._workspaces[name] = BrowserWorkspace(name=name)
        self._active_workspace = name

    def list_workspaces(self) -> List[Dict[str, dict]]:
        return [workspace.snapshot() for workspace in self._workspaces.values()]

    def activate_workspace(self, name: str) -> BrowserWorkspace:
        if name not in self._workspaces:
            self._initialize_workspace(name)
        self._active_workspace = name
        return self._workspaces[name]

    async def open_url(self, url: str, tab_name: Optional[str] = None) -> BrowserTab:
        driver = await self.ensure_driver()
        workspace = self.activate_workspace(self._active_workspace or "default")

        async with self._driver_lock:
            await asyncio.to_thread(driver.get, url)
            handle = driver.current_window_handle
            title = driver.title

        tab_key = tab_name or f"tab-{len(workspace.tabs) + 1}"
        tab = BrowserTab(handle=handle, url=url, title=title)
        workspace.tabs[tab_key] = tab
        workspace.active_tab = tab_key
        return tab

    async def new_tab(self, url: str = "about:blank", tab_name: Optional[str] = None) -> BrowserTab:
        driver = await self.ensure_driver()
        workspace = self.activate_workspace(self._active_workspace or "default")

        async with self._driver_lock:
            await asyncio.to_thread(driver.switch_to.new_window, "tab")
            await asyncio.to_thread(driver.get, url)
            handle = driver.current_window_handle
            title = driver.title

        tab_key = tab_name or f"tab-{len(workspace.tabs) + 1}"
        tab = BrowserTab(handle=handle, url=url, title=title)
        workspace.tabs[tab_key] = tab
        workspace.active_tab = tab_key
        return tab

    async def switch_tab(self, tab_key: str) -> Optional[BrowserTab]:
        driver = await self.ensure_driver()
        workspace = self.activate_workspace(self._active_workspace or "default")
        tab = workspace.tabs.get(tab_key)
        if not tab:
            return None

        async with self._driver_lock:
            await asyncio.to_thread(driver.switch_to.window, tab.handle)

        workspace.active_tab = tab_key
        return tab

    async def close_tab(self, tab_key: str) -> bool:
        driver = await self.ensure_driver()
        workspace = self.activate_workspace(self._active_workspace or "default")
        tab = workspace.tabs.get(tab_key)
        if not tab:
            return False

        async with self._driver_lock:
            try:
                await asyncio.to_thread(driver.switch_to.window, tab.handle)
                await asyncio.to_thread(driver.close)
            except WebDriverException:
                logger.warning("Failed closing tab %s", tab_key, exc_info=True)
                return False

        del workspace.tabs[tab_key]
        if workspace.active_tab == tab_key:
            workspace.active_tab = next(iter(workspace.tabs), None)
        return True

    async def execute_script(self, script: str, *args) -> Optional[str]:
        driver = await self.ensure_driver()
        async with self._driver_lock:
            return await asyncio.to_thread(driver.execute_script, script, *args)

    async def fill_form(self, selector: str, value: str, by: By = By.CSS_SELECTOR) -> bool:
        driver = await self.ensure_driver()

        def _fill() -> bool:
            element = driver.find_element(by, selector)
            element.clear()
            element.send_keys(value)
            return True

        try:
            await asyncio.to_thread(_fill)
            return True
        except WebDriverException:
            logger.exception("Form fill failed")
            return False

    async def click(self, selector: str, by: By = By.CSS_SELECTOR) -> bool:
        driver = await self.ensure_driver()

        def _click() -> bool:
            element = driver.find_element(by, selector)
            element.click()
            return True

        try:
            await asyncio.to_thread(_click)
            return True
        except WebDriverException:
            logger.exception("Click failed")
            return False

    async def scroll(self, amount: int = 500) -> None:
        await self.execute_script("window.scrollBy(0, arguments[0]);", amount)

    async def get_dom(self) -> str:
        driver = await self.ensure_driver()
        async with self._driver_lock:
            return await asyncio.to_thread(lambda: driver.execute_script("return document.documentElement.outerHTML"))

    async def capture_screenshot(self, path: Optional[pathlib.Path] = None) -> bytes:
        driver = await self.ensure_driver()

        def _capture() -> bytes:
            png = driver.get_screenshot_as_png()
            if path:
                with path.open("wb") as handle:
                    handle.write(png)
            return png

        return await asyncio.to_thread(_capture)

    async def export_workspace_state(self) -> str:
        data = {
            "active_workspace": self._active_workspace,
            "workspaces": {name: ws.snapshot() for name, ws in self._workspaces.items()},
        }
        return json.dumps(data, indent=2)

    async def shutdown(self) -> None:
        if not self._driver:
            return
        async with self._driver_lock:
            try:
                await asyncio.to_thread(self._driver.quit)
            except WebDriverException:
                logger.warning("Failed to cleanly shutdown WebDriver", exc_info=True)
            finally:
                self._driver = None
                self._workspaces.clear()
                self._active_workspace = None

    async def process_command(self, command: str) -> str:
        """Very small DSL mapping natural language to browser actions."""
        lowered = command.lower()
        if lowered.startswith("open "):
            url = command.split(" ", 1)[1]
            tab = await self.open_url(url)
            return f"Opened {tab.title or tab.url}"
        if lowered.startswith("new tab"):
            tab = await self.new_tab()
            return f"Created tab {tab.handle}"
        if lowered.startswith("switch to"):
            key = command.split(" ", 2)[-1]
            tab = await self.switch_tab(key)
            return f"Switched to {key}" if tab else f"Tab {key} not found"
        if lowered.startswith("scroll"):
            await self.scroll()
            return "Scrolled page"
        if lowered.startswith("screenshot"):
            buffer = io.BytesIO(await self.capture_screenshot())
            return f"Screenshot captured ({len(buffer.getvalue())} bytes)"
        return "Command not understood"


@contextlib.asynccontextmanager
async def browser_agent_context() -> BrowserAgent:
    agent = BrowserAgent()
    try:
        yield agent
    finally:
        await agent.shutdown()
