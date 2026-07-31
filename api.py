from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from facility_manager import FacilityManager
from exceptions import ParkingException, DuplicateError, StatusError, IncompatibleError, NotFoundError, ValidationError

app = FastAPI(title="Smart Parking API")
fm = FacilityManager()

class LotCreate(BaseModel):
    lot_id: str
    name: str
    location: str

class SpotCreate(BaseModel):
    spot_id: str
    spot_type: str
    hourly_rate: float
    kwh_rate: float = 0.0

class VehicleCreate(BaseModel):
    license_plate: str
    owner_name: str
    vehicle_type: str

class CheckIn(BaseModel):
    license_plate: str
    lot_id: str
    spot_id: str = None

class ChargeStart(BaseModel):
    start_meter: float

class ChargeStop(BaseModel):
    end_meter: float

@app.exception_handler(ParkingException)
async def parking_exception_handler(request, exc):
    code = 400
    if isinstance(exc, DuplicateError): code = 409
    elif isinstance(exc, NotFoundError): code = 404
    elif isinstance(exc, StatusError) or isinstance(exc, IncompatibleError): code = 409
    return {"error": str(exc)}, code

@app.post("/lots", status_code=201)
def create_lot(lot: LotCreate):
    return fm.add_lot(lot.lot_id, lot.name, lot.location)

@app.post("/lots/{lot_id}/spots", status_code=201)
def create_spot(lot_id: str, spot: SpotCreate):
    return fm.add_spot(spot.spot_id, lot_id, spot.spot_type, spot.hourly_rate, spot.kwh_rate)

@app.post("/vehicles", status_code=201)
def register_vehicle(vehicle: VehicleCreate):
    return fm.register_vehicle(vehicle.license_plate, vehicle.owner_name, vehicle.vehicle_type)

@app.post("/sessions/check-in", status_code=201)
def check_in(data: CheckIn):
    return fm.check_in(data.license_plate, data.lot_id, data.spot_id)

@app.post("/sessions/{session_id}/check-out")
def check_out(session_id: str):
    return fm.check_out(session_id)

@app.post("/sessions/{session_id}/charging/start")
def start_charging(session_id: str, data: ChargeStart):
    return fm.start_charging(session_id, data.start_meter)

@app.post("/sessions/charging/{charge_id}/stop")
def stop_charging(charge_id: str, data: ChargeStop):
    return fm.stop_charging(charge_id, data.end_meter)

@app.get("/")
def home():
    return {"message": "Smart Parking API is running. Go to /docs for the API documentation."}

@app.get("/report")
def get_report():
    return fm.generate_report()

@app.get("/export")
def export_csv():
    return fm.export_sessions_csv()