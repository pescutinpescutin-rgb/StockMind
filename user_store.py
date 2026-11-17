from datetime import datetime, timezone


class GuestStore:
    def __init__(self, session_state):
        self.data = session_state.setdefault(
            "_stockmind_guest_data",
            {"watchlist": [], "portfolio": {}, "alerts": [], "next_alert_id": 1},
        )

    def get_watchlist(self):
        return list(self.data["watchlist"])

    def add_ticker(self, symbol):
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Ticker symbol is required.")
        if symbol not in self.data["watchlist"]:
            self.data["watchlist"].insert(0, symbol)

    def remove_ticker(self, symbol):
        symbol = symbol.upper().strip()
        self.data["watchlist"] = [
            item for item in self.data["watchlist"] if item != symbol
        ]

    def get_portfolio(self):
        positions = self.data["portfolio"].values()
        return sorted(
            (dict(position) for position in positions),
            key=lambda position: position["updated_at"],
            reverse=True,
        )

    def add_position(self, symbol, shares, avg_cost):
        symbol = symbol.upper().strip()
        shares = float(shares)
        avg_cost = float(avg_cost)
        if not symbol or shares == 0 or avg_cost < 0:
            raise ValueError("Invalid position input.")

        existing = self.data["portfolio"].get(symbol)
        if existing is None:
            if shares < 0:
                raise ValueError("You cannot sell a ticker that is not in your portfolio.")
            new_shares = shares
            new_avg_cost = avg_cost
        else:
            current_shares = existing["shares"]
            if shares < 0 and abs(shares) > current_shares:
                raise ValueError("You cannot sell more shares than you currently own.")
            new_shares = current_shares + shares
            if new_shares <= 0:
                self.remove_position(symbol)
                return
            new_avg_cost = (
                (existing["avg_cost"] * current_shares + avg_cost * shares) / new_shares
                if shares > 0
                else existing["avg_cost"]
            )

        self.data["portfolio"][symbol] = {
            "symbol": symbol,
            "shares": new_shares,
            "avg_cost": new_avg_cost,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def remove_position(self, symbol):
        self.data["portfolio"].pop(symbol.upper().strip(), None)

    def add_alert(self, symbol, direction, target):
        symbol = symbol.upper().strip()
        direction = direction.lower().strip()
        target = float(target)
        if not symbol or direction not in {"above", "below"} or target <= 0:
            raise ValueError("Invalid alert input.")

        alert_id = self.data["next_alert_id"]
        self.data["next_alert_id"] += 1
        self.data["alerts"].insert(
            0,
            {
                "id": alert_id,
                "symbol": symbol,
                "direction": direction,
                "target": target,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def get_alerts(self):
        return [dict(alert) for alert in self.data["alerts"]]

    def remove_alert(self, alert_id):
        alert_id = int(alert_id)
        self.data["alerts"] = [
            alert for alert in self.data["alerts"] if alert["id"] != alert_id
        ]


class SupabaseStore:
    def __init__(self, client, user_id):
        self.client = client
        self.user_id = user_id

    def get_watchlist(self):
        response = (
            self.client.table("watchlist")
            .select("symbol")
            .eq("user_id", self.user_id)
            .order("added_at", desc=True)
            .execute()
        )
        return [row["symbol"] for row in response.data or []]

    def add_ticker(self, symbol):
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Ticker symbol is required.")
        self.client.table("watchlist").upsert(
            {"user_id": self.user_id, "symbol": symbol},
            on_conflict="user_id,symbol",
            ignore_duplicates=True,
        ).execute()

    def remove_ticker(self, symbol):
        self.client.table("watchlist").delete().eq(
            "user_id", self.user_id
        ).eq("symbol", symbol.upper().strip()).execute()

    def get_portfolio(self):
        response = (
            self.client.table("portfolio")
            .select("symbol,shares,avg_cost,updated_at")
            .eq("user_id", self.user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return [
            {
                "symbol": row["symbol"],
                "shares": float(row["shares"]),
                "avg_cost": float(row["avg_cost"]),
                "updated_at": row["updated_at"],
            }
            for row in response.data or []
        ]

    def add_position(self, symbol, shares, avg_cost):
        symbol = symbol.upper().strip()
        shares = float(shares)
        avg_cost = float(avg_cost)
        if not symbol or shares == 0 or avg_cost < 0:
            raise ValueError("Invalid position input.")

        existing_rows = (
            self.client.table("portfolio")
            .select("shares,avg_cost")
            .eq("user_id", self.user_id)
            .eq("symbol", symbol)
            .execute()
            .data
            or []
        )
        existing = existing_rows[0] if existing_rows else None
        if existing is None:
            if shares < 0:
                raise ValueError("You cannot sell a ticker that is not in your portfolio.")
            new_shares = shares
            new_avg_cost = avg_cost
        else:
            current_shares = float(existing["shares"])
            current_cost = float(existing["avg_cost"])
            if shares < 0 and abs(shares) > current_shares:
                raise ValueError("You cannot sell more shares than you currently own.")
            new_shares = current_shares + shares
            if new_shares <= 0:
                self.remove_position(symbol)
                return
            if shares > 0:
                new_avg_cost = (
                    current_cost * current_shares + avg_cost * shares
                ) / new_shares
            else:
                new_avg_cost = current_cost

        self.client.table("portfolio").upsert(
            {
                "user_id": self.user_id,
                "symbol": symbol,
                "shares": new_shares,
                "avg_cost": new_avg_cost,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="user_id,symbol",
        ).execute()

    def remove_position(self, symbol):
        self.client.table("portfolio").delete().eq(
            "user_id", self.user_id
        ).eq("symbol", symbol.upper().strip()).execute()

    def add_alert(self, symbol, direction, target):
        symbol = symbol.upper().strip()
        direction = direction.lower().strip()
        target = float(target)
        if not symbol or direction not in {"above", "below"} or target <= 0:
            raise ValueError("Invalid alert input.")
        self.client.table("alerts").insert(
            {
                "user_id": self.user_id,
                "symbol": symbol,
                "direction": direction,
                "target": target,
            }
        ).execute()

    def get_alerts(self):
        response = (
            self.client.table("alerts")
            .select("id,symbol,direction,target,created_at")
            .eq("user_id", self.user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [
            {
                "id": row["id"],
                "symbol": row["symbol"],
                "direction": row["direction"],
                "target": float(row["target"]),
                "created_at": row["created_at"],
            }
            for row in response.data or []
        ]

    def remove_alert(self, alert_id):
        self.client.table("alerts").delete().eq(
            "user_id", self.user_id
        ).eq("id", int(alert_id)).execute()

    def import_local_data(self, legacy_db):
        prior_import = (
            self.client.table("legacy_imports")
            .select("user_id")
            .eq("user_id", self.user_id)
            .execute()
            .data
            or []
        )
        if prior_import:
            return None

        watchlist = legacy_db.get_watchlist()
        portfolio = legacy_db.get_portfolio()
        alerts = legacy_db.get_alerts()

        if watchlist:
            self.client.table("watchlist").upsert(
                [
                    {"user_id": self.user_id, "symbol": symbol.upper()}
                    for symbol in watchlist
                ],
                on_conflict="user_id,symbol",
                ignore_duplicates=True,
            ).execute()
        if portfolio:
            self.client.table("portfolio").upsert(
                [
                    {
                        "user_id": self.user_id,
                        "symbol": item["symbol"],
                        "shares": item["shares"],
                        "avg_cost": item["avg_cost"],
                    }
                    for item in portfolio
                ],
                on_conflict="user_id,symbol",
                ignore_duplicates=True,
            ).execute()
        if alerts:
            self.client.table("alerts").upsert(
                [
                    {
                        "user_id": self.user_id,
                        "symbol": item["symbol"],
                        "direction": item["direction"],
                        "target": item["target"],
                        "legacy_id": item["id"],
                        "created_at": item["created_at"],
                    }
                    for item in alerts
                ],
                on_conflict="user_id,legacy_id",
                ignore_duplicates=True,
            ).execute()

        self.client.table("legacy_imports").upsert(
            {"user_id": self.user_id},
            on_conflict="user_id",
        ).execute()
        return {
            "watchlist": len(watchlist),
            "portfolio": len(portfolio),
            "alerts": len(alerts),
        }
