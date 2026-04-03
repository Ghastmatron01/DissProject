class HousingUnit:
    def __init__(self, id, price, rent, location, size, bedrooms, bathrooms, type, quality):
        self.id = id
        self.price = price
        self.rent = rent
        self.location = location
        self.size = size
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.type = type
        self.quality = quality
    def __repr__(self):
        return (f"HousingUnit(id={self.id}, price={self.price}, rent={self.rent}, "
                f"location='{self.location}', size={self.size}, bedrooms={self.bedrooms}, "
                f"bathrooms={self.bathrooms}, type='{self.type}', quality='{self.quality}')")

    #child class for housing unit, will be used for modelling faults in the houses, such as damp, structural damage, etc
    class FaultModellingHouse(HousingUnit):
        def __init__(self, id, price, rent, location, size, bedrooms, bathrooms, type, quality, age, maintenance_history, materials, maintenance_score, boiler_age, occupancy):
            super().__init__(id, price, rent, location, size, bedrooms, bathrooms, type, quality)
            self.age = age
            self.maintenance_history = maintenance_history
            self.materials = materials
            self.maintenance_score = maintenance_score
            self.boiler_age = boiler_age
            self.occupancy = occupancy

