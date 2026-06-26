import sqlite3

import pandas as pd
import pytest
from pydantic import ValidationError

from etl.load import RAW_CSV_PATH, run, validate_rows
from etl.schema import Deal


@pytest.fixture(scope="module")
def raw_df():
    return pd.read_csv(RAW_CSV_PATH)


def test_seed_csv_has_no_duplicate_deal_ids(raw_df):
    assert raw_df["deal_id"].is_unique


def test_seed_csv_has_minimum_row_count(raw_df):
    assert len(raw_df) >= 50


def test_all_rows_pass_schema_validation(raw_df):
    deals = validate_rows(raw_df)
    assert len(deals) == len(raw_df)
    assert all(isinstance(d, Deal) for d in deals)


def test_disclosed_deals_have_positive_value(raw_df):
    deals = validate_rows(raw_df)
    for d in deals:
        if d.deal_value_disclosed:
            assert d.deal_value_usd_m > 0
        else:
            assert d.deal_value_usd_m == 0


def test_invalid_row_raises_validation_error():
    with pytest.raises(ValidationError):
        Deal(
            deal_id="BAD1",
            announced_date="2023-01-01",
            deal_name="Test Deal",
            acquirer="Acme",
            target_or_partner="Beta",
            deal_type="NotARealType",
            capability_area="MRO",
            region="North America",
            deal_value_usd_m=10,
            deal_value_disclosed=True,
            strategic_rationale="Short",
            build_buy_partner="Buy",
            source_name="Test",
            source_url="http://example.com",
            status="Completed",
        )


def test_run_loads_expected_row_count_into_sqlite(tmp_path):
    db_path = tmp_path / "deals_test.db"
    n_loaded = run(csv_path=RAW_CSV_PATH, db_path=db_path)

    conn = sqlite3.connect(db_path)
    n_in_db = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
    conn.close()

    assert n_loaded == n_in_db
    assert n_loaded > 0
