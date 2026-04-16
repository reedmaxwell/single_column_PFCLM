# CLM Input Files

Shipped CLM driver files for both the ET and snow examples. These track the
"best-practice" files published in
[parflow/parflow PR #714](https://github.com/parflow/parflow/pull/714)
(`feature/clm_driver_cleanup` → master).

## Current Layout

```
clm_inputs/
├── drv_clmin_template.dat   # shared (ET + snow) — exact copy of
│                            #   test/tcl/clm/drv_clmin_bestpractice.dat
├── et/
│   └── drv_vegp.dat         # copy of test/tcl/clm/drv_vegp_bestpractice.dat
└── snow/
    └── drv_vegp.dat         # currently identical to et/drv_vegp.dat
```

Each notebook copies the topic-specific `drv_vegp.dat` into its run directory
and patches `drv_clmin_template.dat`'s date fields for the selected water year.

## Why the two `drv_vegp.dat` files are identical

The PR #714 best-practice `drv_vegp.dat` is topic-agnostic — it carries the
full IGBP PFT table with all improvements needed by either example:

- CLM4.5 optical/structural corrections (grass, savanna, crop)
- PFT-specific photosynthesis (`vcmx25` + C3/C4 fixes)
- Medlyn stomatal conductance (`g1_medlyn`)
- Canopy clumping index (`clump`, He et al. 2012)
- Foliage nitrogen (`folnmx`)

None of those hurt a snow run — the snow-specific tuning lives outside this
file, in the ParFlow run script (`run.Solver.CLM.*` keys) and in the
site-specific `drv_vegm.dat` (IGBP=7 for the shrubland snow default).

So today, `et/drv_vegp.dat` and `snow/drv_vegp.dat` are byte-identical copies
of the same upstream file. The duplication is intentional — it keeps the
door open for topic-specific tuning without a restructure.

## Planned Consolidation

When we're confident neither topic needs per-topic vegp overrides, collapse to:

```
clm_inputs/
├── drv_clmin_template.dat   # unchanged
└── drv_vegp.dat             # single shared best-practice file
```

And update the two topic notebooks:

| File | Change |
|------|--------|
| `et/locate_plot_station_get_forcing.ipynb` | `Path("../clm_inputs/et")` → `Path("../clm_inputs")` |
| `snow/locate_plot_station_get_forcing.ipynb` | `Path("../clm_inputs/snow")` → `Path("../clm_inputs")` |

That's a three-line change (two notebook edits + delete the two subdirs).

### Triggers that would *prevent* consolidation

Reasons we might end up keeping the split:

1. **Snow-specific PFT tuning**. If future work finds that snow-site canopy
   radiation/transpiration benefits from different `z0m`, `displa`, `rhol_*`,
   `taul_*` values at high-elevation shrubland sites, those would live in
   `snow/drv_vegp.dat` and diverge from the ET file.
2. **Different `vcmx25` regimes for snow vs. ET sites**. Unlikely but
   possible if PFT photosynthesis is retuned for cold/dormant-season behavior.
3. **Experimental physics branches**. If a future branch ships a new
   `drv_vegp.dat` format with extra columns for one topic only.

None of these apply today.

## Upstream Tracking

When `parflow/master` updates either best-practice file, refresh both copies
here. The fastest check is a `diff` against the upstream raw files:

```bash
for f in drv_clmin_bestpractice drv_vegp_bestpractice; do
  curl -sL "https://raw.githubusercontent.com/parflow/parflow/master/test/tcl/clm/${f}.dat" | \
    diff - clm_inputs/${f%_bestpractice}_template.dat  # or et/drv_vegp.dat, snow/drv_vegp.dat
done
```

(Adjust target paths — `drv_clmin_bestpractice` lands in
`clm_inputs/drv_clmin_template.dat`, `drv_vegp_bestpractice` lands in both
`clm_inputs/et/drv_vegp.dat` and `clm_inputs/snow/drv_vegp.dat`.)

## Background

- PR #714: "Document CLM driver files and remove dead parameters"
  (feature/clm_driver_cleanup, merged March 2026).
- Related PRs: #712 (CLM ET improvements), #695/#698/#701/#709 (snow).
- See the top-level `README.md` for the complete merged-PR table.
