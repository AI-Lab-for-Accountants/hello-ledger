"""Ledger — one account's full activity with a running balance."""

import streamlit as st

import ledger
from ui import account_labels, get_conn, page_header

conn = get_conn()
page_header("Ledger", "One account's full story, entry by entry, with a running balance.")

accounts = ledger.list_accounts(conn)
if not accounts:
    st.info("No accounts yet — set up your chart of accounts first.")
    st.page_link("views/accounts.py", label="Go to Chart of Accounts", icon="📒")
    st.stop()

labels = account_labels(accounts)
choice = st.selectbox("Account", list(labels))
account_id = labels[choice]

rows = ledger.account_ledger(conn, account_id)

if not rows:
    st.info("No activity in this account yet — post a journal entry that touches it.")
else:
    account = next(a for a in accounts if a["id"] == account_id)
    normal = "debit" if account["type"] in ledger.DEBIT_NORMAL else "credit"
    st.caption(f"{account['type']} account — balance shown in its normal {normal} direction.")
    st.dataframe(
        [
            {
                "Date": r["date"],
                "Description": r["description"],
                "Debit": r["debit_cents"] / 100 if r["debit_cents"] else None,
                "Credit": r["credit_cents"] / 100 if r["credit_cents"] else None,
                "Balance": r["balance_cents"] / 100,
            }
            for r in rows
        ],
        hide_index=True,
        width="stretch",
        column_config={
            "Debit": st.column_config.NumberColumn("Debit", format="dollar"),
            "Credit": st.column_config.NumberColumn("Credit", format="dollar"),
            "Balance": st.column_config.NumberColumn("Balance", format="dollar"),
        },
    )
    st.markdown(f"**Ending balance: ${ledger.format_money(rows[-1]['balance_cents'])}**")
