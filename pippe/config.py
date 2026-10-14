"""Paths and ensemble constants. Every data and output path lives here."""

from pathlib import Path

# --- Inputs (read-only shared storage) ---
# One directory per case: <SIM_ROOT>/<case>/<gcomp>/{hist,proc/tseries}
SIM_ROOT = Path("/glade/campaign/cgd/tss/people/czarakas/CoupledPPE/coupled_simulations")
# Maps CLM5 PPE parameter perturbations to coupled PPE member keys
CROSSWALK_CSV = Path("/glade/u/home/bbuchovecky/projects/pi_ppe/data/CLM5PPE_coupledPPE_crosswalk.csv")

# --- Outputs ---
WORK_ROOT = Path("/glade/work/bbuchovecky/pi_ppe")
PROC_DIR = WORK_ROOT / "proc"
FIG_DIR = Path("/glade/u/home/bbuchovecky/projects/pi_ppe/fig")

# --- Ensemble ---
DEFAULT_KEY = "COUP0000"            # control run with default parameters
DEFAULT_CASE_SUFFIX = "_PI_SOM"
MEMBER_CASE_SUFFIX = "_PI_SOM_v02"  # every perturbed member (COUP0012_PI_SOM_v05 is an unused stub)

# Component name -> model name in the history file names
MODEL_NAMES = {"atm": "cam", "lnd": "clm2"}

# Common period across all members, excluding first 40 year throwaway (spinup) period
COMMON_PERIOD = slice("0089", "0188")

# --- Plotting ---
PARAM_COLORS = {
    "#3B00FA": ["fff", "frac_sat_soil_dsl_init", "d_max"],
    "#800F7E": ["sand_pf", "upplim_destruct_metamorph", "z0mr", "zetamaxstable", "zsno"],
    "#278A28": ["kmax", "medlynslope", "medlynintercept"],
    "#38AFA9": ["jmaxb0", "jmaxb1", "tpu25ratio"],
    "#D5A733": ["rhosnir"],
    "#93EC93": ["lmrha"],
    "#F9A92A": ["maximum_leaf_wetted_fraction", "nstem"],
}