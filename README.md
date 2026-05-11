# DougDoug AI Local

`DougDoug AI Local` is a fully local desktop chatbot project that builds a DougDoug-inspired assistant from internet-accessible DougDoug resources without calling any external AI API.

What this project does:

- Builds a local desktop GUI chat app.
- Uses a local open-weight language model through `llama.cpp`.
- Collects DougDoug-related source material from curated web pages and optional YouTube subtitles.
- Distills those sources into a compact local knowledge base to keep disk usage under control.
- Stores its own memory, reflections, and evolving preferences locally.
- Packages into a macOS `.app`, with a Windows `.exe` build path included.

Important honesty note:

- The app itself is built from scratch here.
- The DougDoug-specific knowledge/persona layer is built from scratch here.
- The runtime language model is intentionally a local open-weight base model, because training a capable general-purpose model from absolute zero on consumer hardware is not realistic.
- No cloud model provider or external AI API is used.

## Recommended stack

- Python 3.14+
- `llama.cpp` local binary
- A small GGUF model such as `Qwen2.5-1.5B-Instruct-GGUF`

## Quick start

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Build `llama.cpp` locally:

```bash
./scripts/setup_llama_cpp.sh
```

3. Download the local model:

```bash
python scripts/download_model.py
```

4. Collect compact DougDoug source material:

```bash
python scripts/collect_sources.py
python scripts/build_knowledge.py
```

5. Launch the app:

```bash
python -m dougdoug_ai
```

## Packaging

Build macOS `.app`:

```bash
./scripts/build_mac_app.sh
```

Windows `.exe` build instructions are in:

`scripts/build_windows_exe.ps1`

## Storage strategy

To reduce disk usage, this project:

- Downloads text and subtitles only, not full videos.
- Normalizes and deduplicates source text.
- Chunks text compactly into JSONL.
- Builds a small inverted index instead of a vector database.
- Keeps the model separate from the packaged app by default so you can swap smaller/larger models.

## Suggested source set

The default manifest includes:

- Official DougDoug website
- Wikipedia page
- DougDoug Wikitubia page
- Doug-hole wiki pages
- Optional subtitle scraping from official/fan YouTube channels if subtitles are available

## Current limits

- This is a local persona system, not a guaranteed perfect clone.
- Accuracy depends heavily on the subtitles and text actually available online.
- A true "trained from zero only on DougDoug material" foundation model is outside the scope of normal desktop hardware.
