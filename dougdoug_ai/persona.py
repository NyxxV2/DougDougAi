from __future__ import annotations

from pathlib import Path
import json


def load_persona(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {
        "voice": [
            "Energetic, playful, and slightly chaotic.",
            "Treats streaming stories, challenges, and chat shenanigans as core context.",
            "Likes bits, absurd escalation, and dry self-aware humor.",
            "Should not claim to literally be DougDoug.",
        ],
        "facts": [],
        "memes": [],
        "opinions": [],
    }


def format_persona(persona: dict) -> str:
    parts: list[str] = []
    for key in ("voice", "facts", "memes", "opinions"):
        values = persona.get(key, [])
        if values:
            parts.append(f"{key.upper()}:\n- " + "\n- ".join(values[:12]))
    return "\n\n".join(parts)
