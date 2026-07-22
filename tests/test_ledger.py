"""Tests for the hello-ledger data layer.

Run them with:  pytest
Every test uses a fresh throwaway database, so they never touch your books.
"""

import pytest

import ledger


@pytest.fixture
def conn():
    c = ledger.connect(":memory:")
    ledger.add_account(c, "1000", "Cash", "Asset")
    ledger.add_account(c, "2000", "Credit Card", "Liability")
    ledger.add_account(c, "4000", "Service Revenue", "Revenue")
    ledger.add_account(c, "5000", "Rent Expense", "Expense")
    return c


def ids(conn):
    """Map account numbers to ids for readable tests."""
    return {a["number"]: a["id"] for a in ledger.list_accounts(conn)}


# ----------------------------------------------------------------- money


def test_to_cents_avoids_float_drift():
    assert ledger.to_cents(19.99) == 1999
    assert ledger.to_cents("0.10") == 10
    assert ledger.to_cents(None) == 0


def test_format_money():
    assert ledger.format_money(123456) == "1,234.56"
    assert ledger.format_money(0) == "0.00"


def test_format_money_edge_cases():
    assert ledger.format_money(1) == "0.01"  # exactly one cent
    assert ledger.format_money(-199) == "-1.99"  # negative amount
    assert ledger.format_money(100000001) == "1,000,000.01"  # over a million


def test_to_cents_edge_cases():
    assert ledger.to_cents(0.01) == 1  # exactly one cent
    assert ledger.to_cents(-1.99) == -199  # negative amount
    assert ledger.to_cents("1,234.56") == 123456  # comma thousands separator
    assert ledger.to_cents("1,000,000.01") == 100000001  # over a million with commas
    assert ledger.to_cents("") == 0


# -------------------------------------------------------------- accounts


def test_accounts_listed_in_number_order(conn):
    assert [a["number"] for a in ledger.list_accounts(conn)] == ["1000", "2000", "4000", "5000"]


def test_duplicate_account_number_rejected(conn):
    with pytest.raises(ledger.LedgerError, match="already exists"):
        ledger.add_account(conn, "1000", "Cash Again", "Asset")


def test_bad_account_type_rejected(conn):
    with pytest.raises(ledger.LedgerError, match="Account type"):
        ledger.add_account(conn, "9999", "Mystery", "Wingding")


# --------------------------------------------------------------- posting


def test_balanced_entry_posts(conn):
    a = ids(conn)
    entry_id = ledger.post_entry(
        conn, "2026-01-15", "Client payment",
        [(a["1000"], 50000, 0), (a["4000"], 0, 50000)],
    )
    lines = ledger.entry_lines(conn, entry_id)
    assert len(lines) == 2
    assert sum(l["debit_cents"] for l in lines) == sum(l["credit_cents"] for l in lines) == 50000


def test_unbalanced_entry_rejected_with_off_by_amount(conn):
    a = ids(conn)
    with pytest.raises(ledger.LedgerError, match=r"off by \$2\.00"):
        ledger.post_entry(
            conn, "2026-01-15", "Oops",
            [(a["1000"], 50000, 0), (a["4000"], 0, 49800)],
        )


def test_single_line_entry_rejected(conn):
    a = ids(conn)
    with pytest.raises(ledger.LedgerError, match="at least two lines"):
        ledger.post_entry(conn, "2026-01-15", "Half an entry", [(a["1000"], 100, 0)])


def test_line_with_both_debit_and_credit_rejected(conn):
    a = ids(conn)
    with pytest.raises(ledger.LedgerError, match="not both"):
        ledger.post_entry(
            conn, "2026-01-15", "Confused line",
            [(a["1000"], 100, 100), (a["4000"], 0, 0), (a["5000"], 100, 0)],
        )


def test_blank_description_rejected(conn):
    a = ids(conn)
    with pytest.raises(ledger.LedgerError, match="description"):
        ledger.post_entry(conn, "2026-01-15", "  ", [(a["1000"], 100, 0), (a["4000"], 0, 100)])


def test_failed_post_leaves_no_partial_entry(conn):
    a = ids(conn)
    with pytest.raises(ledger.LedgerError):
        ledger.post_entry(conn, "2026-01-15", "Bad", [(a["1000"], 100, 0), (a["4000"], 0, 99)])
    assert ledger.list_entries(conn) == []


# ---------------------------------------------------------------- reports


def post_sample_activity(conn):
    a = ids(conn)
    ledger.post_entry(conn, "2026-01-10", "Client payment",
                      [(a["1000"], 100000, 0), (a["4000"], 0, 100000)])
    ledger.post_entry(conn, "2026-01-31", "January rent on card",
                      [(a["5000"], 30000, 0), (a["2000"], 0, 30000)])
    ledger.post_entry(conn, "2026-02-05", "Pay card balance",
                      [(a["2000"], 30000, 0), (a["1000"], 0, 30000)])


def test_running_balance_debit_normal_account(conn):
    post_sample_activity(conn)
    rows = ledger.account_ledger(conn, ids(conn)["1000"])  # Cash (Asset)
    assert [r["balance_cents"] for r in rows] == [100000, 70000]


def test_running_balance_credit_normal_account(conn):
    post_sample_activity(conn)
    rows = ledger.account_ledger(conn, ids(conn)["2000"])  # Credit Card (Liability)
    assert [r["balance_cents"] for r in rows] == [30000, 0]


def test_trial_balance_always_balances(conn):
    post_sample_activity(conn)
    rows, total_debits, total_credits = ledger.trial_balance(conn)
    assert total_debits == total_credits == 100000
    by_number = {r["number"]: r for r in rows}
    assert by_number["1000"]["debit_cents"] == 70000   # Cash
    assert by_number["4000"]["credit_cents"] == 100000  # Revenue
    assert by_number["5000"]["debit_cents"] == 30000   # Rent
    # The paid-off credit card shows no balance on either side.
    assert by_number["2000"]["debit_cents"] == by_number["2000"]["credit_cents"] == 0
