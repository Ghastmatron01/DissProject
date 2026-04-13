"""
Standalone script to run data extraction. Loads earnings and housing
datasets, cleans them, and saves the results as CSVs for the simulator.
"""

from pathlib import Path
from Algorithms.Data_Extraction import DataExtractor


def main():
    """
    Entry point for running data extraction. Loads earnings and housing
    data, then saves the cleaned results to CSV.
    """
    project_root = Path(__file__).parent
    data_dir = project_root / "data"

    print("Project root:", project_root)
    print("Looking for data files in:", data_dir)

    if not data_dir.exists():
        print("Data directory not found:", data_dir)
        return

    # List all files in the data directory for a quick sanity check
    found = [p.name for p in data_dir.iterdir() if p.is_file()]
    print("Files found in `data`:", found)

    extractor = DataExtractor(seed=42)

    earnings_path = data_dir / "earn02nov2025 (1).xls"
    housing_path = data_dir / "Housing Prices.xlsx"

    # -- Load and save earnings data --
    if not earnings_path.exists():
        print("Earnings file not found:", earnings_path)
    else:
        try:
            earnings = extractor.load_earnings_2025(str(earnings_path))
            print("Earnings dataframe shape:", earnings.shape)
            earnings.to_csv(data_dir / "earnings_2025_awe.csv", index=False)
        except Exception as e:
            print("Failed to load earnings:", e)

    # -- Load and save housing data --
    if not housing_path.exists():
        print("Housing file not found:", housing_path)
    else:
        try:
            housing = extractor.load_housing_data(str(housing_path))
            housing = extractor.clean_and_melt_housing(housing)
            print("Housing dataframe shape:", housing.shape)
            housing.to_csv(data_dir / "housing_long.csv", index=False)
        except Exception as e:
            print("Failed to load housing:", e)


if __name__ == "__main__":
    main()
