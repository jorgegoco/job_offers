#!/usr/bin/env python3
"""
Analyzes a job offer from URL or text.
Extracts requirements, keywords, tone, and company culture.
"""

import json
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

def scrape_job_url(url):
    """Scrape job posting from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    except requests.exceptions.RequestException as e:
        print(f"Error scraping URL: {e}", file=sys.stderr)
        return None

def analyze_with_llm(job_text):
    """Use Claude to analyze the job posting."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""Analyze this job posting and extract structured information.

Job Posting:
{job_text}

Please provide a JSON response with:
{{
    "language": "primary language of job posting (ISO 639-1 codes: 'en' for English, 'es' for Spanish, 'fr' for French, etc.)",
    "job_title": "exact title from posting",
    "company": "company name",
    "location": "location or remote status",
    "job_level": "entry/mid/senior/lead/etc",
    "required_skills": ["list of must-have skills"],
    "preferred_skills": ["list of nice-to-have skills"],
    "keywords": ["important terminology used in posting"],
    "tone": "formal/casual/enthusiastic/technical/etc",
    "culture_signals": ["indicators about company culture"],
    "key_responsibilities": ["main job duties"],
    "application_instructions": "any specific instructions for applying",
    "salary_range": "if mentioned, otherwise null",
    "gaps_to_watch": ["requirements that may be hard to match"]
}}

Be thorough and extract all relevant information."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract JSON from response
    response_text = message.content[0].text

    # Try to find JSON in the response
    start = response_text.find('{')
    end = response_text.rfind('}') + 1

    if start != -1 and end > start:
        json_str = response_text[start:end]
        return json.loads(json_str)
    else:
        raise ValueError("Could not extract JSON from LLM response")

def main():
    parser = argparse.ArgumentParser(description='Analyze a job offer')
    parser.add_argument('--url', help='Job posting URL')
    parser.add_argument('--text', help='Job posting text directly')
    parser.add_argument('--text-file', help='Path to file containing job posting text')
    parser.add_argument('--output', default='.tmp/job_applications/job_analysis.json',
                       help='Output JSON file path')

    args = parser.parse_args()

    # Get job text from various sources
    job_text = None

    if args.url:
        print(f"Scraping job from URL: {args.url}")
        job_text = scrape_job_url(args.url)
        if not job_text:
            print("Failed to scrape URL. Please provide text directly.", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        job_text = args.text
    elif args.text_file:
        with open(args.text_file, 'r') as f:
            job_text = f.read()
    else:
        print("Error: Must provide --url, --text, or --text-file", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    print("Analyzing job posting with LLM...")
    analysis = analyze_with_llm(job_text)

    # Add source information
    analysis['source'] = {
        'url': args.url if args.url else None,
        'raw_text': job_text[:500] + "..." if len(job_text) > 500 else job_text
    }

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save analysis
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"Analysis saved to: {output_path}")
    print(f"\nJob: {analysis['job_title']} at {analysis['company']}")
    print(f"Required skills: {', '.join(analysis['required_skills'][:5])}...")

    return 0

if __name__ == '__main__':
    sys.exit(main())
