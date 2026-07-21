"""Tests for the CSV importers and the bundled demo data."""

import io
from pathlib import Path

import pytest

import imports
import ledger

DEMO = Path(__file__).resolve().parent.parent / "demo_data"

COA_CSV = (
    "account_number,name,type\n"
    "1000,Cash,Asset\n"
    "3000,Owner Capital,Equity\n"
    "4000,Sales,Revenue\n"
)


@pytest.fixture
def conn():
    return ledger.connect(":memory:")


def upload(text):
    """Simulate an uploaded file (Streamlit hands importers a binary file)."""
    return io.BytesIO(text.encode())


# ---------------------------------------------------------------- accounts


def test_import_accounts(conn):
    assert imports.import_accounts(conn, upload(COA_CSV)) == 3
    assert [a["number"] for a in ledger.list_accounts(conn)] == ["1000", "3000", "4000"]


def test_missing_column_named_in_error(conn):
    with pytest.raises(ledger.LedgerError, match="missing the column.*type"):
        imports.import_accounts(conn, upload("account_number,name\n1000,Cash\n"))


def test_bad_row_reported_with_row_number(conn):
    bad = "account_number,name,type\n1000,Cash,Asset\n2000,Mystery,Wingding\n"
    with pytest.raises(ledger.LedgerError, match="Row 3"):
        imports.import_accounts(conn, upload(bad))


def test_excel_bom_and_messy_headers_tolerated(conn):
    messy = "﻿Account_Number , Name , Type \n1000,Cash,asset\n3000,Capital,equity\n"
    assert imports.import_accounts(conn, upload(messy)) == 2


def test_same_upload_parses_twice(conn):
    """The review step parses the file for preview, then again on confirm."""
    file = upload(COA_CSV)
    first = imports.parse_csv(file, imports.ACCOUNTS_COLUMNS)
    second = imports.parse_csv(file, imports.ACCOUNTS_COLUMNS)
    assert first == second and len(first) == 3
    assert imports.import_accounts(conn, file) == 3  # and the real import still works


# ----------------------------------------------------------- trial balance


TB_CSV = "account_number,debit,credit\n1000,5000.00,\n3000,,5000.00\n"


def test_tb_requires_accounts_first(conn):
    with pytest.raises(ledger.LedgerError, match="step 1"):
        imports.import_trial_balance(conn, upload(TB_CSV))


def test_tb_posts_opening_entry(conn):
    imports.import_accounts(conn, upload(COA_CSV))
    assert imports.import_trial_balance(conn, upload(TB_CSV)) == 2
    assert imports.opening_posted(conn)
    rows, debits, credits = ledger.trial_balance(conn)
    assert debits == credits == 500000
    entry = ledger.list_entries(conn)[0]
    assert entry["entry_date"] == imports.OPENING_DATE


def test_tb_must_balance(conn):
    imports.import_accounts(conn, upload(COA_CSV))
    lopsided = "account_number,debit,credit\n1000,5000.00,\n3000,,4999.00\n"
    with pytest.raises(ledger.LedgerError, match=r"off by \$1\.00"):
        imports.import_trial_balance(conn, upload(lopsided))


def test_tb_unknown_account_reported_with_row(conn):
    imports.import_accounts(conn, upload(COA_CSV))
    stranger = "account_number,debit,credit\n9999,5000.00,\n3000,,5000.00\n"
    with pytest.raises(ledger.LedgerError, match="Row 2.*9999"):
        imports.import_trial_balance(conn, upload(stranger))


def test_tb_cannot_be_imported_twice(conn):
    imports.import_accounts(conn, upload(COA_CSV))
    imports.import_trial_balance(conn, upload(TB_CSV))
    with pytest.raises(ledger.LedgerError, match="already posted"):
        imports.import_trial_balance(conn, upload(TB_CSV))


def test_tb_amounts_with_dollar_signs_and_commas(conn):
    imports.import_accounts(conn, upload(COA_CSV))
    fancy = 'account_number,debit,credit\n1000,"$5,000.00",\n3000,,"$5,000.00"\n'
    imports.import_trial_balance(conn, upload(fancy))
    _, debits, _ = ledger.trial_balance(conn)
    assert debits == 500000


# ------------------------------------------------------------ transactions


def test_transactions_import(conn):
    imports.import_accounts(conn, upload(COA_CSV))
    txns = (
        "date,description,debit_account,credit_account,amount\n"
        "2026-01-05,First sale,1000,4000,250.00\n"
        "2026-01-06,Second sale,1000,4000,100.00\n"
    )
    assert imports.import_transactions(conn, upload(txns)) == 2
    _, debits, credits = ledger.trial_balance(conn)
    assert debits == credits == 35000


def test_bad_row_means_nothing_posts(conn):
    imports.import_accounts(conn, upload(COA_CSV))
    txns = (
        "date,description,debit_account,credit_account,amount\n"
        "2026-01-05,Good row,1000,4000,250.00\n"
        "2026-01-06,Bad row,1000,9999,100.00\n"
    )
    with pytest.raises(ledger.LedgerError, match="Row 3.*9999"):
        imports.import_transactions(conn, upload(txns))
    assert ledger.list_entries(conn) == []  # the good row did NOT sneak in


def test_zero_amount_rejected(conn):
    imports.import_accounts(conn, upload(COA_CSV))
    txns = "date,description,debit_account,credit_account,amount\n2026-01-05,Free?,1000,4000,0\n"
    with pytest.raises(ledger.LedgerError, match="positive"):
        imports.import_transactions(conn, upload(txns))


# ------------------------------------------------- the bundled demo books


def test_demo_data_end_to_end(conn):
    """The bundled Sample Company LLC books must always import and balance."""
    imports.import_accounts(conn, DEMO / "accounts.csv")
    imports.import_trial_balance(conn, DEMO / "trial_balance_2025-12-31.csv")
    posted = imports.import_transactions(conn, DEMO / "transactions_q1_2026.csv")

    assert posted == 47
    rows, debits, credits = ledger.trial_balance(conn)
    assert debits == credits, "demo books are out of balance!"

    by_number = {r["number"]: r for r in rows}
    assert by_number["1000"]["debit_cents"] == 2241000   # Cash $22,410.00
    assert by_number["1100"]["debit_cents"] == 740000    # A/R: Cedar Point still open
    state = imports.setup_state(conn)
    assert state == {"has_accounts": True, "has_opening": True, "transaction_count": 47}
