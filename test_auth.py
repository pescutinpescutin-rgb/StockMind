import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from auth import delete_authenticated_user, restore_auth_session, save_auth_session


class AuthTests(unittest.TestCase):
    def test_saves_only_session_tokens(self):
        session = SimpleNamespace(access_token="access", refresh_token="refresh")

        self.assertEqual(
            save_auth_session(session),
            {"access_token": "access", "refresh_token": "refresh"},
        )

    def test_restores_only_a_verified_session(self):
        client = Mock()
        client.auth.get_user.return_value.user.id = "user-1"
        session = SimpleNamespace(access_token="new-access", refresh_token="new-refresh")
        client.auth.get_session.return_value = session

        user, restored_session = restore_auth_session(
            client,
            {"access_token": "old-access", "refresh_token": "old-refresh"},
        )

        client.auth.set_session.assert_called_once_with("old-access", "old-refresh")
        self.assertEqual(user.id, "user-1")
        self.assertIs(restored_session, session)

    def test_account_deletion_is_limited_to_verified_user(self):
        client = Mock()
        client.auth.get_user.return_value.user.id = "user-1"
        admin_client = Mock()

        with patch("auth.create_admin_client", return_value=admin_client):
            delete_authenticated_user(client, "user-1")

        admin_client.auth.admin.delete_user.assert_called_once_with("user-1")

    def test_account_deletion_rejects_another_user_id(self):
        client = Mock()
        client.auth.get_user.return_value.user.id = "user-1"

        with patch("auth.create_admin_client") as create_admin:
            with self.assertRaises(ValueError):
                delete_authenticated_user(client, "user-2")

        create_admin.assert_not_called()


if __name__ == "__main__":
    unittest.main()
