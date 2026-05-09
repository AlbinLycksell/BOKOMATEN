# scripts/

Exploration utilities. Isolated uv environment so the heavy audio/video deps
(pyaudio, opencv, mss) stay out of the production `backend/` env.

## Setup

```bash
brew install portaudio   # one-time, macOS only — required by pyaudio
cd scripts
uv sync
```

## Run

`gem_live.py` opens a real-time voice chat with Gemini Live, with optional vision
input from webcam or screen capture. See the docstring at the top of the script
for the full contract.

```bash
# webcam (default)
uv run gem_live.py

# screen capture
uv run gem_live.py --mode screen

# audio only
uv run gem_live.py --mode none
```

The script auto-loads `.env` then `.env.local` from the repo root, so set
`GEMINI_API_KEY` there. `Ctrl+C` exits cleanly.
