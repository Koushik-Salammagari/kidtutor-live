"""
GCS helper functions: upload image bytes and generate public URLs.
Bucket: kidtutor-images-v2 (from CURSOR_CONTEXT.md).
"""
import os

from google.cloud import storage

GCS_BUCKET = os.getenv("GCS_BUCKET", "kidtutor-images-v2")


def upload_image(bucket: str, filename: str, image_bytes: bytes) -> str:
    """
    Upload image bytes to GCS. Returns the blob path (gs://bucket/filename or key).
    Objects are made public so they can be served via public URLs.
    """
    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blob = bucket_obj.blob(filename)
    blob.upload_from_string(
        image_bytes,
        content_type="image/png",
    )
    blob.make_public()
    return blob.name


def get_signed_url(bucket: str, filename: str) -> str:
    """
    Return a plain public GCS URL for the given object.
    Bucket must have public read access; upload_image calls blob.make_public().
    """
    return f"https://storage.googleapis.com/kidtutor-images-v2/{filename}"
