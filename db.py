"""StockMind application services."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "stockmind.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS watchlist "
        "(symbol TEXT PRIMARY KEY, added_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS portfolio "
        "(symbol TEXT PRIMARY KEY, shares REAL NOT NULL, avg_cost REAL NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS alerts "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL, direction TEXT NOT NULL, target REAL NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS social_posts "
        "(post_id TEXT PRIMARY KEY, username TEXT NOT NULL, content TEXT NOT NULL, "
        "created_at TEXT, url TEXT NOT NULL, saved_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    return conn


def get_watchlist():
    with _connect() as conn:
        return [
            row[0]
            for row in conn.execute(
                "SELECT symbol FROM watchlist ORDER BY added_at DESC"
            )
        ]


def add_ticker(symbol):
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist(symbol) VALUES (?)",
            (symbol.upper(),),
        )


def remove_ticker(symbol):
    with _connect() as conn:
        conn.execute(
            "DELETE FROM watchlist WHERE symbol = ?",
            (symbol.upper(),),
        )


def get_portfolio():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT symbol, shares, avg_cost, updated_at FROM portfolio ORDER BY updated_at DESC"
        ).fetchall()
        return [
            {
                "symbol": row[0],
                "shares": float(row[1]),
                "avg_cost": float(row[2]),
                "updated_at": row[3],
            }
            for row in rows
        ]


def add_position(symbol, shares, avg_cost):
    symbol = symbol.upper().strip()
    shares = float(shares)
    avg_cost = float(avg_cost)

    if not symbol or shares == 0 or avg_cost < 0:
        raise ValueError("Invalid position input.")

    with _connect() as conn:
        existing = conn.execute(
            "SELECT shares, avg_cost FROM portfolio WHERE symbol = ?",
            (symbol,),
        ).fetchone()

        if existing is None:
            if shares < 0:
                raise ValueError("You cannot sell a ticker that is not in your portfolio.")
            conn.execute(
                "INSERT INTO portfolio(symbol, shares, avg_cost, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (symbol, shares, avg_cost),
            )
            return

        current_shares, current_cost = existing
        if shares < 0 and abs(shares) > float(current_shares):
            raise ValueError("You cannot sell more shares than you currently own.")

        new_shares = float(current_shares) + shares
        if new_shares <= 0:
            conn.execute("DELETE FROM portfolio WHERE symbol = ?", (symbol,))
            return

        if shares > 0:
            total_cost = (float(current_cost) * float(current_shares)) + (avg_cost * shares)
            new_avg_cost = total_cost / new_shares
        else:
            new_avg_cost = float(current_cost)

        conn.execute(
            "UPDATE portfolio SET shares = ?, avg_cost = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?",
            (new_shares, new_avg_cost, symbol),
        )


def remove_position(symbol):
    with _connect() as conn:
        conn.execute("DELETE FROM portfolio WHERE symbol = ?", (symbol.upper().strip(),))


def add_alert(symbol, direction, target):
    symbol = symbol.upper().strip()
    direction = direction.lower().strip()
    target = float(target)
    if not symbol or direction not in {"above", "below"} or target <= 0:
        raise ValueError("Invalid alert input.")

    with _connect() as conn:
        conn.execute(
            "INSERT INTO alerts(symbol, direction, target, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (symbol, direction, target),
        )


def get_alerts():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, symbol, direction, target, created_at FROM alerts ORDER BY created_at DESC"
        ).fetchall()
        return [
            {
                "id": row[0],
                "symbol": row[1],
                "direction": row[2],
                "target": float(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]


def remove_alert(alert_id):
    with _connect() as conn:
        conn.execute("DELETE FROM alerts WHERE id = ?", (int(alert_id),))


def save_social_posts(posts):
    with _connect() as conn:
        before = conn.total_changes
        conn.executemany(
            "INSERT OR IGNORE INTO social_posts(post_id, username, content, created_at, url) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (
                    post["id"],
                    post["username"],
                    post["text"],
                    post.get("created_at"),
                    post["url"],
                )
                for post in posts
            ],
        )
        return conn.total_changes - before


def get_social_posts(limit=30):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT post_id, username, content, created_at, url "
            "FROM social_posts ORDER BY COALESCE(created_at, saved_at) DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [
            {
                "id": row[0],
                "username": row[1],
                "text": row[2],
                "created_at": row[3],
                "url": row[4],
            }
            for row in rows
        ]
