"""Get Started — guided three-step setup, the same way a real client gets onboarded."""

import os

import streamlit as st

import imports
import ledger
from ui import DB_PATH, get_conn, page_header

conn = get_conn()
page_header("Get Started", "Set up your books in three steps — chart of accounts, beginning balances, then transactions.")

state = imports.setup_state(conn)
all_done = state["has_accounts"] and state["has_opening"] and state["transaction_count"] > 0

if (flash := st.session_state.pop("setup_flash", None)):
    st.success(flash)
    if all_done:
        st.balloons()

if all_done:
    st.success("🎉 Your books are set up! Explore the ledger, then check the Trial Balance.")
    st.page_link("views/trial_balance.py", label="See the Trial Balance", icon="⚖️")
else:
    st.markdown(
        "Use the sample files in the **`demo_data/`** folder, or bring your own CSVs "
        "in the same format. In a hurry?"
    )
    if st.button("⚡ Load all the demo data for me", type="primary"):
        try:
            if not state["has_accounts"]:
                imports.import_accounts(conn, "demo_data/accounts.csv")
            if not imports.opening_posted(conn):
                imports.import_trial_balance(conn, "demo_data/trial_balance_2025-12-31.csv")
            count = imports.import_transactions(conn, "demo_data/transactions_q1_2026.csv")
            st.session_state["setup_flash"] = f"Demo books loaded — {count} Q1 transactions posted."
            st.rerun()
        except ledger.LedgerError as e:
            st.error(str(e))

st.divider()


def upload_step(label, key, importer, success_message):
    """One upload-and-import step: a file picker plus an import button."""
    file = st.file_uploader(label, type="csv", key=f"file_{key}")
    if st.button("Import", key=f"btn_{key}", disabled=file is None):
        try:
            count = importer(conn, file)
            st.session_state["setup_flash"] = success_message.format(count=count)
            st.rerun()
        except ledger.LedgerError as e:
            st.error(str(e))


# -- Step 1: chart of accounts ------------------------------------------------
if state["has_accounts"]:
    n = len(ledger.list_accounts(conn))
    st.success(f"① Chart of accounts — done ({n} accounts). ✓")
else:
    with st.container(border=True):
        st.subheader("① Load your chart of accounts")
        st.markdown(
            "The account list every entry will post to. Columns: "
            "`account_number, name, type` — try `demo_data/accounts.csv`."
        )
        upload_step("Chart of accounts CSV", "coa", imports.import_accounts,
                    "Chart of accounts loaded — {count} accounts created.")

# -- Step 2: beginning balances ----------------------------------------------
if state["has_opening"]:
    st.success("② Beginning balances — opening entry posted as of 2026-01-01. ✓")
elif not state["has_accounts"]:
    st.caption("🔒 ② Beginning balances — locked until your chart of accounts is loaded.")
else:
    with st.container(border=True):
        st.subheader("② Post your beginning balances")
        st.markdown(
            "Upload the **prior-year ending trial balance** (post-close: balance sheet "
            "accounts plus retained earnings, as of 2025-12-31). It must balance — the app "
            "checks. Columns: `account_number, debit, credit` — try "
            "`demo_data/trial_balance_2025-12-31.csv`."
        )
        upload_step("Prior-year trial balance CSV", "tb", imports.import_trial_balance,
                    "Beginning balances posted — {count} accounts carried forward into 2026.")

# -- Step 3: transactions ------------------------------------------------------
if state["transaction_count"] > 0 and state["has_opening"]:
    st.success(f"③ Transactions — {state['transaction_count']} entries posted. ✓")
elif not state["has_opening"]:
    st.caption("🔒 ③ Transactions — locked until beginning balances are posted (order matters in accounting!).")
else:
    with st.container(border=True):
        st.subheader("③ Import transactions")
        st.markdown(
            "Q1 2026 activity, one balanced transaction per row. Columns: "
            "`date, description, debit_account, credit_account, amount` — try "
            "`demo_data/transactions_q1_2026.csv`."
        )
        upload_step("Transactions CSV", "txns", imports.import_transactions,
                    "Transactions imported — {count} journal entries posted.")

# -- Start fresh ---------------------------------------------------------------
st.divider()
with st.expander("Start fresh (erase everything)"):
    st.warning(
        "This erases every account and entry in your LOCAL ledger database. "
        "The CSV files are not touched, so you can import them again."
    )
    confirmed = st.checkbox("Yes, erase all my data")
    if st.button("Erase and start over", disabled=not confirmed):
        conn.close()
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        st.cache_resource.clear()
        st.session_state["setup_flash"] = "Fresh books — everything erased. Start with step ①."
        st.rerun()
