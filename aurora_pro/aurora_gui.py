"""Aurora Comet GUI built with Streamlit."""
import asyncio
import contextlib
import io
import logging
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import speech_recognition as sr
import streamlit as st
from PIL import Image
from fpdf import FPDF
from streamlit_ace import st_ace
from streamlit_elements import elements, mui, dashboard

from ai_coordinator import AICoordinator
from analyzer import AIAnalyzer
from browser_agent import BrowserAgent
from database import Database
from extractor import ContentExtractor
from http_client import SafeHTTPClient
from system_controller import KaliSystemController

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Container for analysis metadata."""

    url: str
    title: str
    score: float
    facets: Dict[str, Any]


class AsyncAppState:
    """Manages shared async resources for the Streamlit session."""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.browser: Optional[BrowserAgent] = None
        self.system: Optional[KaliSystemController] = None
        self.database: Optional[Database] = None
        self.analyzer: Optional[AIAnalyzer] = None
        self.extractor: Optional[ContentExtractor] = None
        self.coordinator: Optional[AICoordinator] = None
        self.run(self._initialize())

    async def _initialize(self) -> None:
        self.browser = BrowserAgent()
        self.system = KaliSystemController()
        self.database = Database()
        self.analyzer = AIAnalyzer()
        self.extractor = ContentExtractor()
        self.coordinator = AICoordinator(self.browser, self.system, self.database, self.analyzer)
        await self.database.initialize()
        await self.coordinator.start()

    def run(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def stop(self) -> None:
        if self.coordinator:
            with contextlib.suppress(Exception):
                self.run(self.coordinator.shutdown())
        if self.browser:
            with contextlib.suppress(Exception):
                self.run(self.browser.shutdown())
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=2)


def get_app_state() -> AsyncAppState:
    if "aurora_async_state" not in st.session_state:
        st.session_state["aurora_async_state"] = AsyncAppState()
    return st.session_state["aurora_async_state"]


def init_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("analysis_results", [])
    st.session_state.setdefault("workflow_steps", [])
    st.session_state.setdefault("screen_recordings", [])


def render_sidebar(app_state: AsyncAppState) -> None:
    st.sidebar.title("Aurora Comet Agent")
    st.sidebar.caption("Natural language interface controlling browser, system, and analytics.")

    for message in st.session_state["messages"][-12:]:
        role = message.get("role", "assistant")
        with st.sidebar.chat_message(role):
            st.markdown(message.get("content", ""))

    audio = st.sidebar.audio_input("Voice command")
    if audio is not None:
        transcript = transcribe_audio(audio)
        if transcript:
            st.sidebar.success(f"Voice: {transcript}")
            enqueue_command(app_state, transcript)

    chat_input = st.sidebar.chat_input("Command the agent…")
    if chat_input:
        enqueue_command(app_state, chat_input)

    st.sidebar.markdown("---")
    camera_image = st.sidebar.camera_input("Capture context")
    if camera_image is not None:
        st.sidebar.image(camera_image)

    if app_state.coordinator:
        snapshot = app_state.coordinator.snapshot()
        st.sidebar.metric("Queued Tasks", len(snapshot.get("tasks", [])))
        st.sidebar.json(snapshot, expanded=False)


def enqueue_command(app_state: AsyncAppState, command: str) -> None:
    st.session_state["messages"].append({"role": "user", "content": command})
    try:
        response = app_state.run(app_state.coordinator.process_command(command))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Command processing failed")
        response = f"Command failed: {exc}"
    st.session_state["messages"].append({"role": "assistant", "content": response})


def transcribe_audio(audio) -> Optional[str]:
    recognizer = sr.Recognizer()
    buffer = io.BytesIO(audio.getvalue())
    try:
        with sr.AudioFile(buffer) as source:
            audio_record = recognizer.record(source)
        return recognizer.recognize_google(audio_record)
    except sr.UnknownValueError:
        st.sidebar.warning("Could not understand audio")
    except sr.RequestError as exc:
        st.sidebar.error(f"Speech service error: {exc}")
    except Exception as exc:  # noqa: BLE001
        st.sidebar.error(f"Audio processing error: {exc}")
    return None


def render_research_console(app_state: AsyncAppState) -> None:
    st.subheader("Research Console")
    url = st.text_input("Target URL", placeholder="https://example.com/ai")
    cols = st.columns(2)
    with cols[0]:
        scrape_button = st.button("Analyze URL", type="primary")
    with cols[1]:
        uploads = st.file_uploader("Upload reports", accept_multiple_files=True)
        for uploaded in uploads or []:
            st.success(f"Uploaded {uploaded.name}")

    if scrape_button and url:
        with st.spinner("Analyzing URL with Aurora backend…"):
            result = analyze_url(app_state, url)
            if result:
                st.session_state["analysis_results"].append(result)
                st.success(f"Captured {result.title or result.url}")
            else:
                st.error("Analysis failed or blocked by SSRF policy")

    if st.session_state["analysis_results"]:
        df = pd.DataFrame([
            {
                "URL": res.url,
                "Title": res.title,
                "Score": res.score,
                "Facets": ", ".join(f"{k}:{v}" for k, v in res.facets.items()),
            }
            for res in st.session_state["analysis_results"]
        ])
        st.dataframe(df, use_container_width=True)

    st.markdown("### Code Workspace")
    code = st_ace(language="python", theme="monokai", height=220)
    if code:
        st.code(code, language="python")


def analyze_url(app_state: AsyncAppState, url: str) -> Optional[AnalysisResult]:
    async def _analyze() -> Optional[AnalysisResult]:
        async with SafeHTTPClient() as client:
            response = await client.fetch(url)
            if not response or response.status_code != 200:
                return None
        extractor = app_state.extractor
        analyzer = app_state.analyzer
        if extractor is None or analyzer is None or app_state.database is None:
            return None
        data = extractor.extract(response.text, url)
        if not data.get("text"):
            return None
        analysis = analyzer.analyze(data["text"], data["title"])
        evidence_id = await app_state.database.insert_evidence(
            url=url,
            title=data["title"],
            score=analysis["score"],
            facets=analysis["facets"],
        )
        return AnalysisResult(
            url=url,
            title=data["title"] or evidence_id,
            score=analysis["score"],
            facets=analysis["facets"],
        )

    return app_state.run(_analyze())


def render_browser_agent(app_state: AsyncAppState) -> None:
    st.subheader("Browser Agent")
    if app_state.browser is None:
        st.error("Browser engine not available")
        return

    url = st.text_input("Navigate to URL", key="browser_url", placeholder="https://kali.org")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("Open in active tab") and url:
        app_state.run(app_state.browser.open_url(url))
        st.success(f"Opened {url}")
    if col2.button("New tab") and url:
        app_state.run(app_state.browser.new_tab(url))
        st.success("Created new tab")
    if col3.button("Screenshot"):
        data = app_state.run(app_state.browser.capture_screenshot())
        st.image(Image.open(io.BytesIO(data)), caption="Latest screenshot")
    if col4.button("Export workspaces"):
        snapshot = app_state.run(app_state.browser.export_workspace_state())
        st.download_button("Download workspace JSON", data=snapshot, file_name="workspace.json", mime="application/json")

    st.markdown("#### Workspaces")
    st.json(app_state.browser.list_workspaces())

    st.markdown("#### DOM Tools")
    script = st.text_area("Execute JavaScript", value="return document.title;")
    if st.button("Run script"):
        result = app_state.run(app_state.browser.execute_script(script))
        st.code(result)


def render_system_control(app_state: AsyncAppState) -> None:
    st.subheader("System Control")
    if app_state.system is None:
        st.error("System controller not initialized")
        return

    command = st.text_input("Run command", key="system_cmd", placeholder="whoami")
    if st.button("Execute", type="primary") and command:
        try:
            result = app_state.run(app_state.system.run_command(command))
            st.code(result.stdout or result.stderr)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Command failed: {exc}")

    st.markdown("#### File Browser")
    path = st.text_input("Path", value="/root")
    if st.button("List directory"):
        try:
            listing = app_state.system.list_directory(path)
            st.json(listing)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    st.markdown("#### Log Tail")
    log_path = st.text_input("Log path", value="/var/log/syslog")
    if st.button("Tail log"):
        try:
            tail = app_state.system.tail_file(log_path)
            st.text(tail)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    st.markdown("#### Process Monitor")
    processes = app_state.system.list_processes()[:20]
    st.dataframe(pd.DataFrame(processes))

    st.markdown("#### Network Operations")
    net_col1, net_col2 = st.columns(2)
    target = net_col1.text_input("Nmap target", key="nmap_target", value="127.0.0.1")
    if net_col1.button("Run nmap"):
        result = app_state.run(app_state.system.run_nmap(target))
        st.code(result.stdout or result.stderr)
    if net_col2.button("Show netstat"):
        result = app_state.run(app_state.system.netstat())
        st.code(result.stdout or result.stderr)

    st.markdown("#### Package Management")
    pkg = st.text_input("APT package", key="apt_package")
    if st.button("Inspect package") and pkg:
        result = app_state.run(app_state.system.package_info(pkg))
        st.code(result.stdout or result.stderr)
    pip_pkg = st.text_input("Pip search", key="pip_package")
    if st.button("Search pip") and pip_pkg:
        result = app_state.run(app_state.system.pip_list(pip_pkg))
        st.code(result.stdout or result.stderr)

    st.markdown("#### Git / Plugin Runner")
    repo = st.text_input("Repo path", value="/root/aurora_pro")
    if st.button("Git status"):
        result = app_state.run(app_state.system.git_status(repo))
        st.code(result.stdout or result.stderr)
    plugin_col1, plugin_col2 = st.columns(2)
    plugin_path = plugin_col1.text_input("Plugin script path", value="/opt/codex/plugins/example.sh")
    plugin_args = plugin_col2.text_input("Args", value="")
    if st.button("Run plugin") and plugin_path:
        try:
            args = [arg for arg in plugin_args.split() if arg]
            result = app_state.run(app_state.system.execute_plugin(plugin_path, args))
            st.code(result.stdout or result.stderr)
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

    st.markdown("#### Screen Recording")
    duration = st.slider("Duration (seconds)", min_value=3, max_value=30, value=5)
    if st.button("Capture recording"):
        recording_path = app_state.run(app_state.system.record_screen(duration=duration))
        st.session_state["screen_recordings"].append(str(recording_path))
        st.success(f"Recording saved to {recording_path}")
    for recording in st.session_state["screen_recordings"][-3:]:
        with open(recording, "rb") as handle:
            data = handle.read()
        st.download_button(
            label=f"Download {recording}",
            data=data,
            file_name=recording.split("/")[-1],
            mime="video/mp4",
        )


def render_analytics(app_state: AsyncAppState) -> None:
    st.subheader("Analytics & Dashboards")

    records: List[dict] = []
    if app_state.database is None:
        st.info("Database not ready yet")
    else:
        records = app_state.run(app_state.database.list_evidence(limit=100))
        if records:
            df = pd.DataFrame(records)
            fig = px.bar(df, x="title", y="score", title="Evidence Scores")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No evidence captured yet.")

    st.markdown("#### Live Metrics")
    if app_state.coordinator:
        tasks = app_state.coordinator.queue.snapshot()
        total = len(tasks)
        completed = sum(1 for task in tasks if task.get("status") == "completed")
        progress_value = completed / total if total else 0.0
        progress_text = f"{completed}/{total} tasks completed" if total else "No tasks queued"
        st.progress(progress_value, text=progress_text)
        layout = [
            dashboard.Item("active", 0, 0, 6, 3),
            dashboard.Item("tasks", 6, 0, 6, 3),
        ]
        with elements("metrics"):
            dash = dashboard.Dashboard(layout)
            with dash:
                with mui.Paper(key="active", sx={"padding": "16px"}):
                    mui.Typography("Active URL", variant="caption")
                    mui.Typography(app_state.coordinator.context.get("active_url", ""), variant="body2")
                with mui.Paper(key="tasks", sx={"padding": "16px"}):
                    mui.Typography("Queued Tasks", variant="caption")
                    mui.Typography(str(total), variant="body2")

    st.markdown("#### Automation Script Builder")
    workflow_steps = st.session_state["workflow_steps"]
    new_step = st.text_input("Define a workflow step", key="workflow_step")
    add_col, clear_col = st.columns(2)
    if add_col.button("Add step") and new_step:
        workflow_steps.append(new_step)
        st.session_state["workflow_step"] = ""
    if clear_col.button("Clear steps") and workflow_steps:
        workflow_steps.clear()
    if workflow_steps:
        with elements("workflow"):
            layout = [dashboard.Item(f"step_{idx}", 0, idx * 2, 12, 2) for idx, _ in enumerate(workflow_steps)]
            dash = dashboard.Dashboard(layout)
            with dash:
                for idx, step in enumerate(workflow_steps):
                    with mui.Paper(key=f"step_{idx}", sx={"padding": "12px"}):
                        mui.Typography(f"Step {idx + 1}", variant="caption")
                        mui.Typography(step, variant="body2")
        st.code("\n".join(workflow_steps), language="bash")
        st.download_button(
            label="Download workflow JSON",
            data=pd.Series(workflow_steps).to_json(orient="values"),
            file_name="workflow.json",
            mime="application/json",
        )

    st.markdown("#### Export")
    csv_data = build_csv_export(app_state)
    st.download_button(
        label="Download evidence CSV",
        data=csv_data,
        file_name="aurora_evidence.csv",
        mime="text/csv",
    )
    pdf_data = build_pdf_report(records)
    if pdf_data:
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name="aurora_report.pdf",
            mime="application/pdf",
        )


def build_csv_export(app_state: AsyncAppState) -> str:
    if app_state.database is None:
        return ""
    records = app_state.run(app_state.database.list_evidence(limit=500))
    df = pd.DataFrame(records)
    return df.to_csv(index=False)


def build_pdf_report(records: List[dict]) -> Optional[bytes]:
    if not records:
        return None
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Aurora Findings Report", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=12)
    for record in records[:25]:
        title = record.get("title") or record.get("url")
        score = record.get("score", 0.0)
        pdf.multi_cell(0, 8, f"- {title} (score: {score:.1f})")
    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def inject_theme() -> None:
    st.set_page_config(
        page_title="Aurora Comet Control Center",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
            body {background-color: #0f1117; color: #e8eaf6;}
            section.main > div {padding-top: 1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_theme()
    init_session_state()
    app_state = get_app_state()
    render_sidebar(app_state)

    st.title("Aurora Comet Control Center")
    st.caption("Integrated browser automation, system operations, and research analytics.")

    tabs = st.tabs(["Research Console", "Browser Agent", "System Control", "Analytics"])
    with tabs[0]:
        render_research_console(app_state)
    with tabs[1]:
        render_browser_agent(app_state)
    with tabs[2]:
        render_system_control(app_state)
    with tabs[3]:
        render_analytics(app_state)


def _shutdown() -> None:
    state = st.session_state.get("aurora_async_state")
    if state:
        state.stop()


if __name__ == "__main__":
    try:
        main()
    finally:
        _shutdown()
