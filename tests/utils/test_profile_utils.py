"""
Comprehensive tests for Profile Utils
=====================================

This module provides comprehensive test coverage for the profile utils service,
ensuring proper profile inheritance chain resolution and edge case handling.
"""

import unittest
from typing import Any, Dict

from core.services.profile_utils import profile_aliases, resolve_profile_chain


class TestProfileUtils(unittest.TestCase):
    """Test cases for profile utils functionality"""

    def test_resolve_profile_chain_simple(self) -> None:
        """Test resolving a simple profile with no inheritance"""
        profile = "fastapi/standard"
        profiles_config: Dict[str, Any] = {"profiles": ["fastapi/standard", "fastapi/standard"]}

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_with_inheritance(self) -> None:
        """Test resolving a profile with inheritance"""
        profile = "fastapi/standard"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "fastapi/standard",
                "fastapi/standard: inherits fastapi/standard",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_multiple_inheritance(self) -> None:
        """Test resolving a profile with multiple levels of inheritance"""
        profile = "fastapi/standard"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "fastapi/standard",
                "fastapi/standard: inherits fastapi/standard",
                "fastapi/standard: inherits fastapi/standard",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_circular_inheritance(self) -> None:
        """Test handling circular inheritance"""
        profile = "fastapi/circular1"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "fastapi/circular1: inherits fastapi/circular2",
                "fastapi/circular2: inherits fastapi/circular1",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        # Current implementation returns both profiles in the chain
        expected = ["fastapi/circular2", "fastapi/circular1"]
        self.assertEqual(result, expected)

    def test_resolve_profile_chain_no_profiles_config(self) -> None:
        """Test resolving profile when no profiles config exists"""
        profile = "fastapi/standard"
        profiles_config: Dict[str, Any] = {}

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_empty_profiles_list(self) -> None:
        """Test resolving profile when profiles list is empty"""
        profile = "fastapi/standard"
        profiles_config: Dict[str, Any] = {"profiles": []}

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_with_colon_in_name(self) -> None:
        """Test resolving profile name that contains colon"""
        profile = "fastapi/standard:v1.0"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "fastapi/standard:v1.0",
                "fastapi/standard: inherits fastapi/standard:v1.0",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        # Function strips colon part from profile names
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_inheritance_with_colon(self) -> None:
        """Test resolving inheritance with colon in inherited profile name"""
        profile = "fastapi/standard"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "fastapi/standard:v1.0",
                "fastapi/standard: inherits fastapi/standard:v1.0",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        # Function strips colon part from profile names and resolves inheritance
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_complex_inheritance_chain(self) -> None:
        """Test resolving a complex inheritance chain"""
        profile = "app/production"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "base",
                "web: inherits base",
                "api: inherits web",
                "fastapi: inherits api",
                "app/staging: inherits fastapi",
                "app/production: inherits app/staging",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["base", "web", "api", "fastapi", "app/staging", "app/production"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_no_inheritance_found(self) -> None:
        """Test resolving profile when no inheritance is found"""
        profile = "unknown/profile"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "fastapi/standard",
                "fastapi/standard: inherits fastapi/standard",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["unknown/profile"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_malformed_inheritance(self) -> None:
        """Test handling malformed inheritance declarations"""
        profile = "fastapi/standard"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "fastapi/standard",
                "fastapi/standard: inherits",  # Missing inherited profile
                "fastapi/standard: inherits fastapi/standard",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_whitespace_handling(self) -> None:
        """Test handling whitespace in profile declarations"""
        profile = "fastapi/standard"
        profiles_config: Dict[str, Any] = {
            "profiles": [
                "fastapi/standard",
                "  fastapi/standard  :  inherits  fastapi/standard  ",
            ]
        }

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["fastapi/standard"]

        self.assertEqual(result, expected)

    def test_resolve_profile_chain_empty_profile_name(self) -> None:
        """Test handling empty profile name"""
        profile = ""
        profiles_config: Dict[str, Any] = {"profiles": ["", "fastapi/standard"]}

        result = resolve_profile_chain(profile, profiles_config)
        expected: list[str] = []  # Empty profile name returns empty list

        self.assertEqual(result, expected)

    def test_profile_aliases_provide_dot_and_slash_variants(self) -> None:
        aliases = profile_aliases("fastapi.standard")
        self.assertEqual(aliases[0], "fastapi.standard")
        self.assertIn("fastapi/standard", aliases)

    def test_resolve_profile_chain_handles_dot_separated_profile(self) -> None:
        profile = "fastapi.ddd"
        profiles_config: Dict[str, Any] = {
            "profiles": {
                "fastapi/standard": {},
                "fastapi/ddd": {"inherits": "fastapi/standard"},
            }
        }

        result = resolve_profile_chain(profile, profiles_config)
        expected = ["fastapi/standard", "fastapi/ddd"]

        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
