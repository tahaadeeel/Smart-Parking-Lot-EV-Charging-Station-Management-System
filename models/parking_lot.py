class ParkingLot:
    def __init__(self, lot_id, name, location, spot_ids=None):
        self.lot_id = lot_id
        self.name = name
        self.location = location
        self.spot_ids = spot_ids or []

    def to_dict(self):
        return {
            "lot_id": self.lot_id,
            "name": self.name,
            "location": self.location,
            "spot_ids": self.spot_ids
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)