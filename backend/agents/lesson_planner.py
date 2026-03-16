"""
Phase 1: Lesson planner agent — Gemini generates structured lesson plan JSON with image prompts.
Uses AI Studio client (GOOGLE_API_KEY).
"""
import json
import os
import re
from typing import Any

from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Image prompt suffix per CURSOR_CONTEXT.md (append for Imagen 3)
IMAGEN_PROMPT_SUFFIX = (
    " child-friendly illustration, bright colors, simple clear shapes, "
    "white background, educational, cartoon style, no text in image"
)

LESSON_PLANNER_PROMPT = """You are a lesson planning agent for a children's educational app.

A parent has requested a lesson on: "{topic}"
Grade level: "{grade}" (K-2 = ages 5-7, grade3-5 = ages 8-10, grade6-8 = ages 11-13)

Your job: Generate a structured lesson plan as JSON. Be creative with image prompts.
Make the lesson feel like an adventure, not a textbook.

Generate exactly 4 images:
1. Core concept — the main idea visualized
2. Real-world example — something the kid encounters daily
3. Step by step — a process or comparison shown visually
4. Fun/memorable — the most engaging or surprising version of the concept

Return ONLY valid JSON, no other text:

{{
  "lesson_outline": ["assess", "intro", "analogy", "check_1", "deeper", "check_2", "celebrate"],
  "images": [
    {{
      "id": "img_1",
      "teaching_moment": "short description of when to use this image",
      "imagen_prompt": "detailed prompt for Imagen 3, child-friendly illustration style",
      "teaching_notes": "what the character should say when showing this",
      "can_reuse_for": ["list of kid questions this image can answer"]
    }}
  ],
  "opening_line": "The first thing Zara/Finn says to the kid to start the lesson",
  "key_concepts": ["concept1", "concept2", "concept3"]
}}
"""


def _extract_json(text: str) -> str:
    """Strip markdown code fences and extract JSON blob."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    # Try raw JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        return text[start:end]
    return text


def _ensure_four_images(plan: dict[str, Any]) -> dict[str, Any]:
    """Ensure exactly 4 images; trim or pad to match CURSOR_CONTEXT."""
    images = plan.get("images") or []
    if len(images) > 4:
        plan["images"] = images[:4]
    # IDs img_1..img_4
    for i, img in enumerate(plan["images"], start=1):
        img["id"] = img.get("id") or f"img_{i}"
        prompt = (img.get("imagen_prompt") or "").strip()
        if prompt and not prompt.endswith(IMAGEN_PROMPT_SUFFIX.strip()):
            img["imagen_prompt"] = prompt + IMAGEN_PROMPT_SUFFIX
    return plan


async def generate_lesson_plan(topic: str, grade: str, character: str) -> dict[str, Any]:
    """
    Call Gemini via AI Studio to generate lesson plan JSON.
    Returns dict with lesson_outline, images (4), opening_line, key_concepts.
    """
    prompt = LESSON_PLANNER_PROMPT.format(topic=topic, grade=grade)

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "temperature": 0.7,
            "max_output_tokens": 4096,
            "response_mime_type": "application/json",
        },
    )

    raw = getattr(response, "text", None) or (
        response.candidates[0].content.parts[0].text
        if response.candidates and response.candidates[0].content.parts
        else None
    )
    if not raw:
        raise ValueError("Gemini returned no content")

    json_str = _extract_json(raw)
    plan = json.loads(json_str)
    return _ensure_four_images(plan)
