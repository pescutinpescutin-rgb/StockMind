from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from settings import get_setting


class AuthConfigurationError(ValueError):
    """Raised when required Supabase settings are missing or invalid."""


def _supabase_url():
    url = get_setting("SUPABASE_URL").strip().rstrip("/")
    if not url.startswith("https://") or "your-project" in url:
        raise AuthConfigurationError("Set a valid SUPABASE_URL in .env or Streamlit Secrets.")
    return url


def _client_options():
    return SyncClientOptions(auto_refresh_token=False, persist_session=False)


def create_auth_client():
    anon_key = get_setting("SUPABASE_ANON_KEY").strip()
    if not anon_key or "your_supabase" in anon_key:
        raise AuthConfigurationError("Set SUPABASE_ANON_KEY in .env or Streamlit Secrets.")
    return create_client(_supabase_url(), anon_key, options=_client_options())


def create_admin_client():
    service_key = get_setting("SUPABASE_SERVICE_ROLE_KEY").strip()
    if not service_key or "your_supabase" in service_key:
        raise AuthConfigurationError(
            "Set SUPABASE_SERVICE_ROLE_KEY to enable account deletion."
        )
    return create_client(_supabase_url(), service_key, options=_client_options())


def restore_auth_session(client, tokens):
    if not tokens:
        return None, None

    client.auth.set_session(tokens["access_token"], tokens["refresh_token"])
    verified_user = client.auth.get_user()
    session = client.auth.get_session()
    if not verified_user or not verified_user.user or not session:
        return None, None
    return verified_user.user, session


def save_auth_session(session):
    if not session:
        return None
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    }


def delete_authenticated_user(client, user_id):
    verified_user = client.auth.get_user()
    if not verified_user or not verified_user.user:
        raise ValueError("Your session is no longer valid. Sign in again.")
    if verified_user.user.id != user_id:
        raise ValueError("The signed-in account does not match the account to delete.")

    admin_client = create_admin_client()
    admin_client.auth.admin.delete_user(verified_user.user.id)
