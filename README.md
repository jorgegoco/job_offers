# Job Application Generator

Generates tailored CVs and cover letters from job postings. Paste a job URL or text, review the AI-generated drafts, refine as needed, and download styled PDFs — all from a local web interface.

## Quick Start

**Windows desktop shortcut** (recommended):
1. Run `scripts/create-shortcut.bat` once to create the shortcut
2. Double-click **"Job App Generator"** on your desktop
3. Use `scripts/stop-webapp.bat` to stop the server

**Manual start**:
```bash
pip install -r requirements.txt
uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```
Then open http://localhost:8000

## Project Structure

```
webapp/              Web UI and API endpoints (FastAPI)
execution/           Python scripts that do the actual work
resources/profile.json       Your CV data (single source of truth)
resources/github_repos.json  Curated GitHub project list
output/job_applications/     Saved PDFs (explicitly saved by user)
.tmp/                Intermediate files (safe to delete)
.env                 API keys and model config
scripts/             Windows launcher scripts
```

## Updating Your CV Data

Edit `resources/profile.json` directly. Changes take effect on the next generation. The app also updates this file automatically when you mention new skills during a session.

## Environment Variables

Create a `.env` file with:
```
ANTHROPIC_API_KEY=your-key-here
GITHUB_TOKEN=your-github-pat          # optional, for repo enrichment
MODEL_EXTRACTION=claude-haiku-4-5-20251001
MODEL_GENERATION=claude-sonnet-4-5-20250929
```

## Development

```bash
make dev       # Auto-reload dev server
make run       # Production mode
make clean     # Remove temp files
```

## License

Private project for personal use.
