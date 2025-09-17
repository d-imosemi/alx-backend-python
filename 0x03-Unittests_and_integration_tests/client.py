#!/usr/bin/env python3
"""
client.py
Implements GithubOrgClient with license filtering.
"""

import requests
from typing import Dict, List


def get_json(url: str) -> Dict:
    """Fetch JSON from URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


class GithubOrgClient:
    """GithubOrgClient class."""

    ORG_URL = "https://api.github.com/orgs/{org}"

    def __init__(self, org_name: str) -> None:
        """Initialize client with org name."""
        self.org_name = org_name

    @property
    def org(self) -> Dict:
        """Fetch and return organization data."""
        url = self.ORG_URL.format(org=self.org_name)
        return get_json(url)

    @property
    def _public_repos_url(self) -> str:
        """Return the public repos URL from org payload."""
        return self.org.get("repos_url")

    def public_repos(self, license: str = None) -> List[str]:
        """
        Fetch public repositories.
        If license is provided, filter by license key.
        """
        repos = get_json(self._public_repos_url)
        names = []
        for repo in repos:
            if license is None:
                names.append(repo.get("name"))
            else:
                if self.has_license(repo, license):
                    names.append(repo.get("name"))
        return names

    @staticmethod
    def has_license(repo: Dict, license_key: str) -> bool:
        """Check if a repo has a given license key."""
        repo_license = repo.get("license")
        return repo_license is not None and repo_license.get("key") == license_key
