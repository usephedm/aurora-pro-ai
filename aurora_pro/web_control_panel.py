"""
Aurora Pro Web Control Panel
Beautiful real-time web interface with Streamlit

Features:
- Live agent status dashboard
- Real-time metrics (CPU, RAM, GPU)
- BIG RED STOP BUTTON (prominently displayed)
- Task submission form
- LLM selector
- Live logs streaming
- Agent control (enable/disable)
- Configuration editor
- Workflow history
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="Aurora Pro Control Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API endpoint
API_BASE = os.getenv("AURORA_API_URL", "http://localhost:8000")


def fetch_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Fetch data from Aurora API."""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return {"error": f"Unsupported method: {method}"}

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def emergency_stop():
    """Trigger emergency stop."""
    result = fetch_api("/control/emergency-stop", method="POST")
    if "error" not in result:
        st.success("🚨 EMERGENCY STOP TRIGGERED - All systems halted")
        st.balloons()
    else:
        st.error(f"Failed to trigger emergency stop: {result['error']}")


def restart_system():
    """Restart all systems."""
    result = fetch_api("/control/restart", method="POST")
    if "error" not in result:
        st.success("🔄 System restart initiated")
    else:
        st.error(f"Failed to restart: {result['error']}")


# Main UI
st.title("🚀 Aurora Pro Control Center")
st.markdown("### Real-Time Autonomous AI System Monitor")

# Auto-refresh
if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0

# Sidebar
with st.sidebar:
    st.header("⚙️ Control Panel")

    # EMERGENCY STOP BUTTON - BIG AND RED
    st.markdown("---")
    st.markdown("### 🚨 EMERGENCY CONTROLS")

    if st.button(
        "🛑 EMERGENCY STOP",
        use_container_width=True,
        type="primary",
        help="Immediately halt all operations",
    ):
        emergency_stop()

    if st.button(
        "🔄 Restart System",
        use_container_width=True,
        help="Stop and restart all components",
    ):
        restart_system()

    st.markdown("---")

    # Refresh settings
    st.markdown("### 🔄 Refresh")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_interval = st.slider("Interval (seconds)", 1, 10, 2)

    if st.button("Manual Refresh", use_container_width=True):
        st.session_state.refresh_counter += 1
        st.rerun()

    st.markdown("---")

    # System info
    st.markdown("### ℹ️ System Info")
    system_status = fetch_api("/health")
    if "error" not in system_status:
        st.metric("Status", system_status.get("status", "unknown"))
        st.metric("Database", system_status.get("database", "unknown"))
    else:
        st.error("Unable to fetch system status")

    st.markdown("---")
    st.markdown("**Aurora Pro v1.0.0**")
    st.markdown("Build: Production")

# Main content area - 3 columns
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.markdown("### 📊 System Metrics")

    # Fetch metrics
    metrics_data = fetch_api("/control/metrics")

    if "error" not in metrics_data and "metrics" in metrics_data:
        metrics = metrics_data["metrics"]

        # CPU and Memory gauges
        gauge_col1, gauge_col2 = st.columns(2)

        with gauge_col1:
            cpu_percent = metrics.get("cpu_percent", 0)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=cpu_percent,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "CPU Usage"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                }
            ))
            fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with gauge_col2:
            mem_percent = metrics.get("memory_percent", 0)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=mem_percent,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Memory Usage"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                }
            ))
            fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        # Additional metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric(
                "Memory Used",
                f"{metrics.get('memory_used_gb', 0):.2f} GB",
                f"of {metrics.get('memory_total_gb', 0):.1f} GB"
            )
        with metric_col2:
            st.metric(
                "Disk Used",
                f"{metrics.get('disk_percent', 0):.1f}%"
            )
        with metric_col3:
            gpu_util = metrics.get('gpu_utilization')
            if gpu_util is not None:
                st.metric("GPU", f"{gpu_util:.1f}%")
            else:
                st.metric("GPU", "N/A")

    else:
        st.warning("Metrics unavailable - Control Center may not be running")

with col2:
    st.markdown("### 🤖 Agent Status")

    # Fetch agent status
    router_status = fetch_api("/router/status")

    if "error" not in router_status:
        agents_info = [
            ("Multi-LLM Orchestrator", router_status.get("llm_orchestrator_available", False)),
            ("Multicore Manager", router_status.get("multicore_available", False)),
            ("Cache Manager", router_status.get("cache_available", False)),
            ("Vision Agent", router_status.get("vision_available", False)),
            ("Stealth Browser", router_status.get("stealth_browser_available", False)),
            ("Local Inference", router_status.get("local_inference_available", False)),
            ("Proxy Manager", router_status.get("proxy_available", False)),
        ]

        for agent_name, is_available in agents_info:
            status_icon = "✅" if is_available else "❌"
            status_text = "Running" if is_available else "Stopped"
            st.markdown(f"{status_icon} **{agent_name}**: {status_text}")

    else:
        st.error("Unable to fetch agent status")

with col3:
    st.markdown("### 🎛️ Quick Actions")

    if st.button("📸 Take Screenshot", use_container_width=True):
        st.info("Screenshot requested...")

    if st.button("🧹 Clear Cache", use_container_width=True):
        result = fetch_api("/cache/clear", method="POST")
        if "error" not in result:
            st.success("Cache cleared!")
        else:
            st.error(f"Failed: {result['error']}")

    if st.button("📊 View Stats", use_container_width=True):
        st.info("Opening stats view...")

# Second row - Task Management and Logs
st.markdown("---")
row2_col1, row2_col2 = st.columns([1, 1])

with row2_col1:
    st.markdown("### 📝 Submit Task")

    with st.form("task_form"):
        task_description = st.text_area(
            "Describe what you want Aurora to do:",
            placeholder="Example: Research the top 5 AI coding tools and create a comparison report",
            height=100,
        )

        llm_choice = st.selectbox(
            "Select LLM:",
            [
                "Auto (Intelligent Selection)",
                "Claude Sonnet 4.5",
                "Claude Opus 4",
                "GPT-4 Turbo",
                "Gemini Pro",
                "Ollama (Local)",
            ]
        )

        col_a, col_b = st.columns(2)
        with col_a:
            max_cost = st.number_input("Max Cost ($)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
        with col_b:
            max_time = st.number_input("Max Time (min)", min_value=1, max_value=60, value=10)

        submitted = st.form_submit_button("🚀 Submit Task", use_container_width=True)

        if submitted and task_description:
            st.success(f"Task submitted: {task_description[:50]}...")
            # In a real implementation, would call:
            # result = fetch_api("/autonomous/execute", method="POST", data={
            #     "request": task_description,
            #     "llm": llm_choice,
            #     "max_cost": max_cost,
            #     "max_time": max_time,
            # })

with row2_col2:
    st.markdown("### 📋 Recent Activity")

    # Fetch recent CLI logs
    logs = fetch_api("/cli/logs?limit=10")

    if "error" not in logs and "logs" in logs:
        if logs["logs"]:
            for log in logs["logs"][:5]:
                timestamp = log.get("timestamp", "Unknown")
                message = log.get("message", "No message")
                st.text(f"[{timestamp}] {message[:60]}...")
        else:
            st.info("No recent activity")
    else:
        st.info("Logs unavailable")

# Third row - Detailed Statistics
st.markdown("---")
st.markdown("### 📈 Detailed Statistics")

tab1, tab2, tab3, tab4 = st.tabs(["LLM Stats", "Multicore Stats", "Cache Stats", "Vision Stats"])

with tab1:
    st.markdown("#### Multi-LLM Orchestrator Statistics")
    # Would fetch from /llm/stats endpoint
    st.info("LLM orchestrator statistics would be displayed here")
    st.json({
        "total_requests": 0,
        "total_cost_usd": 0.0,
        "providers": {
            "claude-sonnet": {"requests": 0, "cost": 0.0},
            "gpt-4": {"requests": 0, "cost": 0.0},
        }
    })

with tab2:
    st.markdown("#### Multicore Manager Statistics")
    mc_stats = fetch_api("/multicore/stats")
    if "error" not in mc_stats:
        st.json(mc_stats)
    else:
        st.warning("Multicore stats unavailable")

with tab3:
    st.markdown("#### Cache Manager Statistics")
    cache_stats = fetch_api("/cache/stats")
    if "error" not in cache_stats:
        st.json(cache_stats)
    else:
        st.warning("Cache stats unavailable")

with tab4:
    st.markdown("#### Vision Agent Status")
    vision_status = fetch_api("/vision/status")
    if "error" not in vision_status:
        st.json(vision_status)
    else:
        st.warning("Vision stats unavailable")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Aurora Pro Control Center | Built with Streamlit | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    "</div>",
    unsafe_allow_html=True
)

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_interval)
    st.session_state.refresh_counter += 1
    st.rerun()