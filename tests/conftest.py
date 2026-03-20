"""Shared pytest fixtures for PrayerBot tests."""

import json
import pytest


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory with empty starter files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "prayers.json").write_text(json.dumps({"prayers": []}))
    (data_dir / "verses.json").write_text(json.dumps({"verses": []}))
    (data_dir / "theologians.json").write_text(json.dumps({"quotes": []}))
    return data_dir


@pytest.fixture
def sample_verse():
    """A sample verse object for testing."""
    return {
        "reference": "Philippians 4:13",
        "text": "I can do all things through Christ who strengthens me.",
        "theme": "strength"
    }


@pytest.fixture
def sample_prayer():
    """A sample prayer object for testing."""
    return {
        "id": "test-uuid-1234",
        "text": "Healing for a friend",
        "category": "healing",
        "date_added": "2026-01-01",
        "status": "active",
        "date_answered": None
    }


@pytest.fixture
def sample_quote():
    """A sample theologian quote for testing."""
    return {
        "text": "Thou hast made us for thyself, O Lord, and our heart is restless until it finds its rest in thee.",
        "author": "Augustine of Hippo",
        "source": "Confessions",
        "theme": "longing"
    }
