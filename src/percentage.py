from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from numpy.random import MT19937, RandomState, SeedSequence

from src.clean_data import get_clean_logs, get_revenue_df
from src.config import ProjectConfig
from src.utils import bootstrap_estimate

conf = ProjectConfig()

rng = RandomState(MT19937(SeedSequence(conf.random_seed)))


def compute_rate(exp_A: float, err_A: float, exp_B: float, err_B: float):
    rate = 100 * ((exp_B / exp_A) - 1)
    err_rate = 100 * np.sqrt((err_A * exp_B / (exp_A ** 2)) ** 2 + (err_B / exp_A) ** 2)
    return rate, err_rate


def estimate_percentage(show_cities: bool = True):
    revenue_df = get_revenue_df()
    revenue_df = revenue_df[revenue_df["revenue"] > 0]

    plot_path = conf.fig_path / Path("percentage")
    plot_path.mkdir(exist_ok=True)
    plt.figure()
    sns.displot(
        data=revenue_df,
        x="revenue",
        hue="variant",
        kind="kde",
    ).figure.savefig(plot_path / Path(f"kde_percentage.png"))

    group_A = revenue_df.loc[
        (revenue_df["variant"] == "A"),
        ["revenue", "city"],
    ]
    group_B = revenue_df.loc[
        (revenue_df["variant"] == "B"),
        ["revenue", "city"],
    ]

    exp_A, err_A = bootstrap_estimate(group_A["revenue"].values, np.mean, rng=rng)
    print(f"Estimate for A (95% confidence): {exp_A:.2f} +/- {err_A:.2f}")
    exp_B, err_B = bootstrap_estimate(group_B["revenue"].values, np.mean, rng=rng)
    print(f"Estimate for B (95% confidence): {exp_B:.2f} +/- {err_B:.2f}")

    rate, err_rate = compute_rate(exp_A, err_A, exp_B, err_B)
    print(f"Estimate for rate (95% confidence): {rate:.2f}% +/- {err_rate:.2f}%")

    if show_cities:
        cities = revenue_df["city"].unique()
        for city in cities:
            print("")
            city_A = group_A[group_A["city"] == city]
            city_B = group_B[group_B["city"] == city]
            print(f"--- Estimates for city: {city.title()}")
            exp_A, err_A = bootstrap_estimate(
                city_A["revenue"].values, np.mean, rng=rng
            )
            print(f"Estimate for A (95% confidence): {exp_A:.2f} +/- {err_A:.2f}")
            exp_B, err_B = bootstrap_estimate(
                city_B["revenue"].values, np.mean, rng=rng
            )
            print(f"Estimate for B (95% confidence): {exp_B:.2f} +/- {err_B:.2f}")

            rate, err_rate = compute_rate(exp_A, err_A, exp_B, err_B)
            print(
                f"Estimate for rate (95% confidence): {rate:.2f}% +/- {err_rate:.2f}%"
            )


if __name__ == "__main__":
    print("")
    print("---- Percentage increase estimate ---")
    estimate_percentage()
    print("")
