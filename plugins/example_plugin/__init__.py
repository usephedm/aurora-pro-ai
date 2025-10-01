"""
Example Plugin for Aurora Pro AI

This demonstrates how to create a custom plugin.
"""
from typing import Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.plugins import BasePlugin


class Plugin(BasePlugin):
    """Example plugin implementation"""
    
    def __init__(self):
        super().__init__(
            name="example_plugin",
            version="1.0.0",
            description="Example plugin demonstrating the plugin system"
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin"""
        self.config = config
        print(f"Initializing {self.name} with config: {config}")
        return True
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute plugin functionality"""
        operation = kwargs.get("operation", "default")
        
        if operation == "greet":
            name = kwargs.get("name", "World")
            return f"Hello, {name}! This is {self.name}"
        
        elif operation == "process":
            data = kwargs.get("data", "")
            return f"Processed: {data.upper()}"
        
        else:
            return f"Unknown operation: {operation}"
    
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        print(f"Cleaning up {self.name}")
        self.config = {}
