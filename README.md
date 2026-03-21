# Single-Column ParFlow-CLM ET Simulation

Run PF-CLM single-column simulations at any Ameriflux site using improved
CLM physics (Medlyn stomata, CLM5 tanh interception, canopy clumping).
Compare modeled latent heat against tower observations.

## Prerequisites

### ParFlow (v3.14.1+)

Requires ParFlow with CLM ET improvements from the `feature/clm_et` branch
(Medlyn stomata, CLM5 tanh interception, canopy clumping support).

Build from source: https://github.com/parflow/parflow

Set `PARFLOW_DIR` to your installation:
```bash
export PARFLOW_DIR=/path/to/parflow/install
```

### Python Environment

```bash
pip install parflow subsettools hf_hydrodata xarray numpy pandas matplotlib bokeh
```

Or with conda:
```bash
conda install -c conda-forge parflow subsettools hf_hydrodata xarray numpy pandas matplotlib bokeh
```

### HydroData Account (free)

1. Sign up: https://hydrogen.princeton.edu/signup
2. Get your API PIN: https://hydrogen.princeton.edu/pin
3. Register once in Python:
```python
import hf_hydrodata as hf
hf.register_api_pin("your_email", "your_pin")
```

## Quick Start

1. **`locate_plot_station_get_forcing.ipynb`** — Pick a site, query subsurface parameters, download CW3E forcing, prepare CLM input files.

2. **`Single_Column_PFCLM_netcdf.ipynb`** — Configure soil/WTD parameters, run ParFlow-CLM with improved physics, verify output.

3. **`pfclm_ameriflux_compare.ipynb`** — Load output, fetch Ameriflux observations, compute metrics (KGE, NSE, RMSE, bias), plot time series and scatter plots.

## Tested Sites

| Site ID | Name | IGBP | State | WY | KGE |
|---------|------|------|-------|----|-----|
| US-Slt | Silas Little | DBF | NJ | 2012 | 0.48 |
| US-xUK | NEON Univ. of Kansas | DBF | KS | 2024 | 0.45 |
| US-xBL | NEON Blandy Farm | DBF | VA | 2024 | 0.42 |
| US-GLE | GLEES | ENF | WY | 2020 | 0.15 |
| US-Ro5 | Rosemount I18 South | CRO | MN | 2024 | 0.68 |
| US-Ro1 | Rosemount G21 | CRO | MN | 2016 | 0.55 |
| US-Ro2 | Rosemount C7 | CRO | MN | 2016 | 0.61 |
| US-Fwf | Flagstaff Wildfire | GRA | AZ | 2008 | 0.47 |
| US-Mpj | Mountainair Pinyon-Juniper | WSA | NM | 2024 | 0.35 |
| US-Ton | Tonzi Ranch | WSA | CA | 2024 | 0.30 |
| US-xSR | NEON Santa Rita | OSH | AZ | 2024 | 0.40 |
| US-xJR | NEON Jornada | OSH | NM | 2024 | 0.38 |
| US-xDL | NEON Dead Lake | MF | AL | 2024 | 0.52 |

KGE values are from the `phase8_clump` configuration (best overall).

## Physics Configuration

The shipped CLM input files implement the `phase8_clump` configuration:

- **Medlyn stomatal conductance** (`StomataScheme = "Medlyn"`): VPD-based stomata replacing Ball-Berry. PFT-dependent g1 parameters in `drv_vegp.dat`.
- **CLM5 tanh canopy interception** (`InterceptionScheme = "CLM5Tanh"`): `fpi = tanh(LAI+SAI)`, replacing the CLM3 `0.25*(1-exp(-0.5*LAI))` formula.
- **Canopy clumping** (He et al. 2012): PFT-dependent clumping indices in `drv_vegp.dat`, reducing effective LAI for radiation transfer in forest canopies.
- **CLM4.5 optical/structural parameters**: Updated leaf/stem reflectance and transmittance.
- **PFT-dependent Vcmax**: Custom photosynthesis with PFT-specific `vcmx25` values.

## File Structure

```
clm_inputs/
  drv_vegp.dat               # PFT parameters (CLM4.5 + clumping)
  drv_clmin_template.dat     # CLM driver template (dates patched at runtime)
helpers.py                   # vegm builder, clmin patcher, IGBP/soil tables
locate_plot_station_get_forcing.ipynb
Single_Column_PFCLM_netcdf.ipynb
pfclm_ameriflux_compare.ipynb
```

## References

- Maxwell, R.M. & Miller, N.L. (2005). Development of a coupled land surface and groundwater model. J. Hydrometeorol.
- Medlyn, B.E. et al. (2011). Reconciling the optimal and empirical approaches to modelling stomatal conductance. Global Change Biology.
- He, L. et al. (2012). Global clumping index map derived from the MODIS BRDF product. Remote Sensing of Environment.
