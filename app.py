"""hello-ledger — a tiny general ledger for learning GitHub.

Start the app with:  streamlit run app.py
"""

import streamlit as st

from ui import branding, get_conn

b = branding()

st.set_page_config(page_title=b["app"]["name"], page_icon="📗", layout="wide")

get_conn()  # opens the database and creates tables on first run

if b["firm"]["logo"]:
    st.logo(
        b["firm"]["logo"],
        size="large",
        icon_image=b["firm"].get("logo_icon") or None,
    )

pages = [
    st.Page("views/get_started.py", title="Get Started", icon="🚀", default=True),
    st.Page("views/accounts.py", title="Chart of Accounts", icon="📒"),
    st.Page("views/journal.py", title="Journal Entries", icon="✏️"),
    st.Page("views/account_ledger.py", title="General Ledger", icon="📖"),
    st.Page("views/trial_balance.py", title="Trial Balance", icon="⚖️"),
]

nav = st.navigation(pages)

with st.sidebar:
    st.markdown(f"**{b['firm']['name']}**")
    st.caption(b["app"]["tagline"])

nav.run()
