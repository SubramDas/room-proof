"""Optional disclosed Gemini vision probe; never used as metric geometry."""

import base64
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

MODEL = "gemini-2.5-flash-lite"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
PROMPT = (
    "Inspect this indoor photo. Return only JSON with keys visible_opening_types "
    "(array drawn from door, window, other), visible_damage_classes (array drawn "
    "from discoloration_or_water_stain, crack, coating_failure, surface_breakage, "
    "floor_finish_damage), and notes (short string). Report only directly visible "
    "evidence. Do not infer hidden damage, metric dimensions, or room adjacency."
)


def probe(image_path):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is required for the optional cloud probe")
    path = Path(image_path).resolve(strict=True)
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(path.suffix.lower())
    if not mime:
        raise ValueError("cloud probe accepts JPEG or PNG")
    raw = path.read_bytes()
    if len(raw) > 8_000_000:
        raise ValueError("image exceeds bounded 8 MB pilot limit")
    body = {"contents": [{"parts": [{"text": PROMPT},
                                    {"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode()}}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    request = Request(ENDPOINT, data=json.dumps(body).encode(),
                      headers={"x-goog-api-key": key, "Content-Type": "application/json"}, method="POST")
    started = time.monotonic()
    with urlopen(request, timeout=45) as response:
        payload = json.load(response)
    elapsed = time.monotonic()-started
    candidates = payload.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidate")
    parts = candidates[0].get("content", {}).get("parts", [])
    parsed = json.loads("".join(part.get("text", "") for part in parts))
    if not isinstance(parsed, dict) or not isinstance(parsed.get("notes"), str):
        raise ValueError("Gemini returned an unexpected response shape")
    allowed_openings = {"door", "window", "other"}
    allowed_damage = {"discoloration_or_water_stain", "crack", "coating_failure", "surface_breakage", "floor_finish_damage"}
    openings, damages = parsed.get("visible_opening_types"), parsed.get("visible_damage_classes")
    if not isinstance(openings, list) or not isinstance(damages, list) or any(x not in allowed_openings for x in openings) or any(x not in allowed_damage for x in damages):
        raise ValueError("Gemini returned labels outside the pilot vocabulary")
    return {"model": MODEL, "endpoint": ENDPOINT, "prompt": PROMPT,
            "image_path": str(path), "image_bytes": len(raw), "latency_seconds": round(elapsed, 3),
            "usage_metadata": payload.get("usageMetadata"), "response": parsed,
            "third_party_data_transfer": "original image sent to Google Gemini API"}
