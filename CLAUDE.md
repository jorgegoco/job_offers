# Agent Reference

## What This Project Does

Web app that generates tailored CVs and cover letters from job postings. The user pastes a job URL or text, the system analyzes it, matches it against their profile, and produces PDF documents in the job's language.

## Key Files

- `webapp/main.py` — FastAPI app, entry point for all operations
- `execution/analyze_job_offer.py` — Scrapes/parses job posting, extracts requirements and language
- `execution/analyze_master_cv.py` — Loads profile data from profile.json, provides `update_profile()`
- `execution/fetch_github_repos.py` — Loads curated repos, selects most relevant to job
- `execution/generate_tailored_cv.py` — Generates tailored CV markdown
- `execution/generate_cover_letter.py` — Generates cover letter markdown
- `execution/apply_template.py` — Converts markdown to styled PDFs
- `execution/utils.py` — Shared `load_json`/`load_markdown` helpers
- `resources/profile.json` — Single source of truth for all user profile data
- `resources/github_repos.json` — Curated GitHub repos for CV enrichment
- `.env` — API keys and model configuration

## Architecture

The webapp exposes API endpoints that call execution scripts. `resources/profile.json` is the data source for all profile information. GitHub repos come from a curated list in `resources/github_repos.json`, not fetched live from the API. Intermediate files and generated PDFs go in `.tmp/job_applications/`. Users explicitly save final documents to `output/job_applications/` via the "Save to output/" button.

## Environment Variables

```
ANTHROPIC_API_KEY    — Required. Anthropic API key.
GITHUB_TOKEN         — Optional. Only needed for README enrichment of selected repos and --check-new discovery.
MODEL_EXTRACTION     — Model for extraction tasks (Haiku). Cheaper, used for job analysis and GitHub selection.
MODEL_GENERATION     — Model for generation tasks (Sonnet). Higher quality, used for CV and cover letter.
```

## Technical Notes

### 3-Layer Gap Analysis Defense

The CV generation must never leak internal analysis into the output PDF. Three layers prevent this:
1. **Deterministic separator**: Prompt includes `---GAP_ANALYSIS_SEPARATOR---` to split CV from analysis
2. **Fallback markers**: Expanded list of header patterns ("Análisis de Gaps", "Gap Analysis", etc.) for splitting
3. **Post-split validation**: Forbidden-pattern scan strips any leaked internal content after splitting

Never trust LLM output boundaries based on header matching alone. Always validate with forbidden-pattern scanning.

### Model Tiers

- **Haiku** (`MODEL_EXTRACTION`): Job analysis, GitHub repo selection — extraction tasks
- **Sonnet** (`MODEL_GENERATION`): CV generation, cover letter generation — creative tasks
- ~40-60% cost reduction vs using Sonnet for everything

### User Comments as Primary Directives

User comments override automatic matching. If the user says "emphasize Python" or "downplay management", that takes absolute priority over what the job posting requests. The user knows their audience best.

### Language Auto-Detection

The job posting language is detected automatically and all output (CV, cover letter, section headers) is generated in that language. Supported: en, es, fr, de, it, pt. Bilingual postings use primary language by word count.

### Mandatory Skill Updates

After every CV tailoring session, any new skills, certifications, or experience mentioned during the conversation MUST be saved to `resources/profile.json` using `update_profile()` from `execution/analyze_master_cv.py`. This is not optional — skills revealed during tailoring are real profile data.

### Iterative Refinement

CV and cover letter each support up to 5 refinement iterations. User reviews draft, provides feedback, document is regenerated. Maximum 5 iterations to prevent cost explosion.

### CV Content Boundaries

The tailored CV must contain ONLY standard CV sections (contact info, summary, experience, education, skills, projects, languages). Never include: gap analysis, recommendations, match ratings, internal notes, interview tips, or meta-commentary. All internal analysis goes to `cv_gaps.txt` or is shown separately.

## Learnings Log

### 2026-01-20: CV Content Boundaries
**Issue:** Generated CV included internal gap analysis and match ratings in the output.
**Fix:** Added explicit forbidden content list to generation prompt. CV must contain only standard sections. Internal analysis goes to separate files.

### 2026-02-10: Gap Analysis Separator Fix
**Issue:** CV included gap analysis in PDF because LLM used a header variation not in the marker list.
**Fix:** Implemented 3-layer defense: deterministic separator in prompt, expanded fallback markers, post-split forbidden content validation.

### 2026-02-10: Cost Optimization with Model Tiers
**Issue:** All scripts used Sonnet, making each application expensive.
**Fix:** Introduced MODEL_EXTRACTION (Haiku) and MODEL_GENERATION (Sonnet) tiers. Extraction tasks use Haiku, generation uses Sonnet. Added prompt caching for stable profile data.
**Impact:** ~40-60% cost reduction per application.

### 2026-02-10: Project Refactor
**Changes:** Replaced GitHub API fetching with curated repo list (resources/github_repos.json). Moved PDF output to .tmp/ with explicit save-to-output workflow. Removed dead files (master_cv.pdf, cv_template.pdf, execution/utils/ package). Merged requirements into single file. Extracted shared load_json/load_markdown into execution/utils.py. Unified gap analysis defense — webapp now uses same 3-layer split as CLI.

## Git Commit Rules

- Clear, concise messages describing what changed and why
- Use conventional commits (feat:, fix:, refactor:)
- Never mention AI, Claude, or any LLM in commit messages
- Messages should read as if written by a human developer
