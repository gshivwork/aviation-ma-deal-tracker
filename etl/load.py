"""ETL entry point: validate the raw deal CSV against the schema and load it into SQLite.

Usage:
    python -m etl.load
"""

import sqlite3
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from etl.schema import Deal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "deals_seed.csv"
DB_PATH = PROJECT_ROOT / "data" / "processed" / "deals.db"

DDL = """
CREATE TABLE IF NOT EXISTS deals (
    deal_id TEXT PRIMARY KEY,
    announced_date TEXT NOT NULL,
    deal_name TEXT NOT NULL,
    acquirer TEXT NOT NULL,
    target_or_partner TEXT NOT NULL,
    deal_type TEXT NOT NULL,
    capability_area TEXT NOT NULL,
    region TEXT NOT NULL,
    deal_value_usd_m REAL NOT NULL,
    deal_value_disclosed INTEGER NOT NULL,
    strategic_rationale TEXT NOT NULL,
    build_buy_partner TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL,
    announced_year INTEGER NOT NULL
);
"""


def validate_rows(df: pd.DataFrame) -> list[Deal]:
    """Validate each row with Pydantic, raising on the first failure with row context."""
    validated = []
    errors = []
    for idx, row in df.iterrows():
        try:
            validated.append(Deal(**row.to_dict()))
        except ValidationError as exc:
            errors.append(f"Row {idx} (deal_id={row.get('deal_id')}): {exc}")
    if errors:
        raise ValueError(
            f"{len(errors)} row(s) failed validation:\n" + "\n".join(errors)
        )
    return validated


def load_to_sqlite(deals: list[Deal], db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS deals")
        conn.execute(DDL)
        rows = [
            (
                d.deal_id,
                d.announced_date.isoformat(),
                d.deal_name,
                d.acquirer,
                d.target_or_partner,
                d.deal_type.value,
                d.capability_area,
                d.region,
                d.deal_value_usd_m,
                int(d.deal_value_disclosed),
                d.strategic_rationale,
                d.build_buy_partner.value,
                d.source_name,
                d.source_url,
                d.status.value,
                d.announced_date.year,
            )
            for d in deals
        ]
        conn.executemany(
            """
            INSERT INTO deals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def run(csv_path: Path = RAW_CSV_PATH, db_path: Path = DB_PATH) -> int:
    df = pd.read_csv(csv_path)
    deals = validate_rows(df)
    load_to_sqlite(deals, db_path)
    return len(deals)


if __name__ == "__main__":
    n = run()
    print(f"Loaded {n} validated deals into {DB_PATH}")
