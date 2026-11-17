import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from user_store import GuestStore, SupabaseStore


class GuestStoreTests(unittest.TestCase):
    def test_guest_data_is_isolated_by_session_state(self):
        first_guest = GuestStore({})
        second_guest = GuestStore({})

        first_guest.add_ticker("aapl")
        first_guest.add_position("aapl", 3, 100)
        first_guest.add_alert("aapl", "above", 120)

        self.assertEqual(first_guest.get_watchlist(), ["AAPL"])
        self.assertEqual(len(first_guest.get_portfolio()), 1)
        self.assertEqual(len(first_guest.get_alerts()), 1)
        self.assertEqual(second_guest.get_watchlist(), [])
        self.assertEqual(second_guest.get_portfolio(), [])
        self.assertEqual(second_guest.get_alerts(), [])

    def test_guest_positions_keep_weighted_average_cost_and_reject_overselling(self):
        store = GuestStore({})
        store.add_position("aapl", 10, 100)
        store.add_position("aapl", 2, 130)
        store.add_position("aapl", -2, 0)

        position = store.get_portfolio()[0]
        self.assertEqual(position["shares"], 10)
        self.assertEqual(position["avg_cost"], 105)

        with self.assertRaises(ValueError):
            store.add_position("aapl", -11, 0)


class SupabaseStoreTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.query = MagicMock()
        self.query.select.return_value = self.query
        self.query.eq.return_value = self.query
        self.query.order.return_value = self.query
        self.query.upsert.return_value = self.query
        self.query.execute.return_value = SimpleNamespace(data=[])
        self.client.table.return_value = self.query
        self.store = SupabaseStore(self.client, "user-1")

    def test_watchlist_reads_are_scoped_to_authenticated_user(self):
        self.query.execute.return_value = SimpleNamespace(
            data=[{"symbol": "AAPL"}]
        )

        self.assertEqual(self.store.get_watchlist(), ["AAPL"])
        self.query.eq.assert_called_once_with("user_id", "user-1")

    def test_buy_updates_weighted_average_cost(self):
        self.query.execute.return_value = SimpleNamespace(
            data=[{"shares": 10, "avg_cost": 100}]
        )

        self.store.add_position("aapl", 2, 130)

        payload = self.query.upsert.call_args.args[0]
        self.assertEqual(payload["symbol"], "AAPL")
        self.assertEqual(payload["shares"], 12)
        self.assertEqual(payload["avg_cost"], 105)
        self.assertEqual(payload["user_id"], "user-1")


if __name__ == "__main__":
    unittest.main()
