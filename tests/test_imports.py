"""Basic tests to ensure modules can be imported."""

import importlib

import pytest


playwright_spec = importlib.util.find_spec("playwright")

if playwright_spec is None:  # pragma: no cover - dependency not installed in CI
    pytest.skip("playwright package is not available", allow_module_level=True)


def test_imports():
    """Ensure key modules can be imported without errors."""
    from src.linkedin_notion_migrator.config import Config  # noqa: F401
    from src.linkedin_notion_migrator.migrator import LinkedInNotionMigrator  # noqa: F401
    from src.linkedin_notion_migrator.linkedin_scraper import LinkedInScraper  # noqa: F401
    from src.linkedin_notion_migrator.notion_client import NotionClient  # noqa: F401
    from src.linkedin_notion_migrator.models import SavedPost  # noqa: F401

    assert True
