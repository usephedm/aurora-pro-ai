import asyncio
import os
from typing import Dict

import streamlit as st

try:
    from streamlit_ace import st_ace
except Exception:  # pragma: no cover
    st_ace = None  # allow UI to render even if ace not installed

from .unified_chatbox import UnifiedChatbox


async def get_system_health() -> Dict[str, Dict[str, bool]]:
    import socket
    import subprocess

    def tcp(host: str, port: int, timeout: float = 0.5) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    def redis_ping() -> bool:
        try:
            return (
                subprocess.run(["redis-cli", "ping"], capture_output=True, timeout=1).stdout
                .decode()
                .strip()
                == "PONG"
            )
        except Exception:
            return False

    return {
        "vLLM": {"healthy": tcp("127.0.0.1", 8000)},
        "ChromaDB": {"healthy": tcp("127.0.0.1", 8001)},
        "Grafana": {"healthy": tcp("127.0.0.1", 3000)},
        "Ollama": {"healthy": tcp("127.0.0.1", 11434)},
        "Redis": {"healthy": redis_ping()},
    }


st.set_page_config(page_title="Aurora Pro Unified Control", page_icon="🤖", layout="wide")

if "chatbox" not in st.session_state:
    st.session_state.chatbox = UnifiedChatbox()
    st.session_state.conversation_history = []

with st.sidebar:
    st.header("⚙️ System Configuration")
    agent_override = st.selectbox(
        "Agent Selection",
        ["Auto (Recommended)", "Claude Sonnet 4.5", "Codex CLI", "Local LLM", "Vision"],
    )
    reasoning_level = st.selectbox("Reasoning Depth", ["Medium", "High", "Extended"])
    st.divider()
    st.header("📊 System Health")
    health = asyncio.run(get_system_health())
    for component, status in health.items():
        if status["healthy"]:
            st.success(f"✅ {component}: Online")
        else:
            st.error(f"❌ {component}: Offline")

st.title("🤖 Aurora Pro Unified AI System")

for msg in st.session_state.conversation_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "agent_used" in msg:
            st.caption(f"Agent: {msg['agent_used']} | Confidence: {msg['confidence']:.2f}")

if prompt := st.chat_input("Enter your command..."):
    st.session_state.conversation_history.append({"role": "user", "content": prompt})
    with st.spinner("Processing..."):
        result = asyncio.run(st.session_state.chatbox.process_message(prompt))
    st.session_state.conversation_history.append(
        {
            "role": "assistant",
            "content": str(result["response"]),
            "agent_used": result["agent_used"],
            "confidence": result["confidence"],
        }
    )
    st.rerun()

st.divider()
st.header("💻 Live Code Editor")

if st_ace:
    code = st_ace(
        value=st.session_state.get("current_code", "# Write Python code here"),
        language="python",
        theme="monokai",
        keybinding="vscode",
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=False,
        auto_update=True,
    )
    if st.button("Execute Code"):
        result = asyncio.run(
            st.session_state.chatbox.codex.execute_command(f"Execute this Python code: ```{code}```")
        )
        st.code(result["stdout"], language="text")
else:
    st.info("Install streamlit-ace to enable the live code editor (pip install streamlit-ace)")

