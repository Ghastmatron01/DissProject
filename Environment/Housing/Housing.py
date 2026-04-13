import pandas as pd
import re
from datetime import datetime
from tabulate import tabulate
from pathlib import Path

from Environment.Housing.vocab import (
    UK_REGIONS, UK_COUNTIES, UK_DISTRICTS,
    UK_PROPERTY_TYPES, UK_POSTCODE_AREAS
)
from Environment.Housing.fuzzy_utils import fuzzy_match


class House:
    """Store basic house information from Land Registry or user input."""

    def __init__(self, price, postcode, property_type, date, county, district, bedrooms=None):
        """
        Initialise a house record.

        :param price: Sale price in pounds.
        :param postcode: Full UK postcode.
        :param property_type: One of "flat", "terraced", "semi_detached", "detached", "other".
        :param date: Date of sale or listing.
        :param county: County name.
        :param district: District name.
        :param bedrooms: Number of bedrooms (None if unknown).
        """
        self.price = price
        self.postcode = postcode
        self.property_type = property_type
        self.date = date
        self.county = county
        self.district = district
        self.bedrooms = bedrooms  # None when loaded from Land Registry

    def estimate_bedrooms(self):
        """
        Estimate bedroom count from property type and price.
        Used when real bedroom data is unavailable (e.g. Land Registry CSVs).

        :return: Estimated number of bedrooms.
        """
        ranges = {
            "flat":          (1, 2),
            "terraced":      (2, 3),
            "semi_detached": (3, 4),
            "detached":      (3, 5),
            "other":         (2, 4),
        }

        low, high = ranges.get(self.property_type, (2, 3))

        if self.price < 150_000:
            return low                      # Cheaper -> smaller
        elif self.price > 500_000:
            return high                     # More expensive -> larger
        else:
            return round((low + high) / 2)  # Mid-range -> middle estimate

    def get_bedrooms(self):
        """
        Return real bedroom count if known, otherwise fall back to estimate.

        :return: Bedroom count (real or estimated).
        """
        if self.bedrooms is not None:
            return self.bedrooms
        return self.estimate_bedrooms()


class HousingMarket:
    """
    Store a collection of houses and provide methods to load data from
    the Land Registry, search by various criteria, and display results.
    """

    # Class-level vocab references for efficient access
    UK_REGIONS = UK_REGIONS
    UK_COUNTIES = UK_COUNTIES
    UK_DISTRICTS = UK_DISTRICTS
    UK_PROPERTY_TYPES = UK_PROPERTY_TYPES
    UK_POSTCODE_AREAS = UK_POSTCODE_AREAS

    def __init__(self):
        """Initialise with an empty list of houses."""
        self.houses = []

    def add_house(self, house):
        """
        Add a house to the market.

        :param house: House object to add.
        """
        self.houses.append(house)

    def user_uploading_house(self):
        """
        Let the user manually enter a house they found online. Validates
        every field, creates a House object, adds it to the market, and
        returns it for immediate use by the agent.

        :return: House object, or None if the user cancels or input is invalid.
        """
        print("\n--- Add a Property You've Found ---")
        print("(Type 'cancel' at any prompt to abort)\n")

        # -- Price --
        price_str = input("Enter the house price (e.g. 250000): ").strip()
        if price_str.lower() == "cancel":
            return None
        try:
            price = float(price_str.replace(",", "").replace("£", ""))
        except ValueError:
            print(f"Invalid price: '{price_str}'. Must be a number.")
            return None

        # -- Postcode --
        postcode = input("Enter the postcode (e.g. M1 1AA): ").strip().upper()
        if postcode.lower() == "cancel":
            return None

        # -- Property Type --
        valid_types = ["flat", "terraced", "semi_detached", "detached", "other"]
        print(f"Valid property types: {valid_types}")
        property_type = input("Enter the property type: ").strip().lower()
        if property_type == "cancel":
            return None
        if property_type not in valid_types:
            print(f"Invalid type: '{property_type}'. Must be one of {valid_types}")
            return None

        # -- Date --
        date_str = input("Enter the listing/sale date (YYYY-MM-DD), or press Enter for today: ").strip()
        if date_str.lower() == "cancel":
            return None
        if date_str == "":
            date = datetime.now()
        else:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date: '{date_str}'. Use YYYY-MM-DD format.")
                return None

        # -- County --
        county = input("Enter the county (e.g. GREATER MANCHESTER): ").strip().upper()
        if county.lower() == "cancel":
            return None

        # -- District --
        district = input("Enter the district (e.g. MANCHESTER): ").strip().upper()
        if district.lower() == "cancel":
            return None

        # -- Bedrooms (optional) --
        bedrooms_str = input("Enter the number of bedrooms (or press Enter to estimate): ").strip()
        if bedrooms_str.lower() == "cancel":
            return None
        if bedrooms_str == "":
            bedrooms = None  # Will use estimate_bedrooms() automatically
        else:
            try:
                bedrooms = int(bedrooms_str)
            except ValueError:
                print(f"Invalid bedrooms: '{bedrooms_str}'. Must be a whole number.")
                return None

        # -- Create and store the House --
        house = House(
            price=price,
            postcode=postcode,
            property_type=property_type,
            date=date,
            county=county,
            district=district,
            bedrooms=bedrooms
        )

        self.add_house(house)

        print(f"\n Property added: {property_type} in {district}, {county} - £{price:,.0f}")
        if bedrooms is not None:
            print(f"   Bedrooms: {bedrooms}")
        else:
            print(f"   Bedrooms: ~{house.estimate_bedrooms()} (estimated from type & price)")

        return house

    # --------------------------------------------------------------------
    #  Loading Functions
    # --------------------------------------------------------------------

    def load_year(self, year, base_path):
        """
        Load a single year of Land Registry CSV data.

        :param year: Year to load (e.g. 2023).
        :param base_path: Directory containing pp-YYYY.csv files.
        """
        filename = f"pp-{year}.csv"
        csv_path = Path(base_path) / filename

        if not csv_path.exists():
            print(f"File not found for year {year}: {csv_path}")
            return
        print(f"Loading {csv_path}")

        self.load_from_land_registry(csv_path)

    def load_years(self, years, base_path):
        """
        Load multiple years of Land Registry data.

        :param years: List of years to load.
        :param base_path: Directory containing pp-YYYY.csv files.
        """
        for year in years:
            self.load_year(year, base_path)

    def load_all_available_years(self, base_path):
        """
        Discover and load all available pp-YYYY.csv files in the directory.

        :param base_path: Directory containing pp-YYYY.csv files.
        """
        base = Path(base_path)
        years = []

        for file in base.glob("pp-*.csv"):
            try:
                year = int(file.stem.split("-")[1])
                years.append(year)
            except:
                continue

        years = sorted(years)
        print(f"Found available years: {years}")

        self.load_years(years, base_path)

    def load_from_land_registry(self, csv_path,
                                min_date="2020-01-01",
                                counties=None,
                                districts=None,
                                min_price=50_000,
                                max_price=1_000_000):
        """
        Load and filter Land Registry price paid data from a CSV.

        :param csv_path: Path to the CSV file.
        :param min_date: Only include sales on or after this date.
        :param counties: Optional list of county names to filter by.
        :param districts: Optional list of district names to filter by.
        :param min_price: Minimum sale price to include.
        :param max_price: Maximum sale price to include.
        """
        # Map single-letter codes to readable property types
        type_map = {
            "D": "detached",
            "S": "semi_detached",
            "T": "terraced",
            "F": "flat",
            "O": "other"
        }

        min_date = pd.to_datetime(min_date)

        # Read in chunks to handle large files
        chunksize = 100_000
        for chunk in pd.read_csv(csv_path, header=None, chunksize=chunksize):
            # Assign column names matching the Land Registry standard layout
            chunk.columns = [
                "transaction_id", "price", "date",
                "postcode", "property_type", "new_build",
                "tenure", "primary_address", "secondary_address",
                "street", "locality", "town_city",
                "district", "county", "ppd_category",
                "record_status"
            ]

            # Filter by date
            chunk["date"] = pd.to_datetime(chunk["date"])
            df = chunk[chunk["date"] >= min_date]

            # Apply optional region filters
            if counties:
                df = df[df["county"].isin(counties)]
            if districts:
                df = df[df["district"].isin(districts)]

            # Apply price range filter
            df = df[(df["price"] >= min_price) & (df["price"] <= max_price)]

            # Map property type codes to readable names
            df["property_type_readable"] = df["property_type"].map(type_map)

            # Create House objects from each row
            for _, row in df.iterrows():
                house = House(
                    price=row["price"],
                    postcode=row["postcode"],
                    property_type=row["property_type_readable"],
                    date=row["date"],
                    county=row["county"],
                    district=row["district"]
                )
                self.add_house(house)

    def search(self,
               min_price=None,
               max_price=None,
               property_types=None,
               counties=None,
               districts=None,
               regions=None,
               years=None,
               postcode_prefixes=None,
               after_date=None,
               before_date=None):
        """
        Flexibly search loaded houses by any combination of criteria.
        All parameters are optional and can be combined.

        :param min_price: Minimum price filter.
        :param max_price: Maximum price filter.
        :param property_types: List of property type strings to include.
        :param counties: List of county names to include.
        :param districts: List of district names to include.
        :param regions: List of region names (expanded to counties internally).
        :param years: List of years to filter by sale date.
        :param postcode_prefixes: List of postcode prefixes to match.
        :param after_date: Only include sales on or after this date.
        :param before_date: Only include sales on or before this date.
        :return: List of matching House objects.
        """
        results = self.houses

        if min_price is not None:
            results = [h for h in results if h.price >= min_price]

        if max_price is not None:
            results = [h for h in results if h.price <= max_price]

        if property_types:
            results = [h for h in results if h.property_type in property_types]

        if counties:
            results = [h for h in results if h.county in counties]

        if districts:
            results = [h for h in results if h.district in districts]

        if regions:
            # Expand regions into their constituent counties
            allowed_counties = []
            for region in regions:
                allowed_counties.extend(self.UK_REGIONS.get(region, []))
            results = [h for h in results if h.county in allowed_counties]

        if postcode_prefixes:
            results = [
                h for h in results
                if any(h.postcode.startswith(prefix) for prefix in postcode_prefixes)
            ]

        if years:
            results = [h for h in results if h.date.year in years]

        if after_date:
            results = [h for h in results if h.date >= after_date]

        if before_date:
            results = [h for h in results if h.date <= before_date]

        return results

    # --------------------------------------------------------------------
    #  Query Data
    # --------------------------------------------------------------------

    def natural_search(self, text, base_path):
        """
        Parse a natural language query and run a search.

        :param text: User's natural language search string.
        :param base_path: Directory containing pp-YYYY.csv files.
        :return: Search results displayed to console.
        """
        params = self.interpret_query(text)
        return self.process_and_display(base_path=base_path, **params)

    def interpret_query(self, text):
        """
        Extract search parameters from a natural language query using
        fuzzy matching against known counties, districts, and types.

        :param text: User's natural language search query.
        :return: Dict of extracted search parameters.
        """
        text = text.lower()

        params = {
            "counties": [],
            "districts": [],
            "regions": [],
            "property_types": [],
            "postcode_prefixes": [],
            "min_price": None,
            "max_price": None,
            "years": []
        }

        # Fuzzy match counties
        county_matches = [c for c in self.UK_COUNTIES if fuzzy_match(text, [c])]
        params["counties"].extend(county_matches)

        # Fuzzy match districts
        district_matches = [d for d in self.UK_DISTRICTS if fuzzy_match(text, [d])]
        params["districts"].extend(district_matches)

        # Property types (exact match is fine and fast)
        for p in self.UK_PROPERTY_TYPES:
            if p in text:
                params["property_types"].append(p)

        # Postcode prefixes (exact match)
        for prefix in self.UK_POSTCODE_AREAS:
            if prefix.lower() in text:
                params["postcode_prefixes"].append(prefix)

        # Extract price like "200k"
        price_match = re.search(r"(\d{2,3})k", text)
        if price_match:
            params["max_price"] = int(price_match.group(1)) * 1000

        # Extract years (2018-2025 range)
        for y in range(2018, 2026):
            if str(y) in text:
                params["years"].append(y)

        return params

    # --------------------------------------------------------------------
    #  Printing the data
    # --------------------------------------------------------------------

    def print_search_results(self, houses, limit=20):
        """
        Print search results in a formatted table.

        :param houses: List of House objects to display.
        :param limit: Maximum number of results to show.
        """
        rows = []
        for h in houses[:limit]:
            rows.append([
                h.price,
                h.postcode,
                h.property_type,
                h.date.date(),
                h.county,
                h.district
            ])

        print(tabulate(
            rows,
            headers=["Price", "Postcode", "Type", "Date", "County", "District"],
            tablefmt="pretty"
        ))

    def process_and_display(self,
                            years=None,
                            min_price=None,
                            max_price=None,
                            property_types=None,
                            counties=None,
                            districts=None,
                            regions=None,
                            postcode_prefixes=None,
                            after_date=None,
                            before_date=None,
                            limit=20,
                            base_path=None):
        """
        High-level function that loads data, applies filters, and prints results.

        :param years: List of years to load and filter by.
        :param min_price: Minimum price filter.
        :param max_price: Maximum price filter.
        :param property_types: List of property type strings to include.
        :param counties: List of county names to include.
        :param districts: List of district names to include.
        :param regions: List of region names.
        :param postcode_prefixes: List of postcode prefixes to match.
        :param after_date: Only include sales on or after this date.
        :param before_date: Only include sales on or before this date.
        :param limit: Maximum number of results to display.
        :param base_path: Directory containing pp-YYYY.csv files.
        """
        if base_path and years:
            print(f" Loading data for years: {years}")
            self.load_years(years, base_path)

        results = self.search(
            min_price=min_price,
            max_price=max_price,
            property_types=property_types,
            counties=counties,
            districts=districts,
            regions=regions,
            years=years,
            postcode_prefixes=postcode_prefixes,
            after_date=after_date,
            before_date=before_date
        )

        print(f"\n Found {len(results)} matching houses\n")
        self.print_search_results(results, limit=limit)

        if results:
            prices = [h.price for h in results]
            print("\n Summary:")
            print(f"  Min price: £{min(prices):,}")
            print(f"  Max price: £{max(prices):,}")
            print(f"  Average price: £{sum(prices) / len(prices):,.0f}")
