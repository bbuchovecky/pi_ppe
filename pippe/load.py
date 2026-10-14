"""Open CESM2 PI coupled PPE output as lazy xarray objects.

Reads the standard single-variable time series of every history variable,
`<case>/<gcomp>/proc/tseries/<freq>/<case>.<model>.<stream>.<VAR>.<YYYYMM-YYYYMM>.nc`.

Times are moved to the middle of each averaging interval (CESM stamps them at
the end, so January would read as Feb 1), and lat/lon are cast to float64 and
rounded so atm (double) and lnd (float) fields share identical coordinates.
"""

from functools import cache

import pandas as pd
import xarray as xr

from . import config

COORD_DECIMALS = 4  # float32 lnd lat is off by up to 4e-6 deg
COMMON_PERIOD = config.COMMON_PERIOD


@cache
def read_crosswalk():
    """Crosswalk table indexed by member key (`COUPxxxx`), with `param`, `minmax` etc."""
    df = pd.read_csv(config.CROSSWALK_CSV)
    return df.set_index("key_coupledPPE")


def member_keys():
    """Keys of every ensemble member in the crosswalk, including the default run."""
    return list(read_crosswalk().index)


def case_name(key):
    """Case name of a member key, e.g. `COUP0001` -> `COUP0001_PI_SOM_v02`."""
    suffix = config.DEFAULT_CASE_SUFFIX if key == config.DEFAULT_KEY else config.MEMBER_CASE_SUFFIX
    return key + suffix


def tseries_dir(key, gcomp="atm", freq="month_1"):
    """Directory of the standard time series."""
    return config.SIM_ROOT / case_name(key) / gcomp / "proc" / "tseries" / freq


def list_vars(key=config.DEFAULT_KEY, gcomp="atm", stream="h0", freq="month_1"):
    """Sorted variable names available for `open_var`."""
    prefix = f"{case_name(key)}.{config.MODEL_NAMES[gcomp]}.{stream}."
    files = tseries_dir(key, gcomp, freq).glob(prefix + "*.nc")
    return sorted({f.name[len(prefix):].split(".")[0] for f in files})


def _round_coords(ds):
    return ds.assign_coords(
        {c: ds[c].astype("float64").round(COORD_DECIMALS) for c in ("lat", "lon") if c in ds.coords}
    )


def _open(paths, var, chunks):
    """Open `var` (and its time bounds) from time-ordered files, then center and decode time."""
    parts = []
    for path in sorted(paths):
        # Keep only var + bounds: the CESM bookkeeping variables have other on-disk chunks
        ds = xr.open_dataset(path, decode_times=False)
        bounds = ds["time"].attrs.get("bounds")
        parts.append(ds[[v for v in (var, bounds) if v in ds]].chunk(chunks))
    ds = parts[0] if len(parts) == 1 else xr.concat(parts, "time", data_vars="minimal", coords="minimal")
    if bounds in ds:
        bnd_dim = next(d for d in ds[bounds].dims if d != "time")
        mid = ds[bounds].mean(bnd_dim).values
        ds = ds.assign_coords(time=("time", mid, ds["time"].attrs))
    return _round_coords(xr.decode_cf(ds))[var]


def open_var(key, var, gcomp="atm", stream="h0", freq="month_1", chunks=None):
    """One variable of one member from the standard time series, as a lazy DataArray.

    `stream` is the history tape (`h0` monthly; `h1`/`h2` hold other
    frequencies), `freq` the subdirectory (`month_1`, `day_1`).
    """
    chunks = chunks or {"time": 120}
    pattern = f"{case_name(key)}.{config.MODEL_NAMES[gcomp]}.{stream}.{var}.*.nc"
    paths = list(tseries_dir(key, gcomp, freq).glob(pattern))
    if not paths:
        raise FileNotFoundError(f"no {pattern} in {tseries_dir(key, gcomp, freq)}")
    return _open(paths, var, chunks)


def open_ensemble(var, gcomp="atm", keys=None, time_slice=COMMON_PERIOD, **kwargs):
    """One variable of many members, concatenated along `member`.

    `member` holds the keys, with `param` and `minmax` coords from the
    crosswalk. Members of different lengths are NaN-padded (COUP0012 runs 3
    years longer), so pass `time_slice` to keep a common period.
    """
    keys = keys or member_keys()
    das = []
    for key in keys:
        da = open_var(key, var, gcomp, **kwargs)
        das.append(da.sel(time=time_slice) if time_slice is not None else da)
    ens = xr.concat(das, dim=pd.Index(keys, name="member"), join="outer")
    xwalk = read_crosswalk().reindex(keys)
    return ens.assign_coords(
        param=("member", xwalk["param"].to_numpy()),
        minmax=("member", xwalk["minmax"].to_numpy()),
    )


def open_grid(key=config.DEFAULT_KEY):
    """Static fields: `gw` (atm Gaussian weights), `area` (km2), `landfrac`, `landmask`."""
    atm = next(tseries_dir(key, "atm").glob(f"{case_name(key)}.cam.h0.*.nc"))
    lnd = next(tseries_dir(key, "lnd").glob(f"{case_name(key)}.clm2.h0.*.nc"))
    with xr.open_dataset(atm, decode_times=False) as a, xr.open_dataset(lnd, decode_times=False) as l:
        grid = xr.merge([_round_coords(a[["gw"]]), _round_coords(l[["area", "landfrac", "landmask"]])])
    return grid.load()
