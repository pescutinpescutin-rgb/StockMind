import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import pandas as pd
import yfinance as yf
from settings import get_setting


def _x_api_get(path, bearer_token):
    request = Request(
        f"https://api.x.com/2/{path}",
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code == 401:
            message = "X rejected the bearer token. Check X_BEARER_TOKEN in your app settings."
        elif exc.code == 403:
            message = "X denied access to this endpoint. Check your API plan and permissions."
        elif exc.code == 429:
            message = "X API rate limit reached. The feed will retry on its next refresh."
        else:
            message = f"X API returned HTTP {exc.code}."
        raise RuntimeError(message) from exc
    except URLError as exc:
        raise RuntimeError("Could not reach the X API. Check your internet connection.") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError("X API returned an unreadable response.") from exc


def get_x_posts(handles):
    token = get_setting("X_BEARER_TOKEN").strip()
    if not token or token == "your_x_api_bearer_token":
        return {
            "posts": [],
            "error": "Set X_BEARER_TOKEN in your local .env file or Streamlit Secrets to enable the live X feed.",
        }

    if isinstance(handles, str):
        handles = handles.split(",")
    normalized_handles = list(
        dict.fromkeys(
            handle.strip().lstrip("@")
            for handle in handles
            if handle.strip().lstrip("@")
        )
    )
    if not normalized_handles:
        return {"posts": [], "error": "Enter at least one X account handle."}

    query = urlencode({"usernames": ",".join(normalized_handles), "user.fields": "username"})
    try:
        users_response = _x_api_get(f"users/by?{query}", token)
    except RuntimeError as exc:
        return {"posts": [], "error": str(exc)}

    users = users_response.get("data") or []
    user_by_name = {user.get("username", "").lower(): user for user in users}
    posts = []
    errors = []

    for handle in normalized_handles:
        user = user_by_name.get(handle.lower())
        if not user:
            errors.append(f"@{handle}: account not found or unavailable.")
            continue

        tweets_query = urlencode(
            {
                "max_results": 10,
                "tweet.fields": "created_at",
                "exclude": "replies,retweets",
            }
        )
        try:
            response = _x_api_get(
                f"users/{quote(user['id'], safe='')}/tweets?{tweets_query}",
                token,
            )
        except RuntimeError as exc:
            errors.append(f"@{handle}: {exc}")
            continue

        for tweet in response.get("data") or []:
            tweet_id = tweet.get("id")
            if not tweet_id:
                continue
            posts.append(
                {
                    "id": tweet_id,
                    "username": user.get("username") or handle,
                    "text": tweet.get("text") or "",
                    "created_at": tweet.get("created_at"),
                    "url": f"https://x.com/{quote(user.get('username') or handle, safe='')}/status/{quote(tweet_id, safe='')}",
                }
            )

    return {"posts": posts, "error": "; ".join(errors) if errors else None}


def _fmt_money(value):
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if value != value:  # NaN
        return None

    magnitude = abs(value)
    if magnitude >= 1e12:
        return f"{value / 1e12:,.2f}T"
    if magnitude >= 1e9:
        return f"{value / 1e9:,.2f}B"
    if magnitude >= 1e6:
        return f"{value / 1e6:,.2f}M"
    return f"{value:,.2f}"


def get_market_overview():
    symbols = [
        ("S&P 500", "^GSPC"),
        ("NASDAQ", "^IXIC"),
        ("DAX", "^GDAXI"),
    ]
    output = []

    for name, symbol in symbols:
        try:
            history = yf.Ticker(symbol).history(period="2d")
            if len(history) >= 1:
                price = float(history["Close"].iloc[-1])
                previous = (
                    float(history["Close"].iloc[-2])
                    if len(history) > 1
                    else None
                )
                change = (
                    f"{(price / previous - 1) * 100:+.2f}%"
                    if previous
                    else None
                )
                output.append({
                    "name": name,
                    "price": f"{price:,.2f}",
                    "change": change,
                })
                continue
        except Exception:
            pass

        output.append({"name": name, "price": "—", "change": None})

    return output


def search_companies(query):
    try:
        results = yf.Search(query, max_results=8).quotes
        return [
            {
                "symbol": item.get("symbol", ""),
                "name": (
                    item.get("shortname")
                    or item.get("longname")
                    or item.get("symbol", "")
                ),
                "exchange": item.get("exchange", "—"),
            }
            for item in results
            if item.get("symbol") and item.get("quoteType") == "EQUITY"
        ]
    except Exception:
        return []


def get_company(symbol):
    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.get_info()

        if not info or not info.get("symbol"):
            return {"error": "No company record returned by the data provider."}

        financials = ticker.financials

        def latest_row(*names):
            for name in names:
                if name in financials.index:
                    values = financials.loc[name].dropna()
                    if not values.empty:
                        return values.iloc[0]
            return None

        revenue = latest_row("Total Revenue", "Operating Revenue")
        income = latest_row("Net Income")
        debt = latest_row("Total Debt")

        revenue_value = float(revenue) if revenue is not None and pd.notna(revenue) else None
        income_value = float(income) if income is not None and pd.notna(income) else None
        debt_value = float(debt) if debt is not None and pd.notna(debt) else None
        margin = income_value / revenue_value if income_value is not None and revenue_value else None

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        price_value = float(price) if price is not None and pd.notna(price) else None
        change = info.get("regularMarketChangePercent")
        currency = info.get("currency")
        market_cap = info.get("marketCap")
        market_cap_value = float(market_cap) if market_cap is not None and pd.notna(market_cap) else None
        week_high = info.get("fiftyTwoWeekHigh")
        week_low = info.get("fiftyTwoWeekLow")

        strengths = []
        risks = []

        if margin is not None:
            message = f"Latest reported net margin is {margin:.1%}."
            (strengths if margin > 0 else risks).append(message)

        roe = info.get("returnOnEquity")
        if roe is not None:
            strengths.append(f"Reported return on equity is {roe:.1%}.")

        if debt_value is not None and info.get("totalCash") is not None and debt_value > float(info["totalCash"]):
            risks.append(
                "Reported total debt exceeds reported cash; review maturity and cash flow details."
            )

        def money_with_currency(value):
            formatted = _fmt_money(value)
            if formatted is None:
                return None
            return f"{formatted} {currency}" if currency else formatted

        return {
            "name": info.get("longName") or info.get("shortName"),
            "summary": info.get("longBusinessSummary"),
            "price": (
                f"{price:,.2f} {currency}"
                if price is not None and currency
                else _fmt_money(price)
            ),
            "price_value": price_value,
            "change": f"{change:+.2f}%" if change is not None else None,
            "market_cap": money_with_currency(market_cap),
            "market_cap_value": market_cap_value,
            "revenue": money_with_currency(revenue_value),
            "net_income": money_with_currency(income_value),
            "margin": f"{margin:.1%}" if margin is not None else None,
            "debt": money_with_currency(debt_value),
            "pe": (
                f"{info['trailingPE']:.2f}"
                if info.get("trailingPE") is not None
                else None
            ),
            "fifty_two_week_range": (
                f"{_fmt_money(week_low)} – {_fmt_money(week_high)} {currency}"
                if week_low is not None and week_high is not None and currency
                else None
            ),
            "strengths": strengths,
            "risks": risks,
            "retrieved_at": retrieved,
            "error": None,
        }

    except Exception as exc:
        return {
            "error": f"Data provider error ({type(exc).__name__}). Please retry later."
        }


def get_history(symbol):
    try:
        history = yf.Ticker(symbol).history(period="5y", auto_adjust=True)
        return history if history is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_company_news(symbol, limit=5):
    try:
        items = yf.Ticker(symbol).news or []
        news = []
        for item in items[:limit]:
            title = item.get("title") or item.get("headline") or "Market update"
            link = item.get("link") or item.get("url")
            publisher = item.get("publisher") or item.get("source") or "Yahoo Finance"
            timestamp = item.get("providerPublishTime") or item.get("publishTime")
            date = None
            if timestamp:
                try:
                    date = datetime.fromtimestamp(int(timestamp), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                except (TypeError, ValueError):
                    date = None
            news.append({
                "title": title,
                "link": link,
                "publisher": publisher,
                "date": date,
                "summary": item.get("summary") or item.get("description") or "",
            })
        return news
    except Exception:
        return []


def _parse_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "").replace("%", "")
        if not cleaned:
            return None
        multiplier = 1.0
        upper = cleaned.upper()
        if upper.endswith("T"):
            multiplier = 1_000_000_000_000
            cleaned = cleaned[:-1]
        elif upper.endswith("B"):
            multiplier = 1_000_000_000
            cleaned = cleaned[:-1]
        elif upper.endswith("M"):
            multiplier = 1_000_000
            cleaned = cleaned[:-1]
        try:
            return float(cleaned) * multiplier
        except ValueError:
            return None
    return None


def _parse_change_value(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace("%", "")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def get_company_risk(symbol):
    info = get_company(symbol)
    if info.get("error"):
        return {"score": None, "label": "Unavailable", "summary": "Data unavailable."}

    score = 45
    reasons = []

    margin = None
    if info.get("margin"):
        try:
            margin = float(info["margin"].rstrip("%")) / 100
        except ValueError:
            margin = None

    pe = _parse_number(info.get("pe"))
    market_cap = _parse_number(info.get("market_cap"))
    debt = _parse_number(info.get("debt"))

    if margin is not None:
        if margin > 0.18:
            score -= 12
        elif margin > 0.08:
            score -= 6
        elif margin > 0:
            score += 6
        else:
            score += 18
            reasons.append("Margin is weak or negative.")

    if pe is not None:
        if pe > 35:
            score += 12
            reasons.append("Valuation is elevated relative to earnings.")
        elif pe > 15:
            score += 4
    else:
        score += 5
        reasons.append("Earnings multiple is missing.")

    if market_cap is not None and debt is not None and market_cap > 0:
        debt_ratio = debt / market_cap
        if debt_ratio > 0.6:
            score += 18
            reasons.append("Debt is high relative to market cap.")
        elif debt_ratio > 0.3:
            score += 8

    if info.get("change"):
        try:
            change_value = float(info["change"].rstrip("%"))
            if change_value < -0.10:
                score += 8
                reasons.append("Recent price trend is weaker than average.")
        except ValueError:
            pass

    score = max(0, min(100, int(round(score))))
    if score >= 75:
        label = "High risk"
    elif score >= 55:
        label = "Moderate risk"
    elif score >= 35:
        label = "Balanced"
    else:
        label = "Low risk"

    return {
        "score": score,
        "label": label,
        "summary": reasons[0] if reasons else "No major red flags detected from the available data.",
    }


def get_market_screen(symbols=None):
    default_symbols = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "BRK-B"]
    requested = symbols or default_symbols
    rows = []
    for symbol in requested:
        info = get_company(symbol)
        if info.get("error"):
            rows.append({
                "symbol": symbol,
                "name": "Unavailable",
                "price": "—",
                "change": "—",
                "market_cap": "—",
                "risk": "N/A",
            })
            continue
        risk = get_company_risk(symbol)
        rows.append({
            "symbol": symbol,
            "name": info.get("name") or symbol,
            "price": info.get("price") or "—",
            "change": info.get("change") or "—",
            "market_cap": info.get("market_cap") or "—",
            "risk": risk.get("label") or "N/A",
            "risk_score": risk.get("score"),
        })
    return rows


def get_buyable_candidates(symbols=None):
    default_symbols = [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "META",
        "GOOGL",
        "AVGO",
        "COST",
        "CRM",
        "AMD",
        "NFLX",
        "PEP",
    ]
    requested = symbols or default_symbols
    candidates = []

    for symbol in requested:
        info = get_company(symbol)
        if info.get("error"):
            continue

        risk = get_company_risk(symbol)
        change_value = _parse_change_value(info.get("change"))
        pe = _parse_number(info.get("pe"))
        market_cap = _parse_number(info.get("market_cap"))
        debt = _parse_number(info.get("debt"))

        margin = None
        if info.get("margin"):
            try:
                margin = float(str(info["margin"]).rstrip("%")) / 100
            except ValueError:
                margin = None

        debt_ratio = None
        if market_cap and debt and market_cap > 0:
            debt_ratio = debt / market_cap

        score = 50

        if margin is not None:
            if margin > 0.15:
                score += 18
            elif margin > 0.08:
                score += 8
            elif margin > 0:
                score -= 4
            else:
                score -= 18

        if pe is not None:
            if 10 <= pe <= 30:
                score += 12
            elif pe < 10:
                score += 5
            else:
                score -= 12
        else:
            score -= 4

        if debt_ratio is not None:
            if debt_ratio < 0.25:
                score += 10
            elif debt_ratio > 0.6:
                score -= 12

        if risk.get("score") is not None:
            if risk["score"] <= 40:
                score += 12
            elif risk["score"] <= 60:
                score += 4
            else:
                score -= 10

        if change_value is not None:
            if change_value > 3:
                score += 10
            elif change_value > 0:
                score += 4
            elif change_value < -5:
                score -= 10

        score = max(0, min(100, score))

        if score >= 75:
            label = "Strong buy"
        elif score >= 60:
            label = "Buy"
        elif score >= 45:
            label = "Watch"
        else:
            label = "Avoid"

        candidates.append(
            {
                "symbol": symbol,
                "name": info.get("name") or symbol,
                "price": info.get("price") or "—",
                "change": info.get("change") or "—",
                "pe": info.get("pe") or "—",
                "margin": info.get("margin") or "—",
                "risk": risk.get("label") or "N/A",
                "score": score,
                "idea": label,
            }
        )

    return sorted(candidates, key=lambda row: row["score"], reverse=True)


def compare_companies(symbols):
    rows = []
    for symbol in symbols:
        info = get_company(symbol)
        if info.get("error"):
            rows.append({
                "symbol": symbol,
                "name": "Unavailable",
                "price": "—",
                "market_cap": "—",
                "pe": "—",
                "margin": "—",
            })
            continue
        rows.append({
            "symbol": symbol,
            "name": info.get("name") or symbol,
            "price": info.get("price"),
            "market_cap": info.get("market_cap"),
            "pe": info.get("pe"),
            "margin": info.get("margin"),
            "revenue": info.get("revenue"),
        })
    return rows
