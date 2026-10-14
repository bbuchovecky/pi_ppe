"""Time and spatial reductions and ensemble anomalies for PPE fields."""

import numpy as np

from . import config


def annual_mean(da):
    """Calendar-year means of monthly data, weighted by days per month."""
    days = da["time"].dt.days_in_month
    weights = days.groupby("time.year") / days.groupby("time.year").sum()
    return (da * weights).groupby("time.year").sum("time", min_count=1)


def global_mean(da, weights=None):
    """Area-weighted mean over lat/lon (cos(lat) weights by default; NaNs skipped)."""
    if weights is None:
        weights = np.cos(np.deg2rad(da["lat"]))
    return da.weighted(weights.fillna(0)).mean(("lat", "lon"))


def land_mean(da, grid):
    """Mean over land, weighted by gridcell area times land fraction (``grid`` from ``load.open_grid``)."""
    return global_mean(da, weights=grid["area"] * grid["landfrac"])


def anomaly(ens, ref=config.DEFAULT_KEY):
    """Each member minus the reference member (the default run unless given)."""
    return ens - ens.sel(member=ref).reset_coords(drop=True)
