# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Exploratory analysis of the CESM2 preindustrial slab-ocean coupled perturbed parameter ensemble (PI PPE, by C. Zarakas): CESM2 1850 conditions with a slab ocean (f19, 96x144 lat/lon), one-at-a-time min/max perturbations of 18 CLM5 parameters. Reusable loading and analysis code lives in the `pippe` package; notebooks are for visualization.

Runs on NCAR's glade (Derecho/Casper). Data and outputs live outside the repo, and every path is set in `pippe/config.py`:
- Simulations: `/glade/campaign/cgd/tss/people/czarakas/CoupledPPE/coupled_simulations/` (another user's campaign storage: read-only, never write there).
- Crosswalk (member key -> `param`, `minmax`, descriptions): `data/CLM5PPE_coupledPPE_crosswalk.csv` (copied from `/glade/u/home/czarakas/coupled_PPE/code/02_set_up_ensemble/`).
- Outputs: `/glade/work/bbuchovecky/pi_ppe/{proc,fig}` (`config.PROC_DIR`, `config.FIG_DIR`).

## Commands

The Python env is the pixi env `pippe`, defined in `pyproject.toml` (`[tool.pixi.*]`; loose specs there, exact versions in `pixi.lock`) with the repo installed editable, so changes under `pippe/` take effect without reinstalling. The env is detached to `/glade/work/bbuchovecky/pixi/envs/pippe-<hash>/` by the global pixi config; don't hardcode that path, use `pixi run` (pixi is at `~/.pixi/bin/pixi`). `pixi run` finds the manifest by searching up from the current directory, so outside the repo (e.g. PBS jobs) pass `--manifest-path <repo>/pyproject.toml`. Every `pixi run` first checks the env against `pixi.lock` and re-solves if the manifest changed; use `--frozen` or `--locked` to prevent that. Add dependencies with `pixi add <pkg>` (conda-forge) and commit the updated `pixi.lock` with the manifest.

```bash
pixi install                          # create/update the env from pixi.lock
pixi run kernel                       # (re)register the `pippe` Jupyter kernel on the env
pixi run python -c "import pippe"     # ad-hoc commands run in the env
pixi add <pkg>                        # add a dependency (updates pyproject.toml and pixi.lock)
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.kernel_name=pippe --output-dir <scratch> notebooks/<nb>.ipynb
                                      # run a notebook headless (nbconvert is not in the pippe env; output outside the repo)
```

There are no tests yet. Verify changes by running them against the real data with `pixi run python`.

## Data layout

- Member keys `COUPxxxx`: `COUP0000` is the default run (case `COUP0000_PI_SOM`). Perturbed members are `COUP0001`-`COUP0037` (case `COUPxxxx_PI_SOM_v02`). The ensemble is the 37 crosswalk rows (`load.member_keys()`). `COUP0002` is not in the crosswalk and its run stops at year 85. `COUP0012_PI_SOM_v05` is a stub with no output; `reruns_to_fix_missing_years/` holds reruns of missing years; the `proc` monthly series are complete, so use those rather than the reruns. `COUP0037` (rhosnir max) used a very small perturbation because the exact one crashed.
- Per case: `<gcomp>/hist/` (raw history files) and `<gcomp>/proc/tseries/{month_1,day_1}/`: standard single-variable time series `<case>.<cam|clm2>.<h0|h1|h2>.<VAR>.<YYYYMM-YYYYMM>.nc`, covering every history variable (~340 atm and ~440 lnd on h0). All loading goes through these via `load.open_var`. The `*.timeseries.*` files directly in `proc/tseries/` (including derived `calculated_*` variables) are not used; compute derived quantities from the standard variables instead.
- Monthly output covers model years 49-188 (1680 months) for every member except COUP0012, which runs to 191. Calendar is noleap (cftime).

## Architecture

- `pippe/config.py`: paths, `DEFAULT_KEY`, case-name suffixes, `MODEL_NAMES` (`atm` -> `cam`, `lnd` -> `clm2`), `COMMON_PERIOD`.
- `pippe/load.py` (imported as `load`): `read_crosswalk`, `member_keys`, `case_name`, `tseries_dir`, `list_vars`, `open_var(key, var, gcomp, stream, freq)`, `open_ensemble(var, gcomp, keys, time_slice)`, and `open_grid()` (`gw`, `area` km2, `landfrac`, `landmask`). All loaders return lazy, dask-backed DataArrays chunked as `{"time": 120}`.
- `pippe/analysis.py` (imported as `an`): `annual_mean` (days-in-month weighted, `year` dim), `global_mean` (cos-lat weights by default), `land_mean(da, grid)` (area x landfrac weights), `anomaly(ens, ref=DEFAULT_KEY)`.
- `notebooks/`: visualization. Each notebook starts with a markdown cell naming its kernel (`pippe`). Keep logic that is reused, or that loads data, in `pippe/`, not in notebooks. Notebooks are numbered (`00-explore.ipynb`).

## Conventions that matter

- **Time is centered.** CESM stamps monthly means at the end of the interval (January reads as Feb 1). `load._open` replaces `time` with the midpoint of the time bounds before decoding, so `time.dt.year`/`month` are correct. Use the loaders rather than opening files directly.
- **Coordinates are rounded.** lnd files store lat/lon as float32 (off by up to 4e-6 deg from the atm doubles). The loaders cast to float64 and round to `COORD_DECIMALS = 4`, so atm, lnd and `open_grid` fields align exactly. Without that, xarray's outer join silently misaligns land and atm fields.
- **Ensembles:** `open_ensemble` concatenates on a `member` dim (keys) with `param`/`minmax` coords. `time_slice` defaults to `config.COMMON_PERIOD` (years 49-188); with `time_slice=None` members of different lengths are NaN-padded.
- Opening a file keeps only the requested variable and its time bounds; the CESM bookkeeping variables (`date`, `co2vmr`, ...) are dropped.
- Keep everything lazy until a reduction; call `.compute()` on reduced results. For large jobs (daily data, many members), start a dask cluster (dask-jobqueue is in the env).

## Rules

- Do NOT create stub functions.
- Do NOT modify files outside this repo, and never write to the simulation campaign storage. Write derived data and figures to `config.PROC_DIR` / `config.FIG_DIR`.
- Keep the repo self-contained: no imports from the user's other projects or packages.
- Add comments that aid readability; keep them concise.
