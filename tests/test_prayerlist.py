"""Tests for prayerlist.py."""

import pytest
import prayerlist


@pytest.fixture(autouse=True)
def patch_paths(tmp_data_dir, monkeypatch):
    """Redirect module-level file paths to the temporary data directory."""
    monkeypatch.setattr(prayerlist, "DATA_DIR", tmp_data_dir)
    monkeypatch.setattr(prayerlist, "PRAYERS_FILE", tmp_data_dir / "prayers.json")


class TestLoadSavePrayers:
    def test_load_empty_prayers(self):
        result = prayerlist.load_prayers()
        assert result == []

    def test_save_and_load_round_trip(self, sample_prayer):
        prayerlist.save_prayers([sample_prayer])
        result = prayerlist.load_prayers()
        assert len(result) == 1
        assert result[0]["id"] == sample_prayer["id"]

    def test_save_creates_file(self, tmp_data_dir):
        (tmp_data_dir / "prayers.json").unlink()
        prayerlist.save_prayers([])
        assert (tmp_data_dir / "prayers.json").exists()


class TestAddPrayer:
    def test_returns_dict_with_expected_keys(self):
        prayer = prayerlist.add_prayer("Healing for my friend")
        assert "id" in prayer
        assert "text" in prayer
        assert "category" in prayer
        assert "date_added" in prayer
        assert "status" in prayer
        assert "date_answered" in prayer

    def test_defaults_to_other_category(self):
        prayer = prayerlist.add_prayer("General request")
        assert prayer["category"] == "other"

    def test_custom_category(self):
        prayer = prayerlist.add_prayer("Family healing", category="healing")
        assert prayer["category"] == "healing"

    def test_invalid_category_falls_back_to_other(self):
        prayer = prayerlist.add_prayer("Request", category="invalid_cat")
        assert prayer["category"] == "other"

    def test_status_is_active(self):
        prayer = prayerlist.add_prayer("Active request")
        assert prayer["status"] == "active"

    def test_date_answered_is_none(self):
        prayer = prayerlist.add_prayer("Active request")
        assert prayer["date_answered"] is None

    def test_persists_to_file(self):
        prayerlist.add_prayer("Persisted request")
        result = prayerlist.load_prayers()
        assert len(result) == 1


class TestRemovePrayer:
    def test_remove_existing_prayer(self, sample_prayer):
        prayerlist.save_prayers([sample_prayer])
        result = prayerlist.remove_prayer(sample_prayer["id"])
        assert result is True
        assert prayerlist.load_prayers() == []

    def test_remove_nonexistent_prayer(self):
        result = prayerlist.remove_prayer("nonexistent-id")
        assert result is False

    def test_remove_only_target_prayer(self, sample_prayer):
        other = prayerlist.add_prayer("Other prayer")
        prayerlist.save_prayers([sample_prayer, other])
        prayerlist.remove_prayer(sample_prayer["id"])
        remaining = prayerlist.load_prayers()
        assert len(remaining) == 1
        assert remaining[0]["id"] == other["id"]


class TestMarkAnswered:
    def test_mark_existing_prayer_answered(self, sample_prayer):
        prayerlist.save_prayers([sample_prayer])
        result = prayerlist.mark_answered(sample_prayer["id"])
        assert result is not None
        assert result["status"] == "answered"
        assert result["date_answered"] is not None

    def test_mark_nonexistent_prayer_returns_none(self):
        result = prayerlist.mark_answered("nonexistent-id")
        assert result is None

    def test_answered_date_is_set(self, sample_prayer):
        prayerlist.save_prayers([sample_prayer])
        result = prayerlist.mark_answered(sample_prayer["id"])
        assert len(result["date_answered"]) == 10  # ISO date: YYYY-MM-DD


class TestListPrayers:
    def test_list_active_prayers(self, sample_prayer):
        answered = {**sample_prayer, "id": "answered-id", "status": "answered",
                    "date_answered": "2026-01-05"}
        prayerlist.save_prayers([sample_prayer, answered])
        result = prayerlist.list_prayers("active")
        assert len(result) == 1
        assert result[0]["id"] == sample_prayer["id"]

    def test_list_answered_prayers(self, sample_prayer):
        answered = {**sample_prayer, "id": "answered-id", "status": "answered",
                    "date_answered": "2026-01-05"}
        prayerlist.save_prayers([sample_prayer, answered])
        result = prayerlist.list_prayers("answered")
        assert len(result) == 1
        assert result[0]["id"] == "answered-id"

    def test_list_all_prayers(self, sample_prayer):
        answered = {**sample_prayer, "id": "answered-id", "status": "answered",
                    "date_answered": "2026-01-05"}
        prayerlist.save_prayers([sample_prayer, answered])
        result = prayerlist.list_prayers("all")
        assert len(result) == 2

    def test_list_empty(self):
        result = prayerlist.list_prayers()
        assert result == []


class TestFormatReview:
    def test_returns_string(self, sample_prayer):
        prayerlist.save_prayers([sample_prayer])
        result = prayerlist.format_review()
        assert isinstance(result, str)

    def test_contains_review_header(self, sample_prayer):
        prayerlist.save_prayers([sample_prayer])
        result = prayerlist.format_review()
        assert "Weekly Prayer Review" in result

    def test_shows_active_count(self, sample_prayer):
        prayerlist.save_prayers([sample_prayer])
        result = prayerlist.format_review()
        assert "Active Prayers" in result

    def test_empty_list_message(self):
        result = prayerlist.format_review()
        assert "No active prayers" in result

    def test_contains_encouragement(self, sample_prayer):
        prayerlist.save_prayers([sample_prayer])
        result = prayerlist.format_review()
        assert "James 5:16" in result

    def test_shows_answered_this_week(self, sample_prayer):
        from datetime import date
        answered = {
            **sample_prayer, "id": "answered-id", "status": "answered",
            "date_answered": date.today().isoformat()
        }
        prayerlist.save_prayers([answered])
        result = prayerlist.format_review()
        assert "Answered This Week" in result


class TestSendReview:
    def test_returns_false_without_env(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        assert prayerlist.send_review() is False

    def test_sends_successfully(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

        class MockResponse:
            def raise_for_status(self):
                pass

        monkeypatch.setattr(prayerlist.requests, "post", lambda *a, **kw: MockResponse())
        assert prayerlist.send_review() is True
