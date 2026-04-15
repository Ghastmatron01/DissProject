"""
Postcode Lookup Module
======================
This module provides functionality to look up geographical and dwelling age information
based on UK postcodes. It integrates data from the ONS Postcode Directory and VOA dwelling age datasets.

Key Features:
- Maps postcodes to administrative areas (OA, LSOA, MSOA, LAD)
- Maps postcodes to dwelling age bands for fault modelling
- Provides estimated building ages and RGB colors for visualization

Data Sources:
- PCD_OA21_LSOA21_MSOA21_LAD_NOV24_UK_LU.csv: Postcode to geography mapping
- dwellingages.csv: LSOA to dwelling age band mapping
- dwelling_age_bands.py: Age band definitions and metadata

Usage:
    from data.postcode_lookup import PostcodeLookup

    lookup = PostcodeLookup()
    info = lookup.get_postcode_info("SW1A 1AA")
    age_band = lookup.get_age_band("SW1A 1AA")
"""

import pandas as pd
import os
from typing import Dict, Optional, Tuple
from .dwelling_age_bands import AGE_BAND_LABELS, AGE_BAND_ESTIMATED_AGE, AGE_BAND_RGB

class PostcodeLookup:
    """
    Handles postcode-based lookups for geographical and dwelling age information.
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the lookup with data from CSV files.

        :param data_dir: Directory containing the data files
        """
        self.data_dir = data_dir
        self._postcode_df = None
        self._dwelling_df = None
        self._load_data()

    def _load_data(self):
        """Load the postcode and dwelling age data from CSV files."""
        # Load postcode to geography mapping
        pcd_path = os.path.join(self.data_dir, "PCD_OA21_LSOA21_MSOA21_LAD_NOV24_UK_LU.csv")
        self._postcode_df = pd.read_csv(pcd_path, dtype=str)  # Read as strings to preserve codes
        self._postcode_df['pcds'] = self._postcode_df['pcds'].str.upper().str.replace(' ', '')  # Normalize postcodes
        self._postcode_df.set_index('pcds', inplace=True)

        # Load LSOA to dwelling age mapping
        dwelling_path = os.path.join(self.data_dir, "dwellingages.csv")
        self._dwelling_df = pd.read_csv(dwelling_path, dtype=str)
        self._dwelling_df.set_index('lsoacode', inplace=True)

    def _normalize_postcode(self, postcode: str) -> str:
        """
        Normalize a postcode by converting to uppercase and removing spaces.

        :param postcode: The input postcode
        :return: Normalized postcode
        """
        return postcode.upper().replace(' ', '')

    def get_postcode_info(self, postcode: str) -> Optional[Dict[str, str]]:
        """
        Get geographical information for a given postcode.

        :param postcode: The postcode to look up
        :return: Dictionary with OA21, LSOA21, MSOA21, LAD if found, else None
        """
        norm_pcd = self._normalize_postcode(postcode)
        if norm_pcd in self._postcode_df.index:
            row = self._postcode_df.loc[norm_pcd]
            return {
                'OA21': row['oa21cd'],
                'LSOA21': row['lsoa21cd'],
                'MSOA21': row['msoa21cd'],
                'LAD': row['ladcd']
            }
        return None

    def get_lsoa(self, postcode: str) -> Optional[str]:
        """
        Get the LSOA code for a given postcode.

        :param postcode: The postcode to look up
        :return: LSOA21 code if found, else None
        """
        info = self.get_postcode_info(postcode)
        return info['LSOA21'] if info else None

    def get_age_band(self, postcode: str) -> Optional[str]:
        """
        Get the modal dwelling age band for a given postcode.

        :param postcode: The postcode to look up
        :return: Age band code (A-L, U, X) if found, else None
        """
        lsoa = self.get_lsoa(postcode)
        if lsoa and lsoa in self._dwelling_df.index:
            return self._dwelling_df.loc[lsoa, 'dwe_modbp']
        return None

    def get_age_info(self, postcode: str) -> Optional[Dict]:
        """
        Get detailed age information for a given postcode.

        :param postcode: The postcode to look up
        :return: Dictionary with age band, label, estimated age, RGB color if found, else None
        """
        age_band = self.get_age_band(postcode)
        if age_band:
            return {
                'age_band': age_band,
                'label': AGE_BAND_LABELS.get(age_band, 'Unknown'),
                'estimated_age': AGE_BAND_ESTIMATED_AGE.get(age_band, None),
                'rgb_color': AGE_BAND_RGB.get(age_band, None)
            }
        return None

    def get_dwelling_proportions(self, postcode: str) -> Optional[Dict[str, float]]:
        """
        Get dwelling age proportions for a given postcode's LSOA.

        :param postcode: The postcode to look up
        :return: Dictionary with proportions if found, else None
        """
        lsoa = self.get_lsoa(postcode)
        if lsoa and lsoa in self._dwelling_df.index:
            row = self._dwelling_df.loc[lsoa]
            return {
                'pre_1945': float(row['dwe_p45pc']) if row['dwe_p45pc'] else 0.0,
                'post_2016': float(row['dwe_p16pc']) if row['dwe_p16pc'] else 0.0
            }
        return None

