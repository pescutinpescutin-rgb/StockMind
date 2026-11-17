import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import data
import db


class XFeedTests(unittest.TestCase):
    def test_missing_bearer_token_returns_setup_message(self):
        with patch.dict(os.environ, {"X_BEARER_TOKEN": ""}), patch.object(
            data, "_x_api_get"
        ) as api_get:
            result = data.get_x_posts("@dayxtrading")

        self.assertEqual(result["posts"], [])
        self.assertIn("X_BEARER_TOKEN", result["error"])
        api_get.assert_not_called()

    def test_fetches_posts_and_deduplicates_handles(self):
        responses = [
            {"data": [{"id": "42", "username": "dayxtrading"}]},
            {
                "data": [
                    {
                        "id": "1001",
                        "text": "Market update",
                        "created_at": "2026-11-17T14:00:00Z",
                    }
                ]
            },
        ]
        with patch.dict(os.environ, {"X_BEARER_TOKEN": "test-token"}), patch.object(
            data, "_x_api_get", side_effect=responses
        ) as api_get:
            result = data.get_x_posts("@dayxtrading, dayxtrading")

        self.assertIsNone(result["error"])
        self.assertEqual(len(result["posts"]), 1)
        self.assertEqual(result["posts"][0]["username"], "dayxtrading")
        self.assertEqual(result["posts"][0]["url"], "https://x.com/dayxtrading/status/1001")
        self.assertEqual(api_get.call_count, 2)

    def test_social_posts_are_persisted_once(self):
        post = {
            "id": "1001",
            "username": "dayxtrading",
            "text": "Market update",
            "created_at": "2026-11-17T14:00:00Z",
            "url": "https://x.com/dayxtrading/status/1001",
        }
        original_db_path = db.DB_PATH
        try:
            with tempfile.TemporaryDirectory() as directory:
                db.DB_PATH = Path(directory) / "test.db"
                self.assertEqual(db.save_social_posts([post]), 1)
                self.assertEqual(db.save_social_posts([post]), 0)
                self.assertEqual(db.get_social_posts()[0]["id"], "1001")
        finally:
            db.DB_PATH = original_db_path


if __name__ == "__main__":
    unittest.main()
