# A-mat-Journal
For a journal publication

## Running the simulations
The repository already includes the 2D plane-strain validation model (`mpm_validation.py`) and a parametric sweep driver (`param_sweep.py`). You can run both directly with Python once the dependencies are installed.

### 1) Install dependencies
The scripts rely on standard scientific Python packages. Install them in a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy pandas matplotlib pyarrow
```

### 2) Run a single validation simulation
`mpm_validation.py` exposes the `run_validation_simulation` helper. You can invoke it from the command line using a short Python snippet. The example below runs the baseline Liu et al. case (plane strain with equivalent width) and prints the ultimate load along with basic diagnostics:

```bash
python - <<'PY'
from mpm_validation import run_validation_simulation

result = run_validation_simulation(plot_results=False)
print("Ultimate load (kN):", result["ultimate_load"])
print("Steps computed:", len(result["loads"]))
PY
```

Key outputs returned by `run_validation_simulation` include:
- `ultimate_load` (kN): peak load from the load–displacement curve.
- `settlements`, `loads`, `times`: arrays for further post-processing or plotting.
- `foundation_area`, `soil_surface`: geometry references used for dimensionless metrics.

### 3) Run the parametric sweep
`param_sweep.py` loops over undrained strength, equivalent width, mat thickness, and loading rate. It saves all cases (including load–displacement histories) to `results_raw.parquet` in the repository root.

```bash
python param_sweep.py
```

The resulting Parquet file includes raw parameters, derived ratios (`B_over_H`, `t_over_B`, `q_ult_over_su`), and arrays for settlements, loads, and time steps. You can load it for analysis or to train an ML surrogate:

```bash
python - <<'PY'
import pandas as pd

df = pd.read_parquet("results_raw.parquet")
print(df.head())
print("Total simulations:", len(df))
PY
```

### 4) Notes on runtime and outputs
- The sweep covers a Cartesian product of 10 `su` values × 4 widths × 4 thicknesses × 4 rates (640 simulations). On modest hardware, expect the sweep to take time; use a smaller subset by trimming the parameter lists if needed.
- Plots are disabled by default in the sweep to keep runs fast. For exploratory single cases, set `plot_results=True` in `run_validation_simulation` to visualize the load–displacement response.
