import pandas as pd

def load_earnings_2025(file_path):
    """
    Loads the ONS AWE dataset from sheet '4. NSA sect monthly figs',
    cleans the messy layout, maps CDID codes to readable sector names,
    strips month labels, and returns only 2025 rows.
    """

    # ------------------------------------------------------------
    # 1. Load the raw sheet with NO header
    # ------------------------------------------------------------
    df_raw = pd.read_excel(file_path, sheet_name="4. NSA sect monthly figs", header=None)

    # ------------------------------------------------------------
    # 2. Find the row where 'CDID' appears
    # ------------------------------------------------------------
    cdid_row_idx = df_raw.index[df_raw.iloc[:, 0] == "CDID"][0]

    # ------------------------------------------------------------
    # 3. Use the CDID row as header, and everything after as data
    # ------------------------------------------------------------
    df = df_raw.iloc[cdid_row_idx + 1:].copy()
    df.columns = df_raw.iloc[cdid_row_idx]

    # ------------------------------------------------------------
    # 4. Drop rows that are completely empty
    # ------------------------------------------------------------
    df = df.dropna(how="all")

    # ------------------------------------------------------------
    # 5. Rename the first column to 'Month'
    # ------------------------------------------------------------
    df.rename(columns={df.columns[0]: "Month"}, inplace=True)

    # ------------------------------------------------------------
    # 6. Clean the Month column (remove (p), (r), whitespace)
    # ------------------------------------------------------------
    df["Month"] = (
        df["Month"]
        .astype(str)
        .str.replace("(p)", "", regex=False)
        .str.replace("(r)", "", regex=False)
        .str.strip()
    )

    # ------------------------------------------------------------
    # 7. Map CDID codes → human-readable sector names
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # 8. Keep only readable columns
    # ------------------------------------------------------------
    keep_cols = [col for col in df.columns if not str(col).startswith("Unnamed")]
    df = df[keep_cols]

    # ------------------------------------------------------------
    # 9. Filter to only 2025 rows
    # ------------------------------------------------------------
    df_2025 = df[df["Month"].str.startswith("2025")].copy()

    # ------------------------------------------------------------
    # 10. Keep only Average Weekly Earnings (AWE)
    # ------------------------------------------------------------
    awe_cols = ["Month"] + [col for col in df_2025.columns if col.endswith("AWE")]
    df_2025_awe = df_2025[awe_cols]

    return df_2025_awe

def load_housing_data(file_path):
    """
    Loads housing price data from the specified Excel file.
    """
    df = pd.read_excel(file_path, sheet_name=4, skiprows=2) # Sheet 4 contains housing prices

    # Debug: Print column names to verify
    print("Columns in housing data:", df.columns.tolist())

    # Find the 'Time Period' column(First entry in row)
    time_period_col = df.columns[0]

    # Ensure the first column is in datetime format
    df[time_period_col] = pd.to_datetime(df[time_period_col], errors='coerce')

    # Filter to only the most recent time period
    most_recent_row = df.iloc[-1]

    # Strip the most recent date to only the date part
    most_recent_date = most_recent_row[time_period_col].date()

    # Debug: Print the most recent date
    print("Most recent date in housing data:", most_recent_date)

    #extract headers and prices
    headers = df.columns.tolist()
    prices = most_recent_row

    # Create a DataFrame for housing prices
    housing_prices_df = pd.DataFrame([prices], columns=headers)

    return housing_prices_df

if __name__ == "__main__":
    file_path = r"data/earn02nov2025 (1).xls"  # Use raw string for the path
    earnings_data = load_earnings_2025(file_path)
    print(earnings_data)
    earnings_data.to_csv("earnings_2025_awe.csv", index=False)
    housing_file_path = r"data/Housing Prices.xlsx"
    housing_data = load_housing_data(housing_file_path)
    print(housing_data)

