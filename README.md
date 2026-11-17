# StockMind

StockMind is a Streamlit stock-research workspace with company analysis, market
data, watchlists, portfolios, price alerts, news, risk summaries, and optional
AI and X-feed integrations. It is for research and education, not financial
advice.

## Run without an account

1. Use Python 3.11 or newer.
2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

   3. Start StockMind:

      ```bash
      streamlit run app.py
   ```

   StockMind opens in guest mode by default. Your watchlist, portfolio, and alerts
   are kept in your Streamlit session, isolated from other visitors. Guest data is
   not synced or backed up, and may be lost when the session ends.

   ## Optional account and cloud sync

   To enable sign-in and private cloud data, add these values to
   `.streamlit/secrets.toml`. The file is ignored by Git:

   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_ANON_KEY = "your_supabase_anon_key"
   ```

   For a new Supabase project, run `supabase/schema.sql` in its SQL Editor. The
   StockMind Supabase project created for this workspace already has this schema
   installed. Set the Supabase Authentication Site URL to
   `http://localhost:8501` for local email-confirmation links. Create an account
   and verify its email if email confirmation is enabled.

   The service-role key is optional and is only needed for account deletion. Keep
   it private and never put it in client-side code or a public repository:

   ```toml
   SUPABASE_SERVICE_ROLE_KEY = "your_supabase_service_role_key"
   ```

## Optional integrations

Add these to `.streamlit/secrets.toml` only if you use the corresponding
features:

```toml
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_BASE_URL = ""
X_BEARER_TOKEN = ""
X_MONITOR_HANDLES = "dayxtrading"
```

StockMind can also read settings from a local `.env` file. See `.env.example`
for the supported names. Do not commit `.env`, `.streamlit/secrets.toml`, or
`stockmind.db`.

## Deploy

Deploy from a GitHub repository using Streamlit Community Cloud. Add the
Supabase settings under the app's deployment **Secrets** settings rather than
committing local secrets. Guest mode is session-only and is not shared across
visitors; signed-in accounts provide persistent, user-isolated cloud data.
Update the Supabase Site URL to the deployed app URL and add the local and
deployed URLs to the allowed redirect URLs. Keep the service-role key
server-side and use it only when account deletion is enabled.

The Supabase tables use row-level security so each signed-in user can access
only their own watchlist, portfolio, alerts, and import status. The local
SQLite database is not a shared cloud datastore.
