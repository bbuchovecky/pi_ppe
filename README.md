# pi_ppe

Exploratory analysis of the CESM2 preindustrial slab-ocean coupled perturbed
parameter ensemble (PI PPE): 36 one-at-a-time CLM5 parameter perturbations
(`COUP0001`–`COUP0037` except `COUP0002`, min/max of 18 parameters) plus the default run `COUP0000`.

## Layout

| Path | Contents |
| --- | --- |
| `pippe/config.py` | Every data and output path, ensemble constants |
| `pippe/load.py` | Open model output as lazy xarray objects (`open_var`, `open_ensemble`, `open_grid`) |
| `pippe/analysis.py` | Reductions and anomalies (`annual_mean`, `global_mean`, `land_mean`, `anomaly`) |
| `notebooks/` | Visualization and exploration |
| `pyproject.toml` | Package metadata and the pixi env (`[tool.pixi.*]`) |
| `pixi.lock` | Exact versions of the env |

## Data

- Simulations (read-only): `/glade/campaign/cgd/tss/people/czarakas/CoupledPPE/coupled_simulations/`
- Member → parameter crosswalk: `data/CLM5PPE_coupledPPE_crosswalk.csv` (copied from `/glade/u/home/czarakas/coupled_PPE/code/02_set_up_ensemble/`)
- Outputs: `/glade/work/bbuchovecky/pi_ppe/{proc,fig}`

## Setup

The env is managed by [pixi](https://pixi.sh). One-time setup so envs and the
package cache go to /glade/work instead of home:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi config set --global detached-environments /glade/work/$USER/pixi/envs
export PIXI_CACHE_DIR=/glade/work/$USER/pixi/cache   # also in ~/.bashrc
```

Then, from the repo:

```bash
pixi install       # create the env from pixi.lock (pippe installed editable)
pixi run kernel    # register the `pippe` Jupyter kernel for the notebooks
```

Add a dependency with `pixi add <pkg>` and commit the updated `pixi.lock`.

## Usage

```python
import pippe.load as load
import pippe.analysis as an

ts = load.open_ensemble("TS", gcomp="atm", time_slice=slice("0049", "0188"))
gts = an.global_mean(an.annual_mean(ts))
anom = an.anomaly(gts)          # each member minus COUP0000
```
