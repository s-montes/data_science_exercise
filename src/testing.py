from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as st
import seaborn as sns
from numpy.random import MT19937, RandomState, SeedSequence
from statsmodels.stats.weightstats import ztest

from src.clean_data import get_clean_logs, get_revenue_df
from src.config import ProjectConfig
from src.utils import bootstrap_estimate, merge_series_by_index

conf = ProjectConfig()

rng = RandomState(MT19937(SeedSequence(conf.random_seed)))


def get_experiment_summary(clean_logs: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    if clean_logs is None:
        clean_logs = get_clean_logs()
    experiment = merge_series_by_index(
        (
            clean_logs.drop_duplicates(subset=["user_id"])["variant"]
            .value_counts()
            .rename("tot_users")
        ),
        (
            clean_logs.loc[clean_logs["event_type"] == "booking_request", "variant"]
            .value_counts()
            .rename("tot_bookings")
        ),
        (
            clean_logs.groupby("variant")
            .agg(tot_revenue=("revenue", "sum"))
            .reset_index()
            .round(3)
            .set_index("variant")["tot_revenue"]
        ),
    ).sort_index()
    experiment["cvr"] = (experiment["tot_bookings"] / experiment["tot_users"]).round(3)
    experiment["rpu"] = (experiment["tot_revenue"] / experiment["tot_users"]).round(3)
    # experiment = experiment.reset_index().rename(columns={"index": "variant"})
    return experiment


def bootstrap_test(
    dataframe: pd.DataFrame(),
    group: str,
    target: str,
    n_resamples: int,
    rng: RandomState = None,
):
    if rng is None:
        rng = RandomState(MT19937(SeedSequence(conf.random_seed)))
    samples = []
    # Split A/B
    group_A = dataframe[dataframe[group] == "A"][target]
    size_A = len(group_A)
    exp_A, err_A = bootstrap_estimate(group_A.values, np.mean, rng=rng)
    print(f"Estimate for A (95% confidence): {exp_A:.2f} +/- {err_A:.2f}")
    group_B = dataframe[dataframe[group] == "B"][target]
    size_B = len(group_B)
    exp_B, err_B = bootstrap_estimate(group_B.values, np.mean, rng=rng)
    print(f"Estimate for B (95% confidence): {exp_B:.2f} +/- {err_B:.2f}")
    mean_A = np.mean(group_A)
    mean_B = np.mean(group_B)
    tot_mean = dataframe[target].mean()
    var_A = np.var(group_A)
    var_B = np.var(group_B)
    print(f"Mean A: {mean_A:.2f}")
    print(f"Mean B: {mean_B:.2f}")
    t = (mean_B - mean_A) / np.sqrt((var_B / size_B) + (var_A / size_A))
    print(f"t-statistic: {t:.2f}")
    print(f"Number of resamples: {n_resamples}")
    for _ in range(n_resamples):
        sample_A = rng.choice(group_A - mean_A + tot_mean, size=size_A, replace=True)
        sample_B = rng.choice(group_B - mean_B + tot_mean, size=size_B, replace=True)
        bs_mean_A = np.mean(sample_A)
        bs_mean_B = np.mean(sample_B)
        bs_var_A = np.var(sample_A)
        bs_var_B = np.var(sample_B)
        bs_t = (bs_mean_B - bs_mean_A) / np.sqrt(
            (bs_var_B / size_B) + (bs_var_A / size_A)
        )
        samples.append(bs_t)
    return t, np.array(samples)


def z_test_conversion(
    clean_logs: Optional[pd.DataFrame] = None,
    alternative: str = "two-sided",
):
    if clean_logs is None:
        clean_logs = get_clean_logs()
    print(f"--- Test for: Conversion ---")
    print(f"--- Method: Z-test ---")
    print("")

    experiment = get_experiment_summary(clean_logs)
    exp_dicts = experiment.to_dict("index")

    uplift = (exp_dicts["B"]["cvr"] - exp_dicts["A"]["cvr"]) / exp_dicts["A"]["cvr"]
    if uplift >= 0:
        print(f"Expected uplift: {100*uplift:.2f}%")
    else:
        print(f"Expected downlift: {-100*uplift:.2f}%")

    revenue_df = get_revenue_df(clean_logs)
    group_A = revenue_df[revenue_df["variant"] == "A"]["conversion"]
    group_B = revenue_df[revenue_df["variant"] == "B"]["conversion"]

    p_val = ztest(group_B, group_A, alternative=alternative)[1]
    print(f"P-value: {100*p_val:.2f}%")
    if p_val < 0.05:
        print("Significant at 95%!")
    if p_val < 0.01:
        print("Significant at 99%!")


def bootstrap_pvalue(
    clean_logs: Optional[pd.DataFrame] = None,
    variant_col: str = "variant",
    target_col: str = "conversion",
    kpi_col: str = "cvr",
    n_resamples: int = 10_000,
    alternative: str = "two-sided",
):
    if clean_logs is None:
        clean_logs = get_clean_logs()

    revenue_df = get_revenue_df(clean_logs)
    experiment = get_experiment_summary(clean_logs)
    exp_dicts = experiment.to_dict("index")

    uplift = (exp_dicts["B"][kpi_col] - exp_dicts["A"][kpi_col]) / exp_dicts["A"][
        kpi_col
    ]
    print(f"--- Test for: {target_col.title()} ---")
    print(f"--- Method: Bootstrap resampling ---")
    print("")
    if uplift >= 0:
        print(f"Expected uplift: {100*uplift:.2f}%")
    else:
        print(f"Expected downlift: {-100*uplift:.2f}%")

    t, samples = bootstrap_test(revenue_df, variant_col, target_col, n_resamples, rng)

    plot_path = conf.fig_path / Path("test")
    plot_path.mkdir(exist_ok=True)

    plt.figure()
    t_plot = sns.displot(samples, kde=True)
    t_plot.ax.axvline(t, color="red")
    t_plot.figure.savefig(plot_path / Path(f"test_{target_col}.png"))

    if alternative == "larger":
        p_val = np.mean(samples > t)
    elif alternative == "smaller":
        p_val = np.mean(samples < t)
    elif alternative == "two-sided":
        p_val = np.mean((samples > t) | (samples < t))
    else:
        raise ValueError((f"Incorrect `alternative`!: {alternative}"))
    print(f"P-value: {100*p_val:.2f}%")
    if p_val < 0.05:
        print("Significant at 95%!")
    if p_val < 0.01:
        print("Significant at 99%!")


if __name__ == "__main__":
    clean_logs = get_clean_logs()
    print("")
    print("---- Experiment summary ---")
    print(get_experiment_summary(clean_logs))
    print("")
    z_test_conversion(clean_logs, alternative="smaller")
    print("")
    bootstrap_pvalue(clean_logs, target_col="conversion", alternative="smaller")
    print("")
    bootstrap_pvalue(
        clean_logs, target_col="revenue", kpi_col="rpu", alternative="larger"
    )
    print("")
