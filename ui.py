"""Shared UI helpers: the database connection, branding, and money columns."""

import base64
import os
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


def md_money(cents):
    """Money for markdown text, with the $ escaped.

    In markdown, a *pair* of bare $ signs turns everything between them into
    math notation — so 'Debits: $5 … Credits: $5' renders half the line in
    green math type. Escaping as \\$ keeps it an ordinary dollar sign.
    """
    return "\\$" + ledger.format_money(cents)


def show_error(error):
    """Show a LedgerError with its $ signs escaped for markdown."""
    st.error(str(error).replace("$", "\\$"))


def celebrate():
    """A branded celebration: the app's logo floats up the screen like balloons.

    Pure CSS, no JavaScript — works offline and in Codespaces. Uses whatever
    logo branding.toml points at, so a rebranded fork celebrates with its own
    mark. (left %, delay s, duration s, size px) tuples stagger the flight.
    """
    b = branding()
    icon = b["firm"].get("logo_icon") or b["firm"].get("logo")
    if not icon or not os.path.exists(icon):
        return
    data = base64.b64encode(open(icon, "rb").read()).decode()
    mime = "image/svg+xml" if icon.endswith(".svg") else "image/png"
    flights = [(8, 0.0, 3.2, 38), (20, 0.5, 2.8, 30), (31, 0.2, 3.6, 44),
               (43, 0.7, 3.0, 28), (55, 0.1, 3.4, 40), (66, 0.6, 2.9, 32),
               (77, 0.3, 3.3, 36), (88, 0.8, 3.1, 30), (14, 1.0, 3.5, 26),
               (60, 0.9, 3.2, 34)]
    pieces = "".join(
        f'<div class="alfa-float" style="left:{left}%; animation-delay:{delay}s; '
        f'animation-duration:{duration}s">'
        f'<img src="data:{mime};base64,{data}" width="{size}"></div>'
        for left, delay, duration, size in flights
    )
    st.html(
        """
        <style>
        .alfa-float { position: fixed; bottom: -60px; z-index: 999;
                      pointer-events: none; opacity: 0;
                      animation-name: alfa-rise; animation-timing-function: ease-in;
                      animation-fill-mode: forwards; }
        @keyframes alfa-rise {
          0%   { transform: translateY(0) rotate(-10deg); opacity: 0; }
          12%  { opacity: 1; }
          75%  { opacity: 1; }
          100% { transform: translateY(-105vh) rotate(12deg); opacity: 0; }
        }
        </style>
        """
        + pieces
    )
