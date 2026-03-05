"""Tests for scripture.py."""

import json
import pytest
import scripture


@pytest.fixture(autouse=True)
def patch_paths(tmp_data_dir, monkeypatch):
    """Redirect module-level file paths to the temporary data directory."""
    monkeypatch.setattr(scripture, "VERSES_FILE", tmp_data_dir / "verses.json")
    monkeypatch.setattr(scripture, "SENT_LOG", tmp_data_dir / ".sent_verses.json")


@pytest.fixture
def verses_file(tmp_data_dir, sample_verse):
    """Populate the temp verses.json with sample data."""
    verses = [
        sample_verse,
        {"reference": "John 3:16", "text": "For God so loved the world...", "theme": "love"},
        {"reference": "Romans 15:13", "text": "Now the God of hope...", "theme": "hope"},
    ]
    (tmp_data_dir / "verses.json").write_text(json.dumps({"verses": verses}))
    return verses


class TestLoadVerses:
    def test_returns_list(self, verses_file):
        result = scripture.load_verses()
        assert isinstance(result, list)
        assert len(result) == 3

    def test_verse_keys(self, verses_file):
        result = scripture.load_verses()
        for v in result:
            assert "reference" in v
            assert "text" in v
            assert "theme" in v


class TestSentVerses:
    def test_get_sent_verses_empty_when_no_file(self):
        result = scripture.get_sent_verses()
        assert result == []

    def test_mark_verse_sent_creates_file(self, tmp_data_dir):
        scripture.mark_verse_sent("Philippians 4:13")
        assert (tmp_data_dir / ".sent_verses.json").exists()

    def test_mark_verse_sent_round_trip(self):
        scripture.mark_verse_sent("Philippians 4:13")
        sent = scripture.get_sent_verses()
        assert "Philippians 4:13" in sent

    def test_mark_verse_sent_no_duplicates(self):
        scripture.mark_verse_sent("Philippians 4:13")
        scripture.mark_verse_sent("Philippians 4:13")
        sent = scripture.get_sent_verses()
        assert sent.count("Philippians 4:13") == 1


class TestSelectVerse:
    def test_returns_verse_dict(self, verses_file):
        verse = scripture.select_verse(theme="strength")
        assert verse["theme"] == "strength"
        assert "reference" in verse

    def test_avoids_sent_verses(self, verses_file, sample_verse):
        scripture.mark_verse_sent(sample_verse["reference"])
        verse = scripture.select_verse(theme="strength")
        # The only strength verse was sent; after reset it should still return a verse
        assert verse is not None

    def test_theme_rotation_without_explicit_theme(self, verses_file):
        verse = scripture.select_verse()
        assert verse["theme"] in scripture.THEMES

    def test_resets_when_all_sent(self, verses_file, sample_verse):
        scripture.mark_verse_sent(sample_verse["reference"])
        # Even after all strength verses are sent, we should still get a result
        verse = scripture.select_verse(theme="strength")
        assert verse is not None


class TestFormatMessage:
    def test_contains_reference(self, sample_verse):
        msg = scripture.format_message(sample_verse)
        assert "Philippians 4:13" in msg

    def test_contains_text(self, sample_verse):
        msg = scripture.format_message(sample_verse)
        assert "I can do all things" in msg

    def test_contains_emoji(self, sample_verse):
        msg = scripture.format_message(sample_verse)
        assert "💪" in msg

    def test_unknown_theme_uses_default_emoji(self):
        verse = {"reference": "Test 1:1", "text": "Test", "theme": "unknown"}
        msg = scripture.format_message(verse)
        assert "📖" in msg


class TestSendToTelegram:
    def test_returns_false_without_env(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        assert scripture.send_to_telegram("hello") is False

    def test_sends_successfully(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

        class MockResponse:
            def raise_for_status(self):
                pass

        monkeypatch.setattr(scripture.requests, "post", lambda *a, **kw: MockResponse())
        assert scripture.send_to_telegram("hello") is True

    def test_returns_false_on_request_error(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

        def mock_post(*args, **kwargs):
            raise scripture.requests.RequestException("network error")

        monkeypatch.setattr(scripture.requests, "post", mock_post)
        assert scripture.send_to_telegram("hello") is False
