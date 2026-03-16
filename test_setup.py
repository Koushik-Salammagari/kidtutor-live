import os
from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = "kidtutor-v2"
LOCATION = "us-central1"
BUCKET = "kidtutor-images-v2"

print("=" * 50)
print("KidTutor Live — Setup Verification")
print("=" * 50)

# ── Test 1: Gemini via Vertex AI ──────────────────
print("\n[1/3] Testing Gemini (AI Studio)...")
try:
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Reply with exactly: Gemini OK"
    )
    print("     ✓ Gemini:", response.text.strip())
except Exception as e:
    print("     ✗ Gemini FAILED:", e)

# ── Test 2: Google Cloud Storage ─────────────────
print("\n[2/3] Testing Cloud Storage...")
try:
    from google.cloud import storage
    gcs = storage.Client(project=PROJECT_ID)
    bucket = gcs.bucket(BUCKET)
    exists = bucket.exists()
    if exists:
        print(f"     ✓ GCS bucket '{BUCKET}' exists and is accessible")
    else:
        print(f"     ~ GCS bucket '{BUCKET}' does not exist yet — creating it...")
        new_bucket = gcs.create_bucket(BUCKET, location=LOCATION)
        print(f"     ✓ GCS bucket '{BUCKET}' created successfully")
except Exception as e:
    print("     ✗ GCS FAILED:", e)

# ── Test 3: Firestore ─────────────────────────────
print("\n[3/3] Testing Firestore...")
try:
    from google.cloud import firestore
    db = firestore.Client(project=PROJECT_ID)
    doc_ref = db.collection("test").document("setup_ping")
    doc_ref.set({"status": "ok", "project": PROJECT_ID})
    doc = doc_ref.get()
    if doc.exists:
        print("     ✓ Firestore: read/write working")
        doc_ref.delete()
    else:
        print("     ✗ Firestore: wrote but could not read back")
except Exception as e:
    print("     ✗ Firestore FAILED:", e)

print("\n" + "=" * 50)
print("Done. Fix any ✗ before building.")
print("=" * 50)