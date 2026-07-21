"""hello-ledger data layer.

All the accounting logic lives in this file, with no user-interface code,
so you can read it (and test it) on its own.

Money is stored as integer cents — $12.34 is stored as 1234. Computers are
bad at decimal fractions (try 0.1 + 0.2 in Python), and a ledger that drifts
by pennies is not a ledger. Whole numbers never drift.
"""

import sqlite3

ACCOUNT_TYPES = ["Asset", "Liability", "Equity", "Revenue", "Expense"]

# Assets and Expenses grow with debits; Liabilities, Equity, and Revenue
# grow with credits. This drives the running-balance direction in ledgers.
DEBIT_NORMAL = {"Asset", "Expense"}


class LedgerError(Exception):
    """A problem we explain to the user in plain language."""


# ---------------------------------------------------------------- database


def connect(db_path):
    """Open (or create) the ledger database and make sure tables exist."""
    # check_same_thread=False lets the web app reuse one connection across
    # reruns. This is a single-user learning app, so that's safe here.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id     INTEGER PRIMARY KEY,
            number TEXT NOT NULL UNIQUE,
            name   TEXT NOT NULL,
            type   TEXT NOT NULL CHECK (type IN
                   ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense'))
        );

        CREATE TABLE IF NOT EXISTS journal_entries (
            id          INTEGER PRIMARY KEY,
            entry_date  TEXT NOT NULL,   -- YYYY-MM-DD
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS journal_lines (
            id           INTEGER PRIMARY KEY,
            entry_id     INTEGER NOT NULL REFERENCES journal_entries(id),
            account_id   INTEGER NOT NULL REFERENCES accounts(id),
            debit_cents  INTEGER NOT NULL DEFAULT 0,
            credit_cents INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    conn.commit()
    return conn


# ------------------------------------------------------------------ money


def to_cents(amount):
    """Turn a dollar amount (like 19.99 or '19.99') into integer cents."""
    if amount is None or amount == "":
        return 0
    if isinstance(amount, str):
        amount = amount.strip().replace(",", "")
    return int(round(float(amount) * 100))


def format_money(cents):
    """Turn integer cents into a display string: 123456 -> '1,234.56'."""
    return f"{cents / 100:,.2f}"


# --------------------------------------------------------------- accounts


def add_account(conn, number, name, type_):
    """Add one account to the chart of accounts."""
    number, name = str(number).strip(), str(name).strip()
    if not number or not name:
        raise LedgerError("Every account needs both a number and a name.")
    if type_ not in ACCOUNT_TYPES:
        raise LedgerError(f"Account type must be one of: {', '.join(ACCOUNT_TYPES)}.")
    try:
        conn.execute(
            "INSERT INTO accounts (number, name, type) VALUES (?, ?, ?)",
            (number, name, type_),
        )
    except sqlite3.IntegrityError:
        raise LedgerError(f"Account number {number} already exists — numbers must be unique.")
    conn.commit()


def list_accounts(conn):
    """All accounts, ordered by account number."""
    return conn.execute("SELECT * FROM accounts ORDER BY number").fetchall()


# ---------------------------------------------------------------- posting


def post_entry(conn, entry_date, description, lines):
    """Post one journal entry.

    `lines` is a list of (account_id, debit_cents, credit_cents) tuples.
    The entry must balance: total debits must equal total credits.
    Returns the new entry's id.
    """
    # Ignore blank rows (the entry form may include empty ones).
    lines = [l for l in lines if l[1] or l[2]]

    if not str(description).strip():
        raise LedgerError("Give the entry a short description — your future self will thank you.")
    if len(lines) < 2:
        raise LedgerError("A journal entry needs at least two lines — every debit has a credit.")
    for account_id, debit, credit in lines:
        if debit < 0 or credit < 0:
            raise LedgerError("Amounts can't be negative — swap the debit/credit column instead.")
        if debit and credit:
            raise LedgerError("Each line should be a debit OR a credit, not both.")

    total_debits = sum(l[1] for l in lines)
    total_credits = sum(l[2] for l in lines)
    if total_debits != total_credits:
        off_by = abs(total_debits - total_credits)
        raise LedgerError(
            f"Debits and credits must match. You're off by ${format_money(off_by)} "
            f"(debits ${format_money(total_debits)}, credits ${format_money(total_credits)})."
        )

    cur = conn.execute(
        "INSERT INTO journal_entries (entry_date, description) VALUES (?, ?)",
        (str(entry_date), str(description).strip()),
    )
    entry_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO journal_lines (entry_id, account_id, debit_cents, credit_cents)"
        " VALUES (?, ?, ?, ?)",
        [(entry_id, a, d, c) for a, d, c in lines],
    )
    conn.commit()
    return entry_id


def list_entries(conn, limit=20):
    """Most recent journal entries, newest first, with their line count and size."""
    return conn.execute(
        """
        SELECT e.id, e.entry_date, e.description,
               COUNT(l.id) AS line_count, SUM(l.debit_cents) AS total_cents
        FROM journal_entries e JOIN journal_lines l ON l.entry_id = e.id
        GROUP BY e.id ORDER BY e.entry_date DESC, e.id DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()


def entry_lines(conn, entry_id):
    """The lines of one journal entry, with account labels."""
    return conn.execute(
        """
        SELECT a.number, a.name, l.debit_cents, l.credit_cents
        FROM journal_lines l JOIN accounts a ON a.id = l.account_id
        WHERE l.entry_id = ? ORDER BY l.id
        """,
        (entry_id,),
    ).fetchall()


# ---------------------------------------------------------------- reports


def account_ledger(conn, account_id):
    """One account's activity in date order, with a running balance.

    The running balance is shown in the account's *normal* direction:
    debits increase Assets and Expenses; credits increase everything else.
    """
    account = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    rows = conn.execute(
        """
        SELECT e.entry_date, e.description, l.debit_cents, l.credit_cents
        FROM journal_lines l JOIN journal_entries e ON e.id = l.entry_id
        WHERE l.account_id = ? ORDER BY e.entry_date, e.id, l.id
        """,
        (account_id,),
    ).fetchall()

    direction = 1 if account["type"] in DEBIT_NORMAL else -1
    balance, out = 0, []
    for r in rows:
        balance += direction * (r["debit_cents"] - r["credit_cents"])
        out.append(
            {
                "date": r["entry_date"],
                "description": r["description"],
                "debit_cents": r["debit_cents"],
                "credit_cents": r["credit_cents"],
                "balance_cents": balance,
            }
        )
    return out


def trial_balance(conn):
    """Every account's net balance, shown in the debit or credit column.

    Returns (rows, total_debits_cents, total_credits_cents). If the two
    totals are equal — and they always should be — the books are in balance.
    """
    rows = conn.execute(
        """
        SELECT a.number, a.name, a.type,
               COALESCE(SUM(l.debit_cents), 0) - COALESCE(SUM(l.credit_cents), 0) AS net
        FROM accounts a LEFT JOIN journal_lines l ON l.account_id = a.id
        GROUP BY a.id ORDER BY a.number
        """
    ).fetchall()

    out, total_debits, total_credits = [], 0, 0
    for r in rows:
        debit = r["net"] if r["net"] > 0 else 0
        credit = -r["net"] if r["net"] < 0 else 0
        total_debits += debit
        total_credits += credit
        out.append(
            {
                "number": r["number"],
                "name": r["name"],
                "type": r["type"],
                "debit_cents": debit,
                "credit_cents": credit,
            }
        )
    return out, total_debits, total_credits
