from collections import OrderedDict, defaultdict, namedtuple
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
from liveplot.logger import LiveLogger
from liveplot.plotter import LivePlot
from liveplot.typing import Figure, LiveMetrics, Metrics, ndarray

from custom_inherit import doc_inherit


__all__ = ["create_plot", "save_metrics", "load_metrics"]


@doc_inherit(LivePlot.__init__, style="numpy")
def create_plot(
    metrics: Metrics,
    max_fraction_spent_plotting: float = 0.05,
    nrows: Optional[int] = None,
    ncols: int = 1,
    figsize: Optional[Tuple[int, int]] = None,
) -> Tuple[LivePlot, Figure, ndarray]:
    """ Create matplotlib figure/axes, and a live-plotter, which publishes
    "live" training/testing metric data, at a batch and epoch level, to
    the figure.

    Returns
    -------
    Tuple[liveplot.LivePlot, matplotlib.figure.Figure, numpy.ndarray(matplotlib.axes.Axes)]
        (LivePlot-instance, figure, array-of-axes)


    Examples
    --------
    Creating a live plot in a Jupyter notebook
    >>> %matplotlib notebook
    >>> import numpy as np
    >>> from liveplot import create_plot, save_metrics
    >>> metrics = ["accuracy", "loss"]
    >>> plotter, fig, ax = create_plot(metrics)
    >>> for i, x in enumerate(np.linspace(0, 10, 100)):
    ...     # training
    ...     x += np.random.rand(1)*5
    ...     batch_metrics = {"accuracy": x**2, "loss": 1/x**.5}
    ...     plotter.set_train_batch(batch_metrics, batch_size=1, plot=True)
    ...
    ...     # cue training epoch
    ...     if i%10 == 0 and i > 0:
    ...         plotter.plot_train_epoch()
    ...
    ...         # cue test-time computations
    ...         for x in np.linspace(0, 10, 5):
    ...             x += (np.random.rand(1) - 0.5)*5
    ...             test_metrics = {"accuracy": x**2}
    ...             plotter.set_test_batch(test_metrics, batch_size=1)
    ...         plotter.plot_test_epoch()
    ...
    ... plotter.plot()  # ensures final data gets plotted

    Saving the logged metrics
    >>> save_metrics("./metrics.npz", plotter) # save metrics to numpy-archive
    """
    live_plotter = LivePlot(
        metrics,
        max_fraction_spent_plotting=max_fraction_spent_plotting,
        figsize=figsize,
        ncols=ncols,
        nrows=nrows,
    )
    fig, ax = live_plotter.plot_objects
    return live_plotter, fig, ax


def save_metrics(
    path: Union[str, Path],
    liveplot: Optional[Union[LivePlot, LiveLogger]] = None,
    *,
    train_metrics: LiveMetrics = None,
    test_metrics: LiveMetrics = None
):
    """ Save live-plot metrics to a numpy zipped-archive (.npz). A LivePlot-instance
        can be supplied, or train/test metrics can be passed explicitly to the function.

        Parameters
        ----------
        path: PathLike
           The file-path used to save the archive. E.g. 'path/to/saved_metrics.npz'

        liveplot : Optional[liveplot.LivePlot]
           The LivePlot instance whose metrics will be saves.

        train_metrics : Optional[OrderedDict[str, Dict[str, numpy.ndarray]]]]

            '<metric-name>' -> {'batch_data'   -> array,
                                'epoch_domain' -> array,
                                'epoch_data'   -> array}

        test_metrics : Optional[OrderedDict[str, Dict[str, numpy.ndarray]]]]

            '<metric-name>' -> {'batch_data'   -> array,
                                'epoch_domain' -> array,
                                'epoch_data'   -> array}"""
    if liveplot is not None:
        train_metrics = liveplot.train_metrics
        test_metrics = liveplot.test_metrics
    else:
        if train_metrics is None:
            train_metrics = {}

        if test_metrics is None:
            test_metrics = {}

    # use unique separator
    sep = ";"
    names = "".join(tuple(train_metrics) + tuple(test_metrics))
    while sep in names:
        sep += ";"

    # flatten metrics to single mapping
    save_dict = {}  # train/test;metric_name;metric_data -> array
    for type_, metrics in zip(["train", "test"], [train_metrics, test_metrics]):
        for name, metric in metrics.items():
            save_dict.update({sep.join((type_, name, k)): v for k, v in metric.items()})

    with open(path, "wb") as f:
        np.savez(
            f,
            train_order=list(train_metrics),
            test_order=list(test_metrics),
            sep=sep,
            **save_dict
        )


metrics = namedtuple("metrics", ["train", "test"])


def load_metrics(path: Union[str, Path]) -> Tuple[LiveMetrics, LiveMetrics]:
    """ Load liveplot metrics from a numpy archive.

        Parameters
        ----------
        path : PathLike
            Path to numpy archive.

        Returns
        -------
        Tuple[OrderedDict[str, Dict[str, numpy.ndarray]], OrderedDict[str, Dict[str, numpy.ndarray]]]
           (train-metrics, test-metrics)"""

    def recursive_default_dict():
        return defaultdict(recursive_default_dict)

    out = recursive_default_dict()

    with np.load(path) as f:
        data_dict = dict(f)

    train_order = list(data_dict.pop("train_order"))
    test_order = list(data_dict.pop("test_order"))
    sep = data_dict.pop("sep").item()
    for k, v in data_dict.items():
        type_, metric_name, data_type = k.split(sep)
        out[type_][metric_name][data_type] = v

    train_metrics = OrderedDict(((k, dict(out["train"][k])) for k in train_order))
    test_metrics = OrderedDict(((k, dict(out["test"][k])) for k in test_order))
    return metrics(train_metrics, test_metrics)
