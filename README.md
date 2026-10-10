# Single-Column ParFlow-CLM Examples

Two parallel worked examples of single-column PF-CLM simulations with improved
CLM physics, organized by topic:

- **`et/`** — ET example (Medlyn stomata, CLM5 tanh interception, canopy clumping)
  compared against Ameriflux flux-tower observations.
- **`snow/`** — Snow example (fractional snow cover, albedo decay, shrubland land
  cover) compared against SNOTEL SWE observations.

Each topic is a three-notebook workflow that shares site-configuration and
forcing infrastructure through the top-level `helpers.py`.

## Associated Manuscripts

This repository is the code and data archive for two papers; the examples
here follow their model configurations:

- **Snow** (`snow/`, `rf/`, `data/`): Maxwell, R.M., *Land surface model snow
  formulation sensitivity and a solar-zenith-angle snow covered area scheme
  evaluated across the western United States*, Journal of Hydrology, in
  revision.  The `rf/` folder archives the random forest forcing bias
  correction used in that study (exact script, random seeds, site-grouped
  cross-validation folds, input and output site-year tables; see
  `rf/README.md`), and `data/` holds the station lists, experiment groups,
  and processed per-site-year metrics for the paper's three experiments
  (see `data/README.md`).
- **ET** (`et/`): Maxwell, R.M., Journal of Hydrology X, in review.

Citations will be updated with final titles and DOIs upon acceptance.

## Prerequisites

### ParFlow (v3.15.0)

Both examples run on ParFlow v3.15.0 (https://github.com/parflow/parflow/releases/tag/v3.15.0), which includes the snow-physics options. Earlier CLM-physics PRs
are merged:

| PR | Merged | What it adds |
|----|--------|--------------|
| #695 | 2026-01-28 | CLM snow parameterization options |
| #698 | 2026-02-02 | Extended CLM snow parameterization |
| #701 | 2026-02-11 | Additional CLM snow formulations |
| #709 | 2026-03-11 | SZA-modulated fractional snow cover |
| #712 | 2026-03-19 | CLM ET improvements (Medlyn, CLM5 interception, PFT photosynthesis) |

Build from source: https://github.com/parflow/parflow

#### Codespaces build (class branch)

The `.devcontainer/Dockerfile` does not build v3.15.0.  It builds the
`class-et-2026` branch of https://github.com/reedmaxwell/parflow, which is
`parflow/master` plus two open ET fixes that the ET example uses.  The
Dockerfile pins the branch to one commit so every rebuild compiles the same
source.

| PR | Status | What it adds |
|----|--------|--------------|
| #769 | open | `Solver.CLM.VonKarman` key (default 0.378; the ET notebook sets 0.4) |
| #775 | open | Dry-canopy transpiration fix (`fwet` is set to 0 when the canopy is dry) |

The Dockerfile also builds HDF5 with `--enable-build-mode=production`.  HDF5
1.12.0 and earlier default to a debug build, which made ParFlow's NetCDF output
about 20 times slower than the solver in Codespaces.  If you build HDF5 from
source anywhere else, check `h5pcc -showconfig` for `Build Mode: production`.

Set `PARFLOW_DIR` to your install:
```bash
export PARFLOW_DIR=/path/to/parflow/install
```

### Python Environment

```bash
pip install pftools subsettools hf_hydrodata xarray netcdf4 numpy pandas matplotlib bokeh
```

(`pftools` is the PyPI/conda-forge name of the ParFlow Python package,
imported as `parflow`.)

Or with conda:
```bash
conda install -c conda-forge pftools subsettools hf_hydrodata xarray netcdf4 numpy pandas matplotlib bokeh
```

### HydroData Account (free)

1. Sign up: https://hydrogen.princeton.edu/signup
2. Get your API PIN: https://hydrogen.princeton.edu/pin
3. Register once in Python:
```python
import hf_hydrodata as hf
hf.register_api_pin("your_email", "your_pin")
```

## Repository Layout

```
single_column_PFCLM/
├── README.md                        # this file
├── helpers.py                       # shared site-config, CW3E, IGBP/soil tables,
│                                    #   SNOTEL catalog, vegm builder
├── clm_inputs/
│   ├── drv_clmin_template.dat       # shared CLM driver template (both topics)
│   ├── et/
│   │   └── drv_vegp.dat             # clm_et_improved defaults
│   └── snow/
│       └── drv_vegp.dat             # clm_snow_improved defaults
├── et/                              # ET example (3 notebooks)
│   ├── locate_plot_station_get_forcing.ipynb
│   ├── Single_Column_PFCLM_netcdf.ipynb
│   └── pfclm_ameriflux_compare.ipynb
├── snow/                            # Snow example (3 notebooks)
│   ├── locate_plot_station_get_forcing.ipynb
│   ├── Single_Column_PFCLM_netcdf.ipynb
│   └── pfclm_snotel_compare.ipynb
├── rf/                              # RF forcing bias correction (snow paper):
│   │                                #   script, seeds, CV folds, in/out tables
│   ├── README.md
│   ├── plot_forcing_bias_rfcorrected.py
│   ├── all_siteyears_with_temp.csv
│   └── all_siteyears_rfcorrected.csv
├── data/                            # Snow-paper tables: site-years (Table S1),
│   │                                #   per-site-year metrics for Experiments 1-3
│   ├── README.md
│   ├── Table_S1_siteyears.csv
│   ├── unified_metrics.csv
│   ├── calibration_metrics.csv
│   └── highbias_metrics.csv
└── runs/                            # run output, subfoldered by topic
    ├── et/
    └── snow/
```

## Quick Start

Pick a topic, then run the three notebooks in order from that topic's folder.

### ET example (`et/`)

1. **`locate_plot_station_get_forcing.ipynb`** — Pick an Ameriflux site, query
   CONUS2 subsurface + water-table depth, download CW3E forcing, write CLM
   inputs and `site_config.txt`.
2. **`Single_Column_PFCLM_netcdf.ipynb`** — Configure and run PF-CLM with the
   `clm_et_improved` physics defaults.
3. **`pfclm_ameriflux_compare.ipynb`** — Compare modeled latent heat against
   Ameriflux observations (KGE, NSE, RMSE, bias, time series, ET components).

### Snow example (`snow/`)

1. **`locate_plot_station_get_forcing.ipynb`** — Pick a SNOTEL site, download
   CW3E forcing, preview observed SWE, write CLM inputs and `site_config.txt`.
2. **`Single_Column_PFCLM_netcdf.ipynb`** — Configure and run PF-CLM with the
   `clm_snow_improved` physics defaults (shrubland + slow albedo decay + high
   fresh albedo). An SZA-scheme variant is commented in the same cell.
3. **`pfclm_snotel_compare.ipynb`** — Compare modeled SWE against SNOTEL
   observations (NSE, RMSE, peak |bias|%, melt-out day Δ, time series, scatter,
   CW3E-vs-SNOTEL precipitation check).

## Subsurface Structure (both topics)

Both examples use the same 8m, 10-layer single-column domain with two zones:

| Zone    | Layers  | Physical depth                 | Source                    |
|---------|---------|--------------------------------|---------------------------|
| Soil    | 6-9 (top)   | 2.0 m (1.0 + 0.6 + 0.3 + 0.1 m) | CONUS2.1 top-layer soil type  |
| Geology | 0-5 (bot) | 6.0 m (6 × 1.0 m)              | CONUS2.1 layer-4 geology type |

Soil hydraulic properties (Ksat, porosity, VG α/n) come from the CONUS2.1 soil
texture table (13 types). Geology uses per-type Ksat + porosity with domain-
default Van Genuchten parameters (α=0.5, n=2.5).

Water table depth is queried from CONUS2 baseline or Ma et al. (2025) 30m
products in the ET notebook; the snow notebook defaults to a deep (-10 m) BC
since mountain SNOTEL sites are snowmelt-driven, not groundwater-fed.

## Physics Configuration

### `clm_et_improved` (shipped in `clm_inputs/et/`)

- **Medlyn stomatal conductance** (`StomataScheme="Medlyn"`): VPD-based stomata
  replacing Ball-Berry. PFT-dependent g1 parameters in `drv_vegp.dat`.
- **CLM5 tanh canopy interception** (`InterceptionScheme="CLM5Tanh"`):
  `fpi = tanh(LAI+SAI)`, replacing the CLM3 `0.25·(1-exp(-0.5·LAI))` formula.
- **Canopy clumping** (He et al. 2012): PFT-dependent clumping indices in
  `drv_vegp.dat`, reducing effective LAI for radiation transfer in forest
  canopies.
- **CLM4.5 optical/structural parameters**: Updated leaf/stem reflectance and
  transmittance.
- **PFT-dependent Vcmax**: Custom photosynthesis with PFT-specific `vcmx25`.

### `clm_snow_improved` (shipped in `clm_inputs/snow/`)

- **Fractional snow cover**: `FracSnoScheme="CLM"`, `FracSnoRoughness=1e-8`.
  This was the foundation fix in the sensitivity study — reduced peak
  |bias| from 24% to 13%.
- **Albedo decay (slow)**: `AlbedoDecayVis=0.3`, `AlbedoDecayNir=0.1` — slows
  snow aging so fresh-snow albedo persists longer into spring.
- **Fresh-snow albedo (tuned high)**: `AlbedoVisNew=0.97`, `AlbedoNirNew=0.67`.
- **Shrubland land cover** (IGBP 7): forces a snow-friendly canopy radiative
  transfer treatment — best-performing IGBP class in the low-bias study.
- **Optional SZA-modulated fSCA** (commented in Notebook 2): the interpolating
  FracSnoScheme="SZA" formulation from PR #709, with `FracSnoRoughnessMin/Max`,
  `FracSnoGammaSZA`, and `FracSnoAvgWindow`.

## Tested Sites — ET (Ameriflux)

These are the Ameriflux sites from the ET sensitivity study. KGE values are
for the `clm_et_improved` (phase8_clump) configuration.

| Site ID | Name                        | IGBP | State | WY   | KGE  |
|---------|-----------------------------|------|-------|------|------|
| US-Slt  | Silas Little                | DBF  | NJ    | 2012 | 0.48 |
| US-xUK  | NEON Univ. of Kansas        | DBF  | KS    | 2024 | 0.45 |
| US-xBL  | NEON Blandy Farm            | DBF  | VA    | 2024 | 0.42 |
| US-GLE  | GLEES                       | ENF  | WY    | 2020 | 0.15 |
| US-Ro5  | Rosemount I18 South         | CRO  | MN    | 2024 | 0.68 |
| US-Ro1  | Rosemount G21               | CRO  | MN    | 2016 | 0.55 |
| US-Ro2  | Rosemount C7                | CRO  | MN    | 2016 | 0.61 |
| US-Fwf  | Flagstaff Wildfire          | GRA  | AZ    | 2008 | 0.47 |
| US-Mpj  | Mountainair Pinyon-Juniper  | WSA  | NM    | 2024 | 0.35 |
| US-Ton  | Tonzi Ranch                 | WSA  | CA    | 2024 | 0.30 |
| US-xSR  | NEON Santa Rita             | OSH  | AZ    | 2024 | 0.40 |
| US-xJR  | NEON Jornada                | OSH  | NM    | 2024 | 0.38 |
| US-xDL  | NEON Dead Lake              | MF   | AL    | 2024 | 0.52 |

## Showcase Sites — Snow (SNOTEL)

The snow notebook ships a 6-site showcase picked for geographic diversity
and recent CW3E-covered water years:

| Site               | Region            | State | Elev (m) | WY   | Triplet      |
|--------------------|-------------------|-------|----------|------|--------------|
| Paradise           | Cascades          | WA    | 1564     | 2022 | 679:WA:SNTL  |
| CSS_Lab            | Sierra Nevada     | CA    | 2103     | 2022 | 428:CA:SNTL  |
| Togwotee_Pass      | Wyoming           | WY    | 2936     | 2020 | 822:WY:SNTL  |
| Berthoud_Summit    | Colorado Rockies  | CO    | 3536     | 2024 | 335:CO:SNTL  |
| Brighton           | Wasatch           | UT    | 2667     | 2024 | 366:UT:SNTL  |
| Quemazon           | Southern Rockies  | NM    | 2926     | 2023 | 708:NM:SNTL  |

### Extending to more sites

The `snow_model_sensitivity` study identified 20 **low-bias site-years**
(|T bias| < 1°C and |P bias| < 10% at the SNOTEL gauge) that are reliable
for PF-CLM evaluation:

| Region              | Sites                                          | Years                |
|---------------------|------------------------------------------------|----------------------|
| Cascades            | Stevens_Pass, Paradise                         | 2020, 2022, 2023     |
| Sierra Nevada       | Leavitt_Lake, CSS_Lab, Donner_Summit           | 2015, 2021, 2022, 2024 |
| Wyoming             | Togwotee_Pass, Canyon                          | 1995, 2000, 2020, 2024 |
| Colorado Rockies    | Berthoud_Summit, Schofield_Pass                | 2024                 |
| Northern Rockies    | Northeast_Entrance                             | 1995                 |
| Wasatch             | Brighton                                       | 2024                 |
| Southern Rockies    | Quemazon                                       | 2020, 2023           |

To use another site:
1. Add a new entry to `SNOTEL_SITES` in `helpers.py` (coords, elev_m, state,
   region, triplet). Triplets can be looked up at
   https://www.nrcs.usda.gov/wps/portal/wcc/home/.
2. Set `site_name` and `water_year` in Notebook 1.
3. The notebooks pick up the rest automatically.

## Choosing a Site and Water Year

**For ET:**

- **Data coverage**: use the Bokeh preview in the ET Notebook 1 to check
  Ameriflux latent-heat coverage.
- **IGBP type**: CRO sites tend to perform best (KGE 0.55-0.68). Forest sites
  (DBF, ENF, MF) do well with canopy clumping. WSA/OSH are more WTD-sensitive.
- **Water year**: choose a year with complete CW3E coverage (v1.0 covers
  WY2003-present).

**For snow:**

- **Pair elevation with air temperature**: shallow or intermittent-snow sites
  (Pacific NW low-elevation, arid SW) are harder to fit than continental
  high-elevation sites.
- **Forcing bias check**: Notebook 3 plots cumulative CW3E vs. SNOTEL precip.
  If CW3E/SNOTEL > 1.15 or < 0.85, expect model SWE to be systematically off.
- **Peak SWE year**: the showcase years were chosen from the low-bias set.
  Run them first before experimenting with more difficult site-years.

## Water Table Depth (ET only)

WTD is the most sensitive parameter for ET in single-column simulations.
The snow notebook defaults to a deep WTD (-10 m, below the 8m domain) since
SNOTEL ridges are snowmelt-driven, not groundwater-fed. See the ET Notebook 1
for full WTD sourcing options.

## Troubleshooting

**Solver failure (run stops before completing the water year):**
- Check the ParFlow log (`pfclm_sc.out.log`) for timestep cutting. If dt
  drops below ~0.01 and the run stalls, the solver cannot converge.
- Common cause: sharp property contrast at the soil/geology interface combined
  with a wetting front or freeze/thaw event. Try adjusting WTD or increasing
  `Solver.Nonlinear.MaxIter`.

**HydroData errors:**
- `register_api_pin` only needs to run once per machine. If it fails, check
  your credentials at https://hydrogen.princeton.edu/pin.
- Some Ameriflux variables (e.g., VPD, wind) are not available at all sites.
- SNOTEL triplets: if a fetch returns empty, verify the triplet at
  https://www.nrcs.usda.gov/wps/portal/wcc/home/ and update `helpers.SNOTEL_SITES`.

**Stale kernel after file edits:**
- If `helpers.py` is updated but a notebook throws `ImportError`, restart
  the kernel. Jupyter caches imports and won't pick up on-disk changes
  without a restart.

## References

- Maxwell, R.M. (in revision). Land surface model snow formulation sensitivity
  and a solar-zenith-angle snow covered area scheme evaluated across the
  western United States. Journal of Hydrology.
- Maxwell, R.M. (in review). Journal of Hydrology X.
- Maxwell, R.M. & Miller, N.L. (2005). Development of a coupled land surface
  and groundwater model. J. Hydrometeorol.
- Medlyn, B.E. et al. (2011). Reconciling the optimal and empirical approaches
  to modelling stomatal conductance. Global Change Biology.
- He, L. et al. (2012). Global clumping index map derived from the MODIS BRDF
  product. Remote Sensing of Environment.
- Abolafia-Rosenzweig, R. et al. (2022). Evaluation of snow albedo
  parameterizations in the CLM.
