#!/usr/bin/env python3
"""
Generates a tailored CV for a specific job offer.
Maps experience to requirements, reorders sections, rewrites with job keywords.
"""

import json
import sys
import argparse
from pathlib import Path
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

def load_json(file_path):
    """Load JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def _build_github_section(cv_database):
    """Build prompt section for GitHub projects if available."""
    github_projects = cv_database.get("github_projects", [])
    if not github_projects:
        return ""
    return f"""
CANDIDATE'S RELEVANT GITHUB PROJECTS (RECENT WORK):
{json.dumps(github_projects, indent=2)}

These are the candidate's most recent, actively maintained projects selected from GitHub.
IMPORTANT: Prioritize these over older static projects when they are relevant to the job.
Include the GitHub URL for each project used in the CV.
"""


def generate_tailored_cv(job_analysis, cv_database, user_comments, iteration=1, refinement_feedback=''):
    """Use Claude to generate tailored CV."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Extract language from job analysis
    job_language = job_analysis.get('language', 'en')

    # Language instruction mapping
    language_names = {
        'en': 'ENGLISH',
        'es': 'SPANISH',
        'fr': 'FRENCH',
        'de': 'GERMAN',
        'it': 'ITALIAN',
        'pt': 'PORTUGUESE'
    }
    language_name = language_names.get(job_language, 'ENGLISH')

    language_instruction = f"""
CRITICAL LANGUAGE REQUIREMENT:
- Generate the ENTIRE CV in {language_name} language (language code: '{job_language}')
- If '{job_language}' is 'es', write ALL content in Spanish (including section headers, summaries, experiences)
- If '{job_language}' is 'en', write ALL content in English
- Match linguistic conventions and terminology of the target language
- Use native terminology for roles, skills, and achievements
"""

    # Build iteration context if this is a refinement
    iteration_context = ""
    if iteration > 1 and refinement_feedback:
        iteration_context = f"""
REFINEMENT ITERATION {iteration}:
This is iteration {iteration} of the CV. The user reviewed the previous version and provided the following feedback:

PREVIOUS ITERATION FEEDBACK:
{refinement_feedback}

CRITICAL: Address the feedback above while maintaining the overall quality and structure of the CV.
Focus on the specific changes requested without losing other strong elements from the previous version.
"""

    prompt = f"""You are an expert CV writer. Generate a tailored CV for this specific job offer.
{language_instruction}
{iteration_context}

JOB ANALYSIS:
{json.dumps(job_analysis, indent=2)}

CANDIDATE'S FULL CV DATABASE:
{json.dumps(cv_database, indent=2)}
{_build_github_section(cv_database)}
USER'S SPECIFIC COMMENTS (HIGH PRIORITY - INCORPORATE PROMINENTLY):
{user_comments}

CRITICAL INSTRUCTIONS FOR USER COMMENTS:
1. Treat user comments as PRIMARY DIRECTIVES that override default prioritization
2. If user says "emphasize X", make X the most prominent aspect of the CV
3. If user says "downplay Y", minimize or omit Y even if job requires it
4. If user specifies particular projects, experiences, or skills to highlight, feature them prominently
5. User knows their audience best - follow their guidance explicitly and without compromise

GENERAL REQUIREMENTS:
1. Maximum 2 pages
2. Reorder and emphasize experiences that match job requirements
3. Rewrite achievement bullets using the job's keywords and terminology naturally
4. Highlight the angles mentioned in user comments above all else
5. Match the tone from the job analysis (formal/casual/technical)
6. Remove or de-emphasize experiences less relevant to this specific role
7. Start with a tailored professional summary that speaks directly to this job

OUTPUT FORMAT:
Return a markdown-formatted CV with clear sections.

After the CV, provide a gap analysis section that identifies:
- Key requirements from the job that the candidate lacks or has limited experience with
- Suggestions for how to address these gaps (e.g., emphasize transferable skills, reframe existing experience)

Structure:
# [Candidate Name]
📧 [email] | 🔗 [LinkedIn](linkedin_url) | 💼 [Portfolio](portfolio_url) | 🐙 [GitHub](github_url) | 🌐 [Website](website_url)

IMPORTANT: Use emoji prefix format for contact information:
- 📧 for email (plain text, not a link)
- 🔗 for LinkedIn (clickable link with "LinkedIn" as display text)
- 💼 for Portfolio (clickable link with "Portfolio" as display text)
- 🐙 for GitHub (clickable link with "GitHub" as display text)
- 🌐 for Website (clickable link with "Website" as display text, if separate from portfolio)

Use the actual URLs from cv_database['personal_info'] to create clickable markdown links.
Format: 📧 jorgegoco70@gmail.com | 🔗 [LinkedIn](https://www.linkedin.com/in/jorgegoco/) | 💼 [Portfolio](https://jorgegoco.vercel.app/) | 🐙 [GitHub](https://github.com/jorgegoco) | 🌐 [Website](https://miagentuca.es/)

## Professional Summary
[Tailored summary for this specific role]

## Work Experience
[Most relevant first, rewritten for this job]

## Education
[Relevant education]

## Skills
[Prioritized by job relevance]

## [Other relevant sections]

---GAP_ANALYSIS_SEPARATOR---
## Gap Analysis
- [Identified gaps and suggestions]

CRITICAL SEPARATOR INSTRUCTION:
You MUST use the exact string "---GAP_ANALYSIS_SEPARATOR---" on its own line to separate the CV content from the Gap Analysis section.
Do NOT use "---" or any other separator. The exact text "---GAP_ANALYSIS_SEPARATOR---" is required for automated parsing.
Place all CV content ABOVE the separator. Place all gap analysis, recommendations, and internal notes BELOW the separator.
"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=12000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

def main():
    parser = argparse.ArgumentParser(description='Generate tailored CV')
    parser.add_argument('--job-analysis', default='.tmp/job_applications/job_analysis.json',
                       help='Path to job analysis JSON')
    parser.add_argument('--cv-database', default='.tmp/job_applications/cv_database.json',
                       help='Path to CV database JSON')
    parser.add_argument('--comments', default='',
                       help='User comments on angles to emphasize')
    parser.add_argument('--output', default='.tmp/job_applications/tailored_cv.md',
                       help='Output markdown file path')
    parser.add_argument('--iteration', type=int, default=1,
                       help='Iteration number for refinement tracking (default: 1)')
    parser.add_argument('--refinement-feedback', default='',
                       help='User feedback from previous iteration for refinement')

    args = parser.parse_args()

    # Load inputs
    job_path = Path(args.job_analysis)
    cv_path = Path(args.cv_database)

    if not job_path.exists():
        print(f"Error: Job analysis not found: {job_path}", file=sys.stderr)
        print("Run analyze_job_offer.py first", file=sys.stderr)
        sys.exit(1)

    if not cv_path.exists():
        print(f"Error: CV database not found: {cv_path}", file=sys.stderr)
        print("Run analyze_master_cv.py first", file=sys.stderr)
        sys.exit(1)

    print("Loading job analysis...")
    job_analysis = load_json(job_path)

    print("Loading CV database...")
    cv_database = load_json(cv_path)

    print("Generating tailored CV with LLM...")
    print(f"Job: {job_analysis['job_title']} at {job_analysis['company']}")
    if args.iteration > 1:
        print(f"Iteration: {args.iteration} (refinement)")
        if args.refinement_feedback:
            print(f"Refinement feedback: {args.refinement_feedback[:100]}...")
    if args.comments:
        print(f"User comments: {args.comments}")

    tailored_cv = generate_tailored_cv(job_analysis, cv_database, args.comments, args.iteration, args.refinement_feedback)

    # === 3-LAYER GAP ANALYSIS DEFENSE ===
    DETERMINISTIC_SEPARATOR = "---GAP_ANALYSIS_SEPARATOR---"

    cv_content = tailored_cv
    gap_analysis = "## Gap Analysis\nNo significant gaps identified."
    split_method = "none"

    # --- Layer 1: Deterministic separator (highest priority) ---
    if DETERMINISTIC_SEPARATOR in tailored_cv:
        cv_content, gap_analysis = tailored_cv.split(DETERMINISTIC_SEPARATOR, 1)
        gap_analysis = "## Gap Analysis\n" + gap_analysis.strip()
        split_method = "deterministic_separator"
        print(f"[SPLIT] Used deterministic separator")
    else:
        # --- Layer 2: Fallback gap markers (expanded list) ---
        gap_markers = [
            "## Gap Analysis",
            "## Análisis de Ajuste al Puesto",
            "## Análisis de Brechas",
            "## Analyse des Écarts",
            "## Lückenanalyse",
            "## Analisi delle Lacune",
            "## Análise de Lacunas",
            "## Análisis de Gaps y Recomendaciones",
            "## Análisis de Gaps",
            "## Gaps y Recomendaciones",
            "## Recommendations",
            "## Recomendaciones",
            "## Gap Analysis and Recommendations",
        ]

        for marker in gap_markers:
            if marker in tailored_cv:
                cv_content, gap_analysis = tailored_cv.split(marker, 1)
                gap_analysis = marker + gap_analysis
                split_method = f"marker:{marker}"
                print(f"[SPLIT] Used fallback marker: {marker}")
                break

    # --- Layer 3: Post-split forbidden content validation ---
    forbidden_patterns = [
        "gap analysis", "análisis de gaps", "análisis de brechas",
        "análisis de ajuste", "recomendaciones finales", "recommendations",
        "mitigación", "fortalezas compensatorias", "fortalezas excepcionales",
        "gaps identificados", "gaps y recomendaciones", "sugerencia cv",
        "sugerencia:", "durante la entrevista", "fit prácticamente perfecto",
        "match rating", "% match",
    ]

    cv_lower = cv_content.lower()
    first_forbidden_pos = len(cv_content)
    first_forbidden_pattern = None

    for pattern in forbidden_patterns:
        pos = cv_lower.find(pattern)
        if pos != -1 and pos < first_forbidden_pos:
            first_forbidden_pos = pos
            first_forbidden_pattern = pattern

    if first_forbidden_pattern is not None:
        line_start = cv_content.rfind('\n', 0, first_forbidden_pos)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1

        leaked_content = cv_content[line_start:]
        cv_content = cv_content[:line_start].rstrip()
        gap_analysis = leaked_content.strip() + "\n\n" + gap_analysis
        print(f"WARNING: Forbidden pattern '{first_forbidden_pattern}' found in CV at position {first_forbidden_pos}. "
              f"Stripped {len(leaked_content)} characters from CV content.")
        split_method += f"+layer3_strip:{first_forbidden_pattern}"

    print(f"[SPLIT] Final method: {split_method}")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save CV
    with open(output_path, 'w') as f:
        f.write(cv_content.strip())

    # Save gap analysis separately
    gap_path = output_path.parent / 'cv_gaps.txt'
    with open(gap_path, 'w') as f:
        f.write(gap_analysis)

    print(f"\nTailored CV saved to: {output_path}")
    print(f"Gap analysis saved to: {gap_path}")

    # Show gap analysis
    print("\n" + "="*60)
    print(gap_analysis)
    print("="*60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
