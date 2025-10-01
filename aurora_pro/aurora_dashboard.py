"""Streamlit dashboard for monitoring Aurora evidence processing."""
import time
from typing import Dict, List, Optional, Tuple

import altair as alt
import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timezone
from PIL import Image
from fpdf import FPDF
from streamlit_ace import st_ace
from streamlit_elements import elements, mui, dashboard
API_BASE_URL = "http://0.0.0.0:8000"
REFRESH_SECONDS = 3
CLI_DEFAULT_LIMIT = 50


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_evidence() -> pd.DataFrame:
    """Retrieve evidence records from the Aurora API as a DataFrame."""
    try:
        response = requests.get(f"{API_BASE_URL}/evidence", timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:  # noqa: BLE001
        st.error(f"Failed to fetch evidence: {exc}")
        return pd.DataFrame()

    payload = response.json()
    results = payload.get("results", payload) if isinstance(payload, dict) else payload
    if not isinstance(results, list):
        st.warning("Unexpected evidence response format.")
        return pd.DataFrame()

    df = pd.DataFrame(results)
    if df.empty:
        return df

    df["created_dt"] = pd.to_datetime(df.get("created_at", []), unit="s", errors="coerce")
    df["facet_tags"] = df.get("facets", []).apply(_extract_facet_tags)
    df["facet_summary"] = df.get("facets", []).apply(_summarize_facets)
    return df


def _extract_facet_tags(value) -> List[str]:
    if isinstance(value, dict):
        return sorted(value.keys())
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _summarize_facets(value) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{k}: {v}" for k, v in value.items())
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return ""


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_health() -> Tuple[bool, dict]:
    """Check the API health endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as exc:  # noqa: BLE001
        return False, {"error": str(exc)}


def compute_metrics(df: pd.DataFrame) -> Tuple[int, float, float]:
    if df.empty:
        return 0, 0.0, 0.0
    total = len(df)
    avg_score = float(df["score"].mean()) if "score" in df else 0.0
    created = df["created_dt"].dropna()
    if created.empty:
        return total, avg_score, 0.0
    timespan_hours = (created.max() - created.min()).total_seconds() / 3600
    timespan_hours = max(timespan_hours, 1 / 3600)  # Avoid division by zero
    rate = total / timespan_hours
    return total, avg_score, rate


def render_metrics(df: pd.DataFrame) -> None:
    total, avg_score, rate = compute_metrics(df)
    healthy, health_payload = fetch_health()
    status_text = "Healthy" if healthy else "Unavailable"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total URLs Processed", f"{total}")
    col2.metric("Average Score", f"{avg_score:.2f}")
    col3.metric("Processing Rate (items/hour)", f"{rate:.2f}")
    if healthy:
        col4.metric("API Health", status_text, help=str(health_payload))
    else:
        col4.metric("API Health", status_text)
        st.warning(f"API health check failed: {health_payload.get('error', 'Unknown error')}")


def render_results_table(df: pd.DataFrame) -> None:
    st.markdown("### Evidence Results")
    if df.empty:
        st.info("No evidence captured yet.")
        return

    unique_facets = sorted({tag for tags in df["facet_tags"] for tag in tags})
    selected_facets = st.multiselect("Filter by facet tags", unique_facets)

    filtered = df.copy()
    if selected_facets:
        selected = set(selected_facets)
        filtered = filtered[filtered["facet_tags"].apply(lambda tags: selected.issubset(set(tags)))]

    sort_option = st.radio(
        "Sort by score",
        options=["High → Low", "Low → High"],
        horizontal=True,
        key="sort_option",
    )
    filtered = filtered.sort_values("score", ascending=(sort_option == "Low → High"))

    display_cols = ["title", "url", "score", "facet_summary"]
    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        column_config={
            "title": "Title",
            "url": "URL",
            "score": "Score",
            "facet_summary": "Facets",
        },
    )

    st.markdown("#### Quick Links")
    for _, row in filtered.iterrows():
        label = row["title"] or row["url"]
        st.link_button(str(label), row["url"])


def render_history_chart(df: pd.DataFrame) -> None:
    st.markdown("### Processing History")
    if df.empty or df["created_dt"].dropna().empty:
        st.info("History data not available yet.")
        return

    history = df.sort_values("created_dt").loc[:, ["created_dt"]].dropna()
    history["cumulative"] = range(1, len(history) + 1)

    chart = (
        alt.Chart(history)
        .mark_line()
        .encode(x="created_dt:T", y="cumulative:Q")
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)


def render_submission_form() -> None:
    st.markdown("### Submit New URL")
    with st.form("submit_url"):
        url = st.text_input("URL", placeholder="https://example.com")
        submitted = st.form_submit_button("Submit for Research")
    if not submitted:
        return
    if not url:
        st.error("Please provide a URL before submitting.")
        return
    try:
        response = requests.post(
            f"{API_BASE_URL}/research",
            json={"url": url},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:  # noqa: BLE001
        st.error(f"Submission failed: {exc}")
        return

        st.success("URL submitted successfully.")


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_conversation_state() -> Dict[str, object]:
    try:
        response = requests.get(f"{API_BASE_URL}/agent/state", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:  # noqa: BLE001
        st.error(f"Failed to fetch conversation state: {exc}")
        return {}


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_cli_status() -> Dict[str, dict]:
    try:
        response = requests.get(f"{API_BASE_URL}/cli/status", timeout=5)
        response.raise_for_status()
        payload = response.json()
        return payload.get("agents", {})
    except requests.RequestException as exc:  # noqa: BLE001
        st.error(f"Failed to fetch CLI status: {exc}")
        return {}


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_cli_logs(agent: Optional[str], limit: int) -> List[dict]:
    params = {"limit": limit}
    if agent:
        params["agent"] = agent
    try:
        response = requests.get(f"{API_BASE_URL}/cli/logs", params=params, timeout=5)
        response.raise_for_status()
        payload = response.json()
        logs = payload.get("logs", [])
        return logs if isinstance(logs, list) else []
    except requests.RequestException as exc:  # noqa: BLE001
        st.error(f"Failed to fetch CLI logs: {exc}")
        return []


def render_cli_submit_tab(status_data: Dict[str, dict]) -> None:
    st.subheader("Submit CLI Task")
    with st.form("submit_cli_task"):
        prompt = st.text_area("Prompt", height=200)
        agent_choice = st.selectbox("Agent", options=["Auto", "Claude", "Codex"], index=0)
        timeout_value = st.number_input("Timeout (seconds)", min_value=0, max_value=600, value=0, step=10)
        submitted = st.form_submit_button("Dispatch Task")

    if submitted:
        if not prompt.strip():
            st.error("Prompt cannot be empty.")
        else:
            payload: Dict[str, object] = {"prompt": prompt.strip()}
            if agent_choice.lower() != "auto":
                payload["agent"] = agent_choice.lower()
            if timeout_value > 0:
                payload["timeout"] = int(timeout_value)
            try:
                response = requests.post(
                    f"{API_BASE_URL}/cli/command",
                    json=payload,
                    timeout=15,
                )
                response.raise_for_status()
            except requests.RequestException as exc:  # noqa: BLE001
                st.error(f"Failed to submit CLI task: {exc}")
            else:
                data = response.json()
                st.success(f"Task {data.get('task', {}).get('id', 'queued')} sent to {data.get('agent')} agent.")

    st.markdown("### Agent Status")
    if not status_data:
        st.info("No agent status available yet.")
        return
    for agent, info in status_data.items():
        running_task = info.get("running") or "idle"
        available = info.get("available", 0)
        st.write(f"**{agent.title()}** – available: {available}, running: {running_task}")
        recent = info.get("tasks", [])[-3:]
        if recent:
            st.table(
                pd.DataFrame(
                    [
                        {
                            "Task": task.get("id"),
                            "Status": task.get("status"),
                            "Started": task.get("started_at"),
                            "Finished": task.get("finished_at"),
                        }
                        for task in recent
                    ]
                )
            )


def render_cli_logs_tab(agent: str, status_data: Dict[str, dict]) -> None:
    agent_key = agent.lower()
    st.subheader(f"{agent.title()} CLI Output")
    limit = st.slider(
        "Log entries",
        min_value=10,
        max_value=200,
        value=CLI_DEFAULT_LIMIT,
        step=10,
        key=f"{agent_key}_log_limit",
    )
    logs = fetch_cli_logs(agent_key, limit)
    if not logs:
        st.info("No log entries available yet.")
    else:
        for entry in logs[-limit:]:
            timestamp = entry.get("timestamp", "--")
            stream = entry.get("stream", "stdout")
            message = entry.get("message", "")
            st.markdown(f"`{timestamp}` **{stream}** {message}")

    if agent_key in status_data:
        running = status_data[agent_key].get("running")
        if running:
            st.caption(f"Current task: {running}")


def render_agent_chat_tab(conversation_state: Dict[str, object]) -> None:
    st.subheader("Agent Conversation")
    history = conversation_state.get("history", [])
    if history:
        for item in history[-50:]:
            role = item.get("role", "unknown").title()
            timestamp = item.get("timestamp", 0)
            ts = (
                datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(timespec="seconds")
                if isinstance(timestamp, (int, float))
                else item.get("timestamp", "--")
            )
            content = item.get("content", "")
            st.markdown(f"**{role}** _[{ts}]_\n\n{content}")
    else:
        st.info("No conversation history yet.")

    st.markdown("---")
    prompt = st.text_area("Send a message", height=180, key="chat_prompt")
    agent_pref = st.selectbox("Preferred agent", options=["Auto", "Claude", "Codex"], index=0, key="chat_agent")
    cols = st.columns([1, 1, 2])
    with cols[0]:
        send = st.button("Send", type="primary")
    with cols[1]:
        clear = st.button("Clear Input")
    if clear:
        st.session_state["chat_prompt"] = ""

    if send:
        payload: Dict[str, object] = {"prompt": prompt}
        if agent_pref.lower() != "auto":
            payload["agent"] = agent_pref.lower()
        try:
            response = requests.post(
                f"{API_BASE_URL}/agent/message",
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:  # noqa: BLE001
            st.error(f"Failed to dispatch message: {exc}")
        else:
            data = response.json()
            st.success(f"Routed via {data.get('route')} – {data.get('response')}")
            st.session_state["chat_prompt"] = ""


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_input_status() -> dict:
    """Fetch input agent status."""
    try:
        response = requests.get(f"{API_BASE_URL}/input/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:  # noqa: BLE001
        st.error(f"Failed to fetch input status: {exc}")
        return {}


def render_input_agent_tab(input_status: dict) -> None:
    """Render the Input Agent control tab."""
    st.subheader("Mouse & Keyboard Control Agent")

    # Status display
    queue_size = input_status.get("queue_size", 0)
    screen_size = input_status.get("screen_size", {})
    mouse_pos = input_status.get("mouse_position", {})

    col1, col2, col3 = st.columns(3)
    col1.metric("Queue Size", queue_size)
    col2.metric("Screen Size", f"{screen_size.get('width', 0)}x{screen_size.get('height', 0)}")
    col3.metric("Mouse Position", f"({mouse_pos.get('x', 0)}, {mouse_pos.get('y', 0)})")

    st.markdown("### Submit Input Task")
    st.warning("⚠️ This will control real mouse/keyboard hardware. Ensure control_mouse_keyboard is enabled in config.")

    with st.form("submit_input_task"):
        action_type = st.selectbox(
            "Action Type",
            options=[
                "click",
                "right_click",
                "double_click",
                "move_to",
                "type_text",
                "hotkey",
                "scroll",
                "press_key",
                "drag",
            ],
        )

        # Dynamic parameters based on action type
        parameters = {}

        if action_type in ("click", "right_click", "double_click", "move_to"):
            col_x, col_y = st.columns(2)
            x = col_x.number_input("X coordinate", min_value=0, value=500)
            y = col_y.number_input("Y coordinate", min_value=0, value=500)
            parameters["x"] = int(x)
            parameters["y"] = int(y)

            if action_type == "move_to":
                duration = st.number_input("Duration (seconds)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
                parameters["duration"] = float(duration)

        elif action_type == "type_text":
            text = st.text_area("Text to type", height=100)
            interval = st.number_input("Interval between keys (seconds)", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
            parameters["text"] = text
            parameters["interval"] = float(interval)

        elif action_type == "hotkey":
            keys = st.text_input("Keys (comma-separated)", placeholder="ctrl,c")
            if keys:
                parameters["keys"] = [k.strip() for k in keys.split(",")]

        elif action_type == "scroll":
            amount = st.number_input("Scroll amount (negative=down, positive=up)", value=3, step=1)
            parameters["amount"] = int(amount)

        elif action_type == "press_key":
            key = st.text_input("Key name", placeholder="enter")
            presses = st.number_input("Number of presses", min_value=1, value=1)
            parameters["key"] = key
            parameters["presses"] = int(presses)

        elif action_type == "drag":
            col_x, col_y = st.columns(2)
            x = col_x.number_input("X offset", value=100)
            y = col_y.number_input("Y offset", value=100)
            duration = st.number_input("Duration (seconds)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
            parameters["x"] = int(x)
            parameters["y"] = int(y)
            parameters["duration"] = float(duration)

        operator_user = st.text_input("Operator User", placeholder="root")
        submitted = st.form_submit_button("Execute Input Action", type="primary")

    if submitted:
        if not parameters:
            st.error("Please configure parameters for the selected action.")
        else:
            payload = {
                "action_type": action_type,
                "parameters": parameters,
                "operator_user": operator_user or None,
            }
            try:
                response = requests.post(
                    f"{API_BASE_URL}/input/submit",
                    json=payload,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                st.success(f"Task {data['task_id']} submitted successfully!")
            except requests.RequestException as exc:  # noqa: BLE001
                st.error(f"Failed to submit task: {exc}")

    st.markdown("### Recent Tasks")
    recent_tasks = input_status.get("recent_tasks", [])
    if not recent_tasks:
        st.info("No recent tasks.")
    else:
        for task in reversed(recent_tasks[-10:]):
            with st.expander(f"{task['task_id']} - {task['action_type']} [{task['status']}]"):
                st.json(task)


def main() -> None:
    st.set_page_config(page_title="Aurora Dashboard", layout="wide")
    st.title("Aurora Evidence Dashboard")
    st.caption("Live visibility into Aurora processing metrics and recent evidence.")

    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)

    evidence_df = fetch_evidence()

    conversation_state = fetch_conversation_state()
    cli_status_data = fetch_cli_status()
    input_status_data = fetch_input_status()

    chat_tab, overview_tab, submit_tab, claude_tab, codex_tab, input_tab = st.tabs(
        [
            "Agent Chat",
            "Evidence Overview",
            "Submit Task",
            "Claude CLI Output",
            "Codex CLI Output",
            "Input Agent",
        ]
    )

    with chat_tab:
        render_agent_chat_tab(conversation_state)

    with overview_tab:
        render_metrics(evidence_df)
        render_history_chart(evidence_df)
        render_results_table(evidence_df)
        render_submission_form()

    with submit_tab:
        render_cli_submit_tab(cli_status_data)

    with claude_tab:
        render_cli_logs_tab("claude", cli_status_data)

    with codex_tab:
        render_cli_logs_tab("codex", cli_status_data)

    with input_tab:
        render_input_agent_tab(input_status_data)

    if auto_refresh:
        time.sleep(REFRESH_SECONDS)
        st.rerun()


if __name__ == "__main__":
    main()
