import pandas as pd
from datetime import datetime
from tabulate import tabulate
from pathlib import Path


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
Store a collection of UK regions and their counties, to enable searching by regions
    """
    def __init__(self):
        self.houses = []
        self.UK_REGIONS = UK_REGIONS = {
            "north_east": [
                "County Durham", "Northumberland", "Tyne and Wear"
            ],
            "north_west": [
                "Cheshire", "Cumbria", "Greater Manchester", "Lancashire", "Merseyside"
            ],
            "yorkshire_humber": [
                "East Riding of Yorkshire", "North Lincolnshire", "North East Lincolnshire",
                "North Yorkshire", "South Yorkshire", "West Yorkshire"
            ],
            "east_midlands": [
                "Derbyshire", "Leicestershire", "Lincolnshire", "Northamptonshire", "Nottinghamshire"
            ],
            "west_midlands": [
                "Herefordshire", "Shropshire", "Staffordshire", "Warwickshire", "West Midlands", "Worcestershire"
            ],
            "east_of_england": [
                "Bedfordshire", "Cambridgeshire", "Essex", "Hertfordshire", "Norfolk", "Suffolk"
            ],
            "south_east": [
                "Berkshire", "Buckinghamshire", "East Sussex", "Hampshire", "Kent",
                "Oxfordshire", "Surrey", "West Sussex"
            ],
            "south_west": [
                "Bristol", "Cornwall", "Devon", "Dorset", "Gloucestershire",
                "Somerset", "Wiltshire"
            ],
            "london": [
                "Greater London"
            ],
            "wales": [
                "Blaenau Gwent", "Bridgend", "Caerphilly", "Cardiff", "Carmarthenshire",
                "Ceredigion", "Conwy", "Denbighshire", "Flintshire", "Gwynedd",
                "Isle of Anglesey", "Merthyr Tydfil", "Monmouthshire", "Neath Port Talbot",
                "Newport", "Pembrokeshire", "Powys", "Rhondda Cynon Taf", "Swansea",
                "Torfaen", "Vale of Glamorgan", "Wrexham"
            ]
        }

    def add_house(self, house):
        self.houses.append(house)

    #------------------------------------
    # Loading Functions
    #-------------------------------------

    def load_year(self, year, base_path):
        """
        A function to load the year of the CSV file required for the users search
        :param year:
        :param base_path:
        :return:
        """
        filename = f"pp-{year}.csv"
        csv_path = Path(base_path) / filename

        if not csv_path.exists():
            print(f"File not found for year {year}: {csv_path}")
            return
        print(f"Loading {csv_path}")

        self.load_from_land_registry(csv_path)

    def load_years(self, years, base_path):
        # function for multiple years
        for year in years:
            self.load_year(year, base_path)

    def load_all_available_years(self, base_path):
        base = Path(base_path)
        years = []

        for file in base.glob("pp-*.csv"):
            try:
                year = int(file.stem.split("-")[1])
                years.append(year)
            except:
                continue

        years = sorted(years)
        print(f"📅 Found available years: {years}")

        self.load_years(years, base_path)


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

    def search(self,
               min_price=None,
               max_price=None,
               property_types=None,
               counties=None,
               districts=None,
               regions=None,
               years=None,
               after_date=None,
               before_date=None):
        """
        A function to allow for flexible searching of the houses the user wants by district, county, region, price and date. All parameters are optional and can be combined.
        Will be taking these prices for guesstimate prices of other new houses in the areas
        :param min_price:
        :param max_price:
        :param property_types:
        :param counties:
        :param districts:
        :param regions:
        :param after_date:
        :param before_date:
        :return:
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
            allowed_counties = []
            for region in regions:
                allowed_counties.extend(self.UK_REGIONS.get(region, []))
            results = [h for h in results if h.county in allowed_counties]

        if years:
            results = [h for h in results if h.date.year in years
                       ]
        if after_date:
            results = [h for h in results if h.date >= after_date]

        if before_date:
            results = [h for h in results if h.date <= before_date]

        return results

    # -------------------------
    #Printing the data
    #--------------------------

    def print_search_results(self, houses, limit=20):
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
                            after_date=None,
                            before_date=None,
                            limit=20,
                            base_path=None):
        """
        High-level function that loads data, applies filters, and prints results.
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
            after_date=after_date,
            before_date=before_date
        )

        print(f"\n Found {len(results)} matching houses\n")
        self.print_search_results(results, limit=limit)

        if results:
            prices = [h.price for h in results]
            print("\n Summary:")
            print(f"  • Min price: £{min(prices):,}")
            print(f"  • Max price: £{max(prices):,}")
            print(f"  • Average price: £{sum(prices) / len(prices):,.0f}")


market = HousingMarket()

market.process_and_display(
    years=[2023],
    counties="Nottinghamshire",
    limit=15,
    base_path=r"C:\Users\User\PycharmProjects\Dissertation\Environment\Housing\HM Land Registery Price Paid"
)