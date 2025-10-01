"""
Aurora Pro - Research automation system for discovering and analyzing AI tools.
"""
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from database import Database
from http_client import SafeHTTPClient
from extractor import ContentExtractor
from analyzer import AIAnalyzer
from ai_coordinator import AICoordinator
from browser_agent import BrowserAgent
from system_controller import KaliSystemController
from mouse_keyboard_agent import get_input_agent, InputActionType
from heartbeat_monitor import get_heartbeat_monitor
from vision_agent import get_vision_agent, ScreenRegion
from stealth_browser_agent import get_stealth_browser
from captcha_manager import get_captcha_manager, CaptchaType
from plugin_manager import get_plugin_manager
from multicore_manager import get_multicore_manager
from cache_manager import get_cache_manager
from proxy_manager import get_proxy_manager
from local_inference import get_local_inference
from llm_orchestrator import get_llm_orchestrator, LLMProvider, TaskType
from autonomous_engine import get_autonomous_engine
from reasoning_display import get_reasoning_display, ReasoningLevel
from control_center import get_control_center


# Prometheus metrics
REQUESTS_TOTAL = Counter("aurora_requests_total", "Total requests", ["endpoint", "status"])
FETCH_DURATION = Histogram("aurora_fetch_duration_seconds", "Time to fetch URL")
ANALYSIS_DURATION = Histogram("aurora_analysis_duration_seconds", "Time to analyze content")
DB_SIZE = Gauge("aurora_db_evidence_count", "Number of evidence records in database")


# Request/Response models
class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    id: str
    url: str
    title: Optional[str]
    score: float
    facets: dict


class EvidenceListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: list


class CommandRequest(BaseModel):
    command: str


class CommandResponse(BaseModel):
    result: str


class ConversationRequest(BaseModel):
    prompt: str
    agent: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class ConversationResponse(BaseModel):
    route: str
    response: str
    task: Optional[dict] = None
    history: List[dict]


class CLICommandRequest(BaseModel):
    prompt: str
    agent: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None


class CLITaskResponse(BaseModel):
    agent: str
    task: dict


class InputTaskRequest(BaseModel):
    action_type: str
    parameters: Dict
    operator_user: Optional[str] = None


class InputTaskResponse(BaseModel):
    task_id: str
    status: str
    action_type: str


# Global instances
db = Database()
extractor = ContentExtractor()
analyzer = AIAnalyzer()


# GUI coordination state
browser_agent: Optional[BrowserAgent] = None
system_controller: Optional[KaliSystemController] = None
coordinator: Optional[AICoordinator] = None
input_agent = None
heartbeat_monitor = None

# Enhanced features
vision_agent = None
stealth_browser = None
captcha_manager = None
plugin_manager = None
multicore_manager = None
cache_manager = None
proxy_manager = None
local_inference = None

# New autonomous features
llm_orchestrator = None
autonomous_engine = None
reasoning_display = None
control_center = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared services on startup."""
    global coordinator, browser_agent, system_controller, input_agent, heartbeat_monitor
    global vision_agent, stealth_browser, captcha_manager, plugin_manager
    global multicore_manager, cache_manager, proxy_manager, local_inference
    global llm_orchestrator, autonomous_engine, reasoning_display, control_center

    await db.initialize()
    browser_agent = BrowserAgent()
    system_controller = KaliSystemController()
    coordinator = AICoordinator(browser_agent, system_controller, db, analyzer)
    await coordinator.start()

    # Initialize input agent
    input_agent = get_input_agent()
    await input_agent.start()

    # Initialize heartbeat monitor
    heartbeat_monitor = get_heartbeat_monitor()
    await heartbeat_monitor.start()

    # Initialize enhanced features
    try:
        vision_agent = get_vision_agent()
        await vision_agent.start()
    except Exception as e:
        logger.warning(f"Vision agent failed to start: {e} - continuing without it")
        vision_agent = None

    stealth_browser = get_stealth_browser()
    await stealth_browser.start()

    # Get 2Captcha API key from environment
    captcha_api_key = os.getenv("TWOCAPTCHA_API_KEY")
    captcha_manager = get_captcha_manager(api_key=captcha_api_key)
    await captcha_manager.start()

    plugin_manager = get_plugin_manager()
    await plugin_manager.start()

    multicore_manager = get_multicore_manager(num_workers=30)
    await multicore_manager.start()

    cache_manager = get_cache_manager(memory_size_mb=2048)
    await cache_manager.start()

    proxy_manager = get_proxy_manager()
    await proxy_manager.start()

    local_inference = get_local_inference()
    await local_inference.start()

    # Initialize new autonomous features
    llm_orchestrator = get_llm_orchestrator()
    await llm_orchestrator.start()

    autonomous_engine = get_autonomous_engine()
    await autonomous_engine.start()

    reasoning_display = get_reasoning_display()
    await reasoning_display.start()

    control_center = get_control_center()
    await control_center.start()

    try:
        yield
    finally:
        # Cleanup new features first
        if control_center:
            await control_center.stop()
        if reasoning_display:
            await reasoning_display.stop()
        if autonomous_engine:
            await autonomous_engine.stop()
        if llm_orchestrator:
            await llm_orchestrator.stop()
        # Cleanup in reverse order
        if local_inference:
            await local_inference.stop()
        if proxy_manager:
            await proxy_manager.stop()
        if cache_manager:
            await cache_manager.stop()
        if multicore_manager:
            await multicore_manager.stop()
        if plugin_manager:
            await plugin_manager.stop()
        if captcha_manager:
            await captcha_manager.stop()
        if stealth_browser:
            await stealth_browser.stop()
        if vision_agent:
            await vision_agent.stop()
        if heartbeat_monitor:
            await heartbeat_monitor.stop()
        if coordinator:
            await coordinator.shutdown()
        if browser_agent:
            await browser_agent.shutdown()
        if input_agent:
            await input_agent.stop()


app = FastAPI(
    title="Aurora Pro",
    description="Research automation system for discovering and analyzing AI tools",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    REQUESTS_TOTAL.labels(endpoint="root", status="success").inc()
    return {
        "service": "Aurora Pro",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    REQUESTS_TOTAL.labels(endpoint="health", status="success").inc()
    count = await db.count_evidence()
    DB_SIZE.set(count)
    return {
        "status": "healthy",
        "database": "connected",
        "evidence_count": count
    }


@app.post("/analyze", response_model=AnalyzeResponse, status_code=201)
async def analyze_url(request: AnalyzeRequest):
    """
    Analyze a URL for AI-related content.

    Fetches the URL (with SSRF protection), extracts content, analyzes for
    AI features, scores it, and stores in database.
    """
    url = str(request.url)

    try:
        # Fetch content
        with FETCH_DURATION.time():
            async with SafeHTTPClient() as client:
                response = await client.fetch(url)

        if not response:
            REQUESTS_TOTAL.labels(endpoint="analyze", status="blocked").inc()
            raise HTTPException(
                status_code=403,
                detail="URL blocked by security policy (SSRF, robots.txt, or rate limit)"
            )

        if response.status_code != 200:
            REQUESTS_TOTAL.labels(endpoint="analyze", status="http_error").inc()
            raise HTTPException(
                status_code=400,
                detail=f"HTTP {response.status_code} from target URL"
            )

        # Extract content
        html = response.text
        extracted = extractor.extract(html, url)

        if not extracted["text"]:
            REQUESTS_TOTAL.labels(endpoint="analyze", status="extraction_failed").inc()
            raise HTTPException(
                status_code=422,
                detail="Failed to extract content from URL"
            )

        # Analyze for AI features
        with ANALYSIS_DURATION.time():
            analysis = analyzer.analyze(extracted["text"], extracted["title"])

        # Store in database
        evidence_id = await db.insert_evidence(
            url=url,
            title=extracted["title"],
            score=analysis["score"],
            facets=analysis["facets"]
        )

        REQUESTS_TOTAL.labels(endpoint="analyze", status="success").inc()
        DB_SIZE.inc()

        return AnalyzeResponse(
            id=evidence_id,
            url=url,
            title=extracted["title"],
            score=analysis["score"],
            facets=analysis["facets"]
        )

    except HTTPException:
        raise
    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="analyze", status="error").inc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/evidence/{evidence_id}", response_model=AnalyzeResponse)
async def get_evidence(evidence_id: str):
    """Retrieve evidence by ID."""
    evidence = await db.get_evidence(evidence_id)

    if not evidence:
        REQUESTS_TOTAL.labels(endpoint="get_evidence", status="not_found").inc()
        raise HTTPException(status_code=404, detail="Evidence not found")

    REQUESTS_TOTAL.labels(endpoint="get_evidence", status="success").inc()
    return AnalyzeResponse(
        id=evidence["id"],
        url=evidence["url"],
        title=evidence["title"],
        score=evidence["score"],
        facets=evidence["facets"]
    )


@app.get("/evidence", response_model=EvidenceListResponse)
async def list_evidence(
    limit: int = 100,
    offset: int = 0,
    min_score: Optional[float] = None
):
    """List evidence with optional filtering."""
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 1000")

    results = await db.list_evidence(limit=limit, offset=offset, min_score=min_score)
    total = await db.count_evidence(min_score=min_score)

    REQUESTS_TOTAL.labels(endpoint="list_evidence", status="success").inc()
    return EvidenceListResponse(
        total=total,
        limit=limit,
        offset=offset,
        results=results
    )


@app.post("/gui/command", response_model=CommandResponse)
async def gui_command(request: CommandRequest):
    """Execute a natural language command via the shared coordinator."""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Coordinator not ready")
    result = await coordinator.process_command(request.command)
    return CommandResponse(result=result)


@app.get("/gui/context")
async def gui_context():
    """Expose coordinator snapshot for GUI dashboards."""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Coordinator not ready")
    return coordinator.snapshot()


@app.post("/cli/command", response_model=CLITaskResponse, status_code=202)
async def cli_command(request: CLICommandRequest):
    """Submit a CLI task to Claude or Codex agents."""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Coordinator not ready")
    payload_metadata = request.metadata or {}
    if request.timeout is not None:
        payload_metadata = {**payload_metadata, "timeout": str(request.timeout)}
    REQUESTS_TOTAL.labels(endpoint="cli_command", status="received").inc()
    result = await coordinator.submit_cli_task(
        request.prompt,
        agent=request.agent,
        metadata=payload_metadata,
    )
    REQUESTS_TOTAL.labels(endpoint="cli_command", status="success").inc()
    return CLITaskResponse(**result)


@app.get("/cli/logs")
async def cli_logs(agent: Optional[str] = None, limit: int = 100):
    """Fetch recent CLI log entries for dashboard streaming."""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Coordinator not ready")
    limit = max(1, min(limit, 200))
    REQUESTS_TOTAL.labels(endpoint="cli_logs", status="success").inc()
    logs = await coordinator.cli_logs(agent=agent, limit=limit)
    return {"logs": logs}


@app.get("/cli/status")
async def cli_status():
    """Return current CLI task status per agent."""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Coordinator not ready")
    REQUESTS_TOTAL.labels(endpoint="cli_status", status="success").inc()
    return {"agents": coordinator.cli_status()}


@app.post("/agent/message", response_model=ConversationResponse, status_code=202)
async def agent_message(request: ConversationRequest):
    """Handle conversational prompt routed through the agent coordinator."""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Coordinator not ready")
    REQUESTS_TOTAL.labels(endpoint="agent_message", status="received").inc()
    result = await coordinator.handle_conversation(
        request.prompt,
        agent_preference=request.agent,
        metadata=request.metadata,
    )
    REQUESTS_TOTAL.labels(endpoint="agent_message", status="success").inc()
    return ConversationResponse(
        route=result.get("route", ""),
        response=result.get("response", ""),
        task=result.get("task"),
        history=result.get("history", []),
    )


@app.get("/agent/state")
async def agent_state():
    """Expose current conversational snapshot."""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Coordinator not ready")
    REQUESTS_TOTAL.labels(endpoint="agent_state", status="success").inc()
    return coordinator.agent_router.snapshot()


@app.post("/input/submit", response_model=InputTaskResponse, status_code=202)
async def submit_input_task(request: InputTaskRequest):
    """Submit a mouse/keyboard input task."""
    if input_agent is None:
        raise HTTPException(status_code=503, detail="Input agent not ready")

    try:
        action_type = InputActionType(request.action_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid action_type: {request.action_type}")

    try:
        task = await input_agent.submit_task(
            action_type=action_type,
            parameters=request.parameters,
            operator_user=request.operator_user,
        )
        REQUESTS_TOTAL.labels(endpoint="input_submit", status="success").inc()
        return InputTaskResponse(
            task_id=task.task_id,
            status=task.status,
            action_type=task.action_type.value,
        )
    except PermissionError as exc:
        REQUESTS_TOTAL.labels(endpoint="input_submit", status="unauthorized").inc()
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:
        REQUESTS_TOTAL.labels(endpoint="input_submit", status="error").inc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/input/status")
async def input_status():
    """Get input agent status and recent tasks."""
    if input_agent is None:
        raise HTTPException(status_code=503, detail="Input agent not ready")

    tasks = input_agent.list_tasks(limit=20)
    queue_size = input_agent.get_queue_size()
    screen_size = input_agent.get_screen_size()
    mouse_pos = input_agent.get_mouse_position()

    REQUESTS_TOTAL.labels(endpoint="input_status", status="success").inc()
    return {
        "queue_size": queue_size,
        "screen_size": {"width": screen_size[0], "height": screen_size[1]},
        "mouse_position": {"x": mouse_pos[0], "y": mouse_pos[1]},
        "recent_tasks": [task.to_dict() for task in tasks],
    }


@app.get("/input/task/{task_id}")
async def get_input_task(task_id: str):
    """Get specific input task details."""
    if input_agent is None:
        raise HTTPException(status_code=503, detail="Input agent not ready")

    task = input_agent.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    REQUESTS_TOTAL.labels(endpoint="input_task", status="success").inc()
    return task.to_dict()


@app.get("/health/status")
async def health_status():
    """Get comprehensive health status from all components."""
    if heartbeat_monitor is None:
        raise HTTPException(status_code=503, detail="Heartbeat monitor not ready")

    try:
        # Get component health (pass actual instances)
        cli_agent_instance = coordinator.cli_agent if coordinator else None
        health = await heartbeat_monitor.get_component_health(
            cli_agent=cli_agent_instance,
            input_agent=input_agent,
            coordinator=coordinator,
        )
        REQUESTS_TOTAL.labels(endpoint="health_status", status="success").inc()
        return health
    except Exception as exc:
        REQUESTS_TOTAL.labels(endpoint="health_status", status="error").inc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health/heartbeat")
async def health_heartbeat():
    """Get recent heartbeat entries."""
    if heartbeat_monitor is None:
        raise HTTPException(status_code=503, detail="Heartbeat monitor not ready")

    health = await heartbeat_monitor.get_health_status()
    REQUESTS_TOTAL.labels(endpoint="health_heartbeat", status="success").inc()
    return health


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================================================================
# Enhanced Features Endpoints
# ============================================================================

# Vision Agent Endpoints
@app.post("/vision/analyze")
async def vision_analyze(
    region_x: Optional[int] = None,
    region_y: Optional[int] = None,
    region_width: Optional[int] = None,
    region_height: Optional[int] = None,
    detect_elements: bool = True,
    operator_user: Optional[str] = None,
):
    """Analyze screen with OCR and element detection."""
    if vision_agent is None:
        raise HTTPException(status_code=503, detail="Vision agent not ready")

    try:
        region = None
        if all(v is not None for v in [region_x, region_y, region_width, region_height]):
            region = ScreenRegion(
                x=region_x,
                y=region_y,
                width=region_width,
                height=region_height,
            )

        analysis = await vision_agent.analyze_screen(
            region=region,
            detect_elements=detect_elements,
            operator_user=operator_user,
        )

        REQUESTS_TOTAL.labels(endpoint="vision_analyze", status="success").inc()
        return {
            "task_id": analysis.task_id,
            "timestamp": analysis.timestamp,
            "screenshot_path": analysis.screenshot_path,
            "ocr_text": analysis.ocr_text,
            "ui_elements": [
                {
                    "type": el.element_type,
                    "text": el.text,
                    "x": el.x,
                    "y": el.y,
                    "width": el.width,
                    "height": el.height,
                    "confidence": el.confidence,
                }
                for el in analysis.ui_elements
            ],
            "screen_size": {"width": analysis.screen_size[0], "height": analysis.screen_size[1]},
            "analysis_time_ms": analysis.analysis_time_ms,
        }

    except PermissionError as e:
        REQUESTS_TOTAL.labels(endpoint="vision_analyze", status="unauthorized").inc()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="vision_analyze", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vision/start_streaming")
async def start_vision_streaming():
    """Start the Vision Agent's real-time streaming."""
    try:
        await get_vision_agent().start_streaming()
        return {"status": "Vision agent streaming started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/stop_streaming")
async def stop_vision_streaming():
    """Stop the Vision Agent's real-time streaming."""
    try:
        await get_vision_agent().stop_streaming()
        return {"status": "Vision agent streaming stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vision/status")
async def vision_status():
    """Get vision agent status."""
    if vision_agent is None:
        raise HTTPException(status_code=503, detail="Vision agent not ready")

    status = vision_agent.get_status()
    REQUESTS_TOTAL.labels(endpoint="vision_status", status="success").inc()
    return status


# Stealth Browser Endpoints
@app.post("/browser/stealth/navigate")
async def stealth_navigate(
    url: str,
    wait_time: float = 2.0,
    operator_user: Optional[str] = None,
):
    """Navigate to URL using stealth browser."""
    if stealth_browser is None:
        raise HTTPException(status_code=503, detail="Stealth browser not ready")

    try:
        result = await stealth_browser.navigate(url, wait_time, operator_user)
        REQUESTS_TOTAL.labels(endpoint="stealth_navigate", status="success").inc()
        return result
    except PermissionError as e:
        REQUESTS_TOTAL.labels(endpoint="stealth_navigate", status="unauthorized").inc()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="stealth_navigate", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/browser/stealth/status")
async def stealth_browser_status():
    """Get stealth browser status."""
    if stealth_browser is None:
        raise HTTPException(status_code=503, detail="Stealth browser not ready")

    status = stealth_browser.get_status()
    REQUESTS_TOTAL.labels(endpoint="stealth_browser_status", status="success").inc()
    return status


# CAPTCHA Solver Endpoints
@app.post("/captcha/solve")
async def solve_captcha(
    captcha_type: str,
    site_key: str,
    page_url: str,
    action: Optional[str] = None,
    min_score: Optional[float] = None,
    operator_user: Optional[str] = None,
):
    """Solve CAPTCHA using 2Captcha service."""
    if captcha_manager is None:
        raise HTTPException(status_code=503, detail="CAPTCHA manager not ready")

    try:
        if captcha_type == "recaptcha_v2":
            solution = await captcha_manager.solve_recaptcha_v2(
                site_key, page_url, operator_user
            )
        elif captcha_type == "recaptcha_v3":
            solution = await captcha_manager.solve_recaptcha_v3(
                site_key, page_url, action or "verify", min_score or 0.3, operator_user
            )
        elif captcha_type == "hcaptcha":
            solution = await captcha_manager.solve_hcaptcha(
                site_key, page_url, operator_user
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported CAPTCHA type: {captcha_type}")

        REQUESTS_TOTAL.labels(endpoint="solve_captcha", status="success").inc()
        return {
            "task_id": solution.task_id,
            "captcha_type": solution.captcha_type.value,
            "solution": solution.solution,
            "solve_time_sec": solution.solve_time_sec,
            "cost": solution.cost,
            "status": solution.status,
        }

    except PermissionError as e:
        REQUESTS_TOTAL.labels(endpoint="solve_captcha", status="unauthorized").inc()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="solve_captcha", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/captcha/stats")
async def captcha_stats():
    """Get CAPTCHA solving statistics."""
    if captcha_manager is None:
        raise HTTPException(status_code=503, detail="CAPTCHA manager not ready")

    stats = captcha_manager.get_statistics()
    REQUESTS_TOTAL.labels(endpoint="captcha_stats", status="success").inc()
    return stats


# Plugin Manager Endpoints
@app.get("/plugins/list")
async def list_plugins():
    """List all loaded plugins."""
    if plugin_manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not ready")

    plugins = plugin_manager.list_plugins()
    REQUESTS_TOTAL.labels(endpoint="list_plugins", status="success").inc()
    return {"plugins": plugins}


@app.get("/plugins/discover")
async def discover_plugins():
    """Discover available plugins in plugins directory."""
    if plugin_manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not ready")

    plugins = await plugin_manager.discover_plugins()
    REQUESTS_TOTAL.labels(endpoint="discover_plugins", status="success").inc()
    return {"available_plugins": plugins}


@app.post("/plugins/load")
async def load_plugin(
    plugin_name: str,
    operator_user: Optional[str] = None,
):
    """Load a plugin."""
    if plugin_manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not ready")

    try:
        instance = await plugin_manager.load_plugin(plugin_name, operator_user)
        REQUESTS_TOTAL.labels(endpoint="load_plugin", status="success").inc()
        return {
            "plugin_id": instance.plugin_id,
            "name": instance.metadata.name,
            "version": instance.metadata.version,
            "loaded_at": instance.loaded_at,
        }
    except PermissionError as e:
        REQUESTS_TOTAL.labels(endpoint="load_plugin", status="unauthorized").inc()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="load_plugin", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plugins/unload")
async def unload_plugin(
    plugin_name: str,
    operator_user: Optional[str] = None,
):
    """Unload a plugin."""
    if plugin_manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not ready")

    try:
        await plugin_manager.unload_plugin(plugin_name, operator_user)
        REQUESTS_TOTAL.labels(endpoint="unload_plugin", status="success").inc()
        return {"status": "unloaded", "plugin_name": plugin_name}
    except PermissionError as e:
        REQUESTS_TOTAL.labels(endpoint="unload_plugin", status="unauthorized").inc()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="unload_plugin", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


# Cache Manager Endpoints
@app.post("/cache/clear")
async def clear_cache(namespace: Optional[str] = None):
    """Clear cache (all tiers or specific namespace)."""
    if cache_manager is None:
        raise HTTPException(status_code=503, detail="Cache manager not ready")

    try:
        if namespace:
            await cache_manager.clear_namespace(namespace)
        else:
            await cache_manager.clear_all()

        REQUESTS_TOTAL.labels(endpoint="clear_cache", status="success").inc()
        return {"status": "cleared", "namespace": namespace or "all"}
    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="clear_cache", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    if cache_manager is None:
        raise HTTPException(status_code=503, detail="Cache manager not ready")

    stats = await cache_manager.get_statistics()
    REQUESTS_TOTAL.labels(endpoint="cache_stats", status="success").inc()
    return stats


# Enhanced Router Status
@app.get("/router/status")
async def router_status():
    """Get enhanced router status."""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Coordinator not ready")

    REQUESTS_TOTAL.labels(endpoint="router_status", status="success").inc()
    return {
        "multicore_available": multicore_manager is not None,
        "cache_available": cache_manager is not None,
        "vision_available": vision_agent is not None,
        "stealth_browser_available": stealth_browser is not None,
        "local_inference_available": local_inference is not None,
        "proxy_available": proxy_manager is not None,
    }


# Local Inference Endpoints
@app.post("/inference/local")
async def local_inference_generate(
    prompt: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    operator_user: Optional[str] = None,
):
    """Generate response using local LLM (Ollama)."""
    if local_inference is None:
        raise HTTPException(status_code=503, detail="Local inference not ready")

    try:
        response = await local_inference.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            operator_user=operator_user,
        )

        REQUESTS_TOTAL.labels(endpoint="local_inference", status="success").inc()
        return {
            "request_id": response.request_id,
            "model": response.model,
            "response": response.response,
            "tokens_generated": response.tokens_generated,
            "inference_time_sec": response.inference_time_sec,
            "tokens_per_sec": response.tokens_per_sec,
        }

    except PermissionError as e:
        REQUESTS_TOTAL.labels(endpoint="local_inference", status="unauthorized").inc()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="local_inference", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/inference/models")
async def list_inference_models():
    """List available local inference models."""
    if local_inference is None:
        raise HTTPException(status_code=503, detail="Local inference not ready")

    models = await local_inference.list_models()
    REQUESTS_TOTAL.labels(endpoint="list_models", status="success").inc()
    return {"models": models}


@app.get("/inference/status")
async def inference_status():
    """Get local inference engine status."""
    if local_inference is None:
        raise HTTPException(status_code=503, detail="Local inference not ready")

    status = local_inference.get_status()
    REQUESTS_TOTAL.labels(endpoint="inference_status", status="success").inc()
    return status


# Multicore Manager Endpoints
@app.get("/multicore/stats")
async def multicore_stats():
    """Get multicore manager statistics."""
    if multicore_manager is None:
        raise HTTPException(status_code=503, detail="Multicore manager not ready")

    stats = multicore_manager.get_statistics()
    REQUESTS_TOTAL.labels(endpoint="multicore_stats", status="success").inc()
    return stats


@app.get("/multicore/status")
async def multicore_status():
    """Get multicore manager status."""
    if multicore_manager is None:
        raise HTTPException(status_code=503, detail="Multicore manager not ready")

    status = multicore_manager.get_status()
    REQUESTS_TOTAL.labels(endpoint="multicore_status", status="success").inc()
    return status


@app.get("/proxy/stats")
async def proxy_stats():
    """Get proxy manager statistics."""
    if proxy_manager is None:
        raise HTTPException(status_code=503, detail="Proxy manager not ready")

    stats = proxy_manager.get_statistics()
    REQUESTS_TOTAL.labels(endpoint="proxy_stats", status="success").inc()
    return stats


@app.get("/proxy/list")
async def proxy_list():
    """List all proxies."""
    if proxy_manager is None:
        raise HTTPException(status_code=503, detail="Proxy manager not ready")

    proxies = proxy_manager.list_proxies()
    REQUESTS_TOTAL.labels(endpoint="proxy_list", status="success").inc()
    return {"proxies": proxies}


# ============================================================================
# New Autonomous Features Endpoints
# ============================================================================

# LLM Orchestrator Endpoints
@app.post("/llm/generate")
async def llm_generate(
    prompt: str,
    task_type: Optional[str] = None,
    preferred_provider: Optional[str] = None,
    max_cost_usd: Optional[float] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
):
    """Generate response using multi-LLM orchestrator."""
    if llm_orchestrator is None:
        raise HTTPException(status_code=503, detail="LLM Orchestrator not ready")

    try:
        task_type_enum = TaskType(task_type) if task_type else None
        provider_enum = LLMProvider(preferred_provider) if preferred_provider else None

        response = await llm_orchestrator.generate(
            prompt=prompt,
            task_type=task_type_enum,
            preferred_provider=provider_enum,
            max_cost_usd=max_cost_usd,
            system_prompt=system_prompt,
            temperature=temperature,
        )

        REQUESTS_TOTAL.labels(endpoint="llm_generate", status="success").inc()
        return {
            "provider": response.provider.value,
            "response": response.response,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "latency_ms": response.latency_ms,
            "cost_usd": response.cost_usd,
        }

    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="llm_generate", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/llm/stats")
async def llm_stats():
    """Get LLM orchestrator statistics."""
    if llm_orchestrator is None:
        raise HTTPException(status_code=503, detail="LLM Orchestrator not ready")

    stats = llm_orchestrator.get_statistics()
    REQUESTS_TOTAL.labels(endpoint="llm_stats", status="success").inc()
    return stats


@app.get("/llm/status")
async def llm_status():
    """Get LLM orchestrator status."""
    if llm_orchestrator is None:
        raise HTTPException(status_code=503, detail="LLM Orchestrator not ready")

    status = llm_orchestrator.get_status()
    REQUESTS_TOTAL.labels(endpoint="llm_status", status="success").inc()
    return status


# Autonomous Engine Endpoints
@app.post("/autonomous/execute")
async def autonomous_execute(
    request: str,
    max_actions: int = 50,
    operator_user: Optional[str] = None,
):
    """Execute autonomous workflow."""
    if autonomous_engine is None:
        raise HTTPException(status_code=503, detail="Autonomous Engine not ready")

    try:
        workflow = await autonomous_engine.execute_request(
            request=request,
            max_actions=max_actions,
            operator_user=operator_user,
        )

        REQUESTS_TOTAL.labels(endpoint="autonomous_execute", status="success").inc()
        return {
            "workflow_id": workflow.workflow_id,
            "status": workflow.status.value,
            "total_actions": workflow.total_actions,
            "completed_actions": workflow.completed_actions,
            "failed_actions": workflow.failed_actions,
            "reasoning_chain": workflow.reasoning_chain,
        }

    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="autonomous_execute", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/autonomous/workflow/{workflow_id}")
async def autonomous_workflow(workflow_id: str):
    """Get workflow details."""
    if autonomous_engine is None:
        raise HTTPException(status_code=503, detail="Autonomous Engine not ready")

    workflow = autonomous_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    REQUESTS_TOTAL.labels(endpoint="autonomous_workflow", status="success").inc()
    return {
        "workflow_id": workflow.workflow_id,
        "description": workflow.description,
        "status": workflow.status.value,
        "created_at": workflow.created_at,
        "completed_at": workflow.completed_at,
        "total_actions": workflow.total_actions,
        "completed_actions": workflow.completed_actions,
        "reasoning_chain": workflow.reasoning_chain,
    }


@app.get("/autonomous/workflows")
async def autonomous_workflows(limit: int = 20):
    """List recent workflows."""
    if autonomous_engine is None:
        raise HTTPException(status_code=503, detail="Autonomous Engine not ready")

    workflows = autonomous_engine.list_workflows(limit=limit)
    REQUESTS_TOTAL.labels(endpoint="autonomous_workflows", status="success").inc()
    return {"workflows": workflows}


@app.get("/autonomous/status")
async def autonomous_status():
    """Get autonomous engine status."""
    if autonomous_engine is None:
        raise HTTPException(status_code=503, detail="Autonomous Engine not ready")

    status = autonomous_engine.get_status()
    REQUESTS_TOTAL.labels(endpoint="autonomous_status", status="success").inc()
    return status


# Reasoning Display Endpoints
@app.post("/reasoning/context/begin")
async def reasoning_begin_context(
    task_description: str,
    context_id: Optional[str] = None,
):
    """Begin a new reasoning context."""
    if reasoning_display is None:
        raise HTTPException(status_code=503, detail="Reasoning Display not ready")

    context_id = await reasoning_display.begin_context(task_description, context_id)
    REQUESTS_TOTAL.labels(endpoint="reasoning_begin_context", status="success").inc()
    return {"context_id": context_id}


@app.post("/reasoning/context/end")
async def reasoning_end_context(
    context_id: str,
    status: str = "completed",
):
    """End a reasoning context."""
    if reasoning_display is None:
        raise HTTPException(status_code=503, detail="Reasoning Display not ready")

    await reasoning_display.end_context(context_id, status)
    REQUESTS_TOTAL.labels(endpoint="reasoning_end_context", status="success").inc()
    return {"status": "ended"}


@app.post("/reasoning/thought")
async def reasoning_add_thought(
    thought: str,
    component: str,
    level: str = "info",
    confidence: float = 1.0,
    context_id: Optional[str] = None,
):
    """Add a reasoning thought."""
    if reasoning_display is None:
        raise HTTPException(status_code=503, detail="Reasoning Display not ready")

    try:
        level_enum = ReasoningLevel(level)
        step = await reasoning_display.add_thought(
            thought=thought,
            component=component,
            level=level_enum,
            confidence=confidence,
            context_id=context_id,
        )

        REQUESTS_TOTAL.labels(endpoint="reasoning_add_thought", status="success").inc()
        return {"step_id": step.step_id, "timestamp": step.timestamp}

    except Exception as e:
        REQUESTS_TOTAL.labels(endpoint="reasoning_add_thought", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reasoning/steps")
async def reasoning_steps(limit: int = 50):
    """Get recent reasoning steps."""
    if reasoning_display is None:
        raise HTTPException(status_code=503, detail="Reasoning Display not ready")

    steps = reasoning_display.get_recent_steps(limit=limit)
    REQUESTS_TOTAL.labels(endpoint="reasoning_steps", status="success").inc()
    return {"steps": steps}


@app.get("/reasoning/contexts")
async def reasoning_contexts(limit: int = 20):
    """List recent reasoning contexts."""
    if reasoning_display is None:
        raise HTTPException(status_code=503, detail="Reasoning Display not ready")

    contexts = reasoning_display.list_contexts(limit=limit)
    REQUESTS_TOTAL.labels(endpoint="reasoning_contexts", status="success").inc()
    return {"contexts": contexts}


@app.get("/reasoning/status")
async def reasoning_status():
    """Get reasoning display status."""
    if reasoning_display is None:
        raise HTTPException(status_code=503, detail="Reasoning Display not ready")

    status = reasoning_display.get_status()
    REQUESTS_TOTAL.labels(endpoint="reasoning_status", status="success").inc()
    return status


# Control Center Endpoints
@app.post("/control/emergency-stop")
async def control_emergency_stop(reason: str = "Manual trigger"):
    """EMERGENCY STOP - Kill all operations."""
    if control_center is None:
        raise HTTPException(status_code=503, detail="Control Center not ready")

    await control_center.emergency_stop(reason)
    REQUESTS_TOTAL.labels(endpoint="emergency_stop", status="success").inc()
    return {"status": "stopped", "reason": reason}


@app.post("/control/restart")
async def control_restart():
    """Restart all system components."""
    if control_center is None:
        raise HTTPException(status_code=503, detail="Control Center not ready")

    await control_center.restart_system()
    REQUESTS_TOTAL.labels(endpoint="control_restart", status="success").inc()
    return {"status": "restarted"}


@app.get("/control/metrics")
async def control_metrics():
    """Get current system metrics."""
    if control_center is None:
        raise HTTPException(status_code=503, detail="Control Center not ready")

    status = await control_center._collect_full_status()
    REQUESTS_TOTAL.labels(endpoint="control_metrics", status="success").inc()
    return status


@app.get("/control/metrics/history")
async def control_metrics_history(minutes: int = 5):
    """Get historical metrics."""
    if control_center is None:
        raise HTTPException(status_code=503, detail="Control Center not ready")

    history = control_center.get_metrics_history(minutes=minutes)
    REQUESTS_TOTAL.labels(endpoint="control_metrics_history", status="success").inc()
    return {"history": history}


@app.get("/control/status")
async def control_status():
    """Get control center status."""
    if control_center is None:
        raise HTTPException(status_code=503, detail="Control Center not ready")

    status = control_center.get_status()
    REQUESTS_TOTAL.labels(endpoint="control_status", status="success").inc()
    return status
