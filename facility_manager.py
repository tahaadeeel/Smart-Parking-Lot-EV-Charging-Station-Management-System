import json
import os
import tempfile
import uuid
from datetime import datetime
import csv
from exceptions import DuplicateError, StatusError, IncompatibleError, NotFoundError, ValidationError
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.vehicle import Vehicle
from models.parking_session import ParkingSession
from models.charging_session import ChargingSession

class FacilityManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.files = {
            "lots": os.path.join(data_dir, "lots.json"),
            "spots": os.path.join(data_dir, "spots.json"),
            "vehicles": os.path.join(data_dir, "vehicles.json"),
            "parking_sessions": os.path.join(data_dir, "parking_sessions.json"),
            "charging_sessions": os.path.join(data_dir, "charging_sessions.json")
        }
        for path in self.files.values():
            if not os.path.exists(path):
                self._save_json(path, [])

    def _load_json(self, filepath):
        with open(filepath, 'r') as f:
            return json.load(f)

    def _save_json(self, filepath, data):
        dir_name = os.path.dirname(filepath)
        fd, temp_path = tempfile.mkstemp(dir=dir_name)
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=4)
        os.replace(temp_path, filepath)

    def _now(self):
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def add_lot(self, lot_id, name, location):
        lots = self._load_json(self.files["lots"])
        if any(l["lot_id"] == lot_id for l in lots):
            raise DuplicateError("Lot ID already exists")
        new_lot = ParkingLot(lot_id, name, location)
        lots.append(new_lot.to_dict())
        self._save_json(self.files["lots"], lots)
        return new_lot.to_dict()

    def add_spot(self, spot_id, lot_id, spot_type, hourly_rate, kwh_rate=0.0):
        if hourly_rate <= 0 or kwh_rate < 0:
            raise ValidationError("Rates must be positive")
        lots = self._load_json(self.files["lots"])
        if not any(l["lot_id"] == lot_id for l in lots):
            raise NotFoundError("Lot ID not found")
        spots = self._load_json(self.files["spots"])
        if any(s["spot_id"] == spot_id for s in spots):
            raise DuplicateError("Spot ID already exists")
        
        new_spot = ParkingSpot(spot_id, lot_id, spot_type, "AVAILABLE", hourly_rate, kwh_rate)
        spots.append(new_spot.to_dict())
        self._save_json(self.files["spots"], spots)

        for lot in lots:
            if lot["lot_id"] == lot_id:
                lot["spot_ids"].append(spot_id)
        self._save_json(self.files["lots"], lots)
        return new_spot.to_dict()

    def register_vehicle(self, license_plate, owner_name, vehicle_type):
        vehicles = self._load_json(self.files["vehicles"])
        if any(v["license_plate"] == license_plate for v in vehicles):
            raise DuplicateError("Vehicle already registered")
        new_vehicle = Vehicle(license_plate, owner_name, vehicle_type, self._now())
        vehicles.append(new_vehicle.to_dict())
        self._save_json(self.files["vehicles"], vehicles)
        return new_vehicle.to_dict()

    def check_in(self, license_plate, lot_id, spot_id=None):
        vehicles = self._load_json(self.files["vehicles"])
        vehicle = next((v for v in vehicles if v["license_plate"] == license_plate), None)
        if not vehicle:
            raise NotFoundError("Vehicle not found")

        sessions = self._load_json(self.files["parking_sessions"])
        if any(s["license_plate"] == license_plate and s["status"] == "ACTIVE" for s in sessions):
            raise StatusError("Vehicle already checked in")

        spots = self._load_json(self.files["spots"])
        
        if not spot_id:
            available_spots = [s for s in spots if s["lot_id"] == lot_id and s["status"] == "AVAILABLE"]
            if vehicle["vehicle_type"] == "EV_CAR":
                compatible = [s for s in available_spots if s["spot_type"] == "EV"]
                if not compatible:
                    compatible = [s for s in available_spots if s["spot_type"] == "REGULAR"]
            elif vehicle["vehicle_type"] == "MOTORCYCLE":
                compatible = [s for s in available_spots if s["spot_type"] in ["REGULAR"]]
            else:
                compatible = [s for s in available_spots if s["spot_type"] == "REGULAR"]
            
            if not compatible:
                raise IncompatibleError("No compatible spots available")
            spot_id = compatible[0]["spot_id"]

        spot = next((s for s in spots if s["spot_id"] == spot_id), None)
        if not spot or spot["lot_id"] != lot_id:
            raise NotFoundError("Spot not found in lot")
        if spot["status"] != "AVAILABLE":
            raise StatusError("Spot is not available")
        if vehicle["vehicle_type"] != "EV_CAR" and spot["spot_type"] == "EV":
            raise IncompatibleError("Non-EV vehicle cannot use EV spot")

        spot["status"] = "OCCUPIED"
        self._save_json(self.files["spots"], spots)

        session_id = str(uuid.uuid4())
        new_session = ParkingSession(session_id, license_plate, spot_id, lot_id, self._now())
        sessions.append(new_session.to_dict())
        self._save_json(self.files["parking_sessions"], sessions)
        return new_session.to_dict()

    def check_out(self, session_id):
        sessions = self._load_json(self.files["parking_sessions"])
        session_data = next((s for s in sessions if s["session_id"] == session_id), None)
        if not session_data:
            raise NotFoundError("Session not found")
        if session_data["status"] == "COMPLETED":
            raise StatusError("Session already completed")

        charging = self._load_json(self.files["charging_sessions"])
        if any(c["parking_session_id"] == session_id and c["status"] == "ACTIVE" for c in charging):
            raise StatusError("Cannot checkout with active charging session")

        spots = self._load_json(self.files["spots"])
        spot = next(s for s in spots if s["spot_id"] == session_data["spot_id"])
        
        lot_spots = [s for s in spots if s["lot_id"] == spot["lot_id"]]
        occupied = sum(1 for s in lot_spots if s["status"] == "OCCUPIED")
        multiplier = 1.5 if (occupied / len(lot_spots)) > 0.8 else 1.0

        session = ParkingSession.from_dict(session_data)
        session.check_out_time = self._now()
        session.parking_fee = session.calculate_fee(spot["hourly_rate"], multiplier)
        session.status = "COMPLETED"

        spot["status"] = "AVAILABLE"
        self._save_json(self.files["spots"], spots)

        for i, s in enumerate(sessions):
            if s["session_id"] == session_id:
                sessions[i] = session.to_dict()
                break
        self._save_json(self.files["parking_sessions"], sessions)
        return session.to_dict()

    def start_charging(self, session_id, start_meter):
        sessions = self._load_json(self.files["parking_sessions"])
        session = next((s for s in sessions if s["session_id"] == session_id), None)
        if not session or session["status"] == "COMPLETED":
            raise StatusError("Invalid or completed parking session")

        spots = self._load_json(self.files["spots"])
        spot = next(s for s in spots if s["spot_id"] == session["spot_id"])
        if spot["spot_type"] != "EV":
            raise IncompatibleError("Not an EV spot")

        charging = self._load_json(self.files["charging_sessions"])
        if any(c["parking_session_id"] == session_id and c["status"] == "ACTIVE" for c in charging):
            raise StatusError("Charging already active")

        charge_id = str(uuid.uuid4())
        new_charge = ChargingSession(charge_id, session_id, self._now(), start_meter=start_meter)
        charging.append(new_charge.to_dict())
        self._save_json(self.files["charging_sessions"], charging)
        return new_charge.to_dict()

    def stop_charging(self, charge_id, end_meter):
        charging = self._load_json(self.files["charging_sessions"])
        charge_data = next((c for c in charging if c["charging_session_id"] == charge_id), None)
        if not charge_data:
            raise NotFoundError("Charging session not found")
        if charge_data["status"] == "COMPLETED":
            raise StatusError("Charging already completed")

        sessions = self._load_json(self.files["parking_sessions"])
        session = next(s for s in sessions if s["session_id"] == charge_data["parking_session_id"])
        
        spots = self._load_json(self.files["spots"])
        spot = next(s for s in spots if s["spot_id"] == session["spot_id"])

        c_session = ChargingSession.from_dict(charge_data)
        c_session.end_time = self._now()
        c_session.end_meter = end_meter
        c_session.energy_cost = c_session.calculate_cost(spot["kwh_rate"])
        c_session.status = "COMPLETED"

        for i, c in enumerate(charging):
            if c["charging_session_id"] == charge_id:
                charging[i] = c_session.to_dict()
                break
        self._save_json(self.files["charging_sessions"], charging)
        return c_session.to_dict()

    def generate_report(self):
        lots = self._load_json(self.files["lots"])
        spots = self._load_json(self.files["spots"])
        sessions = self._load_json(self.files["parking_sessions"])
        charging = self._load_json(self.files["charging_sessions"])

        total_lots = len(lots)
        total_spots = len(spots)
        active_sessions = sum(1 for s in sessions if s["status"] == "ACTIVE")
        active_charging = sum(1 for c in charging if c["status"] == "ACTIVE")
        parking_revenue = sum(s.get("parking_fee", 0) for s in sessions)
        charging_revenue = sum(c.get("energy_cost", 0) for c in charging)

        report_lines = [
            "Facility Report",
            f"Generated: {self._now()}",
            "-"*20,
            f"Total Lots: {total_lots}",
            f"Total Spots: {total_spots}",
            f"Active Sessions: {active_sessions}",
            f"Active Charging Sessions: {active_charging}",
            f"Total Parking Revenue: ${parking_revenue:.2f}",
            f"Total Charging Revenue: ${charging_revenue:.2f}"
        ]

        with open("facility_report.txt", "w") as f:
            f.write("\n".join(report_lines))
        return {"message": "Report generated in facility_report.txt"}

    def export_sessions_csv(self):
        sessions = self._load_json(self.files["parking_sessions"])
        if not sessions:
            return
        keys = sessions[0].keys()
        with open("sessions_export.csv", "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(sessions)
        return {"message": "Exported to sessions_export.csv"}