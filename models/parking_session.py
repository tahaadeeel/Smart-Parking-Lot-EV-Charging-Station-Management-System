from datetime import datetime
import math

class ParkingSession:
    def __init__(self, session_id, license_plate, spot_id, lot_id, check_in_time, check_out_time=None, parking_fee=0.0, status="ACTIVE"):
        self.session_id = session_id
        self.license_plate = license_plate
        self.spot_id = spot_id
        self.lot_id = lot_id
        self.check_in_time = check_in_time
        self.check_out_time = check_out_time
        self.parking_fee = parking_fee
        self.status = status

    def calculate_fee(self, hourly_rate, dynamic_multiplier=1.0):
        if not self.check_out_time:
            return 0.0
        
        fmt = "%Y-%m-%dT%H:%M:%S"
        t1 = datetime.strptime(self.check_in_time, fmt)
        t2 = datetime.strptime(self.check_out_time, fmt)
        
        delta = (t2 - t1).total_seconds()
        minutes = delta / 60

        if minutes <= 10:
            return 0.0

        hours = math.ceil(minutes / 60)
        
        if hours > 24:
            base_fee = 24 * hourly_rate
            extra_hours = hours - 24
            extra_fee = extra_hours * (hourly_rate * 1.5)
            total = base_fee + extra_fee
        else:
            total = hours * hourly_rate

        return total * dynamic_multiplier

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "license_plate": self.license_plate,
            "spot_id": self.spot_id,
            "lot_id": self.lot_id,
            "check_in_time": self.check_in_time,
            "check_out_time": self.check_out_time,
            "parking_fee": self.parking_fee,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)