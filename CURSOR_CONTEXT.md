# KidTutor Live — Cursor Master Context File
# Paste this into every Cursor session. Do not deviate from this architecture.

---

## What We Are Building

**KidTutor Live** — an AI-powered educational app for kids aged 5–13.
- A parent sets a topic (e.g. "fractions", "planets", "volcanoes") and a grade level
- A kid picks one of 2 cartoon characters: **Zara the Robot** or **Finn the Fox**
- The character explains the topic using voice + pre-generated images, in real time
- The kid can interrupt at any time and ask questions (barge-in via Gemini Live API)
- The character adapts its explanation based on the kid's questions and confusion signals
- Images are generated BEFORE the lesson starts (no latency during conversation)
- The agent decides whether to show / highlight / reuse / swap / dismiss images in real time

---

## Hackathon Context

- **Hackathon**: Gemini Live Agent Challenge (Google / Devpost)
- **Category**: Live Agents (real-time voice/vision)
- **Deadline**: March 16, 2026 @ 5pm PDT
- **Judging**: 40% Innovation & Multimodal UX, 30% Technical Architecture, 30% Demo
- **Required tech**: Gemini Live API, Google ADK, at least one GCP service, hosted on Cloud Run

---

## Tech Stack — Do Not Change These

| Layer | Technology |
|---|---|
| Backend framework | FastAPI (Python) |
| AI agent framework | Google ADK (google-adk) |
| Live voice AI | Gemini Live API via google-genai |
| Image generation | Imagen 3 via Vertex AI (imagegeneration@006) |
| Image storage | Google Cloud Storage (bucket: kidtutor-images-v2) |
| Session state | Firestore |
| Hosting | Google Cloud Run |
| Frontend | Vanilla HTML + CSS + JavaScript (no React, no Vue) |
| Character animation | SVG + Web Audio API (no Three.js, no external libs) |
| Transport | WebSocket (FastAPI WebSocket) |

---

## Environment Variables (.env)

```
GOOGLE_API_KEY=<from AI Studio>
GOOGLE_CLOUD_PROJECT=kidtutor-v2
GOOGLE_CLOUD_LOCATION=us-central1
GCS_BUCKET=kidtutor-images-v2
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

---

## Project File Structure — Do Not Reorganise

```
kidtutor-v2/
├── backend/
│   ├── main.py                  # FastAPI app + WebSocket endpoints
│   ├── agents/
│   │   ├── lesson_planner.py    # Phase 1: generates image manifest + lesson outline
│   │   ├── orchestrator.py      # Phase 2: Live API agent, talks to kid
│   │   └── adapter.py           # Reads kid signals, returns emotion/confusion state
│   ├── services/
│   │   ├── imagen.py            # Imagen 3 batch image generation
│   │   ├── storage.py           # GCS upload / signed URL generation
│   │   └── session.py           # Firestore read/write for session state
│   └── characters/
│       ├── zara.py              # Zara persona prompt + voice config
│       └── finn.py              # Finn persona prompt + voice config
├── frontend/
│   ├── index.html               # Parent setup screen
│   ├── pick.html                # Kid character selection screen
│   ├── lesson.html              # Main kid lesson screen
│   ├── js/
│   │   ├── characters.js        # SVG character rendering + lip sync + emotions
│   │   ├── audio.js             # Mic capture, PCM streaming, audio playback
│   │   └── session.js           # WebSocket client + image command dispatcher
│   └── css/
│       └── main.css
├── cors.json
├── Dockerfile
├── cloudbuild.yaml
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

## Two-Phase Architecture — Critical to Understand

### Phase 1: Setup (before kid arrives, ~10–15 seconds)
1. Parent submits topic + grade level on `index.html`
2. Backend calls `lesson_planner.py` — Gemini generates a structured JSON lesson plan with image prompts
3. Backend calls `imagen.py` — generates 4–5 images in parallel via Imagen 3
4. Images uploaded to GCS, signed URLs stored in Firestore under session ID
5. Frontend redirects to `pick.html` with session ID in URL

### Phase 2: Live lesson (real-time with kid)
1. Kid picks character on `pick.html`, redirected to `lesson.html`
2. Frontend opens WebSocket to `/ws/{session_id}`
3. Backend starts Gemini Live API session with character persona injected
4. Audio streams bidirectionally: kid mic → backend → Gemini → backend → kid speakers
5. Agent emits JSON commands over WebSocket alongside audio to control the image board
6. Kid can barge in at any time — Live API handles VAD natively

---

## Image Command Protocol (WebSocket JSON messages, server → client)

```json
{ "cmd": "show",      "id": "img_1",  "transition": "slide_in" }
{ "cmd": "highlight", "id": "img_1",  "region": "bottom",  "overlay_text": "← denominator!" }
{ "cmd": "reuse",     "id": "img_1",  "overlay_text": "Count ALL slices" }
{ "cmd": "swap",      "from": "img_1","to": "img_3",        "transition": "slide" }
{ "cmd": "dismiss" }
{ "cmd": "emotion",   "character": "zara", "state": "happy" }
{ "cmd": "emotion",   "character": "finn", "state": "thinking" }
```

Emotion states: `neutral` | `happy` | `thinking` | `surprised` | `question`

---

## Image Manifest Schema (stored in Firestore)

```json
{
  "session_id": "abc123",
  "topic": "fractions",
  "grade": "grade3-5",
  "character": "zara",
  "images": [
    {
      "id": "img_1",
      "teaching_moment": "what a fraction is",
      "gcs_url": "https://storage.googleapis.com/kidtutor-images-v2/abc123/img_1.png",
      "teaching_notes": "Use to show numerator/denominator",
      "can_reuse_for": ["what does the bottom number mean", "equal parts"]
    }
  ],
  "lesson_outline": ["assess", "concept_intro", "analogy", "check", "deeper", "celebrate"],
  "created_at": "2026-03-16T10:00:00Z"
}
```

---

## Character Definitions

### Zara the Robot
- **Visual**: SVG robot, purple color scheme (#4A4E8C body, #7F77DD accents)
- **Voice**: `Gemini voice: "Aoede"` (bright, clear)
- **Persona prompt**:
```
You are Zara, a friendly and enthusiastic robot teacher for kids.
You speak in short, energetic sentences. You use tech and space metaphors.
You say things like "Beep boop! Great question!" and "Let's compute this together!"
You never use words longer than a 3rd grader would know unless you immediately explain them.
You always celebrate when a kid gets something right.
Grade level: {grade}. Topic: {topic}.
Current image on screen: {current_image_teaching_notes}.
Available images: {image_manifest}.
When you want to show or change an image, emit a JSON command on a SEPARATE LINE starting with CMD:
CMD: {"cmd": "show", "id": "img_1"}
CMD: {"cmd": "emotion", "character": "zara", "state": "happy"}
```

### Finn the Fox
- **Visual**: SVG fox, orange/coral color scheme (#D85A30 body, #F5C4B3 belly)
- **Voice**: `Gemini voice: "Charon"` (warm, storytelling)
- **Persona prompt**:
```
You are Finn, a clever and warm fox who loves telling stories to teach kids.
You use nature, forest, and animal metaphors to explain everything.
You say things like "Imagine you're in the forest..." and "Great thinking, little cub!"
You speak warmly and slowly, never rushing.
You always turn abstract concepts into little stories.
Grade level: {grade}. Topic: {topic}.
Current image on screen: {current_image_teaching_notes}.
Available images: {image_manifest}.
When you want to show or change an image, emit a JSON command on a SEPARATE LINE starting with CMD:
CMD: {"cmd": "show", "id": "img_1"}
CMD: {"cmd": "emotion", "character": "finn", "state": "happy"}
```

---

## Image Generation Prompts Strategy

When the Lesson Planner generates image prompts for Imagen 3, always append:
`"child-friendly illustration, bright colors, simple clear shapes, white background, educational, cartoon style, no text in image"`

Generate exactly 4 images per session:
1. **Core concept** — the main idea visualized
2. **Real-world example** — something the kid encounters daily
3. **Step by step** — a process or comparison shown visually
4. **Fun/memorable** — the most engaging/surprising version of the concept

---

## SVG Character Mouth States (lip sync driven by audio amplitude)

```
Volume 0–20%   → mouth: closed (flat line)
Volume 20–45%  → mouth: sm (small open ellipse)
Volume 45–70%  → mouth: md (medium ellipse)
Volume 70–100% → mouth: lg (wide open, show tongue for Finn)
Idle + happy   → mouth: smile
```

Web Audio API reads amplitude from the decoded PCM audio output stream at 30fps.
Call `setVolume(amplitude)` on each animation frame.
Call `applyEmotion(state)` when a CMD emotion message arrives over WebSocket.

---

## Lesson Planner Agent Prompt (send to Gemini, expect JSON back)

```
You are a lesson planning agent for a children's educational app.

A parent has requested a lesson on: "{topic}"
Grade level: "{grade}" (K-2 = ages 5-7, grade3-5 = ages 8-10, grade6-8 = ages 11-13)

Your job: Generate a structured lesson plan as JSON. Be creative with image prompts.
Make the lesson feel like an adventure, not a textbook.

Return ONLY valid JSON, no other text:

{
  "lesson_outline": ["assess", "intro", "analogy", "check_1", "deeper", "check_2", "celebrate"],
  "images": [
    {
      "id": "img_1",
      "teaching_moment": "short description of when to use this image",
      "imagen_prompt": "detailed prompt for Imagen 3, child-friendly illustration style",
      "teaching_notes": "what the character should say when showing this",
      "can_reuse_for": ["list of kid questions this image can answer"]
    }
  ],
  "opening_line": "The first thing Zara/Finn says to the kid to start the lesson",
  "key_concepts": ["concept1", "concept2", "concept3"]
}
```

---

## FastAPI Endpoints

```
POST /setup                     → receives topic+grade+character, runs Phase 1, returns session_id
GET  /session/{session_id}      → returns session metadata (for pick.html)
WS   /ws/{session_id}           → bidirectional: audio PCM + JSON commands
GET  /health                    → returns {"status": "ok"}
```

---

## Audio Protocol (WebSocket binary + text frames)

- **Client → Server binary frames**: raw PCM audio, 16kHz, 16-bit, mono (from MediaRecorder / AudioWorklet)
- **Server → Client binary frames**: raw PCM audio from Gemini (play through AudioContext)
- **Server → Client text frames**: JSON image/emotion commands (parsed by session.js)
- **Client → Server text frames**: `{"type": "barge_in"}` when kid taps mic during playback

---

## Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY frontend/ ./frontend/
EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Run deploy command
```bash
gcloud run deploy kidtutor-v2 \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY,GCS_BUCKET=kidtutor-images-v2,GOOGLE_CLOUD_PROJECT=kidtutor-v2 \
  --memory 1Gi \
  --project kidtutor-v2
```

---

## Grade Level Mapping

| UI Label | Internal Value | Age Range | Language complexity |
|---|---|---|---|
| Kindergarten – Grade 2 | k-2 | 5–7 yrs | Very simple, max 2-syllable words, lots of "imagine" |
| Grade 3 – Grade 5 | grade3-5 | 8–10 yrs | Conversational, real-world examples, some vocabulary |
| Grade 6 – Grade 8 | grade6-8 | 11–13 yrs | More precise language, can introduce proper terms |

---

## Parent UI — Topic Input

Two modes, both on `index.html`:

**Category tiles** (click to pre-fill):
- Math: Fractions | Multiplication | Geometry | Percentages
- Science: Planets | Volcanoes | Human Body | Food Chains
- History: Ancient Egypt | World War II | Space Race | The Constitution
- Nature: Weather | Rainforests | Ocean Life | Ecosystems

**Free text override**: A text input below the tiles. If the parent types something, it overrides the selected category. Any topic is valid — Gemini handles anything.

---

## Key Rules for Cursor

1. **Never use React, Vue, or any JS framework** — vanilla JS only
2. **Never hardcode API keys** — always read from environment variables
3. **Never block the event loop** — all Gemini calls must be async/await
4. **Always stream audio** — never buffer entire response before playing
5. **Character SVGs live in characters.js** — not inline in HTML
6. **Image commands are parsed in session.js** — not in audio.js
7. **Lesson planner runs once at setup** — never during the live lesson
8. **All GCS URLs must be signed URLs** — never expose bucket directly
9. **Firestore session expires after 2 hours** — set TTL on all documents
10. **The frontend serves from `/frontend`** — FastAPI mounts it as StaticFiles

---

## What a Great Demo Video Shows (build toward this)

1. Parent opens app, types "fractions" + selects Grade 3-5, hits Start
2. Loading screen shows "Zara is getting ready..." while images generate
3. Kid picks Zara on the character screen
4. Zara appears, animated, starts speaking — first image slides in
5. Kid (you) interrupts mid-sentence: "Wait, what's the bottom number called?"
6. Zara stops, the same image gets a highlight overlay, Zara answers
7. Kid asks "Can you show me a different example?"
8. Image swaps to the chocolate bar image, Zara pivots the explanation
9. Zara asks the kid a question, kid answers correctly
10. Zara does a happy animation, celebrates
11. Show the GCP console in the background (proof of deployment)

---
*Generated for KidTutor Live hackathon submission — Gemini Live Agent Challenge 2026*
