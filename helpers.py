"""
Utility functions for single-column PF-CLM notebooks.

File-format helpers and reference data that users shouldn't need to modify.
All simulation logic, metrics, and plotting live inline in the notebooks.
"""

import re
from pathlib import Path

# =============================================================================
# IGBP Land Cover Type Tables
# =============================================================================
IGBP_NAMES = {
    1: "ENF",   2: "EBF",   3: "DNF",   4: "DBF",   5: "MF",
    6: "CSH",   7: "OSH",   8: "WSA",   9: "SAV",  10: "GRA",
    11: "WET",  12: "CRO",  13: "URB",  14: "MOS",  15: "SNO",
    16: "BSV",  17: "WAT",  18: "BAR",
}

IGBP_STR_TO_INT = {v: k for k, v in IGBP_NAMES.items()}

# =============================================================================
# CONUS2.1 Soil Hydraulic Properties (Table 3)
# Keys: pf_indicator value (1-13)
# Values: (name, ksat [m/h], porosity, vg_alpha [1/m], vg_n, sres)
# =============================================================================
CONUS2_SOILS = {
    1:  ("Sand",            0.087, 0.375, 3.548, 4.162, 0.0001),
    2:  ("Loamy Sand",      0.055, 0.390, 3.467, 2.738, 0.0001),
    3:  ("Sandy Loam",      0.031, 0.387, 2.692, 2.445, 0.0001),
    4:  ("Silt Loam",       0.019, 0.439, 0.501, 2.659, 0.0001),
    5:  ("Silt",            0.042, 0.489, 0.661, 2.659, 0.0001),
    6:  ("Loam",            0.014, 0.399, 1.122, 2.479, 0.0001),
    7:  ("Sandy Clay Loam", 0.016, 0.384, 2.089, 2.318, 0.0001),
    8:  ("Silty Clay Loam", 0.020, 0.482, 0.832, 2.514, 0.0001),
    9:  ("Clay Loam",       0.025, 0.442, 1.585, 2.413, 0.0001),
    10: ("Sandy Clay",      0.079, 0.385, 3.311, 2.202, 0.0001),
    11: ("Silty Clay",      0.081, 0.481, 1.622, 2.318, 0.0001),
    12: ("Clay",            0.045, 0.459, 1.514, 2.259, 0.0001),
    13: ("Organic",         0.014, 0.399, 1.122, 2.479, 0.0001),
}


def build_vegm(filepath, lat, lon, sand, clay, color, igbp):
    """Write a single-column drv_vegm.dat file.

    Parameters
    ----------
    filepath : str or Path
        Output path for drv_vegm.dat.
    lat, lon : float
        Site coordinates.
    sand, clay : float
        Sand and clay fractions (0-1 scale, e.g. 0.58 for 58%).
    color : int
        Soil color index (1-20).
    igbp : int
        IGBP land cover type (1-18).
    """
    fracs = ["0.0"] * 18
    fracs[igbp - 1] = "1.0"
    frac_str = " ".join(fracs)

    header1 = ("x y lat lon sand clay color fractional coverage of grid, "
               "by vegetation class (Must/Should Add to 1.0) ")
    header2 = ("  (Deg) (Deg) (%/100)  index "
               "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18")
    data_line = f"1 1 {lat:.6f} {lon:.6f} {sand:.2f} {clay:.2f} {color} {frac_str}"

    with open(filepath, "w") as f:
        f.write(header1 + "\n")
        f.write(header2 + "\n")
        f.write(data_line + "\n")


def patch_clmin_dates(template_path, output_path, water_year):
    """Copy drv_clmin template and patch date fields for the target water year.

    Parameters
    ----------
    template_path : str or Path
        Path to drv_clmin_template.dat.
    output_path : str or Path
        Where to write the patched drv_clmin.dat.
    water_year : int
        The water year (e.g. 2012). Start = Oct 1 of WY-1, end = Oct 1 of WY.
    """
    with open(template_path, "r") as f:
        content = f.read()

    wy = water_year
    replacements = {
        "syr": str(wy - 1),
        "smo": "10",
        "sda": "01",
        "shr": "00",
        "eyr": str(wy),
        "emo": "10",
        "eda": "01",
        "ehr": "00",
    }
    for field, value in replacements.items():
        pattern = rf"^({field}\s+)\S+(.*)$"
        content = re.sub(pattern, rf"\g<1>{value}\2", content,
                         count=1, flags=re.MULTILINE)

    with open(output_path, "w") as f:
        f.write(content)
