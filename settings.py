import os

from dotenv import load_dotenv

load_dotenv()


def get_setting(name, default=""):
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        return str(st.secrets.get(name, default))
    except FileNotFoundError:
        return default
