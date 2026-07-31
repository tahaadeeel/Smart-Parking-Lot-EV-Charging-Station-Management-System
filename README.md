# Smart Parking Lot & EV Charging Station Management System

## Overview
This is an advanced Python backend system designed to manage a multi-lot parking facility. It handles mixed spot types (Regular, Handicapped, EV Charging), processes vehicle check-ins and check-outs, and calculates dynamic time-based billing alongside kWh-based EV charging costs.

The entire system is accessible via a RESTful API built with **FastAPI** and includes a CLI interface for generating operational reports. Data is permanently and safely stored using atomic JSON file writes.

## Core Features
- **Mixed Spot Management:** Support for Regular, Handicapped, and EV parking spots.
- **Dynamic Billing Engine:** Calculates time-based fees (with 10-minute grace periods and 1.5x overstay multipliers) and EV charging energy consumption costs.
- **REST API:** Fully featured endpoints for managing lots, spots, vehicles, and sessions.
- **Atomic File Persistence:** Data is securely written to JSON files using atomic write operations to prevent corruption.
- **Robust Error Handling:** Custom exceptions (e.g., `DuplicateError`, `IncompatibleError`) mapped to appropriate HTTP status codes (400, 404, 409).

## Domain Model
- **ParkingLot:** Stores Lot ID, Name, Location, and associated Spot IDs.
- **ParkingSpot:** Stores Spot ID, Lot ID, Spot Type (REGULAR, HANDICAPPED, EV), Status, Hourly Rate, and kWh Rate.
- **Vehicle:** Stores License Plate, Owner Name, Vehicle Type (CAR, MOTORCYCLE, EV_CAR).
- **ParkingSession:** Tracks active parking instances, calculating fees dynamically based on duration and spot rates.
- **ChargingSession:** Linked to a ParkingSession, tracks start/end meter readings (kWh) and calculates energy costs.

## Getting Started

### Prerequisites
- Python 3.10+
- Docker (optional, for containerized deployment)

### 1. Local Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API Server:
   ```bash
   uvicorn api:app --reload
   ```
4. Access the Swagger UI documentation at: `http://127.0.0.1:8000/docs`

### 2. Docker Setup
To run the system using Docker:
```bash
docker-compose up --build
```

## API Endpoints Reference

### Lots & Spots
- `POST /lots` - Create a new parking lot. Requires `lot_id`, `name`, `location`.
- `POST /lots/{lot_id}/spots` - Add a spot. Requires `spot_id`, `spot_type`, `hourly_rate`.

### Vehicles & Sessions
- `POST /vehicles` - Register a vehicle. Requires `license_plate`, `owner_name`, `vehicle_type`.
- `POST /sessions/check-in` - Check in. Requires `license_plate`, `lot_id`. Auto-suggests nearest compatible spot.
- `POST /sessions/{session_id}/check-out` - Check out and compute the final bill.

### EV Charging
- `POST /sessions/{session_id}/charging/start` - Start EV charging. Requires `start_meter`.
- `POST /sessions/charging/{charge_id}/stop` - Stop EV charging. Requires `end_meter`.

### Reports & Export
- `GET /report` - Generate `facility_report.txt` outlining revenue and occupancy.
- `GET /export` - Export all sessions to `sessions_export.csv`.

## CLI Interface
Run the terminal-based Facility Manager to quickly generate reports or export data:
```bash
python main.py
```

## Testing
Run the automated test suite using `pytest` to verify billing logic and exception handling:
```bash
pytest
```