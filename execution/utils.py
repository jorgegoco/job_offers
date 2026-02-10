"""Shared utility functions for execution scripts."""

import json


def load_json(file_path):
    """Load JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def load_markdown(file_path):
    """Load markdown file."""
    with open(file_path, 'r') as f:
        return f.read()
