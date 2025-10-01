"""
Aurora Pro AI - Streamlit GUI Application
"""
import streamlit as st
import requests
from typing import Dict, Any, List
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Aurora Pro AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .status-healthy {
        color: #4CAF50;
        font-weight: bold;
    }
    .status-unhealthy {
        color: #F44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> Dict[str, Any]:
    """Check API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health/ready", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_agents() -> List[Dict[str, Any]]:
    """Get list of registered agents"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/agents", timeout=5)
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch agents: {e}")
        return []


def create_agent(name: str, model: str, provider: str) -> Dict[str, Any]:
    """Create a new agent"""
    try:
        data = {
            "name": name,
            "agent_type": "llm",
            "model_name": model,
            "provider": provider,
            "description": f"LLM Agent with {model}"
        }
        response = requests.post(
            f"{API_BASE_URL}/api/v1/agents",
            json=data,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def execute_task(agent: str, prompt: str) -> Dict[str, Any]:
    """Execute a task"""
    try:
        data = {
            "agent": agent,
            "prompt": prompt
        }
        response = requests.post(
            f"{API_BASE_URL}/api/v1/tasks/execute",
            json=data,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Main UI
st.markdown('<h1 class="main-header">🤖 Aurora Pro AI</h1>', unsafe_allow_html=True)
st.markdown("*Production-grade AI Operating System with multi-agent orchestration*")

# Sidebar
with st.sidebar:
    st.header("System Status")
    
    health = check_api_health()
    if health.get("status") == "ready":
        st.markdown('<p class="status-healthy">✓ System Healthy</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-unhealthy">✗ System Unhealthy</p>', unsafe_allow_html=True)
    
    if "checks" in health:
        st.json(health["checks"])
    
    st.divider()
    
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["Dashboard", "Agents", "Tasks", "Models", "Settings"],
        label_visibility="collapsed"
    )

# Dashboard Page
if page == "Dashboard":
    st.header("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    agents = list_agents()
    
    with col1:
        st.metric("Total Agents", len(agents))
    
    with col2:
        active = sum(1 for a in agents if a.get("status") not in ["failed", "idle"])
        st.metric("Active Agents", active)
    
    with col3:
        st.metric("System Version", "1.0.0")
    
    st.divider()
    
    st.subheader("Recent Activity")
    if agents:
        st.dataframe(agents, use_container_width=True)
    else:
        st.info("No agents registered yet. Go to the Agents page to create one.")

# Agents Page
elif page == "Agents":
    st.header("Agent Management")
    
    tab1, tab2 = st.tabs(["Create Agent", "View Agents"])
    
    with tab1:
        st.subheader("Create New Agent")
        
        with st.form("create_agent_form"):
            agent_name = st.text_input("Agent Name", placeholder="my-agent")
            model = st.selectbox("Model", ["llama2", "mistral", "gpt-3.5-turbo"])
            provider = st.selectbox("Provider", ["ollama", "openai"])
            
            submitted = st.form_submit_button("Create Agent")
            
            if submitted:
                if not agent_name:
                    st.error("Agent name is required")
                else:
                    with st.spinner("Creating agent..."):
                        result = create_agent(agent_name, model, provider)
                        
                        if "error" in result:
                            st.error(f"Failed to create agent: {result['error']}")
                        else:
                            st.success(f"Agent '{agent_name}' created successfully!")
                            st.json(result)
    
    with tab2:
        st.subheader("Registered Agents")
        
        if st.button("Refresh"):
            st.rerun()
        
        agents = list_agents()
        
        if agents:
            for agent in agents:
                with st.expander(f"🤖 {agent.get('name', 'Unknown')}"):
                    st.json(agent)
        else:
            st.info("No agents registered")

# Tasks Page
elif page == "Tasks":
    st.header("Task Execution")
    
    agents = list_agents()
    
    if not agents:
        st.warning("No agents available. Please create an agent first.")
    else:
        agent_names = [a.get("name") for a in agents]
        
        with st.form("execute_task_form"):
            selected_agent = st.selectbox("Select Agent", agent_names)
            prompt = st.text_area(
                "Prompt",
                placeholder="Enter your prompt here...",
                height=150
            )
            
            submitted = st.form_submit_button("Execute Task")
            
            if submitted:
                if not prompt:
                    st.error("Prompt is required")
                else:
                    with st.spinner("Executing task..."):
                        result = execute_task(selected_agent, prompt)
                        
                        if "error" in result:
                            st.error(f"Task failed: {result['error']}")
                        else:
                            st.success("Task completed successfully!")
                            st.json(result)

# Models Page
elif page == "Models":
    st.header("Model Management")
    
    st.info("Model management interface - Load and manage AI models")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Available Providers")
        st.write("- Ollama (Local)")
        st.write("- OpenAI")
        st.write("- HuggingFace")
        st.write("- vLLM")
    
    with col2:
        st.subheader("Popular Models")
        st.write("- llama2")
        st.write("- mistral")
        st.write("- gpt-3.5-turbo")
        st.write("- gpt-4")

# Settings Page
elif page == "Settings":
    st.header("Settings")
    
    st.subheader("API Configuration")
    st.text_input("API Base URL", value=API_BASE_URL, disabled=True)
    
    st.subheader("Display Settings")
    st.checkbox("Dark Mode", value=False)
    st.checkbox("Show Advanced Options", value=False)
    
    st.subheader("About")
    st.write("**Aurora Pro AI** v1.0.0")
    st.write("Production-grade AI Operating System")
    st.write("© 2025 usephedm")
