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
@patch("client.GithubOrgClient.get_json")  # patch where it is used
def test_org(self, org_name, mock_get_json):
    expected = {"login": org_name}
    mock_get_json.return_value = expected

    client = GithubOrgClient(org_name)
    result = client.org  # property access

    mock_get_json.assert_called_once_with(
        f"https://api.github.com/orgs/{org_name}"
    )
    self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
