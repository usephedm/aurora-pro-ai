
"""Inter-Agent Communication Bus for Aurora Pro.

This module provides a Redis-based pub/sub message bus for real-time, 
asynchronous communication between all agents in the Aurora Pro system.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class CommunicationBus:
    """A Redis-based pub/sub message bus for inter-agent communication."""

    def __init__(self, host: str = 'localhost', port: int = 6379):
        self._redis = redis.Redis(host=host, port=port, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        self._listeners: Dict[str, Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]] = {}

    async def connect(self):
        """Connect to the Redis server and start the listener task."""
        try:
            await self._redis.ping()
            logger.info("Successfully connected to Redis for communication bus.")
            asyncio.create_task(self._listener_task())
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish a message to a specific channel."""
        try:
            await self._redis.publish(channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to publish message to channel '{channel}': {e}")

    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]):
        """Subscribe to a channel and register a callback."""
        await self._pubsub.subscribe(channel)
        self._listeners[channel] = callback
        logger.info(f"Subscribed to channel: {channel}")

    async def _listener_task(self):
        """The main listener task that receives messages and calls callbacks."""
        while True:
            try:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    channel = message['channel']
                    if channel in self._listeners:
                        try:
                            data = json.loads(message['data'])
                            await self._listeners[channel](data)
                        except json.JSONDecodeError:
                            logger.warning(f"Received non-JSON message on channel '{channel}': {message['data']}")
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error in communication bus listener: {e}")

# Singleton instance
_communication_bus_instance: CommunicationBus | None = None

def get_communication_bus() -> CommunicationBus:
    """Get or create the communication bus singleton."""
    global _communication_bus_instance
    if _communication_bus_instance is None:
        _communication_bus_instance = CommunicationBus()
    return _communication_bus_instance

__all__ = ["CommunicationBus", "get_communication_bus"]
