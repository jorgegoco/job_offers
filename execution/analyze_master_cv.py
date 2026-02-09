#!/usr/bin/env python3
"""
Loads user profile data from resources/profile.json for CV generation.
Provides get_user_data() for reading and update_profile() for writing.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
import PyPDF2

PROFILE_PATH = Path(__file__).resolve().parent.parent / "resources" / "profile.json"


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file for metadata purposes."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Warning: Could not extract raw text from PDF: {e}", file=sys.stderr)
        return None


def get_user_data():
    """Load user profile from resources/profile.json.

    Returns a fresh dict each call (safe to mutate without affecting the source).
    """
    if not PROFILE_PATH.exists():
        print(f"Error: Profile not found: {PROFILE_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def update_profile(field_path, new_data):
    """Update a field in resources/profile.json.

    Args:
        field_path: Dot-notation path (e.g. "technical_skills.frameworks")
        new_data: Value to append (if target is list) or merge (if target is dict).
                  For lists, pass a list to extend or a single value to append.
    """
    if not PROFILE_PATH.exists():
        print(f"Error: Profile not found: {PROFILE_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)

    # Traverse to the target field
    keys = field_path.split(".")
    target = profile
    for key in keys[:-1]:
        if key not in target or not isinstance(target[key], dict):
            print(f"Error: Invalid path '{field_path}' — '{key}' not found or not a dict", file=sys.stderr)
            return False
        target = target[key]

    final_key = keys[-1]
    if final_key not in target:
        print(f"Error: Key '{final_key}' not found in '{'.'.join(keys[:-1]) or 'root'}'", file=sys.stderr)
        return False

    current = target[final_key]

    if isinstance(current, list):
        items = new_data if isinstance(new_data, list) else [new_data]
        existing_lower = {str(v).lower() for v in current}
        added = []
        for item in items:
            if str(item).lower() not in existing_lower:
                current.append(item)
                existing_lower.add(str(item).lower())
                added.append(item)
        if added:
            print(f"Added to {field_path}: {added}")
        else:
            print(f"No new items to add to {field_path} (all already present)")
    elif isinstance(current, dict):
        if not isinstance(new_data, dict):
            print(f"Error: Target '{field_path}' is a dict but new_data is not", file=sys.stderr)
            return False
        current.update(new_data)
        print(f"Merged into {field_path}: {list(new_data.keys())}")
    else:
        target[final_key] = new_data
        print(f"Set {field_path} = {new_data}")

    profile["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    return True


def main():
    parser = argparse.ArgumentParser(description='Load CV data from user profile')
    parser.add_argument('--cv', default='resources/job_applications/master_cv.pdf',
                       help='Path to master CV PDF (used for raw text metadata only)')
    parser.add_argument('--output', default='.tmp/job_applications/cv_database.json',
                       help='Output JSON file path')

    args = parser.parse_args()

    cv_path = Path(args.cv)
    output_path = Path(args.output)

    print(f"Loading profile from: {PROFILE_PATH}")

    # Load profile data
    cv_database = get_user_data()

    # Extract raw text from PDF if available (for metadata only)
    raw_text = None
    if cv_path.exists():
        print(f"Extracting raw text from: {cv_path}")
        raw_text = extract_text_from_pdf(cv_path)
        if raw_text:
            print(f"  Extracted {len(raw_text)} characters for metadata")
    else:
        print(f"Note: CV file not found at {cv_path} (raw text metadata will be empty)")

    # Add metadata
    cv_database['metadata'] = {
        'source_file': str(cv_path),
        'raw_text': raw_text or "",
        'data_source': 'profile.json'
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save database
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cv_database, f, indent=2, ensure_ascii=False)

    print(f"\nCV database saved to: {output_path}")
    print(f"\nUser information:")
    print(f"  Name: {cv_database['personal_info']['name']}")
    print(f"  Work experiences: {len(cv_database['work_experience'])}")
    print(f"  Education entries: {len(cv_database['education'])}")
    print(f"\nTo update your profile, edit: {PROFILE_PATH}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
