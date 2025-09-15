#!/usr/bin/env python3
"""
Unit tests for client.GithubOrgClient class.

This module tests that the org method correctly returns the
organization data by mocking get_json to avoid external HTTP
calls.
"""

import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """
    TestGithubOrgClient contains unit tests for the GithubOrgClient
    class, verifying that the org method returns the expected
    organization data without performing real HTTP requests.
    """

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch("client.get_json")
    def test_org(self, org_name, mock_get_json):
        """
        Test that GithubOrgClient.org returns the correct value
        and that get_json is called exactly once with the proper URL.
        """
        # Setup mock return value
        expected = {"login": org_name}
        mock_get_json.return_value = expected

        client = GithubOrgClient(org_name)
        result = client.org

        # Assert get_json called once with the correct URL
        mock_get_json.assert_called_once_with(
            f"https://api.github.com/orgs/{org_name}"
        )

        # Assert the returned value is as expected
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
