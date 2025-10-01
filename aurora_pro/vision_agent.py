
"""Vision Agent for Aurora Pro - Screen capture, OCR, and UI element detection.

This module provides real-time screen analysis capabilities using mss for capture
and pytesseract for OCR. All features are gated by operator_enabled.yaml.
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import time
import uuid
from collections import deque
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple

import aiofiles
import cv2
import numpy as np
import pyautogui
import yaml
from pynput import keyboard, mouse

logger = logging.getLogger(__name__)


@dataclass
class ScreenRegion:
    """Defines a rectangular region on screen."""
    x: int
    y: int
    width: int
    height: int


@dataclass
class UIElement:
    """Detected UI element with position and metadata."""
    element_type: str  # button, text_field, label, etc.
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass
class ScreenAnalysis:
    """Results of screen analysis."""
    task_id: str
    timestamp: float
    screenshot_path: Optional[str]
    ocr_text: str
    ui_elements: List[UIElement]
    screen_size: Tuple[int, int]
    analysis_time_ms: float


class VisionAgent:
    """
    Autonomous vision agent for screen capture and analysis.

    Features:
    - Screen capture using mss (hardware-accelerated)
    - OCR text extraction using pytesseract
    - UI element detection (coordinates, types)
    - Real-time screen monitoring
    - Operator authorization gating
    - Real-time streaming of its perspective with mouse and keyboard visualization
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/vision_agent.log"
    CONFIG_PATH = "/root/aurora_pro/config/operator_enabled.yaml"
    SCREENSHOT_DIR = "/root/aurora_pro/logs/screenshots"

    def __init__(self):
        self._running = False
        self._mss_instance = None
        self._pytesseract_available = False
        self._lock = asyncio.Lock()
        self._config: Dict = {}
        self._streaming = False
        self._stream_task = None

        # Mouse and keyboard state
        self._mouse_pos = (0, 0)
        self._mouse_clicks: Deque[Tuple[int, int, float]] = deque(maxlen=5)
        self._key_presses: Deque[Tuple[str, float]] = deque(maxlen=10)
        self._keyboard_listener = None
        self._mouse_listener = None

        # Create screenshot directory
        Path(self.SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Initialize vision agent and check dependencies."""
        self._running = True
        await self._load_config()
        await self._check_dependencies()
        await self._audit_log("system", "Vision agent started")

    async def stop(self):
        """Shutdown vision agent."""
        if self._streaming:
            await self.stop_streaming()
        self._running = False
        if self._mss_instance:
            try:
                self._mss_instance.close()
            except:
                pass
        await self._audit_log("system", "Vision agent stopped")

    async def start_streaming(self):
        """Start streaming the agent's perspective."""
        if not self._check_authorization():
            raise PermissionError("Vision agent not authorized - check operator_enabled.yaml")
        if self._streaming:
            return

        self._streaming = True
        self._start_input_listeners()
        self._stream_task = asyncio.create_task(self._stream_frames())
        await self._audit_log("system", "Vision agent streaming started")

    async def stop_streaming(self):
        """Stop streaming the agent's perspective."""
        if not self._streaming:
            return

        self._streaming = False
        self._stop_input_listeners()
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        await self._audit_log("system", "Vision agent streaming stopped")

    def _start_input_listeners(self):
        """Start listening for mouse and keyboard events."""
        self._mouse_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
        self._keyboard_listener = keyboard.Listener(on_press=self._on_press)
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def _stop_input_listeners(self):
        """Stop listening for mouse and keyboard events."""
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()

    def _on_move(self, x, y):
        self._mouse_pos = (x, y)

    def _on_click(self, x, y, button, pressed):
        if pressed:
            self._mouse_clicks.append((x, y, time.time()))

    def _on_press(self, key):
        try:
            self._key_presses.append((key.char, time.time()))
        except AttributeError:
            self._key_presses.append((str(key), time.time()))

    async def _stream_frames(self):
        """Main loop for streaming frames to the vision_streamer."""
        import httpx
        async with httpx.AsyncClient() as client:
            while self._streaming:
                try:
                    frame = await self.capture_screen(save=False, draw_elements=True, draw_input=True)
                    if frame is not None:
                        _, img_encoded = cv2.imencode('.jpg', frame)
                        base = os.getenv("VISION_STREAMER_URL", "http://127.0.0.1:8011")
                        await client.post(f"{base}/frame", content=img_encoded.tobytes())
                    await asyncio.sleep(1/30)  # 30 FPS
                except httpx.RequestError as e:
                    logger.warning(f"Could not connect to vision streamer: {e}. Retrying...")
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error in streaming loop: {e}")
                    await asyncio.sleep(2)

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

    def _check_authorization(self) -> bool:
        """Check if vision agent is authorized."""
        operator_enabled = self._config.get("operator_enabled", False)
        feature_enabled = self._config.get("features", {}).get("vision_agent", False)
        streaming_enabled = self._config.get("features", {}).get("vision_streaming", False)
        return operator_enabled and feature_enabled and streaming_enabled

    async def capture_screen(
        self,
        region: Optional[ScreenRegion] = None,
        save: bool = True,
        operator_user: Optional[str] = None,
        draw_elements: bool = False,
        draw_input: bool = False,
    ) -> Optional[np.ndarray]:
        """
        Capture screen or region.

        Returns path to saved screenshot or numpy array of the image.
        """
        if not self._check_authorization():
            raise PermissionError("Vision agent not authorized - check operator_enabled.yaml")

        if not self._mss_instance:
            raise RuntimeError("mss not available - install with: pip install mss")

        try:
            # Capture screen
            if region:
                monitor = {
                    "left": region.x,
                    "top": region.y,
                    "width": region.width,
                    "height": region.height,
                }
            else:
                monitor = self._mss_instance.monitors[1]  # Primary monitor

            # Perform capture
            sct_img = self._mss_instance.grab(monitor)
            img = np.array(sct_img)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            if draw_elements:
                elements = await self.detect_ui_elements(image_array=img, operator_user=operator_user)
                for element in elements:
                    cv2.rectangle(img, (element.x, element.y), (element.x + element.width, element.y + element.height), (0, 255, 0), 2)
                    cv2.putText(img, element.text, (element.x, element.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if draw_input:
                self._draw_input_visualizations(img)

            # Save if requested
            if save:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                task_id = str(uuid.uuid4())[:8]
                filename = f"screenshot_{timestamp}_{task_id}.png"
                screenshot_path = str(Path(self.SCREENSHOT_DIR) / filename)
                cv2.imwrite(screenshot_path, img)

                # Audit log
                await self._audit_log(
                    "capture_screen",
                    f"Captured screen region={region is not None} saved={save}",
                    operator_user=operator_user,
                    metadata={"path": screenshot_path},
                )
                return screenshot_path
            
            return img

        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            await self._audit_log("error", f"Screen capture failed: {e}")
            raise

    def _draw_input_visualizations(self, img: np.ndarray):
        """Draw mouse and keyboard visualizations on the frame."""
        # Draw mouse cursor
        cv2.circle(img, self._mouse_pos, 10, (0, 0, 255), -1)

        # Draw mouse clicks
        current_time = time.time()
        for x, y, t in list(self._mouse_clicks):
            age = current_time - t
            if age < 1.0:
                radius = int(10 + age * 40)
                alpha = 1.0 - age
                overlay = img.copy()
                cv2.circle(overlay, (x, y), radius, (0, 255, 255), 2)
                cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
            else:
                self._mouse_clicks.remove((x, y, t))

        # Draw key presses
        for i, (key, t) in enumerate(list(self._key_presses)):
            age = current_time - t
            if age < 2.0:
                alpha = 1.0 - (age / 2.0)
                y_pos = img.shape[0] - 30 - (i * 20)
                cv2.putText(img, key, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            else:
                self._key_presses.remove((key, t))

    async def extract_text(
        self,
        image_path: Optional[str] = None,
        image_array: Optional[np.ndarray] = None,
        region: Optional[ScreenRegion] = None,
        operator_user: Optional[str] = None,
    ) -> str:
        """
        Extract text from screen or image using OCR.

        Args:
            image_path: Path to image file
            image_array: Numpy array of the image
            region: Optional region to analyze
            operator_user: User requesting operation

        Returns:
            Extracted text
        """
        if not self._check_authorization():
            raise PermissionError("Vision agent not authorized - check operator_enabled.yaml")

        if not self._pytesseract_available:
            raise RuntimeError("pytesseract not available - install with: apt-get install tesseract-ocr && pip install pytesseract")

        try:
            import pytesseract
            from PIL import Image

            # Get image
            if image_array is not None:
                img = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
            elif image_path:
                img = Image.open(image_path)
            else:
                # Capture screen first
                temp_path = await self.capture_screen(region=region, save=True, operator_user=operator_user)
                img = Image.open(temp_path)

            # Extract text
            text = pytesseract.image_to_string(img)

            # Audit log
            await self._audit_log(
                "extract_text",
                f"Extracted {len(text)} characters",
                operator_user=operator_user,
                metadata={"source": image_path or "screen", "text_length": len(text)},
            )

            return text.strip()

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            await self._audit_log("error", f"Text extraction failed: {e}")
            raise

    async def detect_ui_elements(
        self,
        image_path: Optional[str] = None,
        image_array: Optional[np.ndarray] = None,
        operator_user: Optional[str] = None,
    ) -> List[UIElement]:
        """
        Detect UI elements (buttons, text fields, etc.) in screen or image.

        Uses OCR data with bounding boxes to identify elements.
        """
        if not self._check_authorization():
            raise PermissionError("Vision agent not authorized - check operator_enabled.yaml")

        if not self._pytesseract_available:
            raise RuntimeError("pytesseract not available")

        try:
            import pytesseract
            from PIL import Image

            # Get image
            if image_array is not None:
                img = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
            elif image_path:
                img = Image.open(image_path)
            else:
                # Capture screen first
                temp_path = await self.capture_screen(save=True, operator_user=operator_user)
                img = Image.open(temp_path)

            # Get OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            # Extract UI elements
            elements = []
            n_boxes = len(ocr_data['text'])

            for i in range(n_boxes):
                text = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i])

                # Filter low confidence and empty text
                if conf > 30 and text:
                    element = UIElement(
                        element_type=self._classify_element(text),
                        text=text,
                        x=ocr_data['left'][i],
                        y=ocr_data['top'][i],
                        width=ocr_data['width'][i],
                        height=ocr_data['height'][i],
                        confidence=conf / 100.0,
                    )
                    elements.append(element)

            # Audit log
            await self._audit_log(
                "detect_ui_elements",
                f"Detected {len(elements)} UI elements",
                operator_user=operator_user,
                metadata={"element_count": len(elements)},
            )

            return elements

        except Exception as e:
            logger.error(f"UI element detection failed: {e}")
            await self._audit_log("error", f"UI element detection failed: {e}")
            raise

    def _classify_element(self, text: str) -> str:
        """Classify UI element type based on text content."""
        text_lower = text.lower()

        # Simple heuristic classification
        if any(word in text_lower for word in ['button', 'click', 'submit', 'ok', 'cancel']):
            return 'button'
        elif any(word in text_lower for word in ['enter', 'input', 'search']):
            return 'text_field'
        elif len(text.split()) > 5:
            return 'paragraph'
        elif text.isupper() and len(text) < 30:
            return 'header'
        else:
            return 'label'

    async def analyze_screen(
        self,
        region: Optional[ScreenRegion] = None,
        detect_elements: bool = True,
        operator_user: Optional[str] = None,
    ) -> ScreenAnalysis:
        """
        Comprehensive screen analysis - capture, OCR, and element detection.

        Returns complete analysis results.
        """
        if not self._check_authorization():
            raise PermissionError("Vision agent not authorized - check operator_enabled.yaml")

        start_time = time.time()
        task_id = str(uuid.uuid4())

        try:
            # Capture screen
            screenshot_path = await self.capture_screen(region=region, save=True, operator_user=operator_user)

            # Get screen size
            if self._mss_instance:
                monitor = self._mss_instance.monitors[1]
                screen_size = (monitor['width'], monitor['height'])
            else:
                screen_size = (0, 0)

            # Extract text
            ocr_text = ""
            if self._pytesseract_available:
                ocr_text = await self.extract_text(image_path=screenshot_path, operator_user=operator_user)

            # Detect UI elements
            ui_elements = []
            if detect_elements and self._pytesseract_available:
                ui_elements = await self.detect_ui_elements(image_path=screenshot_path, operator_user=operator_user)

            # Calculate analysis time
            analysis_time_ms = (time.time() - start_time) * 1000

            # Create analysis result
            analysis = ScreenAnalysis(
                task_id=task_id,
                timestamp=time.time(),
                screenshot_path=screenshot_path,
                ocr_text=ocr_text,
                ui_elements=ui_elements,
                screen_size=screen_size,
                analysis_time_ms=analysis_time_ms,
            )

            # Audit log
            await self._audit_log(
                "analyze_screen",
                f"Completed analysis in {analysis_time_ms:.1f}ms",
                operator_user=operator_user,
                metadata={
                    "task_id": task_id,
                    "text_length": len(ocr_text),
                    "elements_found": len(ui_elements),
                    "analysis_time_ms": analysis_time_ms,
                },
            )

            return analysis

        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            await self._audit_log("error", f"Screen analysis failed: {e}")
            raise

    def get_status(self) -> Dict:
        """Get vision agent status."""
        return {
            "running": self._running,
            "mss_available": self._mss_instance is not None,
            "pytesseract_available": self._pytesseract_available,
            "authorized": self._check_authorization(),
            "screenshot_dir": self.SCREENSHOT_DIR,
            "streaming": self._streaming,
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
_vision_agent_instance: Optional[VisionAgent] = None


def get_vision_agent() -> VisionAgent:
    """Get or create vision agent singleton."""
    global _vision_agent_instance
    if _vision_agent_instance is None:
        _vision_agent_instance = VisionAgent()
    return _vision_agent_instance


__all__ = ["VisionAgent", "get_vision_agent", "ScreenRegion", "UIElement", "ScreenAnalysis"]
