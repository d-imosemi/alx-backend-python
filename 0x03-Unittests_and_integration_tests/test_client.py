#!/usr/bin/env python3
"""
Unit tests for the GithubOrgClient class in client.py.

This module tests that the org, _public_repos_url, and public_repos
methods behave correctly, without making real HTTP requests. All
external calls are mocked using unittest.mock.
"""

import unittest
from unittest.mock import patch, PropertyMock, Mock
from parameterized import parameterized
from client import GithubOrgClient
from utils import get_json


class TestGithubOrgClient(unittest.TestCase):
    """
    TestGithubOrgClient contains unit tests for the GithubOrgClient
    class, verifying correct behavior of org, _public_repos_url, and
    public_repos methods while avoiding external HTTP requests.
    """

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch("client.get_json")
    def test_org(self, org_name, mock_get_json):
        """
        Test that GithubOrgClient.org returns the correct dictionary
        and that get_json is called exactly once with the proper URL.
        """
        expected = {"login": org_name}
        mock_get_json.return_value = expected

        client = GithubOrgClient(org_name)
        result = client.org  # property access

        mock_get_json.assert_called_once_with(
            f"https://api.github.com/orgs/{org_name}"
        )
        self.assertEqual(result, expected)

    def test_public_repos_url(self):
        """
        Test that GithubOrgClient._public_repos_url returns the correct
        repos_url extracted from the org property.
        """
        client = GithubOrgClient("test-org")
        payload = {"repos_url": "https://api.github.com/orgs/test-org/repos"}

        with patch.object(
            GithubOrgClient,
            "org",
            new_callable=PropertyMock,
            return_value=payload
        ):
            self.assertEqual(client._public_repos_url, payload["repos_url"])

    @patch("client.get_json")
    def test_public_repos(self, mock_get_json):
        """
        Test that GithubOrgClient.public_repos returns the correct list
        of repository names, and that _public_repos_url and get_json
        are called exactly once.
        """
        test_payload = [
            {"name": "repo1"},
            {"name": "repo2"},
        ]
        mock_get_json.return_value = test_payload
        client = GithubOrgClient("test-org")

        with patch.object(
            GithubOrgClient,
            "_public_repos_url",
            new_callable=PropertyMock,
            return_value="https://api.github.com/orgs/test-org/repos"
        ) as mock_url:
            result = client.public_repos()

            # Assert the returned repo names match the payload
            self.assertEqual(result, ["repo1", "repo2"])
            # Assert _public_repos_url property was accessed once
            mock_url.assert_called_once()
            # Assert get_json was called once with the mocked URL
            mock_get_json.assert_called_once_with(
                "https://api.github.com/orgs/test-org/repos"
            )


if __name__ == "__main__":
    unittest.main()
