# Random forest forcing bias correction

This folder archives the random forest (RF) bias correction used in
Maxwell (in revision, Journal of Hydrology): two global RF regressors
that predict water-year CW3E temperature and precipitation bias at
SNOTEL sites from site and forcing features.

## Contents

- `plot_forcing_bias_rfcorrected.py` — the exact script used: trains
  both RFs, produces cross-validated skill figures, and writes the
  corrected site-year table.  Paths at the top of the script point to
  the analysis workspace layout (`data/forcing_bias/`); place the input
  CSV accordingly or edit `DATA_CSV` / `OUT_CSV`.
- `all_siteyears_with_temp.csv` — input: 9,258 SNOTEL site-years
  (WY1985-2024) with observed temperature and precipitation biases and
  the feature columns below.
- `all_siteyears_rfcorrected.csv` — output: the same site-years with
  RF-predicted biases and corrected values, as used in Experiment 3.

## Model configuration (fixed in the script)

- `RandomForestRegressor(n_estimators=200, max_depth=12,
  min_samples_leaf=20, random_state=42)`, scikit-learn.
- Features: elevation_m, latitude, longitude, cw3e_mean_temp_c,
  prec_cw3e_total_mm, plus one-hot HUC2 region dummies; standardized
  with `StandardScaler`.
- Cross validation: site-grouped 5-fold.  Sites are permuted with
  `numpy.random.RandomState(42)` and assigned to folds round-robin, so
  no site appears in both train and test folds.  Reported skill is
  pooled out-of-fold (`cross_val_predict`).
- Both random seeds (fold assignment and RF) are 42; no trained model
  binary is archived because retraining from this folder is exact and
  takes minutes.

## Application

Corrections are applied uniformly across all hours of the water year:
precipitation is scaled by the predicted total bias and temperature is
shifted by the predicted mean bias, as described in the paper's
RF-correction section.
