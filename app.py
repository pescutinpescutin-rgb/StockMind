from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthError

import db as local_db
from ai import ask_analyst
from auth import (
    AuthConfigurationError,
    create_auth_client,
    delete_authenticated_user,
    restore_auth_session,
    save_auth_session,
)
from data import (
    compare_companies,
    get_buyable_candidates,
    get_company,
    get_company_news,
    get_company_risk,
    get_history,
    get_market_overview,
    get_market_screen,
    get_x_posts,
    search_companies,
)
from db import (
    get_social_posts,
    save_social_posts,
)
from education import metric_explanation
from i18n import LANGUAGES, translate
from settings import get_setting
from user_store import GuestStore, SupabaseStore
from supabase_auth.errors import AuthError

st.set_page_config(
    page_title="StockMind | Financial Research",
    page_icon="◈",
    layout="wide",
)

language = st.sidebar.selectbox(
    translate(
        "Language ({count} available)",
        st.session_state.get("language", "English"),
        count=len(LANGUAGES),
    ),
    LANGUAGES,
    key="language",
)


def t(message, **values):
    return translate(message, language, **values)


TEXT = {
    "English": {
        "overview": "Market overview",
        "dashboard": "Dashboard",
        "portfolio": "Portfolio",
        "compare": "Compare",
        "analysis": "Company analysis",
        "analyst": "AI Analyst",
        "education": "Educational mode",
        "watchlist": "Watchlist",
        "search": "Search companies",
        "ticker": "Ticker symbol",
        "refresh": "Analyze",
        "missing": "Not reported",
        "source": "Source: Yahoo Finance via yfinance · Retrieved",
        "no_data": "Data is unavailable for this symbol right now.",
    },
    "Deutsch": {
        "overview": "Marktüberblick",
        "dashboard": "Dashboard",
        "portfolio": "Portfolio",
        "compare": "Vergleichen",
        "analysis": "Unternehmensanalyse",
        "analyst": "KI-Analyst",
        "education": "Lernmodus",
        "watchlist": "Beobachtungsliste",
        "search": "Unternehmen suchen",
        "ticker": "Börsenkürzel",
        "refresh": "Analysieren",
        "missing": "Keine Angabe",
        "source": "Quelle: Yahoo Finance via yfinance · Abgerufen",
        "no_data": "Für dieses Symbol sind derzeit keine Daten verfügbar.",
    },
    "Español": {
        "overview": "Resumen del mercado",
        "dashboard": "Panel",
        "portfolio": "Cartera",
        "compare": "Comparar",
        "analysis": "Análisis de la empresa",
        "analyst": "Analista IA",
        "education": "Modo educativo",
        "watchlist": "Lista de seguimiento",
        "search": "Buscar empresas",
        "ticker": "Símbolo",
        "refresh": "Analizar",
        "missing": "No informado",
        "source": "Fuente: Yahoo Finance vía yfinance · Recuperado",
        "no_data": "Los datos no están disponibles para este símbolo en este momento.",
    },
    "Italiano": {
        "overview": "Panoramica di mercato",
        "dashboard": "Dashboard",
        "portfolio": "Portafoglio",
        "compare": "Confronta",
        "analysis": "Analisi aziendale",
        "analyst": "Analista IA",
        "education": "Modalità didattica",
        "watchlist": "Watchlist",
        "search": "Cerca aziende",
        "ticker": "Ticker",
        "refresh": "Analizza",
        "missing": "Non disponibile",
        "source": "Fonte: Yahoo Finance via yfinance · Recuperato",
        "no_data": "I dati non sono disponibili per questo simbolo al momento.",
    },
    "中文": {
        "overview": "市场概览",
        "dashboard": "仪表板",
        "portfolio": "投资组合",
        "compare": "比较",
        "analysis": "公司分析",
        "analyst": "AI 分析师",
        "education": "教育模式",
        "watchlist": "观察列表",
        "search": "搜索公司",
        "ticker": "股票代码",
        "refresh": "分析",
        "missing": "未披露",
        "source": "数据来源：Yahoo Finance via yfinance · 获取时间",
        "no_data": "当前该代码暂无数据。",
    },
    "日本語": {
        "overview": "市場概観",
        "dashboard": "ダッシュボード",
        "portfolio": "ポートフォリオ",
        "compare": "比較",
        "analysis": "会社分析",
        "analyst": "AIアナリスト",
        "education": "学習モード",
        "watchlist": "ウォッチリスト",
        "search": "銘柄を検索",
        "ticker": "ティッカー",
        "refresh": "分析",
        "missing": "未公開",
        "source": "出典: Yahoo Finance via yfinance · 取得日時",
        "no_data": "現在この銘柄のデータは利用できません。",
    },
    "한국어": {
        "overview": "시장 개요",
        "dashboard": "대시보드",
        "portfolio": "포트폴리오",
        "compare": "비교",
        "analysis": "기업 분석",
        "analyst": "AI 분석가",
        "education": "교육 모드",
        "watchlist": "관심종목",
        "search": "기업 검색",
        "ticker": "종목 코드",
        "refresh": "분석",
        "missing": "미공개",
        "source": "출처: Yahoo Finance via yfinance · 조회 시각",
        "no_data": "현재 이 종목의 데이터를 사용할 수 없습니다.",
    },
    "हिन्दी": {
        "overview": "बाजार अवलोकन",
        "dashboard": "डैशबोर्ड",
        "portfolio": "पोर्टफोलियो",
        "compare": "तुलना",
        "analysis": "कंपनी विश्लेषण",
        "analyst": "AI विश्लेषक",
        "education": "शैक्षिक मोड",
        "watchlist": "वॉचलिस्ट",
        "search": "कंपनियाँ खोजें",
        "ticker": "टिकर",
        "refresh": "विश्लेषण",
        "missing": "अभिव्यक्त नहीं",
        "source": "स्रोत: Yahoo Finance via yfinance · प्राप्त",
        "no_data": "इस टिकर के लिए डेटा उपलब्ध नहीं है।",
    },
}

st.markdown(
    """
    <style>
      :root {
        --sm-bg: #070b12;
        --sm-panel: rgba(15, 23, 35, 0.88);
        --sm-panel-strong: #101927;
        --sm-line: rgba(133, 164, 196, 0.16);
        --sm-text: #e8f0fa;
        --sm-muted: #91a1b4;
        --sm-cyan: #7de3f7;
        --sm-blue: #8caeff;
        --sm-amber: #ffb765;
      }
      .stApp {
        background:
          radial-gradient(ellipse at 18% -10%, rgba(29, 119, 151, 0.2), transparent 38%),
          radial-gradient(ellipse at 92% 8%, rgba(60, 83, 163, 0.13), transparent 34%),
          linear-gradient(rgba(117, 165, 203, 0.025) 1px, transparent 1px),
          linear-gradient(90deg, rgba(117, 165, 203, 0.025) 1px, transparent 1px),
          var(--sm-bg);
        background-size: auto, auto, 44px 44px, 44px 44px, auto;
        color: var(--sm-text);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      .block-container {
        max-width: 1680px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
      }
      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1420 0%, #090e16 100%);
        border-right: 1px solid var(--sm-line);
      }
      [data-testid="stSidebar"] > div:first-child {
        background: transparent;
      }
      h1, h2, h3 {
        color: var(--sm-text);
        letter-spacing: -0.035em;
        font-weight: 650;
      }
      h1 {
        font-size: clamp(1.8rem, 3vw, 2.45rem);
      }
      h2, h3 {
        font-size: clamp(1.15rem, 2vw, 1.55rem);
      }
      p, label, [data-testid="stMarkdownContainer"] {
        color: inherit;
      }
      [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(19, 31, 46, 0.95), rgba(11, 18, 28, 0.92));
        border: 1px solid var(--sm-line);
        padding: 15px 16px 13px;
        border-radius: 14px;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.16);
        transition: border-color 160ms ease, transform 160ms ease;
      }
      [data-testid="stMetric"]:hover {
        border-color: rgba(125, 227, 247, 0.34);
        transform: translateY(-1px);
      }
      [data-testid="stMetricValue"] {
        color: #f4f8ff;
        font-weight: 650;
        font-size: clamp(1.2rem, 2vw, 1.55rem);
      }
      [data-testid="stMetricLabel"] {
        color: var(--sm-muted);
        font-size: 0.72rem;
        letter-spacing: 0.045em;
      }
      .disclaimer {
        color: var(--sm-muted);
        font-size: 0.84rem;
      }
      div.stButton > button {
        min-height: 2.55rem;
        border-radius: 10px;
        border: 1px solid rgba(139, 173, 206, 0.22);
        background: linear-gradient(145deg, #172435, #111a27);
        color: #eaf3ff;
        font-weight: 600;
        transition: border-color 150ms ease, box-shadow 150ms ease, transform 150ms ease;
      }
      div.stButton > button:hover {
        border-color: rgba(125, 227, 247, 0.58);
        color: #c6f7ff;
        box-shadow: 0 0 0 3px rgba(125, 227, 247, 0.08);
        transform: translateY(-1px);
      }
      div.stButton > button:focus-visible,
      input:focus-visible,
      textarea:focus-visible {
        outline: 2px solid var(--sm-cyan);
        outline-offset: 2px;
      }
      div.stButton > button[kind="primary"] {
        border: 1px solid rgba(125, 227, 247, 0.54);
        background: linear-gradient(115deg, #127b91, #315c9b);
        color: #f4fdff;
        box-shadow: 0 8px 22px rgba(21, 133, 157, 0.2);
      }
      .glass-card {
        background: var(--sm-panel);
        border: 1px solid var(--sm-line);
        border-radius: 15px;
        padding: 18px;
        box-shadow: 0 16px 38px rgba(0, 0, 0, 0.18);
        backdrop-filter: blur(14px);
      }
      .hero-panel {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 18px;
        position: relative;
        overflow: hidden;
        background:
          radial-gradient(ellipse at 82% 0%, rgba(65, 138, 168, 0.19), transparent 42%),
          linear-gradient(135deg, rgba(17, 29, 44, 0.97), rgba(10, 17, 27, 0.97));
        border: 1px solid rgba(125, 170, 205, 0.2);
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 18px;
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
      }
      .hero-panel::after {
        content: "";
        position: absolute;
        top: 0;
        left: 24px;
        width: 92px;
        height: 2px;
        background: linear-gradient(90deg, var(--sm-cyan), transparent);
        box-shadow: 0 0 16px rgba(125, 227, 247, 0.55);
      }
      .eyebrow {
        font-size: 0.68rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--sm-cyan);
        font-weight: 700;
        margin-bottom: 6px;
      }
      .hero-title {
        font-size: clamp(1.65rem, 3vw, 2.25rem);
        font-weight: 760;
        letter-spacing: -0.045em;
        color: #f5f8ff;
        margin: 0;
      }
      .hero-sub {
        color: #a4b4c7;
        font-size: 0.88rem;
        line-height: 1.4;
        margin-top: 4px;
      }
      .floating-tag {
        display: inline-block;
        margin: 4px 0 4px 6px;
        padding: 7px 10px;
        border-radius: 999px;
        border: 1px solid rgba(141, 174, 207, 0.2);
        background: rgba(17, 29, 43, 0.72);
        color: #c1cede;
        font-size: 0.7rem;
        font-weight: 600;
        backdrop-filter: blur(8px);
      }
      .stat-badge {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255, 183, 101, 0.1);
        color: var(--sm-amber);
        border: 1px solid rgba(255, 183, 101, 0.24);
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }
      .guest-note {
        margin: 0.5rem 0 1.25rem;
        padding: 11px 14px;
        border: 1px solid rgba(125, 227, 247, 0.18);
        border-left: 3px solid var(--sm-cyan);
        border-radius: 10px;
        background: linear-gradient(100deg, rgba(17, 39, 51, 0.78), rgba(15, 23, 35, 0.72));
        color: #b7c8da;
        font-size: 0.86rem;
        line-height: 1.5;
      }
      [data-baseweb="input"] > div,
      [data-baseweb="textarea"] > div,
      [data-baseweb="select"] > div {
        background: rgba(12, 19, 29, 0.86);
        border-color: rgba(139, 173, 206, 0.19);
        border-radius: 10px;
      }
      [data-baseweb="input"]:focus-within > div,
      [data-baseweb="textarea"]:focus-within > div,
      [data-baseweb="select"]:focus-within > div {
        border-color: rgba(125, 227, 247, 0.62);
        box-shadow: 0 0 0 1px rgba(125, 227, 247, 0.22);
      }
      [role="listbox"] {
        padding: 0.35rem;
        border: 1px solid var(--sm-line);
        border-radius: 12px;
        background: #0e1723;
        box-shadow: 0 16px 38px rgba(0, 0, 0, 0.34);
      }
      [role="option"] {
        margin: 2px 0;
        border-radius: 8px;
        transition: background 120ms ease, color 120ms ease;
      }
      [role="option"][aria-selected="true"] {
        background: rgba(39, 133, 153, 0.25);
        color: #e4fbff;
      }
      [data-testid="stTabs"] [role="tab"] {
        color: var(--sm-muted);
      }
      [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: var(--sm-cyan);
      }
      [data-testid="stTabs"] [role="tablist"] {
        gap: 0.35rem;
        padding: 0.3rem;
        border: 1px solid var(--sm-line);
        border-radius: 12px;
        background: rgba(11, 18, 28, 0.78);
      }
      [data-testid="stTabs"] [role="tab"] {
        min-height: 2.45rem;
        padding: 0.45rem 0.9rem;
        border-radius: 9px;
        transition: background 150ms ease, color 150ms ease;
      }
      [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(110deg, rgba(30, 124, 147, 0.28), rgba(63, 85, 145, 0.22));
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 0.35rem;
      }
      [data-testid="stSidebar"] label[data-testid="stRadioOption"] {
        width: 100%;
        margin: 0;
        padding: 0.62rem 0.8rem;
        border: 1px solid rgba(139, 173, 206, 0.08);
        border-radius: 11px;
        background: rgba(15, 24, 36, 0.36);
        color: #aebdd0;
        cursor: pointer;
        transition: background 150ms ease, border-color 150ms ease, color 150ms ease;
      }
      [data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child,
      main label[data-testid="stRadioOption"] > div > div:first-child {
        display: none;
      }
      [data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover {
        background: rgba(107, 151, 185, 0.08);
        border-color: rgba(139, 173, 206, 0.14);
        color: #e2effd;
      }
      [data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] {
        background: linear-gradient(100deg, rgba(33, 140, 159, 0.17), rgba(69, 91, 157, 0.12));
        border-color: rgba(125, 227, 247, 0.24);
        box-shadow: inset 2px 0 0 var(--sm-cyan);
        color: #e4fbff;
      }
      [data-testid="stSidebar"] label[data-testid="stRadioOption"]:focus-within,
      main label[data-testid="stRadioOption"]:focus-within {
        outline: 2px solid rgba(125, 227, 247, 0.7);
        outline-offset: 2px;
      }
      [data-testid="stSidebar"] label[data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] p {
        margin: 0;
        font-size: 0.92rem;
        font-weight: 560;
      }
      main [data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
      }
      main label[data-testid="stRadioOption"] {
        margin: 0;
        padding: 0.45rem 0.85rem;
        border: 1px solid var(--sm-line);
        border-radius: 999px;
        background: rgba(14, 23, 35, 0.78);
        color: var(--sm-muted);
        cursor: pointer;
        transition: background 150ms ease, border-color 150ms ease, color 150ms ease;
      }
      main label[data-testid="stRadioOption"]:hover {
        border-color: rgba(125, 227, 247, 0.4);
        color: #e4fbff;
      }
      main label[data-testid="stRadioOption"][data-selected="true"] {
        border-color: rgba(125, 227, 247, 0.36);
        background: linear-gradient(110deg, rgba(30, 124, 147, 0.28), rgba(63, 85, 145, 0.22));
        color: #e4fbff;
      }
      [data-testid="stExpander"] {
        border: 1px solid var(--sm-line);
        border-radius: 12px;
        background: rgba(13, 21, 32, 0.62);
      }
      [data-testid="stDataFrame"],
      [data-testid="stTable"] {
        border: 1px solid var(--sm-line);
        border-radius: 12px;
        overflow: hidden;
      }
      [data-testid="stAlert"] {
        border-radius: 12px;
      }
      @media (max-width: 700px) {
        .hero-panel {
          padding: 20px 18px;
        }
        .floating-tag {
          margin-left: 0;
          margin-right: 5px;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
          scroll-behavior: auto !important;
          transition-duration: 0.01ms !important;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero-panel">
        <div>
            <div class="eyebrow">{t("Markets · Research")}</div>
            <div class="hero-title">StockMind <span style="color:#f0a54b;">/</span> Terminal</div>
            <div class="hero-sub">{t("Market data and portfolio research in one workspace")}</div>
        </div>
        <div>
            <span class="floating-tag">{t("Market data")}</span>
            <span class="floating-tag">{t("Portfolio tracking")}</span>
            <span class="floating-tag">{t("Risk review")}</span>
            <span class="floating-tag">{t("AI-assisted learning")}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    supabase_client = create_auth_client()
except AuthConfigurationError:
    supabase_client = None

auth_user = None
if "guest_mode" not in st.session_state:
    st.session_state["guest_mode"] = True
if supabase_client is None:
    st.session_state["guest_mode"] = True

auth_tokens = st.session_state.get("auth_tokens")
if auth_tokens and supabase_client:
    try:
        auth_user, active_session = restore_auth_session(
            supabase_client,
            auth_tokens,
        )
        if active_session:
            st.session_state["auth_tokens"] = save_auth_session(active_session)
    except AuthError:
        st.session_state.pop("auth_tokens", None)
        st.session_state["guest_mode"] = True
        st.info(t("Your session expired. Please sign in again."))

if not auth_user and not st.session_state["guest_mode"]:
    st.title(t("Welcome to StockMind"))
    st.caption(t("Sign in or create an account to sync your private research workspace."))
    if notice := st.session_state.pop("auth_notice", None):
        st.warning(notice)
    login_tab, signup_tab = st.tabs([t("Sign in"), t("Create account")])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input(t("Email"), key="login_email").strip().lower()
            login_password = st.text_input(
                t("Password"),
                type="password",
                key="login_password",
            )
            login_submitted = st.form_submit_button(t("Sign in"), use_container_width=True)
        if login_submitted:
            try:
                response = supabase_client.auth.sign_in_with_password(
                    {"email": login_email, "password": login_password}
                )
                if response.session:
                    st.session_state["auth_tokens"] = save_auth_session(response.session)
                    st.session_state["guest_mode"] = False
                    st.rerun()
                st.error(t("Sign-in did not create an active session. Check your email verification."))
            except AuthError as exc:
                st.error(t("Could not sign in: {error}", error=exc))

    with signup_tab:
        with st.form("signup_form"):
            signup_email = st.text_input(t("Email"), key="signup_email").strip().lower()
            signup_password = st.text_input(
                t("Password (at least 8 characters)"),
                type="password",
                key="signup_password",
            )
            signup_confirmation = st.text_input(
                t("Confirm password"),
                type="password",
                key="signup_password_confirmation",
            )
            signup_submitted = st.form_submit_button(
                t("Create account"),
                use_container_width=True,
            )
        if signup_submitted:
            if len(signup_password) < 8:
                st.error(t("Use a password with at least 8 characters."))
            elif signup_password != signup_confirmation:
                st.error(t("The passwords do not match."))
            else:
                try:
                    response = supabase_client.auth.sign_up(
                        {"email": signup_email, "password": signup_password}
                    )
                    if response.session:
                        st.session_state["auth_tokens"] = save_auth_session(response.session)
                        st.session_state["guest_mode"] = False
                        st.rerun()
                    st.success(t("Account created. Check your email to verify it, then sign in."))
                except AuthError as exc:
                    st.error(t("Could not create account: {error}", error=exc))

    if st.button(t("Continue without an account"), use_container_width=True):
        st.session_state["guest_mode"] = True
        st.rerun()

    st.stop()

if auth_user:
    store = SupabaseStore(supabase_client, auth_user.id)
    try:
        supabase_client.table("watchlist").select("symbol").limit(1).execute()
    except APIError as exc:
        st.error(t("The Supabase data tables are not ready. Run `supabase/schema.sql` in the project SQL editor."))
        st.caption(str(exc))
        st.stop()
else:
    store = GuestStore(st.session_state)
    st.markdown(
        f'<div class="guest-note">{t("Guest mode · Watchlist, portfolio, and alerts stay private to this app session. They are not synced or backed up.")}</div>',
        unsafe_allow_html=True,
    )

with st.sidebar:
    st.markdown(
        "# ◈ Stock<span style='color:#ff9b54'>Mind</span>",
        unsafe_allow_html=True,
    )
    with st.expander(t("Account"), expanded=False):
        if auth_user:
            st.caption(t("Signed in as {email}", email=auth_user.email))
            if st.button(t("Log out"), use_container_width=True):
                try:
                    supabase_client.auth.sign_out()
                except AuthError as exc:
                    st.session_state["auth_notice"] = (
                        t("Signed out locally; server sign-out reported: {error}", error=exc)
                    )
                st.session_state.pop("auth_tokens", None)
                st.session_state["guest_mode"] = True
                st.rerun()

            legacy_import_email = get_setting("SUPABASE_LEGACY_IMPORT_EMAIL").strip().lower()
            if local_db.DB_PATH.is_file() and legacy_import_email == auth_user.email.lower():
                st.divider()
                st.caption(
                    t("Copy your existing local watchlist, portfolio, and alerts into this account. The local database will remain unchanged.")
                )
                if st.button(t("Import local data"), use_container_width=True):
                    try:
                        result = store.import_local_data(local_db)
                        if result is None:
                            st.info(t("Local data was already imported into this account."))
                        else:
                            st.success(
                                t("Imported {watchlist} watchlist items, {portfolio} holdings, and {alerts} alerts.",
                                  watchlist=result["watchlist"],
                                  portfolio=result["portfolio"],
                                  alerts=result["alerts"])
                            )
                    except APIError as exc:
                        st.error(t("Could not import local data: {error}", error=exc))
            elif local_db.DB_PATH.is_file():
                st.caption(
                    t("Local data import is restricted to the email configured in SUPABASE_LEGACY_IMPORT_EMAIL.")
                )

            st.divider()
            st.markdown(f"**{t('Delete StockMind account')}**")
            st.caption(t("This permanently deletes your StockMind account and its cloud data."))
            delete_confirmation = st.text_input(
                t("Type DELETE to confirm"),
                key="delete_account_confirmation",
            )
            delete_password = st.text_input(
                t("Confirm your password"),
                type="password",
                key="delete_account_password",
            )
            if st.button(t("Delete account permanently"), use_container_width=True):
                if delete_confirmation != "DELETE" or not delete_password:
                    st.error(t("Enter DELETE and your password to confirm account deletion."))
                else:
                    try:
                        reauthenticated = supabase_client.auth.sign_in_with_password(
                            {
                                "email": auth_user.email,
                                "password": delete_password,
                            }
                        )
                        if not reauthenticated.user or reauthenticated.user.id != auth_user.id:
                            st.error(t("Could not verify the account for deletion."))
                        else:
                            if reauthenticated.session:
                                st.session_state["auth_tokens"] = save_auth_session(
                                    reauthenticated.session
                                )
                            delete_authenticated_user(supabase_client, auth_user.id)
                            st.session_state.pop("auth_tokens", None)
                            st.session_state.pop("delete_account_confirmation", None)
                            st.session_state.pop("delete_account_password", None)
                            st.rerun()
                    except (AuthError, AuthConfigurationError, ValueError) as exc:
                        st.error(t("Could not delete the account: {error}", error=exc))
        else:
            st.caption(t("Guest mode · data is private to this app session."))
            if supabase_client:
                if st.button(t("Sign in or create an account"), use_container_width=True):
                    st.session_state["guest_mode"] = False
                    st.rerun()
            else:
                st.caption(
                    t("Optional cloud accounts are not configured. Add Supabase keys to enable sign-in and sync. Guest mode works without them.")
                )

    if notice := st.session_state.pop("auth_notice", None):
        st.warning(notice)

    text = TEXT[language]

    page = st.radio(
        "Navigation",
        [
            text["dashboard"],
            text["portfolio"],
            text["compare"],
            text["analysis"],
            text["analyst"],
            text["education"],
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption(t("Research and education · No trading"))


@st.fragment(run_every="60s")
def render_x_feed(handles):
    result = get_x_posts(handles)
    new_posts = save_social_posts(result["posts"])
    if new_posts:
        st.toast(t("New posts from monitored X accounts: {count}", count=new_posts))

    st.caption(
        t(
            "X account feed · Refreshes every minute while this dashboard is open · Checked {time}",
            time=datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        )
    )
    if result["error"]:
        st.warning(result["error"])

    posts = get_social_posts()
    if posts:
        for post in posts:
            with st.container(border=True):
                st.markdown(f"**@{post['username']}** · {post['created_at'] or t('Time unavailable')}")
                st.write(post["text"])
                st.markdown(f"[{t('Open post on X')}]({post['url']})")
    elif not result["error"]:
        st.info(t("No posts are available from these accounts yet."))


if page == text["dashboard"]:
    st.subheader(text["overview"])

    overview = get_market_overview()
    columns = st.columns(len(overview))
    for column, item in zip(columns, overview):
        column.metric(item["name"], item["price"], item["change"])

    st.caption(
        f"{text['source']} "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )

    chart_col, market_col = st.columns([2.15, 1])
    with chart_col:
        st.markdown(f"#### {t('S&P 500 · 5Y')}")
        benchmark_history = get_history("^GSPC")
        if not benchmark_history.empty:
            figure = go.Figure(
                go.Scatter(
                    x=benchmark_history.index,
                    y=benchmark_history["Close"],
                    mode="lines",
                    line={"color": "#f0a54b", "width": 1.7},
                    fill="tozeroy",
                    fillcolor="rgba(240,165,75,0.07)",
                    name="S&P 500",
                )
            )
            figure.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0e141c",
                plot_bgcolor="#0e141c",
                height=300,
                margin={"l": 8, "r": 8, "t": 12, "b": 8},
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False,
                hovermode="x unified",
                font={"color": "#aab5c2", "size": 11},
            )
            figure.update_xaxes(showgrid=False, zeroline=False)
            figure.update_yaxes(gridcolor="#202a36", zeroline=False)
            st.plotly_chart(figure, use_container_width=True)
        else:
            st.info(t("Benchmark history is unavailable."))

    with market_col:
        st.markdown(f"#### {t('Market pulse')}")
        for item in overview:
            st.metric(item["name"], item["price"], item["change"])
        st.markdown(
            f'<div class="glass-card"><span style="color:#f0a54b;font-weight:700;">{t("SESSION NOTE")}</span>'
            f'<p style="color:#aab5c2;margin:8px 0 0;">{t("Quotes may be delayed. Confirm prices and market status with your broker before acting.")}</p></div>',
            unsafe_allow_html=True,
        )

    buyable = get_buyable_candidates()
    if buyable:
        st.markdown(f"### {t('Top ideas')}")
        top_ideas = buyable[:3]
        idea_cols = st.columns(len(top_ideas))
        for col, idea in zip(idea_cols, top_ideas):
            with col:
                st.markdown(
                    f"""
                    <div class="glass-card">
                        <div class="stat-badge">{t(idea['idea'])}</div>
                        <h4 style="margin: 12px 0 6px;">{idea['symbol']}</h4>
                        <p style="margin: 0; color: #b9c7d7;">{idea['name']}</p>
                        <p style="margin: 10px 0 0; font-weight: 700;">{idea['price']}</p>
                        <p style="margin: 4px 0 0; color: #a9b5c2;">{idea['change']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(f"#### {t('Find a symbol')}")
    query = st.text_input(
        text["search"],
        placeholder=t("e.g. Apple, Microsoft, SAP"),
    )

    if query:
        results = search_companies(query)
        if results:
            selected = st.selectbox(
                t("Results"),
                results,
                format_func=lambda item: (
                    f"{item['symbol']} — {item['name']} ({item['exchange']})"
                ),
            )
            if st.button(text["refresh"]):
                st.session_state["ticker"] = selected["symbol"]
                st.rerun()
        else:
            st.info(t("No matching listings found."))

    st.subheader(t("Buyable opportunities"))
    if buyable:
        st.dataframe(
            pd.DataFrame(buyable)[["symbol", "name", "idea", "score", "price", "change", "pe", "margin", "risk"]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(t("A simple buy-quality screen based on margin strength, valuation, momentum, and risk profile."))

    st.subheader(t("Screening table"))
    screen_rows = get_market_screen()
    if screen_rows:
        st.dataframe(
            pd.DataFrame(screen_rows)
            .rename(columns={
                "symbol": t("Ticker"),
                "name": t("Company"),
                "price": t("Price"),
                "change": t("Change"),
                "market_cap": t("Market cap"),
                "risk": t("Risk"),
                "risk_score": t("Risk score"),
            })
            .sort_values([t("Risk score"), t("Ticker")], ascending=[True, True], na_position="last"),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader(text["watchlist"])
    existing = store.get_watchlist()

    watch_col, add_col = st.columns([2, 1])
    with add_col:
        new_symbol = st.text_input(
            t("Add ticker"),
            placeholder="MSFT",
        ).upper().strip()
        if st.button(t("＋ Add")) and new_symbol:
            store.add_ticker(new_symbol)
            st.rerun()

    if existing:
        rows = []
        for symbol in existing:
            info = get_company(symbol)
            rows.append(
                {
                    t("Ticker"): symbol,
                    t("Company"): info.get("name") or "—",
                    t("Price"): info.get("price"),
                    t("Change"): info.get("change"),
                }
            )

        with watch_col:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

        remove_col = st.columns(2)[0]
        with remove_col:
            selected_remove = st.selectbox(t("Remove ticker"), existing)
            if st.button(t("Remove")):
                store.remove_ticker(selected_remove)
                st.rerun()
    else:
        if auth_user:
            st.caption(t("Your watchlist is synced with your account."))
        else:
            st.caption(t("Your guest watchlist is saved for this app session only."))

    st.subheader(t("Market notes"))
    market_news = get_company_news("^GSPC", limit=3)
    if market_news:
        for item in market_news:
            st.markdown(f"- [{item['title']}]({item['link']})")
    else:
        st.info(t("No market headlines are available right now."))

    st.subheader(t("Live day-trading X feed"))
    handles = st.text_input(
        t("X accounts to monitor"),
        value=get_setting("X_MONITOR_HANDLES", "dayxtrading"),
        help=t("Enter X usernames separated by commas. Do not include profile URLs."),
        key="x_monitor_handles",
    )
    with st.expander(t("Set up X API access")):
        st.markdown(
            "1. Create an app in the [X Developer Portal](https://developer.x.com/en/portal/dashboard) "
            "and obtain an API v2 Bearer Token.\n"
            "2. Add the token to your local `.env` file or Streamlit Secrets as `X_BEARER_TOKEN`.\n"
            "3. Optionally add `X_MONITOR_HANDLES=dayxtrading` to set the default accounts, then restart StockMind.\n\n"
            "Keep the token private and out of source control. X API access and rate limits depend on your account plan. "
            "This feed polls once per minute only while the dashboard is open."
        )
    render_x_feed(handles)

    st.markdown(
        f'<p class="disclaimer">{t("For research and education only. Not investment advice. StockMind does not execute trades or provide guaranteed price predictions.")}</p>',
        unsafe_allow_html=True,
    )

elif page == text["portfolio"]:
    st.subheader(t("Portfolio"))

    buy_col, sell_col = st.columns(2)
    with buy_col:
        st.markdown(f"#### {t('Add / update position')}")
        buy_symbol = st.text_input(t("Ticker"), key="portfolio_buy_symbol", placeholder="AAPL").upper().strip()
        buy_shares = st.number_input(t("Shares"), min_value=0.01, step=0.01, key="portfolio_buy_shares")
        buy_cost = st.number_input(t("Average cost per share"), min_value=0.01, step=0.01, key="portfolio_buy_cost")
        if st.button(t("Save position")) and buy_symbol:
            try:
                store.add_position(buy_symbol, buy_shares, buy_cost)
                st.success(t("Saved {symbol} to your portfolio.", symbol=buy_symbol))
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))

    with sell_col:
        st.markdown(f"#### {t('Reduce position')}")
        sell_symbol = st.text_input(t("Ticker to sell"), key="portfolio_sell_symbol", placeholder="AAPL").upper().strip()
        sell_shares = st.number_input(t("Shares to sell"), min_value=0.01, step=0.01, key="portfolio_sell_shares")
        if st.button(t("Sell")) and sell_symbol:
            try:
                store.add_position(sell_symbol, -sell_shares, 0)
                st.success(t("Updated {symbol} position.", symbol=sell_symbol))
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))

        if st.button(t("Delete holding")) and sell_symbol:
            store.remove_position(sell_symbol)
            st.success(t("Removed {symbol} from your portfolio.", symbol=sell_symbol))
            st.rerun()

    positions = store.get_portfolio()
    if positions:
        rows = []
        total_value = 0.0
        total_cost = 0.0
        value_series = []

        for item in positions:
            company = get_company(item["symbol"])
            price_value = company.get("price_value")
            market_value = price_value * item["shares"] if price_value is not None else None
            if market_value is not None:
                total_value += market_value
            total_cost += item["avg_cost"] * item["shares"]
            rows.append(
                {
                    t("Ticker"): item["symbol"],
                    t("Shares"): f"{item['shares']:.2f}",
                    t("Avg cost"): f"${item['avg_cost']:.2f}",
                    t("Market value"): f"${market_value:,.2f}" if market_value is not None else "—",
                    t("Last price"): company.get("price") or "—",
                }
            )
            if market_value is not None:
                value_series.append({"Ticker": item["symbol"], "Market value": float(market_value)})

        gain_loss = total_value - total_cost

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if value_series:
            st.bar_chart(pd.DataFrame(value_series).set_index("Ticker"), use_container_width=True)

        st.metric(t("Portfolio value"), f"${total_value:,.2f}")
        st.metric(t("Cost basis"), f"${total_cost:,.2f}")
        st.metric(t("Gain / loss"), f"${gain_loss:,.2f}", delta=f"{gain_loss / total_cost * 100:.2f}%" if total_cost else None)
        if auth_user:
            st.caption(t("Portfolio data is synced with your account."))
        else:
            st.caption(t("Guest portfolio data is available only in this app session."))
    else:
        st.info(t("No positions yet. Add a buy to start tracking your holdings."))

    triggered_alerts = []
    for alert in store.get_alerts():
        company = get_company(alert["symbol"])
        price_value = company.get("price_value")
        if price_value is None:
            continue
        if alert["direction"] == "above" and price_value >= alert["target"]:
            triggered_alerts.append((alert["symbol"], alert["target"], price_value))
        if alert["direction"] == "below" and price_value <= alert["target"]:
            triggered_alerts.append((alert["symbol"], alert["target"], price_value))

    st.subheader(t("Triggered alerts"))
    if triggered_alerts:
        for symbol, target, price in triggered_alerts:
            st.warning(t("{symbol} is at ${price:,.2f}, which triggered the alert target of ${target:,.2f}.",
                         symbol=symbol, price=price, target=target))
    else:
        st.caption(t("No alerts have been triggered yet."))

    st.subheader(t("Alerts"))
    alert_symbol = st.text_input(t("Alert ticker"), key="alert_symbol", placeholder="AAPL").upper().strip()
    alert_direction = st.selectbox(
        t("Alert direction"),
        ["above", "below"],
        format_func=t,
        key="alert_direction",
    )
    alert_target = st.number_input(t("Target price"), min_value=0.01, step=0.01, key="alert_target")
    if st.button(t("Save alert")) and alert_symbol:
        try:
            store.add_alert(alert_symbol, alert_direction, alert_target)
            st.success(t("Saved alert for {symbol}.", symbol=alert_symbol))
            st.rerun()
        except ValueError as exc:
            st.warning(str(exc))

    alerts = store.get_alerts()
    if alerts:
        alert_rows = []
        for alert in alerts:
            alert_rows.append({
                t("Ticker"): alert["symbol"],
                t("Condition"): t(alert["direction"]),
                t("Target"): f"${alert['target']:.2f}",
            })
        st.dataframe(pd.DataFrame(alert_rows), use_container_width=True, hide_index=True)
        alert_to_remove = st.selectbox(t("Delete alert"), [a["id"] for a in alerts], format_func=lambda x: next(a["symbol"] for a in alerts if a["id"] == x), key="alert_delete")
        if st.button(t("Delete selected alert")):
            store.remove_alert(alert_to_remove)
            st.rerun()
    else:
        st.caption(t("No price alerts set yet."))

elif page == text["compare"]:
    st.subheader(t("Compare companies"))
    compare_input = st.text_input(t("Tickers to compare"), value="AAPL, MSFT, NVDA", key="compare_input")
    compare_symbols = [s.strip().upper() for s in compare_input.split(",") if s.strip()]
    if compare_symbols:
        rows = compare_companies(compare_symbols)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(t("Enter one or more tickers separated by commas."))

elif page == text["education"]:
    st.subheader(t("Financial metrics, clearly explained"))

    for name in ["Revenue", "Net income", "Profit margin", "Debt", "P/E ratio"]:
        with st.expander(t(name), expanded=name == "Revenue"):
            professional, beginner = metric_explanation(name, language)
            st.markdown(f"**{t('Professional')}**")
            st.write(professional)
            st.markdown(f"**{t('Beginner friendly')}**")
            st.write(beginner)

elif page == text["analyst"]:
    st.subheader(t("AI Analyst"))

    ticker = st.text_input(text["ticker"], value=st.session_state.get("ticker", "AAPL")).upper().strip()
    level = st.radio(t("Explanation level"), [t("Beginner"), t("Advanced")], horizontal=True)
    question = st.text_area(t("Ask about this company or its financial metrics"))

    if st.button(t("Ask analyst"), disabled=not ticker or not question):
        company = get_company(ticker)
        if company.get("error"):
            st.warning(f"{text['no_data']} {company['error']}")
        else:
            with st.spinner(t("Preparing explanation…")):
                answer = ask_analyst(question, ticker, company, level, language)
            st.markdown(answer)
            st.caption(
                t("AI output may be incomplete or incorrect. Verify material facts with company filings.")
            )

else:
    ticker = st.text_input(
        text["ticker"],
        value=st.session_state.get("ticker", "AAPL"),
    ).upper().strip()

    if ticker:
        info = get_company(ticker)

        if info.get("error"):
            st.warning(f"{text['no_data']} {info['error']}")
        else:
            st.markdown(
                f"<div class='glass-card'><span class='stat-badge'>{ticker}</span><h2 style='margin-top:12px; margin-bottom:8px;'>{info.get('name') or ticker}</h2><p style='color:#b9c7d7; margin:0;'>{info.get('summary') or 'No summary available.'}</p></div>",
                unsafe_allow_html=True,
            )

            st.caption(f"{text['source']} {info.get('retrieved_at')}")

            metrics = [
                ("Price", info.get("price"), info.get("change")),
                ("Market cap", info.get("market_cap"), None),
                ("Revenue (FY)", info.get("revenue"), None),
                ("Net income (FY)", info.get("net_income"), None),
                ("Profit margin", info.get("margin"), None),
                ("P/E ratio", info.get("pe"), None),
                ("52w range", info.get("fifty_two_week_range"), None),
                ("Total debt", info.get("debt"), None),
            ]

            columns = st.columns(3)
            for index, (label, value, delta) in enumerate(metrics):
                column = columns[index % 3]
                column.metric(
                    label,
                    value if value is not None else text["missing"],
                    delta,
                )

            st.caption(
                "Fiscal-year financials are reported values when supplied by "
                "the source; estimates are not shown in this view."
            )

            risk = get_company_risk(ticker)
            if risk["score"] is not None:
                st.markdown("#### Risk profile")
                st.progress(risk["score"] / 100)
                st.caption(f"{risk['label']} ({risk['score']}/100) — {risk['summary']}")

            history = get_history(ticker)
            if not history.empty:
                figure = go.Figure(
                    go.Scatter(
                        x=history.index,
                        y=history["Close"],
                        mode="lines",
                        line={"color": "#ff9b54", "width": 2},
                        name="Close",
                    )
                )
                figure.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0b1018",
                    plot_bgcolor="#0b1018",
                    height=350,
                    margin={"l": 8, "r": 8, "t": 20, "b": 8},
                    xaxis_title=None,
                    yaxis_title="Price",
                )
                st.plotly_chart(figure, use_container_width=True)
            else:
                st.info("Historical prices are unavailable.")

            left, right = st.columns(2)

            with left:
                st.markdown("#### Financial strengths")
                if info.get("strengths"):
                    for item in info["strengths"]:
                        st.write("• " + item)
                else:
                    st.write("Insufficient reported data for an assessment.")

            with right:
                st.markdown("#### Risks and limitations")
                if info.get("risks"):
                    for item in info["risks"]:
                        st.write("• " + item)
                else:
                    st.write(
                        "Review the latest filings; available data may be incomplete."
                    )

st.markdown("---")
st.caption(
    "StockMind is an educational research tool, not investment advice. "
    "Data can be delayed, incomplete, or incorrect. Verify with official filings. "
    "No brokerage connections or trade execution."
)
st.markdown(
    """
    <div style="text-align: center; margin-top: 0.75rem;">
        <strong>Inventor: Enes Sekiraqa</strong><br>
        <a href="tel:+49015258796484">01525 8796484</a>
        &nbsp;·&nbsp;
        <a href="mailto:pescutinpescutin@gmail.com">pescutinpescutin@gmail.com</a>
    </div>
    """,
    unsafe_allow_html=True,
)
