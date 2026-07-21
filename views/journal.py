"""Journal Entries — record transactions. Every debit needs a matching credit."""

import datetime as dt

import streamlit as st

import ledger
from ui import account_labels, get_conn, page_header

conn = get_conn()
page_header("Journal Entries", "Record a transaction — the entry must balance before it posts.")

accounts = ledger.list_accounts(conn)
if not accounts:
    st.info("Set up your chart of accounts first — the journal needs accounts to post to.")
    st.page_link("views/accounts.py", label="Go to Chart of Accounts", icon="📒")
    st.stop()

labels = account_labels(accounts)

if (flash := st.session_state.pop("entry_posted", None)):
    st.success(flash)

# Bumping this version number gives the form fresh widget keys, which is how
# we clear it after a successful post.
version = st.session_state.setdefault("je_version", 0)

col_date, col_desc = st.columns([1, 2])
entry_date = col_date.date_input("Date", value=dt.date.today(), key=f"date_{version}")
description = col_desc.text_input(
    "Description", placeholder="January rent", key=f"desc_{version}"
)

rows = st.data_editor(
    [{"Account": None, "Debit": None, "Credit": None} for _ in range(2)],
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    key=f"lines_{version}",
    column_config={
        "Account": st.column_config.SelectboxColumn("Account", options=list(labels), width="large"),
        "Debit": st.column_config.NumberColumn("Debit", min_value=0.0, format="dollar"),
        "Credit": st.column_config.NumberColumn("Credit", min_value=0.0, format="dollar"),
    },
)

lines = [
    (labels[r["Account"]], ledger.to_cents(r["Debit"]), ledger.to_cents(r["Credit"]))
    for r in rows
    if r["Account"]
]
total_debits = sum(l[1] for l in lines)
total_credits = sum(l[2] for l in lines)

if total_debits or total_credits:
    if total_debits == total_credits:
        st.success(f"✓ In balance — debits and credits both total ${ledger.format_money(total_debits)}.")
    else:
        st.warning(
            f"Not balanced yet — you're off by ${ledger.format_money(abs(total_debits - total_credits))} "
            f"(debits ${ledger.format_money(total_debits)}, credits ${ledger.format_money(total_credits)})."
        )

if st.button("Post entry", type="primary"):
    try:
        ledger.post_entry(conn, entry_date, description, lines)
        st.session_state["entry_posted"] = f"Posted: {entry_date} — {description}."
        st.session_state["je_version"] = version + 1
        st.rerun()
    except ledger.LedgerError as e:
        st.error(str(e))

entries = ledger.list_entries(conn)
if entries:
    st.subheader("Recent entries")
    for e in entries:
        header = f"{e['entry_date']} — {e['description']}  (${ledger.format_money(e['total_cents'])})"
        with st.expander(header):
            st.dataframe(
                [
                    {
                        "Account": f"{l['number']} — {l['name']}",
                        "Debit": l["debit_cents"] / 100 if l["debit_cents"] else None,
                        "Credit": l["credit_cents"] / 100 if l["credit_cents"] else None,
                    }
                    for l in ledger.entry_lines(conn, e["id"])
                ],
                hide_index=True,
                width="stretch",
                column_config={
                    "Debit": st.column_config.NumberColumn("Debit", format="dollar"),
                    "Credit": st.column_config.NumberColumn("Credit", format="dollar"),
                },
            )
