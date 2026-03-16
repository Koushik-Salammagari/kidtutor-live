"""
KidTutor Live — FastAPI app + WebSocket endpoints.
Serves frontend from /frontend. Uses Vertex AI auth (no API key).
"""
import asyncio
import os
import uuid
from pathlib import Path

from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.agents.lesson_planner import generate_lesson_plan
from backend.services.imagen import generate_images
from backend.services.session import create_session


class SetupRequest(BaseModel):
    topic: str
    grade: str  # k-2 | grade3-5 | grade6-8
    character: str  # zara | finn

# Project: kidtutor-v2, bucket: kidtutor-images-v2 (from CURSOR_CONTEXT.md)
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "kidtutor-v2")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GCS_BUCKET = os.getenv("GCS_BUCKET", "kidtutor-images-v2")

app = FastAPI(
    title="KidTutor Live",
    description="AI-powered educational app for kids — Gemini Live API + Imagen 3",
    version="1.0.0",
)

# Mount frontend as StaticFiles at /frontend (CURSOR_CONTEXT: "The frontend serves from /frontend")
_frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(_frontend_path), html=True), name="frontend")


@app.get("/health")
async def health():
    """Returns {"status": "ok"}."""
    return {"status": "ok"}


@app.post("/setup")
async def setup(body: SetupRequest):
    """
    Receives topic + grade + character, runs Phase 1 (lesson plan + images),
    returns session_id. Uses async/await throughout; returns 500 on failure.
    """
    try:
        topic = body.topic.strip() or "general knowledge"
        grade = body.grade
        character = body.character

        # 1. Generate lesson plan JSON with image prompts
        lesson_plan = await generate_lesson_plan(topic, grade, character)

        # 2. Generate 4 images, upload to GCS kidtutor-images-v2; need session_id for paths
        session_id = str(uuid.uuid4())
        images = await generate_images(session_id, lesson_plan["images"])

        # 3. Create session in Firestore (sync call off event loop)
        await asyncio.to_thread(
            create_session,
            {
                "topic": topic,
                "grade": grade,
                "character": character,
                "images": images,
                "lesson_outline": lesson_plan["lesson_outline"],
                "opening_line": lesson_plan["opening_line"],
            },
            session_id,
        )

        return {"session_id": session_id, "status": "ready"}
    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "detail": type(e).__name__},
            status_code=500,
        )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Returns session metadata for pick.html."""
    # TODO: read from Firestore via session service
    return JSONResponse(
        content={"session_id": session_id, "error": "not_found"},
        status_code=404,
    )


@app.websocket("/ws/{session_id}")
async def websocket_lesson(websocket: WebSocket, session_id: str):
    """
    Bidirectional: audio PCM + JSON commands.
    Client → Server: binary PCM 16kHz 16-bit mono; text: {"type": "barge_in"}.
    Server → Client: binary PCM from Gemini; text: image/emotion commands.
    """
    await websocket.accept()
    try:
        # TODO: start Gemini Live API session with character persona (orchestrator)
        # TODO: stream audio bidirectionally, parse and forward JSON commands
        while True:
            await websocket.receive()
            # Skeleton: consume frames until orchestrator is wired (audio → Gemini, Gemini → audio + JSON)
    except WebSocketDisconnect:
        pass
    finally:
        pass  # TODO: tear down Live API session
