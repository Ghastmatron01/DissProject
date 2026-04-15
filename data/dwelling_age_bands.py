"""
Dwelling Age Band Reference Data
=================================
Source: VOA (Valuation Office Agency) dwelling age dataset
        via https://www.ons.gov.uk/

Each LSOA (Lower Super Output Area) in England & Wales has a modal
and median building period expressed as a single-letter code (A–L).
This file maps those codes to year ranges, estimated midpoint years,
estimated ages (from 2024), and the RGB colour used for cartographic
visualisation of the age distribution.

Column reference for dwellingages.csv:
--------------------------------------
  lsoacode   – ONS LSOA code (e.g. E01020634)
  dwe_p45pc  – Proportion of dwellings built before 1945 (0.0–1.0)
  dwe_p16pc  – Proportion of dwellings built after 2016 (0.0–1.0)
  dwe_modbp  – Modal building period (most common age band, A–L / U)
  dwe_mo20bp – Modal building period in 20-year groups (A–L / U / X)
  dwe_medbp  – Median building period (A–L)
  dwe_mdargb – RGB composite colour of the full age distribution

Age band codes
--------------
  A = pre-1900        B = 1900–1918       C = 1919–1929
  D = 1930–1939       E = 1945–1954       F = 1955–1964
  G = 1965–1972       H = 1973–1982       I = 1983–1992
  J = 1993–1999       K = 2000–2008       L = 2009–2021
  U = Unknown         X = Various (no single dominant period)

RGB colours for composite mapping
----------------------------------
  A = (0, 0, 255)        deep blue     – oldest stock
  B = (0, 64, 255)       blue
  C = (0, 128, 255)      sky blue
  D = (0, 192, 255)      light blue
  E = (0, 255, 192)      cyan-green
  F = (0, 255, 0)        green
  G = (192, 255, 0)      yellow-green
  H = (255, 255, 0)      yellow
  I = (255, 192, 0)      orange
  J = (255, 128, 0)      dark orange
  K = (255, 64, 0)       red-orange
  L = (255, 0, 0)        red           – newest stock
  Y = (255, 255, 255)    white         – mixed / no data
"""

# ── Age band code → year range (start, end) ────────────────────────
AGE_BAND_YEAR_RANGES = {
    "A": (1800, 1899),   # pre-1900 (assume mid-Victorian as lower bound)
    "B": (1900, 1918),
    "C": (1919, 1929),
    "D": (1930, 1939),
    "E": (1945, 1954),
    "F": (1955, 1964),
    "G": (1965, 1972),
    "H": (1973, 1982),
    "I": (1983, 1992),
    "J": (1993, 1999),
    "K": (2000, 2008),
    "L": (2009, 2021),
}

# ── Age band code → midpoint year ──────────────────────────────────
AGE_BAND_MIDPOINTS = {
    code: (start + end) // 2
    for code, (start, end) in AGE_BAND_YEAR_RANGES.items()
}
# A → 1849, B → 1909, C → 1924, D → 1934, E → 1949, F → 1959,
# G → 1968, H → 1977, I → 1987, J → 1996, K → 2004, L → 2015

# ── Age band code → estimated age in years (from 2024) ─────────────
AGE_BAND_ESTIMATED_AGE = {
    code: 2024 - midpoint
    for code, midpoint in AGE_BAND_MIDPOINTS.items()
}
# A → 175, B → 115, C → 100, D → 90, E → 75, F → 65,
# G → 56,  H → 47,  I → 37,  J → 28, K → 20, L → 9

# ── Age band code → human-readable label ───────────────────────────
AGE_BAND_LABELS = {
    "A": "Pre-1900 (Victorian / Georgian)",
    "B": "1900–1918 (Edwardian / WW1 era)",
    "C": "1919–1929 (Inter-war early)",
    "D": "1930–1939 (Inter-war / Art Deco)",
    "E": "1945–1954 (Post-war rebuild)",
    "F": "1955–1964 (Post-war expansion)",
    "G": "1965–1972 (1960s/70s boom)",
    "H": "1973–1982 (Oil crisis era)",
    "I": "1983–1992 (Thatcher era)",
    "J": "1993–1999 (1990s recovery)",
    "K": "2000–2008 (Millennium boom)",
    "L": "2009–2021 (Post-recession / modern)",
    "U": "Unknown",
    "X": "Various (mixed building periods)",
}

# ── RGB colours for cartographic visualisation ──────────────────────
AGE_BAND_RGB = {
    "A": (0, 0, 255),
    "B": (0, 64, 255),
    "C": (0, 128, 255),
    "D": (0, 192, 255),
    "E": (0, 255, 192),
    "F": (0, 255, 0),
    "G": (192, 255, 0),
    "H": (255, 255, 0),
    "I": (255, 192, 0),
    "J": (255, 128, 0),
    "K": (255, 64, 0),
    "L": (255, 0, 0),
    "Y": (255, 255, 255),   # mixed / composite fallback
}

# ── Hex equivalents (useful for matplotlib / web charts) ────────────
AGE_BAND_HEX = {
    code: "#{:02x}{:02x}{:02x}".format(*rgb)
    for code, rgb in AGE_BAND_RGB.items()
}

