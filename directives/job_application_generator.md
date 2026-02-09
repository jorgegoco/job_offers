# Job Application Generator

## Purpose
Generate tailored CVs and cover letters for specific job offers, matching the job's requirements, keywords, and tone while maintaining professional design.

## Inputs (per run)
- **Job offer**: Either pasted text or URL (in Spanish or English)
- **User comments**: Specific angles to emphasize, experiences to highlight (high priority - strongly influences output)
- **Cover letter flag**: Yes/No - whether to generate a cover letter
- **Cover letter length**: Word count or character limit (prompted each time if generating cover letter)

## Resources (one-time setup)
- **Master CV** (`resources/job_applications/master_cv.pdf`): Complete CV with all experience
  - **Data source**: `resources/profile.json` — the single source of truth for all profile data
  - No LLM extraction needed - instant data loading
  - To update: edit `resources/profile.json` directly or use `update_profile()` from `execution/analyze_master_cv.py`
- **Design template** (`resources/job_applications/cv_template.pdf`): Visual style reference for final output

## Workflow Steps

### Step 1: Analyze Job Offer
**Tool**: `execution/analyze_job_offer.py`

**What it does**:
- If URL: scrape the job posting content
- If text: parse directly
- Extract:
  - **Language**: Auto-detect job posting language (en/es/fr/etc.) - determines output language
  - Required skills (must-have vs nice-to-have)
  - Keywords and terminology
  - Tone and company culture signals
  - Job level and responsibilities
  - Application instructions

**Output**: JSON file in `.tmp/job_applications/job_analysis.json`

**Language handling**:
- Detects primary language of job posting automatically
- Supported languages: English (en), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt)
- All subsequent CV/cover letter generation uses detected language
- Example: Spanish job posting → Spanish CV and cover letter

**Edge cases**:
- URL requires login: ask user to paste text instead
- Multi-page job description: capture all pages
- Bilingual postings: detects primary language by word count
- Unsupported languages: falls back to English with warning

---

### Step 2: Prompt for Job-Specific Info (Orchestration)
**Who**: Agent (you) handles this interactively

After job analysis is complete:

1. **Display extracted job requirements summary**:
   - Show key required skills
   - Show nice-to-have skills
   - Show detected language and tone

2. **Ask**: "Is there any additional information relevant to THIS job to add to your profile?"

3. **If user provides additional info**:
   - Evaluate if it should be permanently added to `resources/profile.json`
   - **If permanent**: Use `update_profile()` from `execution/analyze_master_cv.py` to save it
   - **If temporary/job-specific**: Pass as `--comments` to generation scripts

4. **MANDATORY: Update profile.json with new skills** (see "Mandatory Skill Updates" section below)
   - Any new skill, certification, or experience mentioned during the conversation MUST be added to `resources/profile.json`
   - This is NOT optional - skills revealed during CV tailoring are valuable profile data
   - Update immediately after generating documents, before ending the conversation

---

### Step 3: Prompt for Generation Options (Orchestration)
**Who**: Agent (you) handles this interactively

1. **Ask**: "What would you like to generate?"
   - CV only
   - Cover letter only
   - Both (default)

2. **If cover letter selected**: "Specify length? (e.g., '300 words', '1500 chars', or Enter for 400 words default)"

---

### Step 4: Load CV Data
**Tool**: `execution/analyze_master_cv.py`

**What it does**:
- Loads profile from `resources/profile.json` (no LLM call, instant)
- Extracts raw text from PDF for metadata (optional)
- Outputs cv_database.json

**Output**: JSON file in `.tmp/job_applications/cv_database.json`

**Performance**: Instant - no API calls needed

---

### Step 5: Show Suggestions Before Generation (Orchestration)
**Who**: Agent (you) displays these suggestions

Before generating documents, display three types of suggestions:

1. **Skill Emphasis Hints**:
   - Compare job requirements with user's skills
   - "Based on job requirements, emphasize: [Python, API development, FastAPI, ...]"
   - Highlight skills that match job's must-haves

2. **Gap Warnings**:
   - Identify requirements not found in user's profile
   - "Job requires [X] but not found in CV - consider addressing in cover letter"
   - Help user decide if they want to add context via comments

3. **Tone/Style Guidance**:
   - Analyze job posting tone (formal/casual/technical)
   - "Job posting tone: [formal/technical] - recommend matching style"
   - Suggest adjustments based on company culture signals

**Then ask**: "Review suggestions above. Proceed with generation? (yes/modify comments)"

If user wants to modify: go back to Step 2 to add more comments.

---

### Step 6: Generate Tailored CV (if selected)
**Tool**: `execution/generate_tailored_cv.py`

**What it does**:
- Map job requirements to CV database
- Reorder sections based on job priorities
- Rewrite descriptions using job's keywords
- **Emphasize user-specified angles from comments (PRIMARY DIRECTIVE - takes precedence over auto-matching)**
- Generate in detected job language (Spanish/English/etc.)
- Apply emoji header format: `📧 email | 🔗 LinkedIn | 💼 Portfolio | 🐙 GitHub`
- Ensure max 2 pages
- Flag gaps between requirements and experience

**CRITICAL - Content that must NEVER appear in the tailored CV:**
- Gap analysis sections ("Análisis de Gaps", "Gap Analysis", "Gaps Identificados")
- Recommendations sections ("Recomendaciones", "Recommendations", "Acciones Recomendadas")
- Match ratings or percentages ("85% match", "Nivel de Adecuación")
- Internal notes or strategies ("Mitigación", "Fortalezas Compensatorias")
- Interview preparation tips
- Any meta-commentary about the CV itself
- Suggested actions for the candidate

**Why this matters:** The tailored CV goes directly to the employer. Including internal analysis is unprofessional and potentially damaging - it reveals weaknesses and strategies that should remain private. The CV must contain ONLY standard CV content: contact info, summary, experience, education, skills, projects, languages.

**Inputs**:
- `.tmp/job_applications/job_analysis.json` (includes language)
- `.tmp/job_applications/cv_database.json`
- User comments
- Iteration number (for refinements)
- Refinement feedback (from previous iteration)

**Output**:
- Markdown draft in `.tmp/job_applications/tailored_cv.md` with emoji header
- Gap analysis in `.tmp/job_applications/cv_gaps.txt`

**Iterative refinement loop**:
1. Generate draft CV (iteration 1)
2. Show draft + gap analysis to user
3. Ask: "Type 'approve'/'done' to continue, or provide feedback for changes"
4. If feedback provided:
   - Regenerate with `--iteration N --refinement-feedback "user's feedback"`
   - Go to step 2
5. If 'approve'/'done': proceed to cover letter (if requested) or final PDF
6. **Maximum 5 iterations** to prevent infinite loops and API cost explosion

**Language handling**:
- Automatically uses language from `job_analysis.json`
- Spanish job → Spanish CV (all content, including section headers)
- English job → English CV
- User doesn't need to specify language

**User comments influence**:
- Treated as PRIMARY DIRECTIVES that override default prioritization
- Example: "emphasize Python projects" → Python experiences become most prominent
- Example: "downplay management roles" → management experience minimized even if job requires it
- User knows their audience best - their guidance takes absolute priority

**Edge cases**:
- Experience doesn't match key requirements: prominently flag in gap analysis
- Over 2 pages: suggest cuts, ask user to choose
- User adds new experience: note to update HARDCODED_USER_DATA later
- Iteration limit reached (5): warn about costs, suggest starting fresh

---

### Step 7: Generate Cover Letter (if selected)
**Tool**: `execution/generate_cover_letter.py`

**What it does**:
- Match tone from job analysis
- Generate in detected job language (same as CV)
- Structure:
  - Opening: why this role/company
  - Body: 2-3 key experiences matching requirements
  - Closing: call to action
- **Incorporate user's specified angles (PRIMARY DIRECTIVE)**
- Max 1 page with user-specified length constraint

**Inputs**:
- `.tmp/job_applications/job_analysis.json` (includes language)
- `.tmp/job_applications/tailored_cv.md`
- User comments
- **Length constraint**: Word count or character limit (from Step 3)
  - Example: "300 words", "1500 characters", or default (400 words)
- Iteration number (for refinements)
- Refinement feedback (from previous iteration)

**Output**: Markdown draft in `.tmp/job_applications/cover_letter.md`

**Iterative refinement loop**:
- Same as CV: Show draft → Get feedback → Regenerate (up to 5 iterations)
- Ask: "Type 'approve'/'done' to proceed to PDF, or provide feedback"

**Language handling**:
- Automatically uses language from `job_analysis.json`
- Matches CV language (Spanish CV → Spanish cover letter)

**User comments influence**:
- Treated as PRIMARY DIRECTIVES for letter focus
- Example: "emphasize international experience" → letter centers on global work
- Example: "mention specific project X" → project X woven into narrative

**Edge cases**:
- Formal vs casual tone: mirror job posting
- Specific application instructions: include as reminder
- Multiple recipients: ask for names
- Iteration limit reached (5): warn about costs

---

### Step 8: Apply Design Template
**Tool**: `execution/apply_template.py`

**What it does**:
- Convert markdown to PDF
- Apply visual style from `resources/job_applications/cv_template.pdf`:
  - Fonts (with emoji support), colors, spacing
  - Section headers with accent colors
  - Layout structure
  - **Emoji rendering**: Properly displays 📧 🔗 💼 🐙 🌐 in headers
- Generate:
  - `output/job_applications/CV_[Company]_[JobTitle]_[Date].pdf`
  - `output/job_applications/CoverLetter_[Company]_[JobTitle]_[Date].pdf` (if applicable)

**Emoji header format**:
- CV headers now include emoji icons for better visual hierarchy
- Format: `📧 email | 🔗 LinkedIn | 💼 Portfolio | 🐙 GitHub | 🌐 Website`
- Fonts include emoji fallbacks: Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji
- Works across Windows, Mac, and Linux

**Edge cases**:
- Template matching fails: generate clean default
- Special characters: ensure UTF-8 encoding
- Long company names: handle line breaks
- Emoji rendering issues: Falls back to text-based icons if font doesn't support emojis

---

## Success Criteria
- CV fits on 2 pages maximum
- Cover letter meets user-specified length constraint
- Uses job's terminology naturally (not keyword stuffing)
- **User comments prominently incorporated** (primary directive satisfied)
- **Output in detected job language** (Spanish/English match)
- User approves both documents before final PDF generation
- Gap analysis clearly flags missing qualifications
- Emoji header renders correctly in PDF
- Suggestions (skill emphasis, gaps, tone) displayed before generation

## Mandatory Skill Updates

**CRITICAL RULE**: When the user mentions ANY new skill, technology, certification, or experience during a CV tailoring conversation, the agent MUST update `resources/profile.json` BEFORE ending the conversation.

### Why this is mandatory:
- Skills mentioned during tailoring are real skills the user has
- Failing to save them means losing valuable profile data
- Future CV generations will be incomplete without this data
- The user shouldn't have to repeat themselves

### What to update:
1. **New programming languages** → `update_profile("technical_skills.programming_languages", ["NewLang"])`
2. **New frameworks/libraries** → `update_profile("technical_skills.frameworks", ["NewFramework"])`
3. **New AI/ML skills** → `update_profile("technical_skills.ai_ml", ["NewSkill"])`
4. **New tools** → `update_profile("technical_skills.tools", ["NewTool"])`
5. **New cloud services** → `update_profile("technical_skills.cloud", ["NewService"])`
6. **New certifications** → `update_profile("certifications", [{"name": "...", "issuer": "...", "date": "..."}])`
7. **New projects** → `update_profile("projects", [{"name": "...", "description": "...", "technologies": [...]}])`
8. **New soft skills** → `update_profile("soft_skills", ["NewSkill"])`
9. **New methodologies** → `update_profile("technical_skills.methodologies", ["NewMethod"])`

### When to update:
- After document generation is complete
- Before asking user for final approval
- Even if skills were only used in `--comments` for this job

### Example workflow:
1. User says: "I also have experience with Kubernetes and AWS EKS"
2. Generate CV/cover letter with these skills via `--comments`
3. AFTER generation, update `resources/profile.json`:
   - `update_profile("technical_skills.tools", ["Kubernetes"])`
   - `update_profile("technical_skills.cloud", ["AWS EKS"])`
4. Inform user: "I've also updated your master profile with Kubernetes and AWS EKS"

**This is NOT optional. Every CV tailoring session should enrich the user's profile.**

---

## Updating User Data

To update your CV information, edit `resources/profile.json` directly or use the `update_profile()` function from `execution/analyze_master_cv.py`.

### Option 1: Edit profile.json directly

Edit the JSON file and modify fields. Changes take effect on next run.

**Example - Adding a new job** (append to `work_experience` array):
```json
{
    "role": "New Job Title",
    "company": "Company Name",
    "location": "Location",
    "start_date": "Month Year",
    "end_date": "Present",
    "duration": "X years",
    "achievements": ["Achievement 1", "Achievement 2"],
    "skills_used": ["Skill 1", "Skill 2"],
    "keywords": ["keyword1", "keyword2"]
}
```

### Option 2: Use update_profile() programmatically

```python
from execution.analyze_master_cv import update_profile

# Add skills (deduplicates automatically)
update_profile("technical_skills.programming_languages", ["Go", "Rust"])
update_profile("technical_skills.tools", ["Kubernetes"])
update_profile("technical_skills.cloud", ["AWS EKS"])

# Add a certification
update_profile("certifications", [{"name": "AWS Solutions Architect", "issuer": "AWS", "date": "Jan 2026"}])

# Add soft skills
update_profile("soft_skills", ["Mentoring", "Public Speaking"])
```

## Error Recovery
- If URL scraping fails → ask for pasted text
- If PDF parsing fails → try OCR, then ask for text version (OCR not yet implemented)
- If template application fails → generate clean default PDF
- If API limits hit → cache results, resume later

## Learnings Log
*(Update this section as issues arise)*

### 2026-01-20: CV Content Boundaries
**Issue:** Generated CV included internal gap analysis, recommendations, and match ratings that should never be sent to employers.
**Root cause:** LLM included helpful internal analysis in the CV markdown without clear boundaries.
**Fix:** Added explicit "CRITICAL - Content that must NEVER appear" section to Step 6 listing forbidden content types.
**Rule:** The tailored CV must contain ONLY standard CV sections. All internal analysis goes to separate files (cv_gaps.txt) or is shown to user separately, never embedded in the CV itself.

