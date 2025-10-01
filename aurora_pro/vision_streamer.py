"""Vision Streamer for Aurora Pro - Real-time visualization server.

This module provides a FastAPI-based web server to stream the Vision Agent's
perspective to a web browser in real-time.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

app = FastAPI()
frame_queue = asyncio.Queue(maxsize=30)

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Send a message to all active WebSocket connections."""
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

async def frame_generator():
    """Generator function that yields video frames from the queue."""
    while True:
        frame = await frame_queue.get()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.post("/frame")
async def receive_frame(request: Request):
    """Endpoint for the VisionAgent to send frames to."""
    frame = await request.body()
    try:
        frame_queue.put_nowait(frame)
    except asyncio.QueueFull:
        # If the queue is full, discard the oldest frame and add the new one.
        await frame_queue.get()
        await frame_queue.put(frame)
    return {"status": "success"}

@app.get("/video_feed")
async def video_feed():
    """Endpoint to stream the video feed."""
    return StreamingResponse(frame_generator(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages from the client if needed
            await manager.broadcast(f"Message text was: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
