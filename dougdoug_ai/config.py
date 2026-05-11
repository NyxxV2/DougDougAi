from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import sys


APP_NAME = "DougDoug AI Local"
APP_DIR_NAME = "DougDoug AI Local"


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


RESOURCE_ROOT = _bundle_root()
PROJECT_ROOT = RESOURCE_ROOT
USER_APP_DIR = Path.home() / "Library" / "Application Support" / APP_DIR_NAME
DATA_DIR = Path(
    os.environ.get(
        "DOUGDOUG_AI_DATA_DIR",
        USER_APP_DIR / "data" if getattr(sys, "frozen", False) else PROJECT_ROOT / "data",
    )
)
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MEMORY_DIR = DATA_DIR / "memory"
MODELS_DIR = Path(
    os.environ.get(
        "DOUGDOUG_AI_MODELS_DIR",
        USER_APP_DIR / "models" if getattr(sys, "frozen", False) else PROJECT_ROOT / "models",
    )
)
BIN_DIR = RESOURCE_ROOT / "bin"
ASSETS_DIR = RESOURCE_ROOT / "assets"

DEFAULT_MODEL = MODELS_DIR / "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"
DEFAULT_LLAMA_CLI = BIN_DIR / "llama.cpp" / "build" / "bin" / "llama-cli"
RESOURCE_MANIFEST = DATA_DIR / "resource_manifest.json"
KNOWLEDGE_FILE = PROCESSED_DIR / "knowledge_chunks.jsonl"
INDEX_FILE = PROCESSED_DIR / "token_index.json"
PERSONA_FILE = PROCESSED_DIR / "persona_profile.json"
MEMORY_FILE = MEMORY_DIR / "memory.json"


@dataclass(slots=True)
class RuntimePaths:
    model_path: Path = DEFAULT_MODEL
    llama_cli_path: Path = DEFAULT_LLAMA_CLI
    knowledge_file: Path = KNOWLEDGE_FILE
    index_file: Path = INDEX_FILE
    persona_file: Path = PERSONA_FILE
    memory_file: Path = MEMORY_FILE


def ensure_dirs() -> None:
    for path in (DATA_DIR, RAW_DIR, PROCESSED_DIR, MEMORY_DIR, MODELS_DIR, BIN_DIR, ASSETS_DIR):
        path.mkdir(parents=True, exist_ok=True)
    _seed_runtime_data()


def _seed_runtime_data() -> None:
    source_data = RESOURCE_ROOT / "data"
    if not source_data.exists():
        return
    for relative in (
        Path("resource_manifest.json"),
        Path("processed/knowledge_chunks.jsonl"),
        Path("processed/token_index.json"),
        Path("processed/persona_profile.json"),
        Path("processed/stats.json"),
    ):
        src = source_data / relative
        dst = DATA_DIR / relative
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
