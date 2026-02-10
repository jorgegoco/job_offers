"""
FastAPI web app wrapping the job_offers execution scripts.
Run with: uvicorn webapp.main:app --host 0.0.0.0 --port 8000
"""

import json
import shutil
import sys
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# --- Path setup: add project root so we can import from execution/ ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# --- Import core functions from execution scripts ---
from execution.analyze_job_offer import scrape_job_url, analyze_with_llm
from execution.analyze_master_cv import get_user_data
from execution.generate_tailored_cv import generate_tailored_cv
from execution.generate_cover_letter import generate_cover_letter
from execution.fetch_github_repos import load_curated_repos, select_relevant_repos
from execution.apply_template import (
    analyze_template_style,
    markdown_to_pdf,
    generate_filename,
    load_markdown,
    load_json,
)

# --- Shared paths ---
TMP_DIR = PROJECT_ROOT / ".tmp" / "job_applications"
OUTPUT_DIR = PROJECT_ROOT / "output" / "job_applications"
TEMPLATE_PATH = PROJECT_ROOT / "resources" / "job_applications" / "cv_template.pdf"

JOB_ANALYSIS_PATH = TMP_DIR / "job_analysis.json"
CV_DATABASE_PATH = TMP_DIR / "cv_database.json"
TAILORED_CV_PATH = TMP_DIR / "tailored_cv.md"
CV_GAPS_PATH = TMP_DIR / "cv_gaps.txt"
COVER_LETTER_PATH = TMP_DIR / "cover_letter.md"
GITHUB_SELECTED_PATH = TMP_DIR / "github_repos_selected.json"

# --- Pydantic models ---

class AnalyzeJobRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None

class GenerateCVRequest(BaseModel):
    comments: str
    iteration: Optional[int] = 1
    refinement_feedback: Optional[str] = ""

class GenerateCoverLetterRequest(BaseModel):
    comments: str
    max_words: Optional[int] = None
    max_chars: Optional[int] = None
    iteration: Optional[int] = 1
    refinement_feedback: Optional[str] = ""

class GeneratePDFsRequest(BaseModel):
    skip_cover_letter: Optional[bool] = False

class GenerateAllRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    comments: str
    generate_cover_letter: bool = True
    max_words: Optional[int] = None
    iteration: Optional[int] = 1
    refinement_feedback: Optional[str] = ""

# --- FastAPI app ---

app = FastAPI(
    title="Job Offers API",
    description="REST API wrapping the job application pipeline scripts.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper functions ---

def _ensure_dirs():
    """Ensure .tmp directory exists."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def _save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _save_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _split_cv_and_gaps(raw_cv: str) -> tuple[str, str]:
    """Split the LLM output into CV content and gap analysis."""
    gap_markers = [
        "## Gap Analysis",
        "## Análisis de Ajuste al Puesto",
        "## Análisis de Brechas",
        "## Analyse des Écarts",
        "## Lückenanalyse",
        "## Analisi delle Lacune",
        "## Análise de Lacunas",
    ]
    for marker in gap_markers:
        if marker in raw_cv:
            cv_content, gap_analysis = raw_cv.split(marker, 1)
            return cv_content.strip(), (marker + gap_analysis).strip()
    return raw_cv.strip(), "## Gap Analysis\nNo significant gaps identified."


def _build_length_constraint(max_words: Optional[int], max_chars: Optional[int]) -> str:
    if max_words and max_chars:
        raise HTTPException(status_code=400, detail="Specify max_words or max_chars, not both.")
    if max_words:
        return f"approximately {max_words} words"
    if max_chars:
        return f"approximately {max_chars} characters"
    return "approximately 300-400 words"


def _get_github_username():
    """Extract GitHub username from profile data."""
    cv_data = get_user_data()
    github_url = cv_data.get("personal_info", {}).get("github", "")
    if not github_url:
        return None
    return github_url.rstrip("/").split("/")[-1]


def _fetch_github_projects(job_analysis):
    """Load curated repos and select relevant ones. Returns (repos, error_msg)."""
    try:
        all_repos = load_curated_repos()
        if not all_repos:
            return [], None
        selected = select_relevant_repos(all_repos, job_analysis)
        _save_json(GITHUB_SELECTED_PATH, selected)
        return selected, None
    except Exception as e:
        return [], str(e)


def _generate_pdfs(skip_cover_letter: bool = False) -> dict:
    """Generate PDFs from the .tmp/ markdown files. Returns paths."""
    _ensure_dirs()

    job_analysis = {}
    if JOB_ANALYSIS_PATH.exists():
        job_analysis = load_json(str(JOB_ANALYSIS_PATH))

    style_config = analyze_template_style(
        str(TEMPLATE_PATH) if TEMPLATE_PATH.exists() else None
    )

    result = {}

    # CV PDF
    if not TAILORED_CV_PATH.exists():
        raise HTTPException(status_code=400, detail="Tailored CV not found. Run /api/generate-cv first.")

    cv_content = load_markdown(str(TAILORED_CV_PATH))
    cv_filename = generate_filename(job_analysis, "CV")
    cv_output = TMP_DIR / cv_filename
    markdown_to_pdf(cv_content, cv_output, style_config)
    result["cv_pdf_path"] = str(cv_output.relative_to(PROJECT_ROOT))

    # Cover letter PDF
    if not skip_cover_letter:
        if not COVER_LETTER_PATH.exists():
            raise HTTPException(
                status_code=400,
                detail="Cover letter not found. Run /api/generate-cover-letter first.",
            )
        cl_content = load_markdown(str(COVER_LETTER_PATH))
        cl_filename = generate_filename(job_analysis, "CoverLetter")
        cl_output = TMP_DIR / cl_filename
        markdown_to_pdf(cl_content, cl_output, style_config)
        result["cover_letter_pdf_path"] = str(cl_output.relative_to(PROJECT_ROOT))

    return result


# --- Endpoints ---

@app.post("/api/analyze-job")
def api_analyze_job(req: AnalyzeJobRequest):
    """Analyze a job offer from URL or raw text."""
    _ensure_dirs()

    if not req.url and not req.text:
        raise HTTPException(status_code=400, detail="Provide either 'url' or 'text'.")

    job_text = None
    if req.url:
        job_text = scrape_job_url(req.url)
        if not job_text:
            raise HTTPException(status_code=422, detail="Failed to scrape URL.")
    else:
        job_text = req.text

    analysis = analyze_with_llm(job_text)

    analysis["source"] = {
        "url": req.url,
        "raw_text": job_text[:500] + "..." if len(job_text) > 500 else job_text,
    }

    _save_json(JOB_ANALYSIS_PATH, analysis)
    return analysis


@app.post("/api/load-cv")
def api_load_cv():
    """Load the user's CV database (hardcoded master CV data)."""
    _ensure_dirs()

    cv_data = get_user_data()
    cv_data["metadata"] = {
        "data_source": "hardcoded",
        "note": "Loaded via web API",
    }

    _save_json(CV_DATABASE_PATH, cv_data)
    return cv_data


@app.post("/api/fetch-github")
def api_fetch_github():
    """Return the curated GitHub repos list."""
    repos = load_curated_repos()
    return {"repos": repos, "count": len(repos)}


@app.post("/api/generate-cv")
def api_generate_cv(req: GenerateCVRequest):
    """Generate a tailored CV from job_analysis + cv_database in .tmp/."""
    if not JOB_ANALYSIS_PATH.exists():
        raise HTTPException(status_code=400, detail="job_analysis.json not found. Run /api/analyze-job first.")
    if not CV_DATABASE_PATH.exists():
        raise HTTPException(status_code=400, detail="cv_database.json not found. Run /api/load-cv first.")

    job_analysis = load_json(str(JOB_ANALYSIS_PATH))
    cv_database = load_json(str(CV_DATABASE_PATH))

    # Inject GitHub projects if available
    github_projects, _ = _fetch_github_projects(job_analysis)
    if github_projects:
        cv_database["github_projects"] = github_projects

    raw_cv = generate_tailored_cv(
        job_analysis,
        cv_database,
        req.comments,
        iteration=req.iteration or 1,
        refinement_feedback=req.refinement_feedback or "",
    )

    cv_content, gap_analysis = _split_cv_and_gaps(raw_cv)

    _save_text(TAILORED_CV_PATH, cv_content)
    _save_text(CV_GAPS_PATH, gap_analysis)

    return {"cv_markdown": cv_content, "gaps": gap_analysis}


@app.post("/api/generate-cover-letter")
def api_generate_cover_letter(req: GenerateCoverLetterRequest):
    """Generate a cover letter from job_analysis + tailored_cv in .tmp/."""
    if not JOB_ANALYSIS_PATH.exists():
        raise HTTPException(status_code=400, detail="job_analysis.json not found. Run /api/analyze-job first.")
    if not TAILORED_CV_PATH.exists():
        raise HTTPException(status_code=400, detail="tailored_cv.md not found. Run /api/generate-cv first.")

    job_analysis = load_json(str(JOB_ANALYSIS_PATH))
    tailored_cv = load_markdown(str(TAILORED_CV_PATH))

    length_constraint = _build_length_constraint(req.max_words, req.max_chars)

    cover_letter_md = generate_cover_letter(
        job_analysis,
        tailored_cv,
        req.comments,
        length_constraint=length_constraint,
        iteration=req.iteration or 1,
        refinement_feedback=req.refinement_feedback or "",
    )

    _save_text(COVER_LETTER_PATH, cover_letter_md)

    return {"cover_letter_markdown": cover_letter_md}


@app.post("/api/generate-pdfs")
def api_generate_pdfs(req: GeneratePDFsRequest):
    """Generate styled PDFs from the markdown files in .tmp/."""
    return _generate_pdfs(skip_cover_letter=req.skip_cover_letter or False)


@app.get("/api/download/{filename:path}")
def api_download(filename: str):
    """Serve a generated file from .tmp/job_applications/."""
    file_path = TMP_DIR / filename
    if not file_path.resolve().is_relative_to(TMP_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied.")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    return FileResponse(path=str(file_path), filename=file_path.name)


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/api/generate-all")
def api_generate_all(req: GenerateAllRequest):
    """
    Full pipeline with SSE progress events.
    Streams: progress -> step_result -> ... -> complete (or error).
    On iteration > 1, skips job analysis (reuses existing .tmp/ data).
    """
    iteration = req.iteration or 1
    refinement_feedback = req.refinement_feedback or ""

    # Validate before starting stream
    if iteration <= 1 and not req.url and not req.text:
        raise HTTPException(status_code=400, detail="Provide either 'url' or 'text'.")
    if iteration > 1 and not JOB_ANALYSIS_PATH.exists():
        raise HTTPException(status_code=400, detail="Cannot refine: no previous job analysis found.")

    def event_stream():
        _ensure_dirs()

        # --- Step 1: Analyze job (skip on refinement) ---
        if iteration <= 1:
            yield _sse_event("progress", {"step": "analyzing_job", "message": "Analyzing job offer..."})
            try:
                job_text = None
                if req.url:
                    job_text = scrape_job_url(req.url)
                    if not job_text:
                        yield _sse_event("error", {
                            "step": "analyzing_job",
                            "message": "Could not access URL. Please paste the job text instead.",
                        })
                        return
                else:
                    job_text = req.text

                analysis = analyze_with_llm(job_text)
                analysis["source"] = {
                    "url": req.url,
                    "raw_text": job_text[:500] + "..." if len(job_text) > 500 else job_text,
                }
                _save_json(JOB_ANALYSIS_PATH, analysis)
            except Exception as e:
                yield _sse_event("error", {"step": "analyzing_job", "message": str(e)})
                return

            yield _sse_event("step_result", {"step": "analyzing_job", "job_analysis": analysis})
        else:
            analysis = load_json(str(JOB_ANALYSIS_PATH))
            yield _sse_event("step_result", {"step": "analyzing_job", "job_analysis": analysis})

        # --- Step 2: Load CV database ---
        yield _sse_event("progress", {"step": "loading_cv", "message": "Loading CV database..."})
        try:
            cv_data = get_user_data()
            cv_data["metadata"] = {"data_source": "hardcoded", "note": "Loaded via generate-all pipeline"}
            _save_json(CV_DATABASE_PATH, cv_data)
        except Exception as e:
            yield _sse_event("error", {"step": "loading_cv", "message": str(e)})
            return

        # --- Step 2b: Fetch GitHub projects ---
        yield _sse_event("progress", {"step": "fetching_github", "message": "Scanning GitHub for relevant projects..."})
        try:
            github_projects, gh_error = _fetch_github_projects(analysis)
            if github_projects:
                cv_data["github_projects"] = github_projects
                _save_json(CV_DATABASE_PATH, cv_data)
        except Exception as e:
            github_projects = []

        yield _sse_event("step_result", {
            "step": "fetching_github",
            "github_projects": github_projects,
        })

        # --- Step 3: Generate tailored CV ---
        yield _sse_event("progress", {"step": "generating_cv", "message": "Generating tailored CV..."})
        try:
            raw_cv = generate_tailored_cv(
                analysis, cv_data, req.comments,
                iteration=iteration, refinement_feedback=refinement_feedback,
            )
            cv_content, gap_analysis = _split_cv_and_gaps(raw_cv)
            _save_text(TAILORED_CV_PATH, cv_content)
            _save_text(CV_GAPS_PATH, gap_analysis)
        except Exception as e:
            yield _sse_event("error", {"step": "generating_cv", "message": str(e)})
            return

        yield _sse_event("step_result", {
            "step": "generating_cv",
            "cv_markdown": cv_content,
            "gaps": gap_analysis,
        })

        # --- Step 4: Generate cover letter (if requested) ---
        cover_letter_md = None
        if req.generate_cover_letter:
            yield _sse_event("progress", {"step": "generating_cover_letter", "message": "Generating cover letter..."})
            try:
                length_constraint = f"approximately {req.max_words} words" if req.max_words else "approximately 300-400 words"
                cover_letter_md = generate_cover_letter(
                    analysis, cv_content, req.comments,
                    length_constraint=length_constraint,
                    iteration=iteration, refinement_feedback=refinement_feedback,
                )
                _save_text(COVER_LETTER_PATH, cover_letter_md)
            except Exception as e:
                yield _sse_event("error", {"step": "generating_cover_letter", "message": str(e)})
                return

            yield _sse_event("step_result", {
                "step": "generating_cover_letter",
                "cover_letter_markdown": cover_letter_md,
            })

        # --- Step 5: Generate PDFs ---
        yield _sse_event("progress", {"step": "creating_pdfs", "message": "Creating PDFs..."})
        try:
            job_analysis_for_pdf = load_json(str(JOB_ANALYSIS_PATH)) if JOB_ANALYSIS_PATH.exists() else {}
            style_config = analyze_template_style(
                str(TEMPLATE_PATH) if TEMPLATE_PATH.exists() else None
            )

            cv_md = load_markdown(str(TAILORED_CV_PATH))
            cv_filename = generate_filename(job_analysis_for_pdf, "CV")
            cv_output = TMP_DIR / cv_filename
            markdown_to_pdf(cv_md, cv_output, style_config)
            pdf_result = {"cv_pdf_path": str(cv_output.relative_to(PROJECT_ROOT))}

            if req.generate_cover_letter and COVER_LETTER_PATH.exists():
                cl_md = load_markdown(str(COVER_LETTER_PATH))
                cl_filename = generate_filename(job_analysis_for_pdf, "CoverLetter")
                cl_output = TMP_DIR / cl_filename
                markdown_to_pdf(cl_md, cl_output, style_config)
                pdf_result["cover_letter_pdf_path"] = str(cl_output.relative_to(PROJECT_ROOT))
        except Exception as e:
            yield _sse_event("error", {"step": "creating_pdfs", "message": str(e)})
            return

        yield _sse_event("complete", pdf_result)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/save-documents")
def api_save_documents():
    """Copy generated PDFs from .tmp/ to output/ for permanent storage."""
    pdfs = list(TMP_DIR.glob("*.pdf"))
    if not pdfs:
        raise HTTPException(status_code=400, detail="No documents to save. Generate PDFs first.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    for pdf in pdfs:
        shutil.copy2(pdf, OUTPUT_DIR / pdf.name)
        saved.append(pdf.name)
    return {"saved": saved, "destination": "output/job_applications/"}


# --- Static files (SPA) - MUST be after all API routes ---
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
