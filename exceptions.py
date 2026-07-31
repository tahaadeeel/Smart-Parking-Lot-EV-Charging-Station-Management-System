class ParkingException(Exception): pass
class DuplicateError(ParkingException): pass
class StatusError(ParkingException): pass
class IncompatibleError(ParkingException): pass
class NotFoundError(ParkingException): pass
class ValidationError(ParkingException): pass