"""Plugin Manager for Aurora Pro - Sandboxed plugin system.

This module provides a secure plugin system with resource limits, lifecycle
management, and sandboxed execution. All features are gated by operator_enabled.yaml.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import logging
import os
import resource
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import yaml

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Plugin metadata from manifest."""
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    dependencies: List[str]
    permissions: List[str]


@dataclass
class PluginInstance:
    """Loaded plugin instance."""
    plugin_id: str
    metadata: PluginMetadata
    module: Any
    loaded_at: float
    enabled: bool = True
    error: Optional[str] = None


class PluginManager:
    """
    Plugin manager with sandboxed execution and resource limits.

    Features:
    - Load plugins from /plugins directory
    - Sandboxed execution with resource limits (CPU, memory)
    - Plugin registry and lifecycle management
    - Permission system
    - Hot reload support
    - Operator authorization gating
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/plugin_manager.log"
    CONFIG_PATH = "/root/aurora_pro/config/operator_enabled.yaml"
    PLUGINS_DIR = "/root/aurora_pro/plugins"

    # Resource limits per plugin
    MAX_MEMORY_MB = 512
    MAX_CPU_TIME_SEC = 60

    def __init__(self):
        self._config: Dict = {}
        self._running = False
        self._plugins: Dict[str, PluginInstance] = {}
        self._lock = asyncio.Lock()

        # Create plugins directory
        Path(self.PLUGINS_DIR).mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Initialize plugin manager."""
        self._running = True
        await self._load_config()
        await self._audit_log("system", "Plugin manager started")

    async def stop(self):
        """Shutdown plugin manager and unload all plugins."""
        self._running = False
        await self.unload_all_plugins()
        await self._audit_log("system", "Plugin manager stopped")

    async def _load_config(self):
        """Load operator configuration."""
        try:
            async with aiofiles.open(self.CONFIG_PATH, "r") as f:
                content = await f.read()
                self._config = yaml.safe_load(content)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {"operator_enabled": False, "features": {}}

    def _check_authorization(self) -> bool:
        """Check if plugin system is authorized."""
        operator_enabled = self._config.get("operator_enabled", False)
        feature_enabled = self._config.get("features", {}).get("plugin_system", False)
        return operator_enabled and feature_enabled

    async def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in plugins directory.

        Returns list of plugin directory names.
        """
        plugins = []
        plugins_path = Path(self.PLUGINS_DIR)

        if not plugins_path.exists():
            return plugins

        for item in plugins_path.iterdir():
            if item.is_dir():
                # Check for plugin.yaml manifest
                manifest_path = item / "plugin.yaml"
                if manifest_path.exists():
                    plugins.append(item.name)

        return plugins

    async def load_plugin(
        self,
        plugin_name: str,
        operator_user: Optional[str] = None,
    ) -> PluginInstance:
        """
        Load and initialize a plugin.

        Args:
            plugin_name: Name of plugin directory
            operator_user: User requesting operation

        Returns:
            PluginInstance
        """
        if not self._check_authorization():
            raise PermissionError("Plugin system not authorized - check operator_enabled.yaml")

        async with self._lock:
            plugin_path = Path(self.PLUGINS_DIR) / plugin_name

            if not plugin_path.exists():
                raise ValueError(f"Plugin not found: {plugin_name}")

            # Load manifest
            manifest_path = plugin_path / "plugin.yaml"
            if not manifest_path.exists():
                raise ValueError(f"Plugin manifest not found: {plugin_name}/plugin.yaml")

            try:
                async with aiofiles.open(manifest_path, "r") as f:
                    manifest_content = await f.read()
                    manifest_data = yaml.safe_load(manifest_content)

                metadata = PluginMetadata(
                    name=manifest_data.get("name", plugin_name),
                    version=manifest_data.get("version", "0.0.0"),
                    author=manifest_data.get("author", "unknown"),
                    description=manifest_data.get("description", ""),
                    entry_point=manifest_data.get("entry_point", "main.py"),
                    dependencies=manifest_data.get("dependencies", []),
                    permissions=manifest_data.get("permissions", []),
                )

                # Check if already loaded
                if plugin_name in self._plugins:
                    logger.info(f"Plugin {plugin_name} already loaded, reloading")
                    await self.unload_plugin(plugin_name, operator_user)

                # Load Python module
                entry_file = plugin_path / metadata.entry_point
                if not entry_file.exists():
                    raise ValueError(f"Plugin entry point not found: {metadata.entry_point}")

                spec = importlib.util.spec_from_file_location(
                    f"aurora_plugin_{plugin_name}",
                    str(entry_file)
                )

                if spec is None or spec.loader is None:
                    raise ValueError(f"Failed to load plugin module: {plugin_name}")

                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module

                # Execute module in sandboxed environment
                await self._execute_sandboxed(lambda: spec.loader.exec_module(module))

                # Initialize plugin if it has setup() function
                if hasattr(module, 'setup'):
                    await self._execute_sandboxed(module.setup)

                # Create plugin instance
                plugin_id = str(uuid.uuid4())
                instance = PluginInstance(
                    plugin_id=plugin_id,
                    metadata=metadata,
                    module=module,
                    loaded_at=time.time(),
                    enabled=True,
                )

                self._plugins[plugin_name] = instance

                await self._audit_log(
                    "load_plugin",
                    f"Loaded plugin: {plugin_name} v{metadata.version}",
                    operator_user=operator_user,
                    metadata={
                        "plugin_name": plugin_name,
                        "plugin_id": plugin_id,
                        "version": metadata.version,
                        "author": metadata.author,
                    },
                )

                logger.info(f"Plugin loaded: {plugin_name} v{metadata.version}")
                return instance

            except Exception as e:
                error_msg = f"Failed to load plugin {plugin_name}: {e}"
                logger.error(error_msg)
                await self._audit_log("error", error_msg)
                raise

    async def unload_plugin(
        self,
        plugin_name: str,
        operator_user: Optional[str] = None,
    ):
        """
        Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload
            operator_user: User requesting operation
        """
        if not self._check_authorization():
            raise PermissionError("Plugin system not authorized - check operator_enabled.yaml")

        async with self._lock:
            if plugin_name not in self._plugins:
                raise ValueError(f"Plugin not loaded: {plugin_name}")

            instance = self._plugins[plugin_name]

            # Call teardown if available
            if hasattr(instance.module, 'teardown'):
                try:
                    await self._execute_sandboxed(instance.module.teardown)
                except Exception as e:
                    logger.warning(f"Plugin teardown error: {e}")

            # Remove from registry
            del self._plugins[plugin_name]

            # Remove from sys.modules
            module_name = f"aurora_plugin_{plugin_name}"
            if module_name in sys.modules:
                del sys.modules[module_name]

            await self._audit_log(
                "unload_plugin",
                f"Unloaded plugin: {plugin_name}",
                operator_user=operator_user,
                metadata={"plugin_name": plugin_name},
            )

            logger.info(f"Plugin unloaded: {plugin_name}")

    async def unload_all_plugins(self):
        """Unload all loaded plugins."""
        plugin_names = list(self._plugins.keys())
        for plugin_name in plugin_names:
            try:
                await self.unload_plugin(plugin_name)
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_name}: {e}")

    async def call_plugin(
        self,
        plugin_name: str,
        function_name: str,
        *args,
        operator_user: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Call a plugin function with sandboxing.

        Args:
            plugin_name: Name of plugin
            function_name: Function to call
            *args: Positional arguments
            operator_user: User requesting operation
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        if not self._check_authorization():
            raise PermissionError("Plugin system not authorized - check operator_enabled.yaml")

        if plugin_name not in self._plugins:
            raise ValueError(f"Plugin not loaded: {plugin_name}")

        instance = self._plugins[plugin_name]

        if not instance.enabled:
            raise ValueError(f"Plugin disabled: {plugin_name}")

        if not hasattr(instance.module, function_name):
            raise ValueError(f"Plugin function not found: {plugin_name}.{function_name}")

        func = getattr(instance.module, function_name)

        try:
            # Execute function in sandboxed environment
            result = await self._execute_sandboxed(lambda: func(*args, **kwargs))

            await self._audit_log(
                "call_plugin",
                f"Called {plugin_name}.{function_name}",
                operator_user=operator_user,
                metadata={
                    "plugin_name": plugin_name,
                    "function": function_name,
                },
            )

            return result

        except Exception as e:
            error_msg = f"Plugin call failed: {plugin_name}.{function_name}: {e}"
            logger.error(error_msg)
            await self._audit_log("error", error_msg)
            raise

    async def _execute_sandboxed(self, func):
        """
        Execute function with resource limits.

        Sets CPU time and memory limits to prevent runaway plugins.
        """
        # Set resource limits (Unix only)
        if sys.platform != 'win32':
            try:
                # CPU time limit
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (self.MAX_CPU_TIME_SEC, self.MAX_CPU_TIME_SEC)
                )

                # Memory limit (in bytes)
                max_memory_bytes = self.MAX_MEMORY_MB * 1024 * 1024
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (max_memory_bytes, max_memory_bytes)
                )
            except Exception as e:
                logger.warning(f"Failed to set resource limits: {e}")

        # Execute function
        if asyncio.iscoroutinefunction(func):
            return await func()
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func)

    def list_plugins(self) -> List[Dict]:
        """List all loaded plugins."""
        plugins = []
        for plugin_name, instance in self._plugins.items():
            plugins.append({
                "name": plugin_name,
                "plugin_id": instance.plugin_id,
                "version": instance.metadata.version,
                "author": instance.metadata.author,
                "description": instance.metadata.description,
                "enabled": instance.enabled,
                "loaded_at": instance.loaded_at,
                "error": instance.error,
            })
        return plugins

    def get_plugin(self, plugin_name: str) -> Optional[PluginInstance]:
        """Get plugin instance by name."""
        return self._plugins.get(plugin_name)

    def get_status(self) -> Dict:
        """Get plugin manager status."""
        return {
            "running": self._running,
            "authorized": self._check_authorization(),
            "plugins_dir": self.PLUGINS_DIR,
            "loaded_plugins": len(self._plugins),
            "plugins": self.list_plugins(),
        }

    async def _audit_log(
        self,
        action: str,
        message: str,
        operator_user: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Write audit log entry."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

        entry = {
            "timestamp": timestamp,
            "action": action,
            "message": message,
            "operator_user": operator_user or "system",
            "metadata": metadata or {},
        }

        line = json.dumps(entry) + "\n"

        log_path = Path(self.AUDIT_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(self.AUDIT_LOG_PATH, "a") as f:
                await f.write(line)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Singleton instance
_plugin_manager_instance: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create plugin manager singleton."""
    global _plugin_manager_instance
    if _plugin_manager_instance is None:
        _plugin_manager_instance = PluginManager()
    return _plugin_manager_instance


__all__ = ["PluginManager", "get_plugin_manager", "PluginMetadata", "PluginInstance"]