from typing import Optional, List, Dict
import pandas as pd
import numpy as np
import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def _robust_parse_dates(series: pd.Series) -> pd.Series:
    """
    Try several common date formats first (fast exact parsing), then
    fall back to pandas/dateutil flexible parsing.

    :param series: A pandas Series of date strings.
    :return: A pandas Series of datetimes (NaT where parsing fails).
    """
    formats = ("%Y-%m-%d", "%Y-%m", "%Y %b", "%Y %B", "%Y")

    for fmt in formats:
        parsed = pd.to_datetime(series, format=fmt, errors="coerce")
        if parsed.notna().any():
            # Keep parsed where possible, use flexible parsing for the rest
            return parsed.fillna(pd.to_datetime(series, errors="coerce"))

    # Final fallback: flexible parsing
    return pd.to_datetime(series, errors="coerce")


class DataExtractor:
    """
    Utility class to load and clean datasets used by the simulator:
      - load_earnings_2025: cleaned ONS AWE dataset for 2025
      - load_housing_data: cleaned housing price data
      - load_ehs: cleaned English Housing Survey data
      - load_land_registry_prices: cleaned time-series of prices
      - load_income_after_tax_percentiles: cleaned percentile wages
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialise the extractor with an optional random seed.

        :param seed: Optional seed for the random number generator.
        """
        self.rng = np.random.default_rng(seed)

    def _read_file(self, file_path: str, sheet_name: Optional[int | str] = None) -> pd.DataFrame:
        """
        Read a file into a DataFrame based on its extension.

        :param file_path: Path to the file.
        :param sheet_name: Optional sheet name or index for Excel files.
        :return: DataFrame with the file contents.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".csv", ".txt"]:
            return pd.read_csv(file_path)
        elif ext in [".xls", ".xlsx"]:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def load_earnings_2025(self, file_path):
        """
        Load the ONS AWE dataset from sheet '4. NSA sect monthly figs',
        clean the messy layout, map CDID codes to readable sector names,
        strip month labels, and return only 2025 rows.

        :param file_path: Path to the earnings .xls file.
        :return: DataFrame with Month column and AWE columns for 2025.
        """
        # Load the raw sheet with no headers
        df_raw = pd.read_excel(file_path, sheet_name="4. NSA sect monthly figs", header=None)

        # Find the row where 'CDID' appears
        cdid_row_idx = df_raw.index[df_raw.iloc[:, 0] == "CDID"][0]

        # Use the CDID row as header, and everything after as data
        df = df_raw.iloc[cdid_row_idx + 1:].copy()
        df.columns = df_raw.iloc[cdid_row_idx]

        # Drop rows that are completely empty
        df = df.dropna(how="all")

        # Rename the first column to 'Month'
        df.rename(columns={df.columns[0]: "Month"}, inplace=True)

        # Clean the Month column (remove provisional/revision markers)
        df["Month"] = (
            df["Month"]
            .astype(str)
            .str.replace("(p)", "", regex=False)
            .str.replace("(r)", "", regex=False)
            .str.strip()
        )

        # Map CDID codes to human-readable sector names
        rename_map = {
            "KA46": "Whole Economy AWE",
            "KA47": "Whole Economy Bonuses",
            "KA48": "Whole Economy Arrears",
            "KA4O": "Private Sector AWE",
            "KA4P": "Private Sector Bonuses",
            "KA4Q": "Private Sector Arrears",
            "KA4R": "Public Sector AWE",
            "KA4S": "Public Sector Bonuses",
            "KA4T": "Public Sector Arrears",
            "K550": "Services AWE",
            "K55P": "Services Bonuses",
            "K55Q": "Services Arrears",
            "K55U": "Finance & Business Services AWE",
            "K55V": "Finance & Business Services Bonuses",
            "K55W": "Finance & Business Services Arrears",
            "K55R": "Public excl. Financial Services AWE",
            "K55S": "Public excl. Financial Services Bonuses",
            "K55T": "Public excl. Financial Services Arrears",
        }

        df = df.rename(columns=rename_map)

        # Keep only readable columns (drop 'Unnamed' leftovers)
        keep_cols = [col for col in df.columns if not str(col).startswith("Unnamed")]
        df = df[keep_cols]

        # Filter to only 2025 rows
        df_2025 = df[df["Month"].str.startswith("2025")].copy()

        # Keep only Average Weekly Earnings (AWE) columns
        awe_cols = ["Month"] + [col for col in df_2025.columns if col.endswith("AWE")]
        df_2025_awe = df_2025[awe_cols]
        return df_2025_awe

    def load_housing_data(self, file_path):
        """
        Load a housing price workbook (sheet index 4), strip column
        whitespace, normalise the date column, and return a single-row
        DataFrame for the most recent time period.

        :param file_path: Path to the Housing Prices Excel file.
        :return: Single-row DataFrame with the most recent housing prices.
        """
        df = pd.read_excel(file_path, sheet_name=4, skiprows=2)

        # Strip whitespace from column names (fix trailing spaces)
        df.columns = df.columns.str.strip()
        print("Columns in housing data:", df.columns.tolist())

        # Identify the time column (always the first column)
        time_period_col = df.columns[0]

        # Remove bracketed notes and whitespace from the time column
        df[time_period_col] = (
            df[time_period_col].astype(str)
            .str.replace(r"\[.*?\]", "", regex=True)
            .str.strip()
        )

        # Try a set of common formats before falling back to flexible parsing
        formats = ['%Y-%m-%d', '%Y-%m', '%b %Y', '%B %Y', '%Y/%m/%d', '%d/%m/%Y']
        parsed = pd.to_datetime(df[time_period_col], format=formats[0], errors='coerce')

        for fmt in formats[1:]:
            mask = parsed.isna()
            if not mask.any():
                break
            parsed.loc[mask] = pd.to_datetime(df.loc[mask, time_period_col], format=fmt, errors='coerce')

        # Final fallback to flexible inference
        parsed = parsed.fillna(_robust_parse_dates(df[time_period_col]))

        # Store as date objects
        df[time_period_col] = parsed.dt.date

        # Grab the most recent row
        most_recent_row = df.iloc[-1]
        most_recent_date = most_recent_row[time_period_col]
        print("Most recent date in housing data:", most_recent_date)

        headers = df.columns.tolist()
        prices = most_recent_row
        housing_prices_df = pd.DataFrame([prices], columns=headers)

        return housing_prices_df

    def load_ehs(self, file_path: str, usecols: Optional[List[str]] = None,
                 sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load English Housing Survey data (CSV or Excel). Attempts to detect
        common column names and standardise them.

        :param file_path: Path to the EHS data file.
        :param usecols: Optional list of columns to keep.
        :param sheet_name: Optional sheet name for Excel files.
        :return: Cleaned DataFrame with standardised column names.
        """
        df = self._read_file(file_path, sheet_name=sheet_name)

        # Optionally subset columns
        if usecols:
            df = df[[c for c in usecols if c in df.columns]]

        # Build a lowercase lookup so we can match columns case-insensitively
        col_map: Dict[str, str] = {}
        lowercols = {c.lower(): c for c in df.columns}

        def find_any(keys: List[str]) -> Optional[str]:
            """Return the first matching column name from a list of candidates."""
            for k in keys:
                if k in lowercols:
                    return lowercols[k]
            return None

        # Map known aliases to standardised names
        mappings = {
            "age": ["dwelling_age", "age", "age_band", "yr_built", "year_built"],
            "damp": ["damp", "presence_of_damp", "damp_or_mould", "mould"],
            "rats": ["rats", "vermin", "pests", "rodents"],
            "tenure": ["tenure", "owner_tenure", "tenure_type"],
            "condition": ["condition_score", "repair_needs", "disrepair"]
        }

        for std, keys in mappings.items():
            found = find_any(keys)
            if found:
                col_map[found] = std

        # Rename matched columns to standardised names
        if col_map:
            df = df.rename(columns=col_map)

        # Basic cleaning: ensure numeric age, booleans for damp/rats
        if "age" in df.columns:
            df["age"] = pd.to_numeric(df["age"], errors="coerce")
        if "damp" in df.columns:
            df["damp"] = df["damp"].apply(lambda x: self._to_bool(x))
        if "rats" in df.columns:
            df["rats"] = df["rats"].apply(lambda x: self._to_bool(x))
        if "condition" in df.columns:
            df["condition"] = pd.to_numeric(df["condition"], errors="coerce")

        return df.reset_index(drop=True)

    def load_land_registry_prices(self, file_path: str, date_col: str = "Date", price_col: Optional[str] = None) -> pd.DataFrame:
        """
        Load Land Registry / price time series data. Returns a tidy
        DataFrame with columns [date, region, price].

        :param file_path: Path to the price data file.
        :param date_col: Name of the date column.
        :param price_col: Optional single price column to extract.
        :return: Tidy DataFrame with date, region (if multiple), and price.
        """
        df = self._read_file(file_path)

        # Try to find the date column automatically if not present
        if date_col not in df.columns:
            for c in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[c]) or df[c].astype(str).str.match(r"\d{4}-\d{2}").any():
                    date_col = c
                    break

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        # If a specific price column was requested, return just that
        if price_col and price_col in df.columns:
            return df[[date_col, price_col]].rename(columns={date_col: "date", price_col: "price"}).dropna().reset_index(drop=True)

        # Otherwise melt all non-date columns into long format
        value_cols = [c for c in df.columns if c != date_col]
        tidy = df.melt(id_vars=[date_col], value_vars=value_cols, var_name="region", value_name="price")
        tidy = tidy.dropna(subset=["price"])
        tidy["date"] = pd.to_datetime(tidy[date_col]).dt.date
        return tidy[["date", "region", "price"]].reset_index(drop=True)

    def load_income_after_tax_percentiles(self, file_path: str, tax_year: str = "2022 to 2023") -> Dict[int, float]:
        """
        Extract income-after-tax percentile points from the HMRC
        Table 3.1a xlsx file by parsing the raw XML inside the zip.

        :param file_path: Path to Table_3.1a_2223.xlsx.
        :param tax_year: The column header to extract, e.g. "2022 to 2023".
        :return: Dict mapping percentile (int) to annual income after tax (float).
        """
        NS = "http://purl.oclc.org/ooxml/spreadsheetml/main"

        # -- Helper functions --
        def col_letter_to_index(col_str: str) -> int:
            """Convert Excel column letter(s) to 0-based index (e.g. 'A' -> 0)."""
            index = 0
            for char in col_str.upper():
                index = index * 26 + (ord(char) - ord("A") + 1)
            return index - 1

        def cell_ref_to_col(ref: str) -> int:
            """Extract column index from cell reference like 'B5' or 'AA10'."""
            letters = "".join(ch for ch in ref if ch.isalpha())
            return col_letter_to_index(letters)

        # Read raw XML from the zip archive
        with zipfile.ZipFile(file_path) as z:
            shared_raw = z.read("xl/sharedStrings.xml").decode("utf-8")
            sheet_raw = z.read("xl/worksheets/sheet3.xml").decode("utf-8")

        # Build shared strings lookup
        sst = ET.fromstring(shared_raw)
        strings: List[str] = [
            "".join(t.text or "" for t in si.iter(f"{{{NS}}}t"))
            for si in sst.findall(f"{{{NS}}}si")
        ]

        def resolve_cell(c_elem) -> str:
            """Return the string value of a cell element."""
            t = c_elem.get("t", "")
            v = c_elem.find(f"{{{NS}}}v")
            raw = v.text if v is not None else ""
            if t == "s" and raw:          # shared string index
                return strings[int(raw)]
            return raw                    # numeric or inline string

        # Parse all rows into a list of dicts {col_index: value}
        root = ET.fromstring(sheet_raw)
        parsed_rows: List[Dict[int, str]] = []

        for row_elem in root.findall(f".//{{{NS}}}row"):
            row_dict: Dict[int, str] = {}
            for c in row_elem.findall(f"{{{NS}}}c"):
                ref = c.get("r", "")
                col_idx = cell_ref_to_col(ref) if ref else len(row_dict)
                row_dict[col_idx] = resolve_cell(c)
            parsed_rows.append(row_dict)

        # Locate the header row by finding a cell that exactly matches "YYYY to YYYY"
        import re
        year_range_pattern = re.compile(r"^\d{4} to \d{4}$")
        header_row_idx = None
        for i, row in enumerate(parsed_rows):
            for val in row.values():
                if year_range_pattern.match(val.strip()):
                    header_row_idx = i
                    break
            if header_row_idx is not None:
                break

        if header_row_idx is None:
            raise ValueError("Could not find header row in sheet. Check the file structure.")

        header = parsed_rows[header_row_idx]

        # Find which column index holds the requested tax year
        target_col = None
        for col_idx, val in header.items():
            if tax_year.lower() in val.lower():
                target_col = col_idx
                break

        if target_col is None:
            available = [v for v in header.values() if "to" in v]
            raise ValueError(
                f"Tax year '{tax_year}' not found in headers.\n"
                f"Available years: {available}"
            )

        # Extract percentile to income pairs from data rows
        percentile_col = min(header.keys())   # leftmost column = percentile number
        result: Dict[int, float] = {}

        for row in parsed_rows[header_row_idx + 1:]:
            # Skip footer rows (e.g. "End of worksheet")
            percentile_raw = row.get(percentile_col, "").strip()
            if not percentile_raw.isdigit():
                continue

            income_raw = row.get(target_col, "").strip()
            if not income_raw or income_raw.lower() in {"[not available]", "n/a", ""}:
                continue  # omit unavailable entries

            try:
                result[int(percentile_raw)] = float(income_raw)
            except ValueError:
                continue   # skip any unexpected non-numeric value

        return result

    @staticmethod
    def _to_bool(val) -> Optional[bool]:
        """
        Convert a value to a boolean. Handles strings like 'yes'/'no',
        numeric values, and numpy booleans.

        :param val: The value to convert.
        :return: True, False, or None if the value cannot be converted.
        """
        if pd.isna(val):
            return None
        if isinstance(val, (bool, np.bool_)):
            return bool(val)
        s = str(val).strip().lower()
        if s in {"yes", "y", "true", "1", "t"}:
            return True
        if s in {"no", "n", "false", "0", "f"}:
            return False
        # Numeric heuristic: positive = True
        try:
            n = float(s)
            return n > 0
        except Exception:
            return None

    def clean_and_melt_housing(self, df, time_col='Time period'):
        """
        Strip whitespace from column names, parse the time column
        robustly, and melt the wide DataFrame to long form.

        :param df: Wide-format housing DataFrame.
        :param time_col: Name of the time period column.
        :return: Long-form DataFrame with columns: Time period, Region, Price.
        """
        # Work on a copy to avoid modifying the original
        df = df.copy()

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        if time_col not in df.columns:
            raise KeyError(f"Missing column: `{time_col}`")

        # Try common formats first, then fall back to flexible inference
        formats = ['%Y-%m-%d', '%Y-%m', '%b %Y', '%B %Y', '%Y/%m/%d', '%d/%m/%Y']
        parsed = pd.to_datetime(df[time_col], format='%Y-%m-%d', errors='coerce')

        for fmt in formats[1:]:
            if not parsed.isna().any():
                break
            mask = parsed.isna()
            parsed.loc[mask] = pd.to_datetime(df.loc[mask, time_col], format=fmt, errors='coerce')

        # Final fallback to pandas inference
        parsed = parsed.fillna(_robust_parse_dates(df[time_col]))
        df[time_col] = parsed

        # Show most recent date for sanity check
        most_recent = df[time_col].max()
        print("Most recent date in housing data:", most_recent)

        # Melt wide format to long form
        long = df.melt(id_vars=[time_col], var_name='Region', value_name='Price')
        long = long.dropna(subset=['Price']).reset_index(drop=True)

        return long


# --------------------------------------------------------------------
#  Main guard: run extraction when executed directly
# --------------------------------------------------------------------
if __name__ == "__main__":
    extractor = DataExtractor(seed=42)

    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # -- Earnings --
    file_path = data_dir / "earn02nov2025 (1).xls"
    try:
        earnings = extractor.load_earnings_2025(str(file_path))
        print(earnings.head())
        earnings.to_csv(data_dir / "earnings_2025_awe.csv", index=False)
    except Exception as e:
        print("Failed to load earnings:", e)

        # -- Housing --
        housing_file_path = data_dir / "Housing Prices.xlsx"
        try:
            housing = extractor.load_housing_data(str(housing_file_path))
            print(housing.head())
            try:
                housing_long = extractor.clean_and_melt_housing(housing, time_col=housing.columns[0])
                housing_long.to_csv(data_dir / "housing_long.csv", index=False)
                print("Housing long shape:", housing_long.shape)
            except Exception:
                # If cleaning/melting fails, still save the single-row wide snapshot
                housing.to_csv(data_dir / "housing_latest_row.csv", index=False)
        except Exception as e:
            print("Failed to load housing data:", e)
