from functools import reduce

import pandas as pd


def merge_series_by_index(*ss):
    return reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True), ss)
