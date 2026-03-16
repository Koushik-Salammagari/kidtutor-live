"""
Imagen 3 via Vertex AI: generate 4 images, upload to GCS bucket kidtutor-images-v2, return signed URLs.
Project: kidtutor-v2, location: us-central1.
"""
import asyncio
import io
import os
from typing import Any

from backend.services import storage

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "kidtutor-v2")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GCS_BUCKET = os.getenv("GCS_BUCKET", "kidtutor-images-v2")

# Imagen 3 model (Vertex AI). Use imagegeneration@006 or imagen-3.0-generate-002 per docs.
IMAGEN_MODEL = "imagen-3.0-generate-002"


async def generate_and_upload_images(
    session_id: str,
    images_spec: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    For each of up to 4 image specs (id, imagen_prompt, ...), call Imagen 3 to generate,
    upload to GCS at {session_id}/{id}.png, then return list of {id, gcs_url, signed_url, ...}.
    On any failure, returns placeholders instead of raising.
    """
    def _placeholder(image: dict[str, Any], idx: int) -> dict[str, Any]:
        return {
            "id": image.get("id", f"img_{idx + 1}"),
            "gcs_url": "https://placehold.co/800x600/4A4E8C/FFFFFF?text=Loading+Image",
            "teaching_notes": image.get("teaching_notes", ""),
            "can_reuse_for": image.get("can_reuse_for", []),
        }

    try:
        try:
            import vertexai
            from vertexai.preview.vision_models import ImageGenerationModel
        except ImportError:
            raise RuntimeError(
                "google-cloud-aiplatform is required for Imagen; pip install google-cloud-aiplatform"
            )

        vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
        model = ImageGenerationModel.from_pretrained(IMAGEN_MODEL)

        results: list[dict[str, Any]] = []
        def _generate_one(prompt: str):
            return model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_some",
            )

        for spec in images_spec[:4]:
            img_id = spec.get("id", f"img_{len(results) + 1}")
            prompt = (spec.get("imagen_prompt") or "").strip()
            if not prompt:
                continue
            response = await asyncio.to_thread(_generate_one, prompt)
            if not response.images:
                continue
            image = response.images[0]
            buf = io.BytesIO()
            pil = getattr(image, "_pil_image", image)
            if hasattr(pil, "save"):
                pil.save(buf, format="PNG")
            else:
                raise ValueError("Imagen response image has no save/_pil_image")
            image_bytes = buf.getvalue()
            filename = f"{session_id}/{img_id}.png"
            await asyncio.to_thread(storage.upload_image, GCS_BUCKET, filename, image_bytes)
            signed_url = await asyncio.to_thread(storage.get_signed_url, GCS_BUCKET, filename)
            results.append({
                **spec,
                "id": img_id,
                "gcs_url": f"gs://{GCS_BUCKET}/{filename}",
                "signed_url": signed_url,
            })
        return results
    except Exception as e:
        print(e)
        return [_placeholder(image, i) for i, image in enumerate(images_spec[:4])]


async def generate_images(session_id: str, images_spec: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Generate 4 images via Imagen 3, upload to GCS kidtutor-images-v2.
    Returns list of {id, gcs_url, teaching_notes, can_reuse_for}.
    """
    raw = await generate_and_upload_images(session_id, images_spec)
    return [
        {
            "id": r["id"],
            "gcs_url": r["gcs_url"],
            "teaching_notes": r.get("teaching_notes", ""),
            "can_reuse_for": r.get("can_reuse_for") or [],
        }
        for r in raw
    ]
