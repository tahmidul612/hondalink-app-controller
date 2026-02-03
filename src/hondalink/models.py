from enum import Enum

from pydantic import BaseModel


class CommandType(str, Enum):
    LOCK = "lock"
    UNLOCK = "unlock"
    START = "start"
    STOP = "stop"
    # Find, Lights, Horn could be added later


class VehicleStatus(BaseModel):
    odometer: str
    fuel_level: str
    range_remaining: str
    oil_life: str
    is_locked: bool
    last_updated: str


class RemoteStartStatus(BaseModel):
    """Status information for an active remote start session."""

    is_active: bool
    remaining_time: str  # Format: "MM:SS" or "Unknown"
    cabin_temperature: str  # Format: "XX °C" or "Unknown"
