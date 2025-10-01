"""
Aurora Pro AI - Plugin System
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import importlib
import os
from pathlib import Path

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger("plugins")
settings = get_settings()


class BasePlugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self, name: str, version: str, description: str = ""):
        self.name = name
        self.version = version
        self.description = description
        self.enabled = False
        self.config: Dict[str, Any] = {}
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration
        
        Args:
            config: Plugin configuration dictionary
        
        Returns:
            bool: True if initialization successful
        """
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute plugin functionality
        
        Returns:
            Any: Plugin execution result
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
            "config": self.config
        }


class PluginManager:
    """Manage plugins lifecycle"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugins_dir = Path(settings.plugins_dir)
        logger.info("Plugin manager initialized")
    
    def discover_plugins(self) -> None:
        """Discover available plugins in plugins directory"""
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                try:
                    self._load_plugin(plugin_dir.name)
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_dir.name}: {e}")
    
    def _load_plugin(self, plugin_name: str) -> None:
        """Load a specific plugin"""
        try:
            # Dynamically import plugin module
            module = importlib.import_module(f"plugins.{plugin_name}")
            
            # Get plugin class (should be named Plugin)
            if hasattr(module, "Plugin"):
                plugin_class = getattr(module, "Plugin")
                plugin = plugin_class()
                
                if isinstance(plugin, BasePlugin):
                    self.plugins[plugin_name] = plugin
                    logger.info(f"Plugin loaded: {plugin_name}")
                else:
                    logger.warning(f"Plugin {plugin_name} does not inherit from BasePlugin")
            else:
                logger.warning(f"Plugin {plugin_name} does not have Plugin class")
                
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
    
    def enable_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Enable a plugin"""
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not found: {plugin_name}")
            return False
        
        plugin = self.plugins[plugin_name]
        
        try:
            if plugin.initialize(config or {}):
                plugin.enabled = True
                logger.info(f"Plugin enabled: {plugin_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_name}: {e}")
            return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        try:
            plugin.cleanup()
            plugin.enabled = False
            logger.info(f"Plugin disabled: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to disable plugin {plugin_name}: {e}")
            return False
    
    def execute_plugin(self, plugin_name: str, *args, **kwargs) -> Any:
        """Execute a plugin"""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin not found: {plugin_name}")
        
        plugin = self.plugins[plugin_name]
        
        if not plugin.enabled:
            raise RuntimeError(f"Plugin not enabled: {plugin_name}")
        
        return plugin.execute(*args, **kwargs)
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins"""
        return {name: plugin.get_info() for name, plugin in self.plugins.items()}
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a specific plugin"""
        return self.plugins.get(plugin_name)


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager instance"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
        if settings.plugins_enabled:
            _plugin_manager.discover_plugins()
    return _plugin_manager
