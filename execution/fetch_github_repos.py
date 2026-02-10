#!/usr/bin/env python3
"""
GitHub repo data for CV enrichment.

Loads curated repos from resources/github_repos.json (no API calls needed).
Optionally selects job-relevant repos via LLM and enriches with README content.

GitHub token (.env GITHUB_TOKEN) only needed for:
  - README fetching (inside select_relevant_repos)
  - --check-new discovery mode
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
import requests
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_API = "https://api.github.com"
CURATED_REPOS_PATH = Path("resources/github_repos.json")


def _github_get(url, token, params=None, accept="application/vnd.github+json"):
    """Authenticated GitHub API GET request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return requests.get(url, headers=headers, params=params, timeout=15)


def load_curated_repos():
    """Load the curated repo list from resources/github_repos.json.

    Returns a list of repo dicts. No API calls, no token needed.
    """
    if not CURATED_REPOS_PATH.exists():
        print(f"Warning: {CURATED_REPOS_PATH} not found", file=sys.stderr)
        return []

    with open(CURATED_REPOS_PATH, "r") as f:
        return json.load(f)


def fetch_repo_readmes(repos):
    """Fetch README content for a short list of repos (3-5 max).

    Returns the same repos enriched with a 'readme_summary' key.
    If GITHUB_TOKEN is not set, returns repos with readme_summary=None.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN not set, skipping README fetch", file=sys.stderr)
        for repo in repos:
            repo["readme_summary"] = None
        return repos

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


def _check_for_new_repos(username):
    """Fetch repos from GitHub API and report any not in the curated list."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN required for --check-new", file=sys.stderr)
        sys.exit(1)

    curated_names = {r["name"] for r in load_curated_repos()}

    print(f"Fetching repos for {username} from GitHub API...")
    all_repos = []
    url = f"{GITHUB_API}/user/repos"
    params = {"type": "all", "sort": "pushed", "per_page": 100}

    while url:
        resp = _github_get(url, token, params=params)
        if resp.status_code != 200:
            print(f"Error: GitHub API returned {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
        all_repos.extend(resp.json())
        url = None
        params = None
        link_header = resp.headers.get("Link", "")
        for part in link_header.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
                break

    cutoff = datetime(2026, 2, 10, tzinfo=timezone.utc)
    new_repos = []
    for repo in all_repos:
        if repo.get("archived"):
            continue
        pushed_at = repo.get("pushed_at")
        if not pushed_at:
            continue
        dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        if dt > cutoff and repo["name"] not in curated_names:
            new_repos.append({
                "name": repo["name"],
                "pushed_at": pushed_at,
                "description": repo.get("description"),
                "language": repo.get("language"),
                "fork": repo.get("fork", False),
            })

    if new_repos:
        print(f"\nFound {len(new_repos)} new repo(s) not in curated list:\n")
        for r in new_repos:
            fork_tag = " [fork]" if r["fork"] else ""
            print(f"  {r['name']}{fork_tag} ({r['language'] or 'unknown'}) — pushed {r['pushed_at']}")
            if r["description"]:
                print(f"    {r['description']}")
        print(f"\nTo add: edit resources/github_repos.json manually.")
    else:
        print("No new repos found since 2026-02-10.")


def main():
    parser = argparse.ArgumentParser(description='GitHub repos for CV enrichment')
    parser.add_argument('--username',
                       help='GitHub username (required for --check-new)')
    parser.add_argument('--check-new', action='store_true',
                       help='Check GitHub API for repos not in curated list')
    parser.add_argument('--job-analysis',
                       help='Path to job analysis JSON for repo selection')

    args = parser.parse_args()

    if args.check_new:
        if not args.username:
            print("Error: --username required with --check-new", file=sys.stderr)
            sys.exit(1)
        _check_for_new_repos(args.username)
        return 0

    repos = load_curated_repos()
    print(f"Loaded {len(repos)} curated repos")

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
