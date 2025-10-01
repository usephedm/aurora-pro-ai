"""
Tests for Multi-Agent Orchestrator
"""
import pytest
from src.agents.orchestrator import (
    MultiAgentOrchestrator,
    OrchestrationMode,
    get_orchestrator
)
from src.agents.llm_agent import LLMAgent


@pytest.fixture
def orchestrator():
    """Create orchestrator fixture"""
    return MultiAgentOrchestrator(mode=OrchestrationMode.SEQUENTIAL)


@pytest.fixture
def sample_agent():
    """Create sample agent fixture"""
    return LLMAgent(name="test-agent", model_name="llama2")


def test_orchestrator_creation(orchestrator):
    """Test orchestrator instantiation"""
    assert orchestrator is not None
    assert orchestrator.mode == OrchestrationMode.SEQUENTIAL
    assert len(orchestrator.agents) == 0


def test_register_agent(orchestrator, sample_agent):
    """Test agent registration"""
    result = orchestrator.register_agent(sample_agent)
    
    assert result is True
    assert len(orchestrator.agents) == 1
    assert "test-agent" in orchestrator.agents


def test_duplicate_agent_registration(orchestrator, sample_agent):
    """Test duplicate agent registration fails"""
    orchestrator.register_agent(sample_agent)
    result = orchestrator.register_agent(sample_agent)
    
    assert result is False


def test_unregister_agent(orchestrator, sample_agent):
    """Test agent unregistration"""
    orchestrator.register_agent(sample_agent)
    result = orchestrator.unregister_agent("test-agent")
    
    assert result is True
    assert len(orchestrator.agents) == 0


def test_get_agent(orchestrator, sample_agent):
    """Test retrieving registered agent"""
    orchestrator.register_agent(sample_agent)
    agent = orchestrator.get_agent("test-agent")
    
    assert agent is not None
    assert agent.name == "test-agent"


def test_list_agents(orchestrator, sample_agent):
    """Test listing all agents"""
    orchestrator.register_agent(sample_agent)
    agents = orchestrator.list_agents()
    
    assert len(agents) == 1
    assert agents[0]["name"] == "test-agent"


@pytest.mark.asyncio
async def test_execute_sequential(orchestrator, sample_agent):
    """Test sequential task execution"""
    orchestrator.register_agent(sample_agent)
    
    tasks = [
        {"agent": "test-agent", "prompt": "Test prompt 1"},
        {"agent": "test-agent", "prompt": "Test prompt 2"}
    ]
    
    results = await orchestrator.execute(tasks)
    
    assert len(results) == 2
    assert results[0]["status"] == "completed"
    assert results[1]["status"] == "completed"


@pytest.mark.asyncio
async def test_execute_parallel(sample_agent):
    """Test parallel task execution"""
    orchestrator = MultiAgentOrchestrator(mode=OrchestrationMode.PARALLEL)
    orchestrator.register_agent(sample_agent)
    
    tasks = [
        {"agent": "test-agent", "prompt": "Test prompt 1"},
        {"agent": "test-agent", "prompt": "Test prompt 2"}
    ]
    
    results = await orchestrator.execute(tasks)
    
    assert len(results) == 2
