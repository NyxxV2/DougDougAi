from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess


@dataclass(slots=True)
class LLMResult:
    text: str
    ok: bool
    error: str = ""


class LocalLLM:
    def __init__(self, llama_cli_path: Path, model_path: Path) -> None:
        self.llama_cli_path = llama_cli_path
        self.model_path = model_path

    def ready(self) -> tuple[bool, str]:
        if not self.llama_cli_path.exists():
            return False, f"Missing llama.cpp binary at {self.llama_cli_path}"
        if not self.model_path.exists():
            return False, f"Missing local model at {self.model_path}"
        return True, "ready"

    def generate(self, prompt: str, max_tokens: int = 300, temperature: float = 0.85) -> LLMResult:
        ok, reason = self.ready()
        if not ok:
            return LLMResult(text="", ok=False, error=reason)
        cmd = [
            str(self.llama_cli_path),
            "-m", str(self.model_path),
            "-ngl", "999",
            "-c", "8192",
            "-n", str(max_tokens),
            "--temp", str(temperature),
            "--top-p", "0.92",
            "--repeat-penalty", "1.08",
            "-p", prompt,
            "--no-display-prompt",
        ]
        try:
            env = os.environ.copy()
            lib_dir = str(self.llama_cli_path.parent)
            env["DYLD_LIBRARY_PATH"] = lib_dir + (":" + env["DYLD_LIBRARY_PATH"] if env.get("DYLD_LIBRARY_PATH") else "")
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=self.llama_cli_path.parent,
                env=env,
            )
        except Exception as exc:
            return LLMResult(text="", ok=False, error=str(exc))

        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            return LLMResult(text="", ok=False, error=stderr[:1000])

        text = completed.stdout.strip()
        return LLMResult(text=text, ok=True)
