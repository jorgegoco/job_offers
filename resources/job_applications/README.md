# Job Application Generator Workflow

Automated workflow for generating tailored CVs and cover letters for specific job offers.

## Quick Start

### 1. Upload your resources

Place these files in this directory (`resources/job_applications/`):
- `master_cv.pdf` - Your complete CV with all experience
- `cv_template.pdf` - Your design template (optional, defaults to professional styling)

### 2. Generate application documents

Tell the AI agent:
```
I want to generate a CV for [job title] at [company].

Job offer: [paste URL or text]

My comments: [what you want to emphasize]

Cover letter: [yes/no]
```

The agent will:
1. Analyze the job posting (detects language automatically)
2. Use your cached CV data (or extract if first run)
3. Generate tailored drafts
4. Allow iterative refinement based on your feedback
5. Generate final PDFs in `output/job_applications/`

## Features

### Core Functionality
- Analyzes job requirements and extracts keywords
- **Auto-detects job language** (Spanish/English/French/etc.) and generates matching output
- Maps your experience to job requirements
- Rewrites content using job's terminology
- Identifies gaps in your experience
- Generates tailored cover letters with **custom length constraints**
- Applies your design template with **emoji header format** (📧 🔗 💼 🐙)
- Max 2 pages for CV, customizable length for cover letter

### Performance & Cost Optimization
- **Intelligent CV caching**: Extracts master CV once, reuses cached data
  - Saves ~$0.15-0.20 per application
  - Reduces workflow from 5-8 minutes to 30 seconds after first run
  - Auto-invalidates when PDF content changes

### Enhanced Workflow
- **Iterative refinement**: Get draft → provide feedback → regenerate (up to 5 iterations)
- **User comments as primary directive**: Your guidance takes precedence over auto-matching
- **Multi-language support**: Spanish jobs → Spanish CV/cover letter (automatic)
- **Flexible cover letter lengths**: Specify word count or character limit per job

## Manual Execution

You can also run scripts directly:

```bash
# 1. Analyze job offer (detects language automatically)
python execution/analyze_job_offer.py --url "https://example.com/job"

# 2. Analyze your master CV (uses cache on subsequent runs)
python execution/analyze_master_cv.py

# 3. Generate tailored CV (iteration 1)
python execution/generate_tailored_cv.py --comments "Emphasize leadership and Python skills"

# 3b. Refine CV based on feedback (iteration 2)
python execution/generate_tailored_cv.py --iteration 2 --refinement-feedback "Add more technical details"

# 4. Generate cover letter with custom length
python execution/generate_cover_letter.py --comments "Show enthusiasm" --max-words 300

# 4b. Refine cover letter (iteration 2)
python execution/generate_cover_letter.py --iteration 2 --refinement-feedback "Make opening stronger"

# 5. Create final PDFs
python execution/apply_template.py
```

## Outputs

Generated files in `output/job_applications/`:
- `CV_[Company]_[JobTitle]_[Date].pdf`
- `CoverLetter_[Company]_[JobTitle]_[Date].pdf`

Intermediate files in `.tmp/job_applications/` (can be deleted):
- `job_analysis.json` - Extracted job requirements (includes language detection)
- `cv_database.json` - Structured version of your CV (cached)
- `cv_cache_metadata.json` - Cache validation metadata
- `tailored_cv.md` - Draft CV in markdown with emoji headers
- `cover_letter.md` - Draft cover letter in markdown
- `cv_gaps.txt` - Gap analysis

## Tips

### Performance
- **CV caching saves time and money**: After first run, subsequent applications are ~30 seconds (vs 5-8 minutes)
- Only update `master_cv.pdf` when you add new experience (triggers re-extraction)
- CV cache is automatic - no manual management needed

### Language Support
- Job postings in Spanish automatically generate Spanish CV/cover letter
- No need to specify language - detection is automatic
- Supported: English, Spanish, French, German, Italian, Portuguese

### Refinement Workflow
- Don't worry about perfection on first draft - use iteration refinement
- Provide specific feedback: "Add more Python details" instead of "make it better"
- Maximum 5 iterations per document to control API costs
- Each iteration costs ~$0.05-0.10

### User Comments
- **Your comments take priority** over automatic matching
- Be specific: "Emphasize leadership in remote teams" vs "emphasize leadership"
- Use comments to override: "Downplay management roles" works even if job requires it
- Comments are PRIMARY DIRECTIVES - the generator follows your guidance first

## Detailed Documentation

For complete workflow documentation, see: `directives/job_application_generator.md`
