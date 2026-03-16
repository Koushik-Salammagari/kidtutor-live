"""
Phase 2: Live API agent — Gemini Live session with character persona.
Skeleton: persona prompts + voice config for Zara and Finn; Live API session to be wired to WebSocket.
Uses Vertex AI auth (no API key). Project: kidtutor-v2.
"""
import json
import os
from typing import Any, AsyncIterator

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "kidtutor-v2")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# --- Character personas (CURSOR_CONTEXT.md) ---

ZARA_PERSONA = """You are Zara, a friendly and enthusiastic robot teacher for kids.
You speak in short, energetic sentences. You use tech and space metaphors.
You say things like "Beep boop! Great question!" and "Let's compute this together!"
You never use words longer than a 3rd grader would know unless you immediately explain them.
You always celebrate when a kid gets something right.
Grade level: {grade}. Topic: {topic}.
Current image on screen: {current_image_teaching_notes}.
Available images: {image_manifest}.
When you want to show or change an image, emit a JSON command on a SEPARATE LINE starting with CMD:
CMD: {{"cmd": "show", "id": "img_1"}}
CMD: {{"cmd": "emotion", "character": "zara", "state": "happy"}}
"""

FINN_PERSONA = """You are Finn, a clever and warm fox who loves telling stories to teach kids.
You use nature, forest, and animal metaphors to explain everything.
You say things like "Imagine you're in the forest..." and "Great thinking, little cub!"
You speak warmly and slowly, never rushing.
You always turn abstract concepts into little stories.
Grade level: {grade}. Topic: {topic}.
Current image on screen: {current_image_teaching_notes}.
Available images: {image_manifest}.
When you want to show or change an image, emit a JSON command on a SEPARATE LINE starting with CMD:
CMD: {{"cmd": "show", "id": "img_1"}}
CMD: {{"cmd": "emotion", "character": "finn", "state": "happy"}}
"""

# Voice: Gemini voice names per CURSOR_CONTEXT
VOICE_ZARA = "Aoede"   # bright, clear
VOICE_FINN = "Charon"  # warm, storytelling


def get_persona_prompt(
    character: str,
    grade: str,
    topic: str,
    current_image_teaching_notes: str = "",
    image_manifest: str | None = None,
) -> str:
    """Build system prompt for the chosen character. Used to inject into Live API."""
    manifest_str = image_manifest if image_manifest is not None else "[]"
    if character == "zara":
        return ZARA_PERSONA.format(
            grade=grade,
            topic=topic,
            current_image_teaching_notes=current_image_teaching_notes or "(none yet)",
            image_manifest=manifest_str,
        )
    if character == "finn":
        return FINN_PERSONA.format(
            grade=grade,
            topic=topic,
            current_image_teaching_notes=current_image_teaching_notes or "(none yet)",
            image_manifest=manifest_str,
        )
    raise ValueError(f"Unknown character: {character}. Use 'zara' or 'finn'.")


def get_voice_config(character: str) -> dict[str, Any]:
    """Return voice config for Gemini Live API."""
    if character == "zara":
        return {"voice": VOICE_ZARA}
    if character == "finn":
        return {"voice": VOICE_FINN}
    raise ValueError(f"Unknown character: {character}. Use 'zara' or 'finn'.")


def parse_cmd_line(line: str) -> dict[str, Any] | None:
    """If line is 'CMD: {...}', return parsed JSON; else None."""
    line = line.strip()
    if line.upper().startswith("CMD:"):
        json_str = line[4:].strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    return None


async def run_live_session(
    session_id: str,
    character: str,
    grade: str,
    topic: str,
    opening_line: str,
    image_manifest: list[dict[str, Any]],
) -> AsyncIterator[tuple[str, bytes | dict | None]]:
    """
    Skeleton: run Gemini Live API session with character persona.
    Yields ("audio", pcm_bytes) or ("command", cmd_dict) for the WebSocket handler to forward.
    To be wired to WebSocket: client PCM in → this session; yields → client (audio + JSON commands).
    """
    # TODO: Initialize Gemini Live API client (Vertex AI, no API key).
    # TODO: Send system instruction = get_persona_prompt(character, grade, topic, "", json.dumps(image_manifest))
    # TODO: Send opening_line as first user turn or system prompt addition.
    # TODO: Stream client PCM into Live API; stream model response out.
    # TODO: Parse model text for CMD: lines and yield ("command", parsed); yield ("audio", pcm) for audio.
    yield ("command", {"cmd": "emotion", "character": character, "state": "happy"})
    yield ("audio", None)  # placeholder; real implementation will stream PCM
    return
