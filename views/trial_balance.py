"""Trial Balance — every account's balance; total debits must equal total credits."""

import streamlit as st

import ledger
from ui import get_conn, md_money, page_header

conn = get_conn()
page_header("Trial Balance", "Every account's net balance. If the totals match, the books balance.")

rows, total_debits, total_credits = ledger.trial_balance(conn)

if not rows:
    st.info("Nothing to show yet — set up your chart of accounts and post an entry first.")
    st.page_link("views/accounts.py", label="Go to Chart of Accounts", icon="📒")
    st.stop()

st.dataframe(
    [
        {
            "Number": r["number"],
            "Account": r["name"],
            "Type": r["type"],
            "Debit": r["debit_cents"] / 100 if r["debit_cents"] else None,
            "Credit": r["credit_cents"] / 100 if r["credit_cents"] else None,
        }
        for r in rows
    ],
    hide_index=True,
    width="stretch",
    column_config={
        "Debit": st.column_config.NumberColumn("Debit", format="dollar"),
        "Credit": st.column_config.NumberColumn("Credit", format="dollar"),
    },
)

st.divider()
st.markdown(
    f"**Totals — Debits: {md_money(total_debits)} · Credits: {md_money(total_credits)}**"
)

if total_debits == total_credits:
    st.success("✓ In balance — total debits equal total credits.")
else:
    st.error(
        f"Out of balance by {md_money(abs(total_debits - total_credits))}. "
        "This should never happen — it means an unbalanced entry got into the database."
    )
