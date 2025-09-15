#!/usr/bin/env python3
"""
GithubOrgClient module for interacting with GitHub API.

Provides a client class to fetch organization information,
public repository URLs, repository lists, and check licenses.
"""

from typing import Any, Dict, List
from utils import get_json


class GithubOrgClient:
    """
    GithubOrgClient represents a GitHub organization and provides
    methods to fetch org info, public repository URLs, and repository
    data.
    """

    def __init__(self, org_name: str) -> None:
        """Initialize the client with the organization name."""
        self.org_name = org_name

    @property
    def org(self) -> Dict[str, Any]:
        """Return the GitHub organization information as a dictionary."""
        url = f"https://api.github.com/orgs/{self.org_name}"
        return get_json(url)

    @property
    def _public_repos_url(self) -> str:
        """Return the public repos URL extracted from the org info."""
        return self.org.get("repos_url", "")

    def public_repos(self) -> List[str]:
        """Return a list of public repository names for the organization."""
        repos = get_json(self._public_repos_url)
        return [repo.get("name") for repo in repos]

    @staticmethod
    def has_license(repo: Dict[str, Any], license_key: str) -> bool:
        """Return True if the repository has the specified license."""
        return repo.get("license") is not None and \
               repo["license"].get("key") == license_key
