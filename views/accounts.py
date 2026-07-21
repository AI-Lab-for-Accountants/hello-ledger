"""Chart of Accounts — see every account and add new ones."""

import streamlit as st

import ledger
from ui import get_conn, page_header

conn = get_conn()
page_header("Chart of Accounts", "Every account in your books, ordered by number.")

if (flash := st.session_state.pop("account_added", None)):
    st.success(flash)

accounts = ledger.list_accounts(conn)

if accounts:
    st.dataframe(
        [{"Number": a["number"], "Account": a["name"], "Type": a["type"]} for a in accounts],
        hide_index=True,
        width="stretch",
    )
else:
    st.info(
        "No accounts yet — add your first one below. Tip: the usual numbering puts "
        "Assets in the 1000s, Liabilities in the 2000s, Equity in the 3000s, "
        "Revenue in the 4000s, and Expenses in the 5000s and up."
    )

st.subheader("Add an account")
with st.form("add_account", clear_on_submit=True):
    col_number, col_name, col_type = st.columns([1, 2, 1])
    number = col_number.text_input("Number", placeholder="1000")
    name = col_name.text_input("Name", placeholder="Cash")
    type_ = col_type.selectbox("Type", ledger.ACCOUNT_TYPES)
    if st.form_submit_button("Add account", type="primary"):
        try:
            ledger.add_account(conn, number, name, type_)
            st.session_state["account_added"] = f"Added {number} — {name} ({type_})."
            st.rerun()
        except ledger.LedgerError as e:
            st.error(str(e))
