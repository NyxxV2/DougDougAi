from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import threading
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import APP_NAME, PROJECT_ROOT, RESOURCE_MANIFEST, RuntimePaths, ensure_dirs
from .knowledge import KnowledgeBase
from .llm import LocalLLM
from .memory import MemoryStore
from .persona import format_persona, load_persona
from .prompts import build_prompt, build_reflection_prompt


class DougDougWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ensure_dirs()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 860)

        self.paths = RuntimePaths()
        self.memory = MemoryStore(self.paths.memory_file)
        self.memory.load()
        self.knowledge = KnowledgeBase(self.paths.knowledge_file, self.paths.index_file)
        self.knowledge.load()
        self.persona = load_persona(self.paths.persona_file)
        self.persona_text = format_persona(self.persona)
        self.llm = LocalLLM(self.paths.llama_cli_path, self.paths.model_path)
        self.messages: list[tuple[str, str]] = []
        self.current_sources: list[dict[str, str]] = []

        self.status_label = QLabel()
        self.chat_box = QTextEdit()
        self.entry = QTextEdit()
        self.sidebar = QTextEdit()

        self._build_ui()
        self._refresh_status()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        header = QLabel("DougDoug AI Local")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #ffce54;")
        subtitle = QLabel("Offline local chaos, compact DougDoug brain, zero external AI APIs.")
        subtitle.setStyleSheet("font-size: 13px; color: #dccb9b;")
        outer.addWidget(header)
        outer.addWidget(subtitle)

        controls = QHBoxLayout()
        for label, handler in (
            ("Collect Sources", self.collect_sources),
            ("Build Brain", self.build_knowledge),
            ("Download Model", self.download_model),
            ("Pick Model", self.pick_model),
            ("Send", self.send_message),
        ):
            button = QPushButton(label)
            button.clicked.connect(handler)
            button.setStyleSheet(
                "QPushButton { background: #2e2c22; color: #f6eccd; border-radius: 8px; padding: 10px 14px; }"
                "QPushButton:hover { background: #3b382c; }"
            )
            controls.addWidget(button)
        outer.addLayout(controls)

        body = QHBoxLayout()
        body.setSpacing(12)

        left = QVBoxLayout()
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet(
            "QTextEdit { background: #1b1b17; color: #f7f2de; border: 1px solid #302d21; border-radius: 10px; "
            "font-family: Menlo; font-size: 14px; padding: 10px; }"
        )
        self.chat_box.setPlainText("System: Welcome to DougDoug AI Local.\n")

        self.entry.setStyleSheet(
            "QTextEdit { background: #23231d; color: #fff8df; border: 1px solid #302d21; border-radius: 10px; "
            "font-family: Menlo; font-size: 14px; padding: 8px; }"
        )
        self.entry.setPlaceholderText("Ask for chaos, lore, opinions, or challenge ideas...")
        self.entry.setFixedHeight(130)
        left.addWidget(self.chat_box, 1)
        left.addWidget(self.entry)

        right = QVBoxLayout()
        sidebar_label = QLabel("Brain State")
        sidebar_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #ffce54;")
        self.sidebar.setReadOnly(True)
        self.sidebar.setStyleSheet(
            "QTextEdit { background: #161611; color: #ecdcae; border: 1px solid #302d21; border-radius: 10px; "
            "font-family: Menlo; font-size: 12px; padding: 10px; }"
        )
        right.addWidget(sidebar_label)
        right.addWidget(self.sidebar, 1)

        body.addLayout(left, 3)
        body.addLayout(right, 2)
        outer.addLayout(body, 1)

        self.status_label.setStyleSheet("font-size: 12px; color: #d7ca9e;")
        outer.addWidget(self.status_label)

        act = QAction(self)
        act.setShortcut("Meta+Return")
        act.triggered.connect(self.send_message)
        self.addAction(act)

        self.setStyleSheet("QMainWindow { background: #12120f; }")

    def _sidebar_text(self) -> str:
        ok, reason = self.llm.ready()
        source_text = "\n".join(f"- {item['title']}\n  {item['url']}" for item in self.current_sources) or "- No sources used yet."
        topics = self.memory.data.get("recent_topics", [])[:8] or ["None"]
        reflections = [r["text"] for r in self.memory.data.get("reflections", [])[:6]] or ["None"]
        return (
            f"Model path:\n{self.paths.model_path}\n\n"
            f"llama.cpp:\n{self.paths.llama_cli_path}\n\n"
            f"LLM ready: {ok}\n{reason}\n\n"
            f"Knowledge chunks: {len(self.knowledge.chunks)}\n"
            f"Conversation count: {self.memory.data.get('conversation_count', 0)}\n\n"
            f"Recent topics:\n- " + "\n- ".join(topics) + "\n\n"
            f"Reflections:\n- " + "\n- ".join(reflections) + "\n\n"
            f"Current sources:\n{source_text}"
        )

    def _refresh_sidebar(self) -> None:
        self.sidebar.setPlainText(self._sidebar_text())

    def _refresh_status(self) -> None:
        ok, reason = self.llm.ready()
        self.status_label.setText(
            "Local model ready. Prepared for deeply unnecessary chaos."
            if ok else reason
        )
        self._refresh_sidebar()

    def _append_chat(self, speaker: str, text: str) -> None:
        self.chat_box.moveCursor(QTextCursor.End)
        self.chat_box.insertPlainText(f"\n{speaker}: {text.strip()}\n")
        self.chat_box.moveCursor(QTextCursor.End)

    def _show_message(self, title: str, text: str, critical: bool = False) -> None:
        if critical:
            QMessageBox.critical(self, title, text[:5000] or "Unknown error")
        else:
            QMessageBox.information(self, title, text[:5000] or "Done.")

    def pick_model(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            self,
            "Select GGUF Model",
            str(self.paths.model_path.parent),
            "GGUF models (*.gguf);;All files (*)",
        )
        if chosen:
            self.paths.model_path = Path(chosen)
            self.llm = LocalLLM(self.paths.llama_cli_path, self.paths.model_path)
            self._refresh_status()

    def collect_sources(self) -> None:
        self._run_background("Collecting DougDoug web sources...", [sys.executable, "scripts/collect_sources.py"])

    def build_knowledge(self) -> None:
        self._run_background(
            "Building compact DougDoug brain...",
            [sys.executable, "scripts/build_knowledge.py"],
            reload_brain=True,
        )

    def download_model(self) -> None:
        self._run_background(
            "Downloading compact local model...",
            [sys.executable, "scripts/download_model.py"],
            refresh_only=True,
        )

    def _run_background(
        self,
        status_text: str,
        cmd: list[str],
        reload_brain: bool = False,
        refresh_only: bool = False,
    ) -> None:
        self.status_label.setText(status_text)

        def task() -> None:
            completed = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
                env={
                    **os.environ,
                    "DOUGDOUG_AI_DATA_DIR": str(self.paths.knowledge_file.parent.parent),
                    "DOUGDOUG_AI_MODELS_DIR": str(self.paths.model_path.parent),
                },
            )
            output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
            if completed.returncode != 0:
                QTimer.singleShot(0, lambda: self._show_message("Command failed", output, critical=True))
            else:
                if reload_brain:
                    self.knowledge.load()
                    self.persona = load_persona(self.paths.persona_file)
                    self.persona_text = format_persona(self.persona)
                if refresh_only or reload_brain:
                    self.llm = LocalLLM(self.paths.llama_cli_path, self.paths.model_path)
                QTimer.singleShot(0, lambda: self._show_message("Finished", output))
            QTimer.singleShot(0, self._refresh_status)

        threading.Thread(target=task, daemon=True).start()

    def send_message(self) -> None:
        user_message = self.entry.toPlainText().strip()
        if not user_message:
            return
        self.entry.clear()
        self._append_chat("You", user_message)
        self.messages.append(("User", user_message))
        self.memory.add_topic(user_message[:120])
        self.status_label.setText("Thinking locally...")

        def task() -> None:
            chunks = self.knowledge.search(user_message, limit=6)
            self.current_sources = [{"title": chunk.title, "url": chunk.url} for chunk in chunks]
            source_context = "\n\n".join(
                f"[{chunk.title}] {chunk.text}\nSource: {chunk.url}" for chunk in chunks
            )
            prompt = build_prompt(
                user_message=user_message,
                persona_text=self.persona_text,
                source_context=source_context,
                recent_messages=self.messages,
                reflections=[r["text"] for r in self.memory.data.get("reflections", [])],
                preferences=self.memory.data.get("preferences", []),
            )
            result = self.llm.generate(prompt, max_tokens=320, temperature=0.9)
            if not result.ok:
                reply = (
                    "My local brain is not fully wired yet.\n\n"
                    f"Problem: {result.error}\n\n"
                    "Use the controls above to collect sources, build the brain, and download a local GGUF model."
                )
            else:
                reply = result.text.strip()
                self.memory.increment_conversations()
            self.messages.append(("Assistant", reply))

            def finish_reply() -> None:
                self._append_chat("DougDoug AI", reply)
                self._refresh_sidebar()
                self.status_label.setText("Ready for more nonsense.")

            QTimer.singleShot(0, finish_reply)

            if result.ok:
                reflection_result = self.llm.generate(
                    build_reflection_prompt(user_message, reply),
                    max_tokens=60,
                    temperature=0.7,
                )
                if reflection_result.ok:
                    reflection = reflection_result.text.strip().splitlines()[0][:240]
                    self.memory.add_reflection(reflection)
                    if any(word in reflection.lower() for word in ("prefer", "like", "love", "hate", "think")):
                        self.memory.add_preference(reflection)
                QTimer.singleShot(0, self._refresh_sidebar)

        threading.Thread(target=task, daemon=True).start()


def main() -> None:
    ensure_dirs()
    if not RESOURCE_MANIFEST.exists():
        RESOURCE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        RESOURCE_MANIFEST.write_text(json.dumps({"sources": []}, indent=2))
    app = QApplication.instance() or QApplication([])
    window = DougDougWindow()
    window.show()
    app.exec()
