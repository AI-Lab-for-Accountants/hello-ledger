"""Trial Balance — every account's balance; total debits must equal total credits."""

import csv
import io

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

buffer = io.StringIO()
writer = csv.writer(buffer)
writer.writerow(["number", "account", "type", "debit", "credit"])
for r in rows:
    writer.writerow(
        [
            r["number"],
            r["name"],
            r["type"],
            f"{r['debit_cents'] / 100:.2f}" if r["debit_cents"] else "",
            f"{r['credit_cents'] / 100:.2f}" if r["credit_cents"] else "",
        ]
    )
writer.writerow(["", "Totals", "", f"{total_debits / 100:.2f}", f"{total_credits / 100:.2f}"])

st.download_button(
    "Download as CSV",
    buffer.getvalue(),
    file_name="trial_balance.csv",
    mime="text/csv",
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
