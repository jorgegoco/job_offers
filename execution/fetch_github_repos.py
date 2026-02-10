#!/usr/bin/env python3
"""
Fetches GitHub profile and repository data for CV enrichment.
Pulls repos, languages, topics, and README content from the GitHub API.

GitHub token (.env GITHUB_TOKEN) needs these fine-grained permissions:
  - Contents: read (for README access)
  - Metadata: read (for repo listing)
"""

import json
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone
import requests
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

CACHE_PATH = Path(".tmp/github_repos.json")
CACHE_MAX_AGE = 86400  # 24 hours
GITHUB_API = "https://api.github.com"


def _github_get(url, token, params=None, accept="application/vnd.github+json"):
    """Authenticated GitHub API GET request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return requests.get(url, headers=headers, params=params, timeout=15)


def _merge_technologies(primary_language, languages_dict, topics):
    """Merge language, languages breakdown, and topics into a deduplicated list."""
    seen_lower = set()
    result = []

    sources = []
    if primary_language:
        sources.append(primary_language)
    sources.extend(languages_dict.keys())
    sources.extend(topics)

    for tech in sources:
        key = tech.lower()
        if key not in seen_lower:
            seen_lower.add(key)
            result.append(tech)

    return result


def _is_recent(pushed_at, months=12):
    """Check if a date string is within the last N months."""
    if not pushed_at:
        return False
    pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta_days = (now - pushed).days
    return delta_days <= months * 30


def fetch_all_repos(username, force=False):
    """Fetch all repos for a user from GitHub API with caching.

    Returns a list of condensed repo summaries sorted by last activity.
    """
    # Check cache
    if not force and CACHE_PATH.exists():
        age = time.time() - CACHE_PATH.stat().st_mtime
        if age < CACHE_MAX_AGE:
            print(f"Loading from cache ({CACHE_PATH}, {int(age)}s old)")
            with open(CACHE_PATH, "r") as f:
                return json.load(f)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in .env", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching GitHub repos for: {username}")

    # Paginate through all repos
    all_repos = []
    url = f"{GITHUB_API}/user/repos"
    params = {"type": "all", "sort": "pushed", "per_page": 100}

    while url:
        resp = _github_get(url, token, params=params)
        if resp.status_code != 200:
            print(f"Error: GitHub API returned {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
        all_repos.extend(resp.json())

        # Follow pagination
        url = None
        params = None  # params only needed on first request
        link_header = resp.headers.get("Link", "")
        for part in link_header.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
                break

    # Filter and build condensed summaries
    results = []
    skipped_forks = 0
    skipped_archived = 0

    for repo in all_repos:
        # Skip archived
        if repo.get("archived"):
            skipped_archived += 1
            continue

        # Skip forks unless user has 5+ commits
        if repo.get("fork"):
            owner = repo["owner"]["login"]
            contrib_url = f"{GITHUB_API}/repos/{owner}/{repo['name']}/contributors"
            contrib_resp = _github_get(contrib_url, token)
            keep = False
            if contrib_resp.status_code == 200:
                for contributor in contrib_resp.json():
                    if contributor.get("login", "").lower() == username.lower():
                        if contributor.get("contributions", 0) >= 5:
                            keep = True
                        break
            if not keep:
                skipped_forks += 1
                continue

        # Fetch languages breakdown
        owner = repo["owner"]["login"]
        lang_url = f"{GITHUB_API}/repos/{owner}/{repo['name']}/languages"
        lang_resp = _github_get(lang_url, token)
        languages = lang_resp.json() if lang_resp.status_code == 200 else {}

        technologies = _merge_technologies(
            repo.get("language"),
            languages,
            repo.get("topics") or [],
        )

        results.append({
            "name": repo["name"],
            "description": repo.get("description"),
            "technologies": technologies,
            "html_url": repo["html_url"],
            "private": repo.get("private", False),
            "last_activity": repo.get("pushed_at"),
            "is_recent": _is_recent(repo.get("pushed_at")),
        })

    # Already sorted by pushed_at from API, but ensure it
    results.sort(key=lambda r: r.get("last_activity") or "", reverse=True)

    print(f"Found {len(results)} repos (skipped {skipped_forks} forks, {skipped_archived} archived)")

    # Save cache
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved to: {CACHE_PATH}")
    return results


def fetch_repo_readmes(repos):
    """Fetch README content for a short list of repos (3-5 max).

    Returns the same repos enriched with a 'readme_summary' key.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not found in .env", file=sys.stderr)
        sys.exit(1)

    for repo in repos:
        # Extract owner from html_url: https://github.com/owner/name
        parts = repo["html_url"].rstrip("/").split("/")
        owner = parts[-2]
        name = parts[-1]

        readme_url = f"{GITHUB_API}/repos/{owner}/{name}/readme"
        resp = _github_get(readme_url, token, accept="application/vnd.github.raw")

        if resp.status_code == 200:
            repo["readme_summary"] = resp.text[:1000]
        else:
            repo["readme_summary"] = None

    return repos


def select_relevant_repos(repos, job_analysis):
    """Use Claude to select 3-5 repos most relevant to a job posting.

    Returns selected repos enriched with 'relevance_reason' and README content.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Build condensed input (no READMEs, no URLs)
    summaries = []
    for r in repos:
        summaries.append({
            "name": r["name"],
            "description": r["description"],
            "technologies": r["technologies"],
            "last_activity": r["last_activity"],
            "is_recent": r["is_recent"],
        })

    job_context = {
        "job_title": job_analysis.get("job_title"),
        "company": job_analysis.get("company"),
        "required_skills": job_analysis.get("required_skills", []),
        "preferred_skills": job_analysis.get("preferred_skills", []),
    }

    prompt = f"""Select the 3-5 GitHub repositories most relevant to this job application.

JOB:
{json.dumps(job_context, indent=2)}

REPOSITORIES:
{json.dumps(summaries, indent=2)}

Return a JSON array of selected repos. Each entry must have:
- "name": exact repo name from the list
- "relevance_reason": 1-2 sentence explanation of why this repo is relevant

Prioritize:
1. Repos using technologies required by the job
2. Recent activity (is_recent: true) over stale repos
3. Repos with clear descriptions showing relevant work

Return ONLY the JSON array, no other text."""

    message = client.messages.create(
        model=os.getenv("MODEL_EXTRACTION", "claude-haiku-4-5-20251001"),
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text
    start = response_text.find("[")
    end = response_text.rfind("]") + 1
    if start == -1 or end <= start:
        raise ValueError("Could not extract JSON array from LLM response")

    selections = json.loads(response_text[start:end])

    # Match selections back to full repo objects
    repo_map = {r["name"]: r for r in repos}
    selected = []
    for sel in selections:
        name = sel["name"]
        if name in repo_map:
            repo = dict(repo_map[name])
            repo["relevance_reason"] = sel["relevance_reason"]
            selected.append(repo)

    print(f"Selected {len(selected)} repos: {', '.join(r['name'] for r in selected)}")

    # Enrich with README content
    selected = fetch_repo_readmes(selected)

    return selected


def main():
    parser = argparse.ArgumentParser(description='Fetch GitHub repos for CV enrichment')
    parser.add_argument('--username', required=True,
                       help='GitHub username')
    parser.add_argument('--force', action='store_true',
                       help='Force refresh, skip cache')
    parser.add_argument('--job-analysis',
                       help='Path to job analysis JSON for repo selection')

    args = parser.parse_args()

    # Fetch all repos
    repos = fetch_all_repos(args.username, force=args.force)

    # Optionally select relevant repos
    if args.job_analysis:
        job_path = Path(args.job_analysis)
        if not job_path.exists():
            print(f"Error: Job analysis not found: {job_path}", file=sys.stderr)
            sys.exit(1)

        with open(job_path, "r") as f:
            job_analysis = json.load(f)

        print(f"Selecting relevant repos for: {job_analysis.get('job_title', '?')} at {job_analysis.get('company', '?')}")
        selected = select_relevant_repos(repos, job_analysis)

        output_path = Path(".tmp/github_repos_selected.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(selected, f, indent=2)

        print(f"Saved to: {output_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
