from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
import json


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class MemoryStore:
    path: Path
    data: dict = field(default_factory=dict)

    def load(self) -> None:
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            self.data = {
                "created_at": utc_now(),
                "recent_topics": [],
                "reflections": [],
                "preferences": [],
                "conversation_count": 0,
            }
            self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))

    def add_topic(self, topic: str) -> None:
        topic = topic.strip()
        if not topic:
            return
        topics = [topic] + [t for t in self.data["recent_topics"] if t != topic]
        self.data["recent_topics"] = topics[:20]
        self.save()

    def add_reflection(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        reflections = [{"at": utc_now(), "text": text}] + self.data["reflections"]
        self.data["reflections"] = reflections[:20]
        self.save()

    def add_preference(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        prefs = [text] + [p for p in self.data["preferences"] if p != text]
        self.data["preferences"] = prefs[:20]
        self.save()

    def increment_conversations(self) -> None:
        self.data["conversation_count"] = int(self.data.get("conversation_count", 0)) + 1
        self.save()
