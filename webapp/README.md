# Job Offers Web API

FastAPI wrapper around the job application pipeline scripts.

## Setup

Install the webapp dependencies (on top of the project root deps):

```bash
pip install -r webapp/requirements.txt
```

## Run

From the **project root**:

```bash
uvicorn webapp.main:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs for the interactive Swagger UI.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/analyze-job` | Analyze a job offer from URL or text |
| POST | `/api/load-cv` | Load the master CV database |
| POST | `/api/generate-cv` | Generate a tailored CV |
| POST | `/api/generate-cover-letter` | Generate a cover letter |
| POST | `/api/generate-pdfs` | Convert markdown to styled PDFs |
| GET | `/api/download/{filename}` | Download a generated PDF |
| POST | `/api/generate-all` | Full pipeline in one call |

## Typical flow

1. `POST /api/analyze-job` with `{"url": "..."}` or `{"text": "..."}`
2. `POST /api/load-cv`
3. `POST /api/generate-cv` with `{"comments": "emphasize Python and AI experience"}`
4. `POST /api/generate-cover-letter` with `{"comments": "mention freelance work"}`
5. `POST /api/generate-pdfs`
6. `GET /api/download/CV_Company_Title_20260209.pdf`

Or use `/api/generate-all` to run steps 1-5 in a single request.

## Windows Desktop Launcher

One-click launch from your Windows desktop:

1. Run `scripts/create-shortcut.bat` once to create a desktop shortcut
2. Double-click **"Job App Generator"** on your desktop to start the server and open the browser
3. Run `scripts/stop-webapp.bat` to stop the server

## Development Commands

```bash
make dev       # Auto-reload development server (watches webapp/ and execution/)
make run       # Production mode (no reload)
make install   # Install all dependencies
make clean     # Remove temp files and __pycache__
```

**VS Code shortcuts:**
- `Ctrl+Shift+B` — Start dev server (runs `make dev`)
- `F5` — Debug with breakpoints (debugpy + uvicorn)
