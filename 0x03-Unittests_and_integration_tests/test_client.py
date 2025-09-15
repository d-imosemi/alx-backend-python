#!/usr/bin/env python3
"""
Self-contained unit tests for GithubOrgClient.
"""

import unittest
from unittest.mock import patch, PropertyMock
from parameterized import parameterized
from typing import Any, Dict, List


def get_json(url: str) -> Dict[str, Any]:
    """Stub function to simulate fetching JSON from a URL."""
    return {"stub": True}


class GithubOrgClient:
    """Minimal GithubOrgClient class for testing purposes."""

    def __init__(self, org_name: str) -> None:
        self.org_name = org_name

    @property
    def org(self) -> Dict[str, Any]:
        url = f"https://api.github.com/orgs/{self.org_name}"
        return get_json(url)

    @property
    def _public_repos_url(self) -> str:
        return self.org.get("repos_url", "")

    def public_repos(self) -> List[str]:
        repos = get_json(self._public_repos_url)
        return [repo.get("name") for repo in repos]

    @staticmethod
    def has_license(repo: Dict[str, Any], license_key: str) -> bool:
        return (
            repo.get("license") is not None
            and repo["license"].get("key") == license_key
        )


class TestGithubOrgClient(unittest.TestCase):
    """Unit tests for GithubOrgClient."""

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch("__main__.get_json")
    def test_org(self, org_name, mock_get_json):
        """Test org property with multiple org names."""
        expected = {"login": org_name}
        mock_get_json.return_value = expected

        client = GithubOrgClient(org_name)
        result = client.org

        mock_get_json.assert_called_once_with(
            f"https://api.github.com/orgs/{org_name}"
        )
        self.assertEqual(result, expected)

    def test_public_repos_url(self):
        """Test _public_repos_url property returns the correct URL."""
        client = GithubOrgClient("test-org")
        payload = {"repos_url": "https://api.github.com/orgs/test-org/repos"}

        with patch.object(
            GithubOrgClient,
            "org",
            new_callable=PropertyMock,
            return_value=payload
        ):
            self.assertEqual(client._public_repos_url, payload["repos_url"])

    @patch("__main__.get_json")
    def test_public_repos(self, mock_get_json):
        """Test public_repos returns correct repo names and mocks called once."""
        test_payload = [{"name": "repo1"}, {"name": "repo2"}]
        mock_get_json.return_value = test_payload
        client = GithubOrgClient("test-org")

        with patch.object(
            GithubOrgClient,
            "_public_repos_url",
            new_callable=PropertyMock,
            return_value="https://api.github.com/orgs/test-org/repos"
        ) as mock_url:
            result = client.public_repos()

            self.assertEqual(result, ["repo1", "repo2"])
            mock_url.assert_called_once()
            mock_get_json.assert_called_once_with(
                "https://api.github.com/orgs/test-org/repos"
            )


if __name__ == "__main__":
    unittest.main()

            self.assertEqual(result, ["repo1", "repo2"])
            mock_url.assert_called_once()
            mock_get_json.assert_called_once_with(
                "https://api.github.com/orgs/test-org/repos"
            )


if __name__ == "__main__":
    unittest.main()
