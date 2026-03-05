"""Tests for theologian.py."""

import json
import pytest
import theologian


@pytest.fixture(autouse=True)
def patch_paths(tmp_data_dir, monkeypatch):
    """Redirect module-level file paths to the temporary data directory."""
    monkeypatch.setattr(theologian, "THEOLOGIANS_FILE", tmp_data_dir / "theologians.json")
    monkeypatch.setattr(theologian, "SENT_LOG", tmp_data_dir / ".sent_quotes.json")


@pytest.fixture
def quotes_file(tmp_data_dir, sample_quote):
    """Populate the temp theologians.json with sample data."""
    quotes = [
        sample_quote,
        {
            "text": "Faith is to believe what you do not see.",
            "author": "Augustine of Hippo",
            "source": "Sermones",
            "theme": "faith",
        },
        {
            "text": "To one who has faith, no explanation is necessary.",
            "author": "Thomas Aquinas",
            "source": "attributed",
            "theme": "faith",
        },
    ]
    (tmp_data_dir / "theologians.json").write_text(json.dumps({"quotes": quotes}))
    return quotes


class TestLoadQuotes:
    def test_returns_list(self, quotes_file):
        result = theologian.load_quotes()
        assert isinstance(result, list)
        assert len(result) == 3

    def test_quote_keys(self, quotes_file):
        result = theologian.load_quotes()
        for q in result:
            assert "text" in q
            assert "author" in q


class TestSentQuotes:
    def test_get_sent_quotes_empty_when_no_file(self):
        result = theologian.get_sent_quotes()
        assert result == []

    def test_mark_quote_sent_creates_file(self, tmp_data_dir):
        theologian.mark_quote_sent(0)
        assert (tmp_data_dir / ".sent_quotes.json").exists()

    def test_mark_quote_sent_round_trip(self):
        theologian.mark_quote_sent(0)
        sent = theologian.get_sent_quotes()
        assert 0 in sent

    def test_mark_quote_sent_no_duplicates(self):
        theologian.mark_quote_sent(0)
        theologian.mark_quote_sent(0)
        sent = theologian.get_sent_quotes()
        assert sent.count(0) == 1


class TestSelectQuote:
    def test_returns_index_and_dict(self, quotes_file):
        index, quote = theologian.select_quote()
        assert isinstance(index, int)
        assert "text" in quote
        assert "author" in quote

    def test_avoids_sent_quotes(self, quotes_file):
        theologian.mark_quote_sent(0)
        theologian.mark_quote_sent(1)
        index, quote = theologian.select_quote()
        assert index == 2

    def test_resets_when_all_sent(self, quotes_file):
        for i in range(3):
            theologian.mark_quote_sent(i)
        index, quote = theologian.select_quote()
        assert quote is not None
        assert "text" in quote


class TestFormatMessage:
    def test_contains_quote_text(self, sample_quote):
        msg = theologian.format_message(sample_quote)
        assert "Thou hast made us for thyself" in msg

    def test_contains_author(self, sample_quote):
        msg = theologian.format_message(sample_quote)
        assert "Augustine of Hippo" in msg

    def test_contains_source_when_not_attributed(self, sample_quote):
        msg = theologian.format_message(sample_quote)
        assert "Confessions" in msg

    def test_does_not_include_attributed_source(self):
        quote = {
            "text": "Test quote.", "author": "Author",
            "source": "attributed", "theme": "faith"
        }
        msg = theologian.format_message(quote)
        assert "attributed" not in msg

    def test_includes_reflection_when_provided(self, sample_quote):
        msg = theologian.format_message(sample_quote, reflection="What draws you to rest?")
        assert "What draws you to rest?" in msg

    def test_no_reflect_section_without_reflection(self, sample_quote):
        msg = theologian.format_message(sample_quote, reflection=None)
        assert "Reflect:" not in msg

    def test_contains_emoji(self, sample_quote):
        msg = theologian.format_message(sample_quote)
        assert "💭" in msg


class TestGenerateReflection:
    def test_returns_none_on_connection_error(self, sample_quote, monkeypatch):
        def mock_post(*args, **kwargs):
            raise theologian.requests.RequestException("connection refused")

        monkeypatch.setattr(theologian.requests, "post", mock_post)
        result = theologian.generate_reflection(sample_quote)
        assert result is None

    def test_returns_reflection_text_on_success(self, sample_quote, monkeypatch):
        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "choices": [{"message": {"content": "  How does rest in God feel to you?  "}}]
                }

        monkeypatch.setattr(theologian.requests, "post", lambda *a, **kw: MockResponse())
        result = theologian.generate_reflection(sample_quote)
        assert result == "How does rest in God feel to you?"


class TestSendToTelegram:
    def test_returns_false_without_env(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        assert theologian.send_to_telegram("hello") is False

    def test_sends_successfully(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

        class MockResponse:
            def raise_for_status(self):
                pass

        monkeypatch.setattr(theologian.requests, "post", lambda *a, **kw: MockResponse())
        assert theologian.send_to_telegram("hello") is True

    def test_returns_false_on_request_error(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

        def mock_post(*args, **kwargs):
            raise theologian.requests.RequestException("network error")

        monkeypatch.setattr(theologian.requests, "post", mock_post)
        assert theologian.send_to_telegram("hello") is False
