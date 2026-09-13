#!/usr/bin/env python3
"""
RF-corrected CW3E temperature and precipitation bias analysis.

Trains global Random Forests to predict T and P bias from site/forcing features,
applies corrections to CW3E values, and evaluates the improvement.

Outputs:
  CSV:  data/forcing_bias/all_siteyears_rfcorrected.csv
  Figs: evaluation/figures/forcing_bias/
    - snotel_vs_cw3e_rfcorrected.png   (2x2 pred-obs: orig vs corrected, T and P)
    - bias_scatter_rfcorrected.png      (2x2 bias summary with corrected T and P)
    - bias_map_rfcorrected.png          (map colored by corrected bias categories)

Usage:
    cd ~/Projects/snow_model_sensitivity/evaluation/scripts
    source ~/miniforge3.1/etc/profile.d/conda.sh && conda activate subsettools
    python plot_forcing_bias_rfcorrected.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error

# ── paths ──────────────────────────────────────────────────────────────
DATA_CSV = Path(__file__).parent.parent.parent / "data" / "forcing_bias" / "all_siteyears_with_temp.csv"
METADATA_CSV = Path.home() / "Projects" / "wy2003_forcing_bias" / "data" / "snotel_metadata.csv"
OUT_CSV = Path(__file__).parent.parent.parent / "data" / "forcing_bias" / "all_siteyears_rfcorrected.csv"
FIG_DIR = Path(__file__).parent.parent / "figures" / "forcing_bias"

# ── constants ──────────────────────────────────────────────────────────
TEMP_THRESH = 1.0   # °C
PREC_THRESH = 10.0  # %

COLORS = {
    'LOW_BIAS':        '#2ca02c',
    'TEMP_BIAS_ONLY':  '#ff7f0e',
    'PRECIP_BIAS_ONLY':'#9467bd',
    'BOTH_BIASES':     '#d62728',
}
LABELS = {
    'LOW_BIAS':        'Low Bias',
    'TEMP_BIAS_ONLY':  'Temp Bias Only',
    'PRECIP_BIAS_ONLY':'Precip Bias Only',
    'BOTH_BIASES':     'Both Biases',
}
CATEGORY_ORDER = ['LOW_BIAS', 'TEMP_BIAS_ONLY', 'PRECIP_BIAS_ONLY', 'BOTH_BIASES']

FEATURE_COLS = ['elevation_m', 'latitude', 'longitude',
                'cw3e_mean_temp_c', 'prec_cw3e_total_mm']


# ── data loading ──────────────────────────────────────────────────────

def load_data():
    """Load QC'd CSV, join HUC, apply temp QC."""
    df = pd.read_csv(DATA_CSV)
    print(f"Loaded {len(df)} site-years from {DATA_CSV.name}")

    # Join HUC
    meta = pd.read_csv(METADATA_CSV)[['site_id', 'huc8']]
    df = df.merge(meta, on='site_id', how='left')
    df['huc2'] = df['huc8'].astype(str).str[:2]
    df.loc[df['huc2'].isin(['na', 'nan', '90']), 'huc2'] = np.nan

    # Temp QC: null bad SNOTEL temp rows
    has_source = df['source'] != 'sensitivity'
    bad_temp = has_source & df['snotel_mean_temp_c'].isna() & df['temp_bias_c'].notna()
    n_bad = bad_temp.sum()
    if n_bad > 0:
        df.loc[bad_temp, ['temp_bias_c', 'temp_mae_c', 'temp_rmse_c', 'temp_corr']] = np.nan
        print(f"  QC: nulled temp bias for {n_bad} rows")

    extreme = df['temp_bias_c'].abs() > 5.0
    n_ext = extreme.sum()
    if n_ext > 0:
        df.loc[extreme, ['temp_bias_c', 'temp_mae_c', 'temp_rmse_c', 'temp_corr']] = np.nan
        print(f"  QC: nulled {n_ext} rows with |temp_bias| > 5°C")

    return df


# ── generic RF trainer ───────────────────────────────────────────────

def _train_rf(df, target_col, label):
    """Train global RF on a bias target with site-grouped 5-fold CV.

    Returns (cv_predictions_series_aligned_to_df, stats_dict).
    """
    trainable = df.dropna(subset=FEATURE_COLS + [target_col]).copy()
    train_idx = trainable.index

    huc_dummies = pd.get_dummies(trainable['huc2'], prefix='huc2',
                                  drop_first=True, dtype=float)
    X = pd.concat([trainable[FEATURE_COLS].reset_index(drop=True),
                    huc_dummies.reset_index(drop=True)], axis=1)
    y = trainable[target_col].values
    site_ids = trainable['site_id'].values

    print(f"\n  {label} RF: {len(X)} rows, {X.shape[1]} features")

    # Site-grouped 5-fold CV
    unique_sites = np.unique(site_ids)
    rng = np.random.RandomState(42)
    site_to_fold = {s: i % 5 for i, s in enumerate(rng.permutation(unique_sites))}
    groups = np.array([site_to_fold[s] for s in site_ids])
    cv = [(np.where(groups != f)[0], np.where(groups == f)[0]) for f in range(5)]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    rf = RandomForestRegressor(n_estimators=200, max_depth=12,
                                min_samples_leaf=20, random_state=42,
                                n_jobs=-1)
    y_pred_cv = cross_val_predict(rf, X_scaled, y, cv=cv)

    rf.fit(X_scaled, y)
    importances = dict(zip(X.columns, rf.feature_importances_))

    r2 = r2_score(y, y_pred_cv)
    rmse = np.sqrt(mean_squared_error(y, y_pred_cv))
    print(f"  {label} RF CV: R² = {r2:.3f}, RMSE = {rmse:.2f}")
    top5 = sorted(importances.items(), key=lambda x: -x[1])[:5]
    print(f"  Top features: {[(k, f'{v:.3f}') for k, v in top5]}")

    # Align predictions back to full dataframe
    preds = pd.Series(np.nan, index=df.index)
    preds.loc[train_idx] = y_pred_cv

    return preds, {'r2': r2, 'rmse': rmse, 'importances': importances,
                   'y_true': y, 'y_pred': y_pred_cv, 'n': len(y)}


# ── correction logic ─────────────────────────────────────────────────

def train_and_correct(df):
    """Train RF for both T and P bias, apply corrections, recategorize."""

    # ── Precipitation (multiplicative correction) ─────────────────
    p_preds, p_stats = _train_rf(df, 'prec_total_bias_pct', 'Precip')

    df['rf_predicted_pbias_pct'] = p_preds
    df['prec_cw3e_corrected_mm'] = df['prec_cw3e_total_mm'].copy()
    p_ok = p_preds.notna() & df['prec_cw3e_total_mm'].notna()
    factor = (1.0 + df.loc[p_ok, 'rf_predicted_pbias_pct'] / 100.0).clip(lower=0.2)
    df.loc[p_ok, 'prec_cw3e_corrected_mm'] = df.loc[p_ok, 'prec_cw3e_total_mm'] / factor

    # Corrected precip bias vs SNOTEL
    df['prec_corrected_bias_pct'] = np.nan
    has_p = df['prec_cw3e_corrected_mm'].notna() & (df['prec_snotel_total_mm'] > 0)
    df.loc[has_p, 'prec_corrected_bias_pct'] = (
        (df.loc[has_p, 'prec_cw3e_corrected_mm']
         - df.loc[has_p, 'prec_snotel_total_mm'])
        / df.loc[has_p, 'prec_snotel_total_mm'] * 100.0
    )
    print(f"  Precip: corrected {p_ok.sum()}/{len(df)} rows")

    # ── Temperature (additive correction) ─────────────────────────
    t_preds, t_stats = _train_rf(df, 'temp_bias_c', 'Temp')

    df['rf_predicted_tbias_c'] = t_preds
    df['cw3e_temp_corrected_c'] = df['cw3e_mean_temp_c'].copy()
    t_ok = t_preds.notna() & df['cw3e_mean_temp_c'].notna()
    df.loc[t_ok, 'cw3e_temp_corrected_c'] = (
        df.loc[t_ok, 'cw3e_mean_temp_c'] - df.loc[t_ok, 'rf_predicted_tbias_c']
    )

    # Corrected temp bias vs SNOTEL
    df['temp_corrected_bias_c'] = np.nan
    has_t = df['cw3e_temp_corrected_c'].notna() & df['snotel_mean_temp_c'].notna()
    df.loc[has_t, 'temp_corrected_bias_c'] = (
        df.loc[has_t, 'cw3e_temp_corrected_c'] - df.loc[has_t, 'snotel_mean_temp_c']
    )
    print(f"  Temp:   corrected {t_ok.sum()}/{len(df)} rows")

    # ── Recategorize using both corrected biases ──────────────────
    _assign_categories(df)

    # ── Summary ───────────────────────────────────────────────────
    for label, orig_col, corr_col, thresh, unit in [
        ('Temp',   'temp_bias_c',          'temp_corrected_bias_c',   TEMP_THRESH, '°C'),
        ('Precip', 'prec_total_bias_pct',  'prec_corrected_bias_pct', PREC_THRESH, '%'),
    ]:
        orig = df[orig_col].dropna()
        corr = df[corr_col].dropna()
        print(f"\n  {label} bias ({unit}):")
        print(f"    Original:  median={orig.median():+.2f}, "
              f"MAE={orig.abs().mean():.2f}, within ±{thresh}: "
              f"{(orig.abs() <= thresh).mean()*100:.1f}%")
        print(f"    Corrected: median={corr.median():+.2f}, "
              f"MAE={corr.abs().mean():.2f}, within ±{thresh}: "
              f"{(corr.abs() <= thresh).mean()*100:.1f}%")

    return df, {'precip': p_stats, 'temp': t_stats}


def _assign_categories(df):
    """Assign bias_category using corrected T and P bias where available."""
    t_bias = df['temp_corrected_bias_c'].where(
        df['temp_corrected_bias_c'].notna(), df['temp_bias_c'])
    p_bias = df['prec_corrected_bias_pct'].where(
        df['prec_corrected_bias_pct'].notna(), df['prec_total_bias_pct'])

    t_ok = t_bias.abs() <= TEMP_THRESH
    p_ok = p_bias.abs() <= PREC_THRESH
    t_na = t_bias.isna()
    p_na = p_bias.isna()

    df['bias_category_corrected'] = 'BOTH_BIASES'
    df.loc[t_ok & p_ok, 'bias_category_corrected'] = 'LOW_BIAS'
    df.loc[~t_ok & p_ok, 'bias_category_corrected'] = 'TEMP_BIAS_ONLY'
    df.loc[t_ok & ~p_ok, 'bias_category_corrected'] = 'PRECIP_BIAS_ONLY'
    df.loc[t_na & p_ok, 'bias_category_corrected'] = 'LOW_BIAS'
    df.loc[t_na & ~p_ok, 'bias_category_corrected'] = 'PRECIP_BIAS_ONLY'
    df.loc[p_na & t_ok, 'bias_category_corrected'] = 'LOW_BIAS'
    df.loc[p_na & ~t_ok, 'bias_category_corrected'] = 'TEMP_BIAS_ONLY'
    df.loc[t_na & p_na, 'bias_category_corrected'] = 'LOW_BIAS'


# ── Figure 1: SNOTEL vs CW3E (2x2: T orig/corr, P orig/corr) ───────

def fig_snotel_vs_cw3e_corrected(df, rf_stats):
    """2×2: original and corrected CW3E vs SNOTEL for both T and P."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 13))

    # --- Row 1: Temperature ---
    t_mask = (df['snotel_mean_temp_c'].notna()
              & df['cw3e_mean_temp_c'].notna()
              & df['cw3e_temp_corrected_c'].notna())
    obs_t = df.loc[t_mask, 'snotel_mean_temp_c'].values
    raw_t = df.loc[t_mask, 'cw3e_mean_temp_c'].values
    cor_t = df.loc[t_mask, 'cw3e_temp_corrected_c'].values

    lim_t = [min(obs_t.min(), raw_t.min(), cor_t.min()) - 1,
             max(obs_t.max(), raw_t.max(), cor_t.max()) + 1]

    for ax, cw3e, title, cmap in [
        (axes[0, 0], raw_t, 'CW3E Original Temperature', 'viridis'),
        (axes[0, 1], cor_t, 'CW3E RF-Corrected Temperature', 'magma'),
    ]:
        hb = ax.hexbin(obs_t, cw3e, gridsize=50, cmap=cmap, mincnt=1,
                        norm=LogNorm(), alpha=0.9)
        plt.colorbar(hb, ax=ax, label='Count', shrink=0.8, pad=0.02)
        ax.plot(lim_t, lim_t, 'r-', lw=2, label='1:1')
        r = np.corrcoef(obs_t, cw3e)[0, 1]
        bias = np.mean(cw3e - obs_t)
        rmse = np.sqrt(np.mean((cw3e - obs_t)**2))
        ax.text(0.04, 0.96,
                f'r = {r:.3f}\nBias = {bias:+.2f} °C\n'
                f'RMSE = {rmse:.2f} °C\nn = {len(obs_t):,}',
                transform=ax.transAxes, fontsize=10, va='top',
                bbox=dict(facecolor='white', alpha=0.85, edgecolor='none'))
        ax.set_xlabel('SNOTEL Mean Temp (°C)', fontsize=11)
        ax.set_ylabel('CW3E Mean Temp (°C)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlim(lim_t); ax.set_ylim(lim_t)
        ax.set_aspect('equal')
        ax.legend(loc='lower right', fontsize=9)
        ax.grid(True, alpha=0.15)

    # --- Row 2: Precipitation ---
    p_mask = (df['prec_snotel_total_mm'].notna()
              & df['prec_cw3e_total_mm'].notna()
              & df['prec_cw3e_corrected_mm'].notna())
    obs_p = df.loc[p_mask, 'prec_snotel_total_mm'].values
    raw_p = df.loc[p_mask, 'prec_cw3e_total_mm'].values
    cor_p = df.loc[p_mask, 'prec_cw3e_corrected_mm'].values
    max_p = max(obs_p.max(), raw_p.max(), cor_p.max()) * 1.05

    for ax, cw3e, title, cmap in [
        (axes[1, 0], raw_p, 'CW3E Original Precipitation', 'viridis'),
        (axes[1, 1], cor_p, 'CW3E RF-Corrected Precipitation', 'magma'),
    ]:
        hb = ax.hexbin(obs_p, cw3e, gridsize=50, cmap=cmap, mincnt=1,
                        norm=LogNorm(), alpha=0.9)
        plt.colorbar(hb, ax=ax, label='Count', shrink=0.8, pad=0.02)
        ax.plot([0, max_p], [0, max_p], 'r-', lw=2, label='1:1')
        r = np.corrcoef(obs_p, cw3e)[0, 1]
        total_bias = (cw3e.sum() - obs_p.sum()) / obs_p.sum() * 100
        rmse = np.sqrt(np.mean((cw3e - obs_p)**2))
        ax.text(0.04, 0.96,
                f'r = {r:.3f}\nTotal bias = {total_bias:+.1f}%\n'
                f'RMSE = {rmse:.0f} mm\nn = {len(obs_p):,}',
                transform=ax.transAxes, fontsize=10, va='top',
                bbox=dict(facecolor='white', alpha=0.85, edgecolor='none'))
        ax.set_xlabel('SNOTEL Total Precip (mm)', fontsize=11)
        ax.set_ylabel('CW3E Total Precip (mm)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlim(0, max_p); ax.set_ylim(0, max_p)
        ax.set_aspect('equal')
        ax.legend(loc='lower right', fontsize=9)
        ax.grid(True, alpha=0.15)

    t_r2 = rf_stats['temp']['r2']
    p_r2 = rf_stats['precip']['r2']
    fig.suptitle(f'CW3E vs SNOTEL: Original and RF-Corrected\n'
                 f'(RF CV R²: T = {t_r2:.3f}, P = {p_r2:.3f})',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    outpath = FIG_DIR / "snotel_vs_cw3e_rfcorrected.png"
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    print(f"Saved: {outpath}")
    plt.close()


# ── Figure 2: bias scatter summary (both corrected) ─────────────────

def fig_scatter_corrected(df):
    """2x2: corrected-T vs corrected-P scatter, T histogram, P histogram,
    bias vs elevation."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    t_col = 'temp_corrected_bias_c'
    p_col = 'prec_corrected_bias_pct'
    cat_col = 'bias_category_corrected'

    # --- Top-left: scatter of corrected T vs corrected P bias ---
    ax = axes[0, 0]
    has_both = df[t_col].notna() & df[p_col].notna()
    for cat in CATEGORY_ORDER:
        mask = has_both & (df[cat_col] == cat)
        if mask.sum() > 0:
            ax.scatter(df.loc[mask, t_col], df.loc[mask, p_col],
                       c=COLORS[cat], label=f"{LABELS[cat]} ({mask.sum()})",
                       s=12, alpha=0.4, edgecolors='none')

    ax.axhline(PREC_THRESH, color='gray', ls='--', lw=0.8, alpha=0.6)
    ax.axhline(-PREC_THRESH, color='gray', ls='--', lw=0.8, alpha=0.6)
    ax.axvline(TEMP_THRESH, color='gray', ls='--', lw=0.8, alpha=0.6)
    ax.axvline(-TEMP_THRESH, color='gray', ls='--', lw=0.8, alpha=0.6)
    ax.axhspan(-PREC_THRESH, PREC_THRESH, color='green', alpha=0.04, zorder=0)
    ax.axvspan(-TEMP_THRESH, TEMP_THRESH, color='green', alpha=0.04, zorder=0)
    ax.set_xlabel('RF-Corrected Temperature Bias (°C)')
    ax.set_ylabel('RF-Corrected Precipitation Bias (%)')
    ax.set_title('Corrected T vs Corrected P Bias')
    ax.legend(loc='upper left', fontsize=7, markerscale=2)
    ax.set_xlim(-6, 6); ax.set_ylim(-80, 80)
    ax.grid(True, alpha=0.2)

    # --- Top-right: temp bias histogram (original + corrected) ---
    ax = axes[0, 1]
    t_orig = df['temp_bias_c'].dropna()
    t_corr = df[t_col].dropna()
    ax.hist(t_orig, bins=60, range=(-6, 6), color='#1f77b4', alpha=0.35,
            edgecolor='white', lw=0.3, label=f'Original (n={len(t_orig):,})')
    ax.hist(t_corr, bins=60, range=(-6, 6), color='#2ca02c', alpha=0.55,
            edgecolor='white', lw=0.3, label=f'RF-Corrected (n={len(t_corr):,})')
    ax.axvline(0, color='k', ls='-', lw=0.8)
    ax.axvline(-TEMP_THRESH, color='gray', ls='--', lw=0.8)
    ax.axvline(TEMP_THRESH, color='gray', ls='--', lw=0.8)
    ax.axvspan(-TEMP_THRESH, TEMP_THRESH, color='green', alpha=0.08)
    med_orig = t_orig.median()
    med_corr = t_corr.median()
    ax.axvline(med_orig, color='#1f77b4', ls='-', lw=1.5,
               label=f'Orig median = {med_orig:+.2f}°C')
    ax.axvline(med_corr, color='#2ca02c', ls='-', lw=1.5,
               label=f'Corr median = {med_corr:+.2f}°C')
    ax.set_xlabel('Temperature Bias (°C)')
    ax.set_ylabel('Count')
    ax.set_title('Temperature Bias: Original vs RF-Corrected')
    ax.legend(fontsize=8); ax.grid(True, alpha=0.2)

    # --- Bottom-left: precip bias histogram (original + corrected) ---
    ax = axes[1, 0]
    p_orig = df['prec_total_bias_pct'].dropna()
    p_corr = df[p_col].dropna()
    ax.hist(p_orig, bins=60, range=(-80, 80), color='#9467bd', alpha=0.35,
            edgecolor='white', lw=0.3, label=f'Original (n={len(p_orig):,})')
    ax.hist(p_corr, bins=60, range=(-80, 80), color='#2ca02c', alpha=0.55,
            edgecolor='white', lw=0.3, label=f'RF-Corrected (n={len(p_corr):,})')
    ax.axvline(0, color='k', ls='-', lw=0.8)
    ax.axvline(-PREC_THRESH, color='gray', ls='--', lw=0.8)
    ax.axvline(PREC_THRESH, color='gray', ls='--', lw=0.8)
    ax.axvspan(-PREC_THRESH, PREC_THRESH, color='green', alpha=0.08)
    med_orig_p = p_orig.median()
    med_corr_p = p_corr.median()
    ax.axvline(med_orig_p, color='#9467bd', ls='-', lw=1.5,
               label=f'Orig median = {med_orig_p:+.1f}%')
    ax.axvline(med_corr_p, color='#2ca02c', ls='-', lw=1.5,
               label=f'Corr median = {med_corr_p:+.1f}%')
    ax.set_xlabel('Precipitation Bias (%)')
    ax.set_ylabel('Count')
    ax.set_title('Precipitation Bias: Original vs RF-Corrected')
    ax.legend(fontsize=8); ax.grid(True, alpha=0.2)

    # --- Bottom-right: corrected bias vs elevation (both T and P) ---
    ax = axes[1, 1]
    has_elev = df['elevation_m'].notna()

    # Corrected temp
    tm = has_elev & df[t_col].notna()
    ax.scatter(df.loc[tm, 'elevation_m'], df.loc[tm, t_col],
               c='#1f77b4', s=6, alpha=0.15, label='Temp bias (°C)')
    ax.set_ylabel('Temperature Bias (°C)', color='#1f77b4')
    ax.tick_params(axis='y', labelcolor='#1f77b4')
    ax.set_ylim(-6, 6)
    ax.axhline(0, color='k', ls='-', lw=0.5, alpha=0.5)
    ax.grid(True, alpha=0.2)

    ax2 = ax.twinx()
    pm = has_elev & df[p_col].notna()
    ax2.scatter(df.loc[pm, 'elevation_m'], df.loc[pm, p_col],
                c='#2ca02c', s=6, alpha=0.15, label='Precip bias (%)')
    ax2.set_ylabel('Precipitation Bias (%)', color='#2ca02c')
    ax2.tick_params(axis='y', labelcolor='#2ca02c')
    ax2.set_ylim(-80, 80)

    ax.set_xlabel('Elevation (m)')
    ax.set_title('RF-Corrected Bias vs Elevation')
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right',
              fontsize=8, markerscale=3)

    n_low = (df[cat_col] == 'LOW_BIAS').sum()
    n_low_orig = (df['bias_category'] == 'LOW_BIAS').sum() if 'bias_category' in df else '?'
    fig.suptitle(f'RF-Corrected Forcing Bias Summary — {len(df):,} site-years\n'
                 f'Low-bias: {n_low:,} (corrected) vs {n_low_orig} (original)',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    outpath = FIG_DIR / "bias_scatter_rfcorrected.png"
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    print(f"Saved: {outpath}")
    plt.close()


# ── Figure 3: spatial map (corrected categories) ────────────────────

def fig_bias_map_corrected(df):
    """Western US map colored by corrected dominant bias category."""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    cat_col = 'bias_category_corrected'
    spatial = df[df['latitude'].notna() & df['longitude'].notna()].copy()

    site_stats = (
        spatial.groupby(['site_id', 'latitude', 'longitude'])
        .agg(
            n_years=('water_year', 'nunique'),
            dominant_cat=(cat_col, lambda x: x.value_counts().index[0]),
        )
        .reset_index()
    )

    site_stats_orig = (
        spatial.groupby(['site_id', 'latitude', 'longitude'])
        .agg(dominant_cat_orig=('bias_category', lambda x: x.value_counts().index[0]))
        .reset_index()
    )
    site_stats = site_stats.merge(
        site_stats_orig[['site_id', 'dominant_cat_orig']], on='site_id', how='left')

    n_changed = (site_stats['dominant_cat'] != site_stats['dominant_cat_orig']).sum()
    n_to_low = ((site_stats['dominant_cat'] == 'LOW_BIAS')
                & (site_stats['dominant_cat_orig'] != 'LOW_BIAS')).sum()
    print(f"  Map: {len(site_stats)} sites, {n_changed} changed category, "
          f"{n_to_low} newly low-bias")

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([-125, -102, 31, 50], crs=ccrs.PlateCarree())

    ax.add_feature(cfeature.LAND, facecolor='#f5f5f5')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, alpha=0.5)
    ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor='gray')

    for st, (lon, lat) in {
        'WA': (-120.5, 47.5), 'OR': (-120.5, 44), 'CA': (-119.5, 37),
        'NV': (-117, 39.5), 'ID': (-114.5, 44.5), 'MT': (-110, 47),
        'WY': (-107.5, 43), 'UT': (-111.5, 39.5), 'CO': (-105.5, 39),
        'AZ': (-111.5, 34.5), 'NM': (-106, 34.5),
    }.items():
        ax.text(lon, lat, st, fontsize=10, fontweight='bold', color='dimgray',
                ha='center', va='center', alpha=0.7, transform=ccrs.PlateCarree())

    for cat in ['BOTH_BIASES', 'PRECIP_BIAS_ONLY', 'TEMP_BIAS_ONLY', 'LOW_BIAS']:
        mask = site_stats['dominant_cat'] == cat
        if mask.sum() == 0:
            continue
        sub = site_stats[mask]
        sizes = 15 + sub['n_years'] * 5
        ax.scatter(sub['longitude'], sub['latitude'],
                   c=COLORS[cat], s=sizes,
                   label=f"{LABELS[cat]} ({mask.sum()})",
                   alpha=0.75, edgecolors='white', linewidth=0.4,
                   zorder=3 if cat == 'LOW_BIAS' else 2,
                   transform=ccrs.PlateCarree())

    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray',
                       alpha=0.5, linestyle='--')
    gl.top_labels = False; gl.right_labels = False

    n_low = (site_stats['dominant_cat'] == 'LOW_BIAS').sum()
    n_low_orig = (site_stats['dominant_cat_orig'] == 'LOW_BIAS').sum()
    ax.set_title(f'SNOTEL Sites by RF-Corrected Bias Category (T + P)\n'
                 f'Low-bias: {n_low} sites (was {n_low_orig}, +{n_to_low} new)',
                 fontsize=13, fontweight='bold')
    ax.legend(loc='lower left', fontsize=10)

    plt.tight_layout()
    outpath = FIG_DIR / "bias_map_rfcorrected.png"
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    print(f"Saved: {outpath}")
    plt.close()


# ── main ──────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("RF-Corrected CW3E Temperature & Precipitation Bias Analysis")
    print("=" * 70)

    df = load_data()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # Train RF and apply both corrections
    df, rf_stats = train_and_correct(df)

    # Save corrected CSV (drop working HUC columns)
    out_cols = [c for c in df.columns if c not in ['huc8', 'huc2']]
    df[out_cols].to_csv(OUT_CSV, index=False)
    print(f"\nSaved: {OUT_CSV}")

    # Category comparison
    print(f"\n  Category counts (original → corrected):")
    for cat in CATEGORY_ORDER:
        n_orig = (df['bias_category'] == cat).sum()
        n_corr = (df['bias_category_corrected'] == cat).sum()
        delta = n_corr - n_orig
        print(f"    {LABELS[cat]:20s}: {n_orig:5d} → {n_corr:5d}  ({delta:+d})")

    # Generate figures
    print(f"\nGenerating figures ...")
    fig_snotel_vs_cw3e_corrected(df, rf_stats)
    fig_scatter_corrected(df)
    fig_bias_map_corrected(df)

    print(f"\nDone — 3 figures + 1 CSV saved.")


if __name__ == "__main__":
    main()
