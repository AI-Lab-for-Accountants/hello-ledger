"""Shared UI helpers: the database connection, branding, and money columns."""

import tomllib

import streamlit as st

import ledger

DB_PATH = "hello_ledger.db"


@st.cache_resource
def get_conn():
    """One shared database connection for the whole app session."""
    return ledger.connect(DB_PATH)


@st.cache_data
def branding():
    """Read branding.toml — the file the branding exercise edits."""
    with open("branding.toml", "rb") as f:
        return tomllib.load(f)


def page_header(title, subtitle):
    st.title(title)
    st.caption(subtitle)


def money_column(label):
    """A right-aligned dollar column for st.dataframe."""
    return st.column_config.NumberColumn(label, format="dollar")


def dollars(cents):
    """Cents -> float dollars for display in tables (None hides a zero cell)."""
    return cents / 100 if cents else None


def account_labels(accounts):
    """Human-friendly labels like '1000 — Cash' mapped to account ids."""
    return {f"{a['number']} — {a['name']}": a["id"] for a in accounts}
