#!/usr/bin/env python3
"""
Unit tests for utils.py functions and decorators.

This module includes test cases for access_nested_map, get_json,
and memoize. It ensures correct functionality, error handling,
and caching behavior. All tests follow pycodestyle conventions.
"""

import unittest
from parameterized import parameterized
from unittest.mock import patch, Mock
from utils import access_nested_map, get_json, memoize


class TestAccessNestedMap(unittest.TestCase):
    """
    TestAccessNestedMap contains unit tests for the
    access_nested_map function, verifying correct retrieval
    of nested values and proper exception handling when keys
    are missing.
    """

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(self, nested_map, path, expected):
        """Test that access_nested_map returns expected values."""
        self.assertEqual(access_nested_map(nested_map, path), expected)

    @parameterized.expand([
        ({}, ("a",)),
        ({"a": 1}, ("a", "b")),
    ])
    def test_access_nested_map_exception(self, nested_map, path):
        """Test that access_nested_map raises KeyError as expected."""
        with self.assertRaises(KeyError) as cm:
            access_nested_map(nested_map, path)
        self.assertEqual(str(cm.exception), repr(path[-1]))


class TestGetJson(unittest.TestCase):
    """
    TestGetJson contains unit tests for the get_json function,
    ensuring it correctly calls requests.get and returns the
    expected JSON payload without performing real HTTP requests.
    """

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    def test_get_json(self, test_url, test_payload):
        """Test that get_json returns expected JSON payload."""
        with patch("utils.requests.get") as mock_get:
            mock_resp = Mock()
            mock_resp.json.return_value = test_payload
            mock_get.return_value = mock_resp

            result = get_json(test_url)

            mock_get.assert_called_once_with(test_url)
            self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """
    TestMemoize contains unit tests for the memoize decorator.
    It ensures that methods decorated with memoize only execute
    once and subsequent calls return the cached result without
    calling the original method again.
    """

    def test_memoize(self):
        """Test that memoize caches method results correctly."""

        class TestClass:
            """Helper class with a method and memoized property."""

            def a_method(self):
                """Return a fixed integer value for testing."""
                return 42

            @memoize
            def a_property(self):
                """Return result of a_method, cached via memoize."""
                return self.a_method()

        with patch.object(TestClass, "a_method",
                          return_value=42) as mock_method:
            obj = TestClass()
            self.assertEqual(obj.a_property, 42)
            self.assertEqual(obj.a_property, 42)
            mock_method.assert_called_once()
