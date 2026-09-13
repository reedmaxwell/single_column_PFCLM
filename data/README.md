# Paper data tables

Processed data tables for Maxwell (in revision, Journal of Hydrology).

- `Table_S1_siteyears.csv` — the 220 experiment site-years: station IDs
  and names, state, coordinates, elevation, water year, CW3E temperature
  and precipitation biases, experiment group (1 development / 2 low-bias
  validation / 3 high-bias test), and notes.  Built from the experiment
  selection files and the deduplicated forcing-bias pool.
- `unified_metrics.csv` — Experiment 1 per-site-year metrics for the 40
  retained configurations (800 rows): peak SWE and bias, peak-date and
  melt-out bias, RMSE, NSE, correlation, configuration and study group.
- `calibration_metrics.csv` — Experiment 2 (low-bias validation)
  per-site-year metrics, 6 configurations x 100 site-years.
- `highbias_metrics.csv` — Experiment 3 (high-bias test) per-site-year
  metrics, 4 configurations (baseline and SZ3, each with raw and
  RF-corrected CW3E forcing) x 100 site-years.

Melt-out date in all metrics tables: first day on or after 1 February
with SWE below 10 mm following the spring peak.
