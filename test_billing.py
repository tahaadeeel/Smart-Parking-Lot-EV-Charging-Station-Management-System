import pytest
from models.parking_session import ParkingSession

def test_grace_period():
    session = ParkingSession("1", "ABC", "S1", "L1", "2023-10-10T10:00:00")
    session.check_out_time = "2023-10-10T10:08:00"
    fee = session.calculate_fee(10.0)
    assert fee == 0.0

def test_standard_billing():
    session = ParkingSession("2", "XYZ", "S2", "L1", "2023-10-10T10:00:00")
    session.check_out_time = "2023-10-10T11:15:00"
    fee = session.calculate_fee(10.0)
    assert fee == 20.0

def test_overstay_billing():
    session = ParkingSession("3", "DEF", "S3", "L1", "2023-10-10T10:00:00")
    session.check_out_time = "2023-10-11T12:00:00"
    fee = session.calculate_fee(10.0)
    assert fee == 270.0