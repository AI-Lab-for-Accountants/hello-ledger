"""General Ledger — every account's activity, or one account's full story."""

import streamlit as st

import ledger
from ui import account_labels, get_conn, md_money, page_header

ALL_ACCOUNTS = "📖 All accounts — the full general ledger"

MONEY_CONFIG = {
    "Debit": st.column_config.NumberColumn("Debit", format="dollar"),
    "Credit": st.column_config.NumberColumn("Credit", format="dollar"),
    "Balance": st.column_config.NumberColumn("Balance", format="dollar"),
}


def activity_table(rows):
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
        column_config=MONEY_CONFIG,
    )


conn = get_conn()
page_header("General Ledger", "The books themselves — every entry, account by account, with running balances.")

accounts = ledger.list_accounts(conn)
if not accounts:
    st.info("No accounts yet — set up your chart of accounts first.")
    st.page_link("views/accounts.py", label="Go to Chart of Accounts", icon="📒")
    st.stop()

labels = account_labels(accounts)
choice = st.selectbox("View", [ALL_ACCOUNTS] + list(labels))

if choice == ALL_ACCOUNTS:
    any_activity = False
    for account in accounts:
        rows = ledger.account_ledger(conn, account["id"])
        if not rows:
            continue
        any_activity = True
        normal = "debit" if account["type"] in ledger.DEBIT_NORMAL else "credit"
        header = (
            f"{account['number']} — {account['name']}  ·  "
            f"ending balance {md_money(rows[-1]['balance_cents'])} {normal}"
        )
        with st.expander(header, expanded=False):
            st.caption(f"{account['type']} account — {len(rows)} entries, balance in its normal {normal} direction.")
            activity_table(rows)
    if not any_activity:
        st.info("No activity anywhere yet — post a journal entry or run Get Started.")
else:
    account_id = labels[choice]
    rows = ledger.account_ledger(conn, account_id)
    if not rows:
        st.info("No activity in this account yet — post a journal entry that touches it.")
    else:
        account = next(a for a in accounts if a["id"] == account_id)
        normal = "debit" if account["type"] in ledger.DEBIT_NORMAL else "credit"
        st.caption(f"{account['type']} account — balance shown in its normal {normal} direction.")
        activity_table(rows)
        st.markdown(f"**Ending balance: {md_money(rows[-1]['balance_cents'])}**")
