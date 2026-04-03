import pandas as pd
from datetime import datetime
from tabulate import tabulate
import random


class House:
    """
    Store basic house information
    """
    def __init__(self, price, postcode, property_type, date, county, district):
        self.price = price
        self.postcode = postcode
        self.property_type = property_type
        self.date = date
        self.county = county
        self.district = district

class HousingMarket:
    """
Store a collection of houses and provide methods to load data from the Land Registry
    """
    def __init__(self):
        self.houses = []

    def add_house(self, house):
        self.houses.append(house)

    def load_from_land_registry(self, csv_path,
                                min_date="2020-01-01",
                                counties=None,
                                districts=None,
                                min_price=50_000,
                                max_price=1_000_000):
        """
        counties / districts: list of strings or None
        """
        type_map = {
            "D": "detached",
            "S": "semi_detached",
            "T": "terraced",
            "F": "flat",
            "O": "other"
        }

        min_date = pd.to_datetime(min_date)

        chunksize = 100_000
        for chunk in pd.read_csv(csv_path, header=None, chunksize=chunksize):
            # Land Registry price paid standard layout
            chunk.columns = [
                "transaction_id", "price", "date",
                "postcode", "property_type", "new_build",
                "tenure", "primary_address", "secondary_address",
                "street", "locality", "town_city",
                "district", "county", "ppd_category",
                "record_status"
            ]

            # Basic cleaning
            chunk["date"] = pd.to_datetime(chunk["date"])
            df = chunk[chunk["date"] >= min_date]

            # Region filters
            if counties:
                df = df[df["county"].isin(counties)]
            if districts:
                df = df[df["district"].isin(districts)]

            # Price filters
            df = df[(df["price"] >= min_price) & (df["price"] <= max_price)]

            # Map property types
            df["property_type_readable"] = df["property_type"].map(type_map)

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

    def print_random_table(self, limit=20):
        if not self.houses:
            print("No houses loaded.")
            return

        # Random sample (handles case where n > number of houses)
        sample = random.sample(self.houses, min(limit, len(self.houses)))

        rows = []
        for h in sample:
            rows.append([
                h.price,
                h.postcode,
                h.property_type,
                h.date.date() if hasattr(h.date, "date") else h.date,
                h.county,
                h.district
            ])

        print(tabulate(
            rows,
            headers=["Price", "Postcode", "Type", "Date", "County", "District"],
            tablefmt="pretty"
        ))


market = HousingMarket()
csv_path = r"C:\Users\User\PycharmProjects\Dissertation\Environment\Housing\HM Land Registery Price Paid\pp-2024.csv"
market.load_from_land_registry(
    csv_path,
    min_date="2020-01-01",
    counties=["NOTTINGHAMSHIRE"],
)
print(len(market.houses))
market.print_random_table(limit=20)