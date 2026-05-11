from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import json
import math
import re


TOKEN_RE = re.compile(r"[A-Za-z0-9_']+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "had", "has", "have",
    "he", "her", "his", "i", "if", "in", "into", "is", "it", "its", "me", "my", "of", "on", "or",
    "our", "she", "that", "the", "their", "them", "they", "this", "to", "was", "we", "with", "you",
    "your",
}


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOPWORDS]


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    source_id: str
    title: str
    url: str
    text: str


class KnowledgeBase:
    def __init__(self, chunks_path: Path, index_path: Path) -> None:
        self.chunks_path = chunks_path
        self.index_path = index_path
        self.chunks: list[Chunk] = []
        self.index: dict[str, dict[str, float]] = {}
        self.document_freq: dict[str, int] = {}
        self._chunk_lookup: dict[str, Chunk] = {}

    def load(self) -> None:
        self.chunks = []
        if self.chunks_path.exists():
            for line in self.chunks_path.read_text().splitlines():
                if not line.strip():
                    continue
                raw = json.loads(line)
                chunk = Chunk(**raw)
                self.chunks.append(chunk)
                self._chunk_lookup[chunk.chunk_id] = chunk
        if self.index_path.exists():
            data = json.loads(self.index_path.read_text())
            self.index = data["index"]
            self.document_freq = data["document_freq"]

    def search(self, query: str, limit: int = 6) -> list[Chunk]:
        if not self.chunks or not self.index:
            return []
        scores: dict[str, float] = defaultdict(float)
        query_tokens = tokenize(query)
        doc_count = max(1, len(self.chunks))
        for token in query_tokens:
            postings = self.index.get(token, {})
            df = max(1, self.document_freq.get(token, 1))
            idf = math.log((doc_count + 1) / df) + 1.0
            for chunk_id, tf in postings.items():
                scores[chunk_id] += tf * idf
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
        return [self._chunk_lookup[chunk_id] for chunk_id, _ in ranked]

    @staticmethod
    def build_index(chunks: list[Chunk]) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
        postings: dict[str, dict[str, float]] = defaultdict(dict)
        doc_freq: Counter[str] = Counter()
        for chunk in chunks:
            tokens = tokenize(chunk.text)
            tokens.extend(tokenize(chunk.title))
            tokens.extend(tokenize(chunk.title))
            if not tokens:
                continue
            counts = Counter(tokens)
            max_count = max(counts.values())
            for token, count in counts.items():
                postings[token][chunk.chunk_id] = count / max_count
            doc_freq.update(counts.keys())
        return dict(postings), dict(doc_freq)
