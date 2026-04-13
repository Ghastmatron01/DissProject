# Fault Modelling class
# Class will be for modelling faults in the houses, such as damp, structural damage, etc

class Fault_Modelling:
    """
    Model faults in houses such as damp, structural damage, boiler
    failure, etc. Uses base probabilities adjusted by house attributes.
    Probabilities and weights are placeholders until real EHS data is
    integrated.
    """

    def __init__(self, house):
        """
        Initialise the fault model from a house object.

        :param house: House object with age, maintenance_history, location,
                      materials, and occupancy attributes.
        """
        self.house = house
        self.age = house.age
        self.maintenance_history = house.maintenance_history
        self.location = house.location
        self.materials = house.materials
        self.occupancy = house.occupancy

        # Placeholder faults and values - will be calibrated from real EHS data
        self.faults = {
            "damp": {
                "base_probability": 0.05,
                "factors": ["age", "wall_type", "ventilation", "climate"]
            },
            "boiler_failure": {
                "base_probability": 0.03,
                "factors": ["age", "maintenance_history", "usage"]
            },
            "structural_damage": {
                "base_probability": 0.02,
                "factors": ["age", "materials", "occupancy"]
            },
            "electrical_fault": {
                "base_probability": 0.04,
                "factors": ["age", "maintenance_history", "usage"]
            },
            "plumbing_issue": {
                "base_probability": 0.03,
                "factors": ["age", "maintenance_history", "usage"]
            },
            "roof_leak": {
                "base_probability": 0.02,
                "factors": ["age", "materials", "climate"]
            },
            "foundation_issue": {
                "base_probability": 0.01,
                "factors": ["age", "materials", "occupancy"]
            },
        }

    def calculate_fault_probability(self, fault):
        """
        Calculate the probability of a specific fault occurring based
        on the house's attributes and the fault's contributing factors.
        Weights are placeholders until real EHS research is complete.

        :param fault: Name of the fault (e.g. "damp", "boiler_failure").
        :return: Probability of the fault occurring (float).
        """
        if fault not in self.faults:
            raise ValueError(f"Fault '{fault}' not recognized.")

        fault_info = self.faults[fault]
        probability = fault_info["base_probability"]

        for factor in fault_info["factors"]:
            if factor == "age":
                # Older houses are more prone to faults
                probability += self.age * 0.001
            elif factor == "maintenance_history":
                # Better maintenance reduces probability
                probability -= self.maintenance_history * 0.002
            elif factor == "materials":
                # Brick is more resilient than wood
                if self.materials == "brick":
                    probability -= 0.01
                elif self.materials == "wood":
                    probability += 0.01
            elif factor == "occupancy":
                # Higher occupancy increases wear and tear
                if self.occupancy > 4:
                    probability += 0.01

        return probability
