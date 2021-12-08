from functools import reduce

import pandas as pd
import scipy.stats as st

from src.config import ProjectConfig

conf = ProjectConfig()


def merge_series_by_index(*ss):
    return reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True), ss)


def bootstrap_estimate(
    data, statistic, confidence_level=0.95, n_resamples=9999, rng=None
):
    bs = st.bootstrap(
        (data,),
        statistic,
        confidence_level=confidence_level,
        n_resamples=n_resamples,
        random_state=rng,
    )
    expected = (bs.confidence_interval.high + bs.confidence_interval.low) / 2
    error = (bs.confidence_interval.high - bs.confidence_interval.low) / 2
    return expected, error
