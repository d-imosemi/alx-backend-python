#!/usr/bin/env python3
"""
Unit tests for GithubOrgClient class in client module.
"""

import unittest
from unittest.mock import patch, PropertyMock
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """Unit tests for the GithubOrgClient class."""

    @patch("client.get_json")
    def test_public_repos(self, mock_get_json):
        """
        Test that GithubOrgClient.public_repos returns the correct list
        of repository names and that _public_repos_url and get_json
        are called exactly once.
        """
        # Mocked payload returned by get_json
        test_payload = [
            {"name": "repo1"},
            {"name": "repo2"},
        ]
        mock_get_json.return_value = test_payload

        client = GithubOrgClient("test-org")

        # Mock _public_repos_url property
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
