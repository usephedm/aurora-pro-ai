"""
Tests for Aurora Pro AI Core Configuration
"""
import pytest
from src.core.config import get_settings, Settings


def test_get_settings():
    """Test settings retrieval"""
    settings = get_settings()
    assert settings is not None
    assert isinstance(settings, Settings)


def test_settings_defaults():
    """Test default settings values"""
    settings = get_settings()
    
    assert settings.app_name == "aurora-pro-ai"
    assert settings.app_version == "1.0.0"
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.max_agents == 10


def test_settings_caching():
    """Test that settings are cached"""
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2
