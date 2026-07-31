class ChargingSession:
    def __init__(self, charging_session_id, parking_session_id, start_time, end_time=None, start_meter=0.0, end_meter=0.0, energy_cost=0.0, status="ACTIVE"):
        self.charging_session_id = charging_session_id
        self.parking_session_id = parking_session_id
        self.start_time = start_time
        self.end_time = end_time
        self.start_meter = start_meter
        self.end_meter = end_meter
        self.energy_cost = energy_cost
        self.status = status

    def calculate_cost(self, kwh_rate):
        if not self.end_time:
            return 0.0
        consumed = self.end_meter - self.start_meter
        if consumed < 0:
            consumed = 0
        return consumed * kwh_rate

    def to_dict(self):
        return {
            "charging_session_id": self.charging_session_id,
            "parking_session_id": self.parking_session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "start_meter": self.start_meter,
            "end_meter": self.end_meter,
            "energy_cost": self.energy_cost,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)