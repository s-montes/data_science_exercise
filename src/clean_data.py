import sqlite3
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import ProjectConfig

conf = ProjectConfig()


def get_raw_logs() -> pd.DataFrame:
    # Read sqlite query results into a pandas DataFrame
    with sqlite3.connect(conf.db_path) as conn:
        raw_records = pd.read_sql_query(f"SELECT * from {conf.raw_records}", conn)
    return raw_records


def get_zero_revenue_ids(df) -> list:
    return list(
        df.loc[((~df["revenue"].isna()) & (df["revenue"] < 0.1)), "user_id"].unique()
    )


def get_several_experiment_variants_ids(df) -> list:
    return list(
        df.groupby("user_id")
        .agg(tot_variants=("variant", lambda x: len(set(x))))
        .where(lambda x: x > 1)
        .dropna()
        .index
    )


def get_sevel_bookings_ids(df) -> list:
    return list(
        df.loc[df["event_type"] == "booking_request", "user_id"]
        .value_counts()
        .where(lambda x: x > 1)
        .dropna()
        .index
    )


def get_clean_logs(
    raw_records: Optional[pd.DataFrame] = None,
    save_to_db: bool = False,
    read_from_df: bool = False,
    return_df: bool = True,
) -> Optional[pd.DataFrame]:
    if read_from_df:
        with sqlite3.connect(conf.db_path) as conn:
            clean_records = pd.read_sql_query(
                f"SELECT * from {conf.clean_records}", conn
            )
    else:
        # Load raw records if needed
        if raw_records is None:
            raw_records = get_raw_logs()
            assert len(raw_records) > 0, "No records in DB!"

        # Find invalid user_id records and remove them
        zero_revenue = get_zero_revenue_ids(raw_records)
        several_variants = get_several_experiment_variants_ids(raw_records)
        several_bookings = get_sevel_bookings_ids(raw_records)
        clean_records = raw_records[
            ~raw_records["user_id"].isin(
                zero_revenue + several_variants + several_bookings
            )
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


def get_revenue_df(clean_logs: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    if clean_logs is None:
        clean_logs = get_clean_logs()
    revenue_df = (
        clean_logs.fillna({"revenue": 0})
        .groupby("user_id")
        .agg(
            revenue=("revenue", "sum"),
            variant=("variant", "first"),
            city=("city", "first"),
        )
    )
    revenue_df["conversion"] = (revenue_df["revenue"] > 0).astype(float)
    return revenue_df


def general_metrics(df: pd.DataFrame, plot_folder: str):
    print(f"Number of records:\n{len(df)}\n")
    df["datetime"] = pd.to_datetime(df["datetime"])
    print(f"Date range:\n{df['datetime'].min(), df['datetime'].max()}\n")
    print(f"Number of events:\n{df['event_type'].value_counts()}\n")
    print(f"Number of unique users:\n{len(df['user_id'].unique())}\n")
    print(
        f"""Median number of records per user:
    {(df['user_id'].value_counts().median())}
        """
    )
    print(
        f"""Number of users assigned to each variant:
    {(df.drop_duplicates(subset=['user_id'])['variant']
    .value_counts()
    .reset_index()
    .to_string(index=False))}
        """
    )
    print(
        f"""Number of users visiting each city:
    {(df.drop_duplicates(subset=["user_id"])["city"]
    .value_counts().reset_index()
    .to_string(index=False))}
        """
    )
    # Plots
    plot_path = conf.fig_path / Path(plot_folder)
    plot_path.mkdir(exist_ok=True)

    plt.figure()
    ecdf = sns.displot(
        data=df,
        x="revenue",
        hue="variant",
        kind="ecdf",
    ).figure.savefig(plot_path / Path("revenue_ecdf.png"))

    plt.figure()
    kde = sns.displot(
        data=df,
        x="revenue",
        row="variant",
        kind="kde",
        hue="city",
        row_order=("A", "B"),
    ).figure.savefig(plot_path / Path("revenue_kde_city.png"))

    plt.figure()
    box = sns.boxplot(data=df, x="revenue", y="variant").figure.savefig(
        plot_path / Path("revenue_box.png")
    )


if __name__ == "__main__":
    raw_logs = get_raw_logs()
    print("--- Raw logs metrics ---")
    print("")
    general_metrics(raw_logs, "raw_logs_eda")
    print("")
    print("--- Log cleaning ---")
    clean_logs = get_clean_logs(raw_logs, return_df=True)
    print("")
    print("--- Clean logs metrics ---")
    print("")
    general_metrics(clean_logs, "clean_logs_eda")
