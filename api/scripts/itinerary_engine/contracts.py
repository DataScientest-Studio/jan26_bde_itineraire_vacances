from pydantic import BaseModel
from typing import List, Optional, Union

# -----------------------------
# REQUEST
# -----------------------------

class ItineraryRequest(BaseModel):
    postalcodeinsee: str
    themeid: int
    days: int

# -----------------------------
# POI (utilisé en interne)
# -----------------------------

class POI(BaseModel):
    uuid: str
    label: str
    latitude: float
    longitude: float
    themeid: int
    postalcodeinsee: str

# -----------------------------
# STEPS
# -----------------------------

class StepPOI(BaseModel):
    type: str = "poi"
    uuid: str
    label: str
    latitude: float
    longitude: float
    themeid: int
    distance_m: int

    # Champs enrichis depuis Postgres (optionnels)
    address: Optional[str] = None
    description: Optional[str] = None
    telephone: Optional[str] = None
    website: Optional[str] = None

class StepEvent(BaseModel):
    type: str = "event"
    event_id: str
    label: str

Step = Union[StepPOI, StepEvent]

# -----------------------------
# DAY
# -----------------------------

class Day(BaseModel):
    day: int
    steps: List[Step]

# -----------------------------
# SUMMARY
# -----------------------------

class Summary(BaseModel):
    total_distance_m: int
    estimated_duration_s: int
    days_count: int
    poi_count: int
    steps_count: int

# -----------------------------
# RESPONSE
# -----------------------------

class ItineraryResponse(BaseModel):
    postalcodeinsee: str
    themeid: int
    summary: Summary
    days: List[Day]
    execution_time_seconds: float | None = None
