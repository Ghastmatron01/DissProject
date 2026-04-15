# Fault Modelling class
# Models faults in houses using EHS 2024 real probability data,
# adjusted by dwelling age from the VOA dwelling-age dataset.

import random
import pandas as pd
from pathlib import Path

# Age band reference data (codes → year ranges, estimated ages, etc.)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "data"))
from data.dwelling_age_bands import (
    AGE_BAND_YEAR_RANGES,
    AGE_BAND_MIDPOINTS,
    AGE_BAND_ESTIMATED_AGE,
    AGE_BAND_LABELS,
)


class DwellingAgeData:
    """
    Loads the VOA dwelling-age-by-LSOA dataset (dwellingages.csv) and
    provides lookup methods to estimate a property's building age from
    its LSOA code.

    The dataset covers ~34,700 LSOAs across England and Wales. Each row
    contains the modal, modal-20-year, and median building period for
    all dwellings in that LSOA, expressed as a single letter code (A-L).

    Usage:
        loader = DwellingAgeData()                   # loads CSV once
        age = loader.estimate_age("E01020636")       # -> 65 (band F)
        band = loader.get_median_band("E01020636")   # -> "F"
    """

    _instance = None   # singleton so the CSV is only loaded once

    def __new__(cls):
        """Singleton pattern - only read the CSV on the first instantiation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        csv_path = Path(__file__).parent.parent / "data" / "dwellingages.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path, dtype={"lsoacode": str})
            # Build a dict keyed on LSOA code for O(1) lookups
            self._lsoa_lookup = {}
            for _, row in df.iterrows():
                self._lsoa_lookup[row["lsoacode"]] = {
                    "median_band": row["dwe_medbp"],
                    "modal_band": row["dwe_modbp"],
                    "modal_20_band": row["dwe_mo20bp"],
                    "pre_1945_pct": row["dwe_p45pc"],
                    "post_2016_pct": row["dwe_p16pc"],
                    "rgb": row["dwe_mdargb"],
                }
            print(f"  [DwellingAgeData] Loaded {len(self._lsoa_lookup):,} LSOAs")
        else:
            print(f"  [DwellingAgeData] WARNING: {csv_path} not found - age lookups disabled")
            self._lsoa_lookup = {}
        self._loaded = True

    # -- Public lookup methods -----------------------------------------

    def has_lsoa(self, lsoa_code):
        """Check whether an LSOA code exists in the dataset."""
        return lsoa_code in self._lsoa_lookup

    def get_median_band(self, lsoa_code):
        """
        Return the median building-period code (A-L) for an LSOA,
        or None if the LSOA is not in the dataset.
        """
        entry = self._lsoa_lookup.get(lsoa_code)
        return entry["median_band"] if entry else None

    def get_modal_band(self, lsoa_code):
        """Return the modal building-period code for an LSOA, or None."""
        entry = self._lsoa_lookup.get(lsoa_code)
        return entry["modal_band"] if entry else None

    def get_lsoa_info(self, lsoa_code):
        """Return the full dict of age data for an LSOA, or None."""
        return self._lsoa_lookup.get(lsoa_code)

    def estimate_age_from_band(self, band_code):
        """
        Convert a building-period code (A-L) to an estimated property
        age in years (relative to 2024).

        :param band_code: Single-letter code (e.g. "F").
        :return: Estimated age in years, or None for unknown codes.
        """
        return AGE_BAND_ESTIMATED_AGE.get(band_code)

    def estimate_age(self, lsoa_code):
        """
        Estimate a property's age from its LSOA code by looking up the
        median building period and converting to years.

        :param lsoa_code: ONS LSOA code (e.g. "E01020636").
        :return: Estimated age in years, or None if LSOA not found.
        """
        band = self.get_median_band(lsoa_code)
        if band:
            return self.estimate_age_from_band(band)
        return None

    def get_pre_1945_proportion(self, lsoa_code):
        """Return the proportion of pre-1945 dwellings in an LSOA (0.0-1.0)."""
        entry = self._lsoa_lookup.get(lsoa_code)
        return entry["pre_1945_pct"] if entry else None


class FaultModelling:
    """
    Model property faults using EHS 2024 real probability data,
    adjusted by the property's estimated building age.

    Age estimation priority:
        1. LSOA code -> look up median building period from VOA data
        2. Property type + price heuristic (fallback)

    Probabilities come from the English Housing Survey 2024:
        - AT1_7: Reasons for failing Decent Homes Standard
        - AT1_8: Most common Category 1 hazards
        - AT1_10: Damp problems by tenure
    """

    # -- EHS-derived annual probabilities ----------------------------
    # EHS gives snapshot %s (homes with a current problem).
    # Dividing by ~5 (average fault duration) gives annual new-fault rate.
    BASE_ANNUAL_PROBABILITIES = {
        "damp":              0.0075,   # 3.77% snapshot / 5
        "excess_cold":       0.0060,   # 2.98% / 5
        "disrepair":         0.0065,   # 3.26% / 5
        "electrical_fault":  0.0030,   # ~1.5% estimated / 5
        "boiler_failure":    0.0060,   # ~3% from thermal comfort / 5
        "roof_leak":         0.0020,   # ~1% from disrepair subset / 5
        "plumbing_issue":    0.0040,   # ~2% estimated / 5
    }

    # -- Typical UK repair cost ranges (min, max) in pounds ----------
    REPAIR_COSTS = {
        "damp":              (1_500, 6_000),
        "excess_cold":       (2_000, 8_000),   # insulation / windows
        "disrepair":         (1_000, 5_000),
        "electrical_fault":  (500, 3_000),
        "boiler_failure":    (2_000, 4_000),
        "roof_leak":         (1_000, 15_000),
        "plumbing_issue":    (300, 2_000),
    }

    # -- Age multiplier: older properties have more faults -----------
    # Brackets are (min_age, max_age, multiplier)
    AGE_MULTIPLIER_BRACKETS = [
        (0,   10,  0.3),    # new-build, few faults
        (10,  30,  0.7),
        (30,  60,  1.0),    # baseline
        (60, 100,  1.5),
        (100, 999, 2.0),    # Victorian / Georgian
    ]

    # -- Property-type multiplier ------------------------------------
    PROPERTY_TYPE_MULTIPLIERS = {
        "flat":           0.8,   # shared structure, less exposure
        "terraced":       1.2,   # party walls, often older stock
        "semi_detached":  1.0,   # baseline
        "detached":       1.1,   # more roof / wall area exposed
        "other":          1.0,
    }

    # -- Property-type -> fallback estimated age (years) -------------
    # Used only when no LSOA data is available
    PROPERTY_TYPE_FALLBACK_AGE = {
        "terraced":       60,    # typically Victorian/Edwardian
        "semi_detached":  50,    # often 1930s
        "detached":       30,    # mixed, but many are newer
        "flat":           25,    # many purpose-built post-war
        "other":          40,
    }

    def __init__(self, house, lsoa_code=None, rng=None):
        """
        Initialise the fault model for a specific property.

        :param house: House object (has .price, .property_type, .county,
                      .district, .date).
        :param lsoa_code: Optional ONS LSOA code for precise age lookup.
        :param rng: Optional random.Random instance for reproducibility.
        """
        self.house = house
        self.rng = rng or random.Random()

        # -- Estimate property age -----------------------------------
        self.lsoa_code = lsoa_code
        self.age_band = None           # e.g. "F"
        self.age_source = "fallback"   # "lsoa" or "fallback"

        if lsoa_code:
            dwelling_data = DwellingAgeData()
            band = dwelling_data.get_median_band(lsoa_code)
            if band:
                estimated = dwelling_data.estimate_age_from_band(band)
                if estimated is not None:
                    self.estimated_age = estimated
                    self.age_band = band
                    self.age_source = "lsoa"

        # Fallback if LSOA lookup didn't produce a result
        if self.age_source == "fallback":
            prop_type = getattr(house, "property_type", "other") or "other"
            self.estimated_age = self.PROPERTY_TYPE_FALLBACK_AGE.get(prop_type, 40)

        # -- Fault tracking ------------------------------------------
        self.active_faults = []    # currently unresolved faults
        self.fault_history = []    # every fault that ever occurred

    # -- Multiplier methods ------------------------------------------

    def _get_age_multiplier(self):
        """
        Return a multiplier (0.3-2.0) based on the property's estimated age.
        Older properties are more prone to faults.
        """
        for min_age, max_age, multiplier in self.AGE_MULTIPLIER_BRACKETS:
            if min_age <= self.estimated_age < max_age:
                return multiplier
        return 1.0   # safety fallback

    def _get_property_type_multiplier(self):
        """
        Return a multiplier (0.8-1.2) based on the property type.
        Terraced houses (older stock, party walls) score higher.
        """
        prop_type = getattr(self.house, "property_type", "other") or "other"
        return self.PROPERTY_TYPE_MULTIPLIERS.get(prop_type, 1.0)

    # -- Core fault assessment ---------------------------------------

    def assess_annual_faults(self, current_year=None):
        """
        Roll for each fault type to see if a NEW fault occurs this year.
        Probability = base_rate x age_multiplier x property_type_multiplier.

        :param current_year: The simulation year (stored in fault records).
        :return: List of new fault dicts that occurred (may be empty).
        """
        age_mult = self._get_age_multiplier()
        type_mult = self._get_property_type_multiplier()
        new_faults = []

        for fault_type, base_prob in self.BASE_ANNUAL_PROBABILITIES.items():
            adjusted_prob = base_prob * age_mult * type_mult
            # Clamp to [0, 1] just in case multipliers stack high
            adjusted_prob = min(adjusted_prob, 1.0)

            if self.rng.random() < adjusted_prob:
                # Fault occurred - pick a random repair cost
                cost_min, cost_max = self.REPAIR_COSTS[fault_type]
                repair_cost = self.rng.randint(cost_min, cost_max)

                fault_record = {
                    "fault_type":    fault_type,
                    "repair_cost":   repair_cost,
                    "year_occurred": current_year,
                    "age_band":      self.age_band,
                    "estimated_age": self.estimated_age,
                    "probability":   round(adjusted_prob, 6),
                }

                self.active_faults.append(fault_record)
                self.fault_history.append(fault_record)
                new_faults.append(fault_record)

        return new_faults

    # -- Repair methods ----------------------------------------------

    def get_total_repair_cost(self):
        """Sum the repair cost of all currently active (unresolved) faults."""
        return sum(f["repair_cost"] for f in self.active_faults)

    def repair_fault(self, fault_type):
        """
        Find and remove the first active fault of the given type.

        :param fault_type: e.g. "damp", "boiler_failure".
        :return: The removed fault dict, or None if no match.
        """
        for i, fault in enumerate(self.active_faults):
            if fault["fault_type"] == fault_type:
                return self.active_faults.pop(i)
        return None

    def repair_all_faults(self):
        """
        Remove all active faults and return the total cost paid.

        :return: Total repair cost (float).
        """
        total = self.get_total_repair_cost()
        self.active_faults.clear()
        return total

    # -- Info / debugging --------------------------------------------

    def get_summary(self):
        """
        Return a human-readable summary of the fault model state.

        :return: Dict with age info, active faults, and history count.
        """
        return {
            "estimated_age": self.estimated_age,
            "age_band": self.age_band,
            "age_source": self.age_source,
            "age_multiplier": self._get_age_multiplier(),
            "type_multiplier": self._get_property_type_multiplier(),
            "active_faults": len(self.active_faults),
            "total_repair_cost": self.get_total_repair_cost(),
            "lifetime_faults": len(self.fault_history),
            "property_type": getattr(self.house, "property_type", "unknown"),
        }

    def __repr__(self):
        band_str = f" band={self.age_band}" if self.age_band else ""
        return (
            f"FaultModelling(age~{self.estimated_age}y{band_str}, "
            f"active={len(self.active_faults)}, "
            f"history={len(self.fault_history)})"
        )
