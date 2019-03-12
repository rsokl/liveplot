from collections import defaultdict
from typing import Dict, Sequence, Tuple

import numpy as np

import hypothesis.strategies as st
import hypothesis.extra.numpy as hnp

from liveplot.typing import LiveMetrics
from liveplot.plotter import LivePlot, LiveLogger
from liveplot import recreate_plot


def finite_array(size):
    return hnp.arrays(
        shape=(size,),
        dtype=np.float64,
        elements=st.floats(allow_infinity=False, allow_nan=False),
    )


def choices(seq: Sequence, size: int) -> st.SearchStrategy[Tuple]:
    strat = st.permutations(tuple(range(len(seq))))
    return strat.map(lambda x: tuple(seq[i] for i in x[:size]))


@st.composite
def metric_dict(draw, num_batch_data=None, num_epoch_data=None) -> st.SearchStrategy[Dict[str, np.ndarray]]:
    if all(x is not None for x in (num_batch_data, num_epoch_data)):
        assert num_batch_data >= num_epoch_data

    if num_batch_data is None:
        num_batch_data = draw(st.integers(0, 5))

    if num_epoch_data is None:
        num_epoch_data = draw(st.integers(0, num_batch_data))

    epoch_domain = draw(choices(np.arange(1, num_batch_data + 1), size=num_epoch_data))

    out = {}  # type: Dict[str, np.ndarray]
    out["batch_data"] = draw(finite_array(num_batch_data))  # type: np.ndarray
    out["epoch_data"] = draw(finite_array(num_epoch_data))  # type: np.ndarray
    out["epoch_domain"] = np.asarray(epoch_domain)
    out["cnt_since_epoch"] = draw(st.integers(0, num_batch_data - num_epoch_data))
    out["total_weighting"] = draw(st.floats(0., 10.)) if out["cnt_since_epoch"] else 0.
    out["running_weighted_sum"] = draw(st.floats(-10., 10.)) if out["cnt_since_epoch"] else 0.
    return out


@st.composite
def live_metrics(draw) -> st.SearchStrategy[LiveMetrics]:
    num_metrics = draw(st.integers(0, 3))
    num_batch_data = draw(st.integers(0, 5))
    num_epoch_data = draw(st.integers(0, num_batch_data))
    epoch_domain = draw(choices(np.arange(1, num_batch_data + 1), size=num_epoch_data))

    out = defaultdict(dict)  # type: Dict[str, Dict[str, np.ndarray]]
    for name in ["metric_a", "metric_b", "metric_c"][:num_metrics]:
        out[name]["batch_data"] = draw(finite_array(num_batch_data))  # type: np.ndarray
        out[name]["epoch_data"] = draw(finite_array(num_epoch_data))  # type: np.ndarray
        out[name]["epoch_domain"] = np.asarray(epoch_domain)
    return dict(out.items())

