#!/usr/bin/env python3
"""
Generates a tailored cover letter for a specific job offer.
Matches job tone, highlights key experiences, includes call to action.
"""

import json
import sys
import argparse
from pathlib import Path
import anthropic
import os
from dotenv import load_dotenv

from execution.utils import load_json, load_markdown

load_dotenv()

def generate_cover_letter(job_analysis, tailored_cv, user_comments, length_constraint="approximately 300-400 words", iteration=1, refinement_feedback=''):
    """Use Claude to generate cover letter."""
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
- Generate the ENTIRE cover letter in {language_name} language (language code: '{job_language}')
- If '{job_language}' is 'es', write ALL content in Spanish
- If '{job_language}' is 'en', write ALL content in English
- Match linguistic conventions and professional writing style of the target language
- Use native terminology and expressions
"""

    # Build iteration context if this is a refinement
    iteration_context = ""
    if iteration > 1 and refinement_feedback:
        iteration_context = f"""
REFINEMENT ITERATION {iteration}:
This is iteration {iteration} of the cover letter. The user reviewed the previous version and provided the following feedback:

PREVIOUS ITERATION FEEDBACK:
{refinement_feedback}

CRITICAL: Address the feedback above while maintaining the overall professionalism and persuasiveness of the letter.
Focus on the specific changes requested without compromising other strong elements from the previous version.
"""

    # --- System message: stable CV content (cached across iterations) ---
    system_content = [
        {
            "type": "text",
            "text": "You are an expert cover letter writer. You will be given the candidate's tailored CV below. Use it as the basis for generating compelling cover letters."
        },
        {
            "type": "text",
            "text": f"CANDIDATE'S TAILORED CV FOR THIS JOB:\n{tailored_cv}",
            "cache_control": {"type": "ephemeral"}
        }
    ]

    # --- User message: job-specific content (changes per iteration) ---
    user_prompt = f"""Generate a compelling cover letter for this job application.
{language_instruction}
{iteration_context}

JOB ANALYSIS:
{json.dumps(job_analysis, indent=2)}

USER'S SPECIFIC COMMENTS (HIGH PRIORITY - INCORPORATE PROMINENTLY):
{user_comments}

CRITICAL INSTRUCTIONS FOR USER COMMENTS:
1. Treat user comments as PRIMARY DIRECTIVES for the cover letter focus
2. If user says "emphasize X", center the letter narrative around X
3. If user says "mention specific experience Y", weave Y into the letter naturally
4. If user provides tone guidance, follow it precisely
5. User knows what resonates with this employer - prioritize their insights

GENERAL REQUIREMENTS:
1. Maximum 1 page ({length_constraint})
2. Match the tone from job analysis (formal/casual/enthusiastic/technical)
3. Structure:
   - Opening: Why this specific role and company (show you've researched them)
   - Body: 2-3 key experiences that directly address main job requirements
   - Closing: Clear call to action and enthusiasm
4. Incorporate user's specified angles naturally and prominently
5. Use company and role terminology from the job posting
6. Be authentic and specific, not generic
7. Show enthusiasm without being over-the-top

OUTPUT FORMAT:
Return a markdown-formatted cover letter ready to be converted to PDF.

Do NOT include:
- Address blocks (will be added during PDF formatting)
- Date (will be added during PDF formatting)

Start with:
## [Job Title] at [Company Name]

Then the letter content.
"""

    message = client.messages.create(
        model=os.getenv("MODEL_GENERATION", "claude-sonnet-4-5-20250929"),
        max_tokens=4000,
        system=system_content,
        messages=[{"role": "user", "content": user_prompt}]
    )

    return message.content[0].text

def main():
    parser = argparse.ArgumentParser(description='Generate cover letter')
    parser.add_argument('--job-analysis', default='.tmp/job_applications/job_analysis.json',
                       help='Path to job analysis JSON')
    parser.add_argument('--tailored-cv', default='.tmp/job_applications/tailored_cv.md',
                       help='Path to tailored CV markdown')
    parser.add_argument('--comments', default='',
                       help='User comments on angles to emphasize')
    parser.add_argument('--output', default='.tmp/job_applications/cover_letter.md',
                       help='Output markdown file path')
    parser.add_argument('--max-words', type=int, default=None,
                       help='Maximum word count (e.g., 300)')
    parser.add_argument('--max-chars', type=int, default=None,
                       help='Maximum character count (e.g., 1500)')
    parser.add_argument('--iteration', type=int, default=1,
                       help='Iteration number for refinement tracking (default: 1)')
    parser.add_argument('--refinement-feedback', default='',
                       help='User feedback from previous iteration for refinement')

    args = parser.parse_args()

    # Validate length constraints (only one should be specified)
    if args.max_words and args.max_chars:
        print("Error: Specify either --max-words or --max-chars, not both", file=sys.stderr)
        sys.exit(1)

    # Build length constraint string
    if args.max_words:
        length_constraint = f"approximately {args.max_words} words"
    elif args.max_chars:
        length_constraint = f"approximately {args.max_chars} characters"
    else:
        # Default: 300-400 words
        length_constraint = "approximately 300-400 words"

    # Load inputs
    job_path = Path(args.job_analysis)
    cv_path = Path(args.tailored_cv)

    if not job_path.exists():
        print(f"Error: Job analysis not found: {job_path}", file=sys.stderr)
        print("Run analyze_job_offer.py first", file=sys.stderr)
        sys.exit(1)

    if not cv_path.exists():
        print(f"Error: Tailored CV not found: {cv_path}", file=sys.stderr)
        print("Run generate_tailored_cv.py first", file=sys.stderr)
        sys.exit(1)

    print("Loading job analysis...")
    job_analysis = load_json(job_path)

    print("Loading tailored CV...")
    tailored_cv = load_markdown(cv_path)

    print("Generating cover letter with LLM...")
    print(f"Job: {job_analysis['job_title']} at {job_analysis['company']}")
    print(f"Length: {length_constraint}")
    if args.iteration > 1:
        print(f"Iteration: {args.iteration} (refinement)")
        if args.refinement_feedback:
            print(f"Refinement feedback: {args.refinement_feedback[:100]}...")
    if args.comments:
        print(f"User comments: {args.comments}")

    cover_letter = generate_cover_letter(job_analysis, tailored_cv, args.comments, length_constraint, args.iteration, args.refinement_feedback)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save cover letter
    with open(output_path, 'w') as f:
        f.write(cover_letter)

    print(f"\nCover letter saved to: {output_path}")

    # Show preview
    print("\n" + "="*60)
    print("PREVIEW:")
    print("="*60)
    lines = cover_letter.split('\n')
    preview_lines = lines[:30] if len(lines) > 30 else lines
    print('\n'.join(preview_lines))
    if len(lines) > 30:
        print("\n[...truncated...]")
    print("="*60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
