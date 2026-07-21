"""Get Started — guided three-step setup, the same way a real client gets onboarded."""

import os

import streamlit as st

import imports
import ledger
from ui import DB_PATH, get_conn, md_money, page_header, show_error

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
            show_error(e)

st.divider()


def money_or_zero(text):
    """Best-effort cents for preview math; deep validation happens on import."""
    try:
        return ledger.to_cents(str(text or 0).replace("$", "").replace(",", ""))
    except ValueError:
        return 0


def preview_accounts(rows):
    counts = {}
    for r in rows:
        t = r["type"].title() or "?"
        counts[t] = counts.get(t, 0) + 1
    st.caption(f"{len(rows)} accounts — " + ", ".join(f"{n} {t}" for t, n in counts.items()))


def preview_trial_balance(rows):
    debits = sum(money_or_zero(r["debit"]) for r in rows)
    credits = sum(money_or_zero(r["credit"]) for r in rows)
    if debits == credits:
        st.success(f"✓ Balances — debits and credits both total {md_money(debits)}.")
    else:
        st.warning(
            f"⚠️ This trial balance doesn't balance — debits {md_money(debits)}, "
            f"credits {md_money(credits)}. The import will refuse it; fix the file first."
        )


def preview_transactions(rows):
    total = sum(money_or_zero(r["amount"]) for r in rows)
    dates = sorted(r["date"] for r in rows if r["date"])
    span = f"{dates[0]} to {dates[-1]}" if dates else "no dates found"
    st.caption(f"{len(rows)} transactions, {span}, totaling {md_money(total)}.")


def upload_step(label, key, importer, success_message, sample_path, columns, preview):
    """One step: grab the sample file, upload a CSV, review it, confirm the import."""
    filename = os.path.basename(sample_path)
    with open(sample_path, "rb") as f:
        st.download_button(
            f"⬇️ Get the sample file ({filename})",
            f.read(),
            file_name=filename,
            mime="text/csv",
            key=f"dl_{key}",
            help="Saves the sample CSV to your Downloads — then upload it below.",
        )
    file = st.file_uploader(label, type="csv", key=f"file_{key}")
    if file is None:
        return

    try:
        rows = imports.parse_csv(file, columns)
    except ledger.LedgerError as e:
        show_error(e)
        return

    st.markdown(f"**Review before importing** — this is what's in `{file.name}`:")
    preview(rows)
    st.dataframe(rows, hide_index=True, width="stretch", height=240)
    st.caption("Not right? Remove the file above, fix it, and upload again. Nothing is imported until you confirm.")
    if st.button("✓ Looks right — import it", key=f"btn_{key}", type="primary"):
        try:
            count = importer(conn, file)
            st.session_state["setup_flash"] = success_message.format(count=count)
            st.rerun()
        except ledger.LedgerError as e:
            show_error(e)


# -- Step 1: chart of accounts ------------------------------------------------
if state["has_accounts"]:
    n = len(ledger.list_accounts(conn))
    st.success(f"① Chart of accounts — done ({n} accounts). ✓")
else:
    with st.container(border=True):
        st.subheader("① Load your chart of accounts")
        st.markdown(
            "The account list every entry will post to. Grab the sample below "
            "(or bring your own CSV with columns `account_number, name, type`), "
            "then upload it."
        )
        upload_step("Chart of accounts CSV", "coa", imports.import_accounts,
                    "Chart of accounts loaded — {count} accounts created.",
                    "demo_data/accounts.csv", imports.ACCOUNTS_COLUMNS, preview_accounts)

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
            "accounts plus retained earnings, as of 2025-12-31). It must balance — the "
            "app checks. Columns: `account_number, debit, credit`."
        )
        upload_step("Prior-year trial balance CSV", "tb", imports.import_trial_balance,
                    "Beginning balances posted — {count} accounts carried forward into 2026.",
                    "demo_data/trial_balance_2025-12-31.csv", imports.TRIAL_BALANCE_COLUMNS,
                    preview_trial_balance)

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
            "`date, description, debit_account, credit_account, amount`."
        )
        upload_step("Transactions CSV", "txns", imports.import_transactions,
                    "Transactions imported — {count} journal entries posted.",
                    "demo_data/transactions_q1_2026.csv", imports.TRANSACTIONS_COLUMNS,
                    preview_transactions)

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
