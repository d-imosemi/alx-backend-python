#!/usr/bin/env python3
"""
Minimal utils module for testing GithubOrgClient.
"""

import requests
from typing import Any, Dict


def get_json(url: str) -> Dict[str, Any]:
    """Perform HTTP GET request and return JSON response."""
    response = requests.get(url)
    return response.json()

