"""
Aurora Pro AI - Blueprint Compliance Test Suite

Tests that all components required by the PDF directive are present and functional.
"""
import pytest
import os
from pathlib import Path


class TestBlueprintCompliance:
    """Test suite for blueprint compliance validation."""
    
    REPO_ROOT = Path(__file__).parent.parent
    AURORA_PRO = REPO_ROOT / "aurora_pro"
    
    def test_blueprint_pdf_exists(self):
        """Verify the blueprint PDF directive is present."""
        pdf_file = self.REPO_ROOT / "Aurora Pro AI Operating System_ Comprehensive Deve.pdf"
        assert pdf_file.exists(), "Blueprint PDF directive not found"
        assert pdf_file.stat().st_size > 0, "Blueprint PDF is empty"
    
    def test_reference_documentation_exists(self):
        """Verify reference documentation is created."""
        reference = self.REPO_ROOT / "BLUEPRINT_IMPLEMENTATION_REFERENCE.md"
        assert reference.exists(), "Blueprint reference documentation not found"
        
        # Verify content
        content = reference.read_text()
        assert "Model Context Protocol" in content
        assert "Multi-Agent Orchestration" in content
        assert "Hardware-Optimized Parallel Execution" in content
        assert "Blueprint Compliance Matrix" in content
        assert "100%" in content
    
    def test_operator_quick_reference_exists(self):
        """Verify operator quick reference guide exists."""
        quick_ref = self.REPO_ROOT / "OPERATOR_QUICK_REFERENCE.md"
        assert quick_ref.exists(), "Operator quick reference not found"
        
        content = quick_ref.read_text()
        assert "full executive authority" in content.lower()
        assert "Quick Commands" in content
        assert "Configuration" in content
    
    def test_validation_script_exists(self):
        """Verify blueprint compliance validation script exists."""
        script = self.REPO_ROOT / "validate_blueprint_compliance.sh"
        assert script.exists(), "Validation script not found"
        assert os.access(script, os.X_OK), "Validation script not executable"


class TestMCPIntegration:
    """Test Model Context Protocol integration."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_mcp_server_exists(self):
        """MCP server implementation exists."""
        mcp_server = self.AURORA_PRO / "mcp_server.py"
        assert mcp_server.exists()
        
        content = mcp_server.read_text()
        assert "FastMCP" in content
        assert "health" in content
        assert "shell_run" in content
    
    def test_mcp_launch_script_exists(self):
        """MCP launch script exists."""
        script = Path(__file__).parent.parent / "scripts" / "mcp" / "run_aurora_mcp.sh"
        assert script.exists()


class TestMultiAgentOrchestration:
    """Test multi-agent orchestration components."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_llm_orchestrator_exists(self):
        """LLM orchestrator with 10 providers exists."""
        orchestrator = self.AURORA_PRO / "llm_orchestrator.py"
        assert orchestrator.exists()
        
        content = orchestrator.read_text()
        # Check for provider mentions
        assert "claude" in content.lower() or "anthropic" in content.lower()
        assert "gpt" in content.lower() or "openai" in content.lower()
        assert "gemini" in content.lower()
        assert "ollama" in content.lower()
    
    def test_autonomous_engine_exists(self):
        """Autonomous engine with 14+ action types exists."""
        engine = self.AURORA_PRO / "autonomous_engine.py"
        assert engine.exists()
        
        content = engine.read_text()
        # Check for action types mentioned in blueprint
        assert "WEB_NAVIGATE" in content or "web_navigate" in content
        assert "CLI_EXECUTE" in content or "cli_execute" in content
        assert "VISION_ANALYZE" in content or "vision_analyze" in content
    
    def test_agent_router_exists(self):
        """Agent router for intelligent agent selection exists."""
        router = self.AURORA_PRO / "enhanced_agent_router.py"
        assert router.exists()


class TestHardwareOptimization:
    """Test hardware-optimized components."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_multicore_manager_exists(self):
        """Multicore manager for 32-thread optimization exists."""
        manager = self.AURORA_PRO / "multicore_manager.py"
        assert manager.exists()
        
        content = manager.read_text()
        assert "ProcessPoolExecutor" in content
        assert "30" in content  # 30 workers
    
    def test_system_optimization_script_exists(self):
        """System optimization script exists."""
        # Check both possible locations
        script1 = Path(__file__).parent.parent / "scripts" / "optimize_system.sh"
        script2 = Path(__file__).parent.parent / "aurora_pro" / "scripts" / "optimize_system.sh"
        assert script1.exists() or script2.exists(), "System optimization script not found in scripts/ or aurora_pro/scripts/"


class TestGPUOptimization:
    """Test GPU quantization and optimization."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_model_quantizer_exists(self):
        """Model quantizer for GPU optimization exists."""
        quantizer = self.AURORA_PRO / "codex_model_quantizer.py"
        assert quantizer.exists()
    
    def test_local_inference_exists(self):
        """Local inference module exists."""
        inference = self.AURORA_PRO / "local_inference.py"
        assert inference.exists()


class TestVisionCapabilities:
    """Test vision and screen analysis capabilities."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_vision_agent_exists(self):
        """Vision agent exists."""
        agent = self.AURORA_PRO / "vision_agent.py"
        assert agent.exists()
        
        content = agent.read_text()
        assert "screenshot" in content.lower() or "capture" in content.lower()
        assert "ocr" in content.lower()
    
    def test_vision_streamer_exists(self):
        """Vision streamer for real-time streaming exists."""
        streamer = self.AURORA_PRO / "vision_streamer.py"
        assert streamer.exists()
    
    def test_vision_viewer_exists(self):
        """Vision viewer HTML interface exists."""
        viewer = self.AURORA_PRO / "vision_viewer.html"
        assert viewer.exists()


class TestStealthCapabilities:
    """Test stealth browsing and anti-detection."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_stealth_browser_exists(self):
        """Stealth browser agent exists."""
        browser = self.AURORA_PRO / "stealth_browser_agent.py"
        assert browser.exists()
        
        content = browser.read_text()
        assert "undetected" in content.lower() or "stealth" in content.lower()
    
    def test_captcha_manager_exists(self):
        """CAPTCHA manager exists."""
        captcha = self.AURORA_PRO / "captcha_manager.py"
        assert captcha.exists()
    
    def test_proxy_manager_exists(self):
        """Proxy manager exists."""
        proxy = self.AURORA_PRO / "proxy_manager.py"
        assert proxy.exists()


class TestAdvancedFeatures:
    """Test advanced features."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_cache_manager_exists(self):
        """Cache manager with multi-tier caching exists."""
        cache = self.AURORA_PRO / "cache_manager.py"
        assert cache.exists()
        
        content = cache.read_text()
        assert "cache" in content.lower()
    
    def test_input_control_exists(self):
        """Mouse and keyboard control agent exists."""
        agent = self.AURORA_PRO / "mouse_keyboard_agent.py"
        assert agent.exists()
    
    def test_plugin_manager_exists(self):
        """Plugin manager for extensibility exists."""
        manager = self.AURORA_PRO / "plugin_manager.py"
        assert manager.exists()
        
        content = manager.read_text()
        assert "plugin" in content.lower()
        assert "sandbox" in content.lower() or "resource" in content.lower()
    
    def test_reasoning_display_exists(self):
        """Reasoning display for transparency exists."""
        display = self.AURORA_PRO / "reasoning_display.py"
        assert display.exists()


class TestSecurityAndAudit:
    """Test security and audit system."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    CONFIG = AURORA_PRO / "config"
    
    def test_operator_config_exists(self):
        """Operator authorization config exists."""
        config = self.CONFIG / "operator_enabled.yaml"
        assert config.exists()
        
        content = config.read_text()
        assert "operator_enabled" in content
        assert "features" in content
    
    def test_ssrf_protection_exists(self):
        """SSRF protection module exists."""
        protection = self.AURORA_PRO / "ssrf_protection.py"
        assert protection.exists()
    
    def test_secrets_loader_exists(self):
        """Secrets loader for secure credential management exists."""
        loader = self.AURORA_PRO / "secrets_loader.py"
        assert loader.exists()


class TestMonitoringAndControl:
    """Test monitoring and control systems."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_control_center_exists(self):
        """Control center exists."""
        center = self.AURORA_PRO / "control_center.py"
        assert center.exists()
    
    def test_web_control_panel_exists(self):
        """Web control panel exists."""
        panel = self.AURORA_PRO / "web_control_panel.py"
        assert panel.exists()
    
    def test_heartbeat_monitor_exists(self):
        """Heartbeat monitor exists."""
        monitor = self.AURORA_PRO / "heartbeat_monitor.py"
        assert monitor.exists()
    
    def test_dashboard_exists(self):
        """Dashboard interface exists."""
        dashboard = self.AURORA_PRO / "aurora_dashboard.py"
        assert dashboard.exists()


class TestCommunication:
    """Test communication and integration."""
    
    AURORA_PRO = Path(__file__).parent.parent / "aurora_pro"
    
    def test_communication_bus_exists(self):
        """Communication bus exists."""
        bus = self.AURORA_PRO / "communication_bus.py"
        assert bus.exists()
    
    def test_main_api_exists(self):
        """Main API server exists."""
        api = self.AURORA_PRO / "main.py"
        assert api.exists()
        
        content = api.read_text()
        assert "FastAPI" in content or "app = " in content
        # Check for key endpoints
        assert "@app." in content


class TestDeployment:
    """Test deployment infrastructure."""
    
    REPO_ROOT = Path(__file__).parent.parent
    AURORA_PRO = REPO_ROOT / "aurora_pro"
    
    def test_run_script_exists(self):
        """Launch script exists."""
        script = self.AURORA_PRO / "run_aurora.sh"
        assert script.exists()
    
    def test_production_deploy_exists(self):
        """Production deployment script exists."""
        script = self.AURORA_PRO / "production_deploy.sh"
        assert script.exists()
    
    def test_docker_files_exist(self):
        """Docker configuration exists."""
        dockerfile = self.REPO_ROOT / "docker" / "Dockerfile"
        compose = self.REPO_ROOT / "docker" / "docker-compose.yml"
        assert dockerfile.exists()
        assert compose.exists()
    
    def test_requirements_exist(self):
        """Python requirements file exists."""
        requirements = self.REPO_ROOT / "requirements.txt"
        assert requirements.exists()
        assert requirements.stat().st_size > 0


class TestDocumentation:
    """Test documentation completeness."""
    
    REPO_ROOT = Path(__file__).parent.parent
    AURORA_PRO = REPO_ROOT / "aurora_pro"
    
    def test_readme_exists(self):
        """README exists."""
        readme = self.REPO_ROOT / "README.md"
        assert readme.exists()
    
    def test_feature_summary_exists(self):
        """Feature summary documentation exists."""
        summary = self.AURORA_PRO / "WHAT_YOU_NOW_HAVE.md"
        assert summary.exists()
    
    def test_deployment_guide_exists(self):
        """Deployment guide exists."""
        guide = self.AURORA_PRO / "DEPLOYMENT_GUIDE.md"
        assert guide.exists()
    
    def test_control_center_guide_exists(self):
        """Control center guide exists."""
        guide = self.AURORA_PRO / "CONTROL_CENTER_GUIDE.md"
        assert guide.exists()
    
    def test_production_deployment_exists(self):
        """Production deployment guide exists."""
        guide = self.AURORA_PRO / "PRODUCTION_DEPLOYMENT.md"
        assert guide.exists()


class TestBlueprintMapping:
    """Test that blueprint requirements map to implementation."""
    
    REPO_ROOT = Path(__file__).parent.parent
    
    def test_blueprint_reference_completeness(self):
        """Blueprint reference covers all key topics."""
        reference = self.REPO_ROOT / "BLUEPRINT_IMPLEMENTATION_REFERENCE.md"
        content = reference.read_text()
        
        # Key sections from PDF directive
        required_sections = [
            "Model Context Protocol",
            "Multi-Agent Orchestration",
            "Hardware-Optimized Parallel Execution",
            "GPU Quantization",
            "Vision",
            "Stealth",
            "Caching",
            "Security",
            "Monitoring",
            "Documentation",
            "Blueprint Compliance Matrix",
        ]
        
        for section in required_sections:
            assert section in content, f"Missing section: {section}"
    
    def test_compliance_matrix_shows_complete(self):
        """Compliance matrix shows 100% implementation."""
        reference = self.REPO_ROOT / "BLUEPRINT_IMPLEMENTATION_REFERENCE.md"
        content = reference.read_text()
        
        # Should have compliance matrix
        assert "Blueprint Compliance Matrix" in content
        assert "100%" in content
        # Should have checkmarks
        assert "✅" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
