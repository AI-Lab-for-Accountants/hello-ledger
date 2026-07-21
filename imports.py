"""CSV importers for the guided three-step setup.

The setup mirrors how a real client gets onboarded into a general ledger:
  1. Chart of accounts        -> creates the accounts
  2. Prior-year trial balance -> posts ONE opening-balance entry
  3. Transactions             -> posts one journal entry per row

Each importer validates everything it can BEFORE posting, so a bad file
leaves your books untouched.
"""

import csv
import io
from pathlib import Path

import ledger

OPENING_DESCRIPTION = "Opening balances as of 2025-12-31"
OPENING_DATE = "2026-01-01"

ACCOUNTS_COLUMNS = ["account_number", "name", "type"]
TRIAL_BALANCE_COLUMNS = ["account_number", "debit", "credit"]
TRANSACTIONS_COLUMNS = ["date", "description", "debit_account", "credit_account", "amount"]


def _rows(source, required_columns):
    """Read a CSV from a path or an uploaded file; normalize the headers.

    utf-8-sig handles the invisible marker Excel adds to CSVs it saves.
    Headers are lowercased and stripped so 'Account_Number ' still works.
    Uploaded files are read via getvalue() so the same file can be parsed
    twice — once for the review preview, once for the actual import.
    """
    if isinstance(source, (str, Path)):
        f = open(source, newline="", encoding="utf-8-sig")
    else:
        f = io.StringIO(source.getvalue().decode("utf-8-sig"), newline="")
    reader = csv.DictReader(f)
    headers = [h.lower().strip() for h in (reader.fieldnames or [])]
    missing = [c for c in required_columns if c not in headers]
    if missing:
        raise ledger.LedgerError(
            f"This file is missing the column(s): {', '.join(missing)}. "
            f"Expected columns: {', '.join(required_columns)}."
        )
    rows = []
    for raw in reader:
        clean = {k.lower().strip(): (v or "").strip() for k, v in raw.items() if k}
        if any(clean.values()):  # skip fully blank lines
            rows.append(clean)
    return rows


def parse_csv(source, required_columns):
    """Parse and lightly check a CSV so the user can REVIEW it before importing."""
    return _rows(source, required_columns)


def _account_map(conn):
    return {a["number"]: a["id"] for a in ledger.list_accounts(conn)}


def _amount_cents(text, row_number, column):
    """Parse a money amount, tolerating $ signs and thousands commas."""
    try:
        return ledger.to_cents(str(text).replace("$", "").replace(",", ""))
    except ValueError:
        raise ledger.LedgerError(
            f"Row {row_number}: couldn't read the {column} amount {text!r} — "
            "use plain numbers like 1234.56."
        )


def import_accounts(conn, source):
    """Step 1 — load the chart of accounts. Returns how many were added."""
    rows = _rows(source, ACCOUNTS_COLUMNS)
    if not rows:
        raise ledger.LedgerError("The file has no account rows in it.")
    for i, r in enumerate(rows, start=2):  # row 1 is the header
        try:
            ledger.add_account(conn, r["account_number"], r["name"], r["type"].title())
        except ledger.LedgerError as e:
            raise ledger.LedgerError(f"Row {i}: {e}")
    return len(rows)


def opening_posted(conn):
    """Has the opening-balance entry from step 2 already been posted?"""
    row = conn.execute(
        "SELECT 1 FROM journal_entries WHERE description = ?", (OPENING_DESCRIPTION,)
    ).fetchone()
    return row is not None


def import_trial_balance(conn, source):
    """Step 2 — post beginning balances from the prior-year ending trial balance.

    Expects the POST-CLOSE trial balance (balance sheet accounts plus retained
    earnings). Posts one opening entry dated Jan 1. Returns the line count.
    """
    accounts = _account_map(conn)
    if not accounts:
        raise ledger.LedgerError("Load the chart of accounts first (step 1).")
    if opening_posted(conn):
        raise ledger.LedgerError(
            "Beginning balances are already posted. Use 'Start fresh' below if you "
            "want to erase everything and import again."
        )

    rows = _rows(source, TRIAL_BALANCE_COLUMNS)
    lines = []
    for i, r in enumerate(rows, start=2):
        number = r["account_number"]
        if number not in accounts:
            raise ledger.LedgerError(
                f"Row {i}: account {number} isn't in your chart of accounts — "
                "import may be out of order, or the file has a typo."
            )
        debit = _amount_cents(r["debit"] or 0, i, "debit")
        credit = _amount_cents(r["credit"] or 0, i, "credit")
        if debit or credit:
            lines.append((accounts[number], debit, credit))

    ledger.post_entry(conn, OPENING_DATE, OPENING_DESCRIPTION, lines)
    return len(lines)


def import_transactions(conn, source):
    """Step 3 — post transactions, one balanced journal entry per row.

    Every row is validated before anything posts, so a bad row number 40
    doesn't leave 39 half-imported entries behind.
    """
    accounts = _account_map(conn)
    if not accounts:
        raise ledger.LedgerError("Load the chart of accounts first (step 1).")

    rows = _rows(source, TRANSACTIONS_COLUMNS)
    if not rows:
        raise ledger.LedgerError("The file has no transaction rows in it.")

    prepared = []
    for i, r in enumerate(rows, start=2):
        for column in ("debit_account", "credit_account"):
            if r[column] not in accounts:
                raise ledger.LedgerError(
                    f"Row {i}: account {r[column]} isn't in your chart of accounts."
                )
        amount = _amount_cents(r["amount"], i, "amount")
        if amount <= 0:
            raise ledger.LedgerError(f"Row {i}: the amount must be a positive number.")
        if not r["description"]:
            raise ledger.LedgerError(f"Row {i}: every transaction needs a description.")
        prepared.append(
            (
                r["date"],
                r["description"],
                [(accounts[r["debit_account"]], amount, 0), (accounts[r["credit_account"]], 0, amount)],
            )
        )

    for entry_date, description, lines in prepared:
        ledger.post_entry(conn, entry_date, description, lines)
    return len(prepared)


def setup_state(conn):
    """Where is this ledger in the three-step setup?"""
    has_accounts = bool(ledger.list_accounts(conn))
    has_opening = opening_posted(conn)
    entry_count = conn.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]
    return {
        "has_accounts": has_accounts,
        "has_opening": has_opening,
        "transaction_count": entry_count - (1 if has_opening else 0),
    }
