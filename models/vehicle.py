class Vehicle:
    def __init__(self, license_plate, owner_name, vehicle_type, registered_date):
        self.license_plate = license_plate
        self.owner_name = owner_name
        self.vehicle_type = vehicle_type
        self.registered_date = registered_date

    def to_dict(self):
        return {
            "license_plate": self.license_plate,
            "owner_name": self.owner_name,
            "vehicle_type": self.vehicle_type,
            "registered_date": self.registered_date
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)