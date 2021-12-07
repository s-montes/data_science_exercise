import sqlite3
from typing import Optional

import pandas as pd

from src.config import ProjectConfig

conf = ProjectConfig()


def get_raw_logs() -> pd.DataFrame:
    # Read sqlite query results into a pandas DataFrame
    with sqlite3.connect(conf.db_path) as conn:
        raw_records = pd.read_sql_query(f"SELECT * from {conf.raw_records}", conn)
    return raw_records


def get_zero_revenue_ids(df) -> pd.DataFrame:
    return list(
        df.loc[((~df["revenue"].isna()) & (df["revenue"] < 0.1)), "user_id"].unique()
    )


def get_several_experiment_variants_ids(df) -> pd.DataFrame:
    return list(
        df.groupby("user_id")
        .agg(tot_variants=("variant", lambda x: len(set(x))))
        .where(lambda x: x > 1)
        .dropna()
        .index
    )


def get_clean_logs(
    raw_records: Optional[pd.DataFrame] = None,
    save_to_db: bool = False,
    return_df: bool = True,
) -> Optional[pd.DataFrame]:
    # Load raw records if needed
    if raw_records is None:
        raw_records = get_raw_logs()
        assert len(raw_records) > 0, "No records in DB!"

    # Find invalid user_id records and remove them
    zero_revenue = get_zero_revenue_ids(raw_records)
    several_variants = get_several_experiment_variants_ids(raw_records)
    clean_records = raw_records[
        ~raw_records["user_id"].isin(zero_revenue + several_variants)
    ].reset_index(drop=True)

    # Assert that cleaning was successful
    assert (
        len(get_zero_revenue_ids(clean_records)) == 0
    ), "Some records have revenue equal 0"
    assert (
        len(get_several_experiment_variants_ids(clean_records)) == 0
    ), "Some IDs have more than one variant associated to them"

    # Save to DB if needed
    if save_to_db:
        with sqlite3.connect(conf.db_path) as conn:
            clean_records.to_sql(conf.clean_records, conn)

    if return_df:
        return clean_records


if __name__ == "__main__":
    get_clean_logs(return_df=False)
