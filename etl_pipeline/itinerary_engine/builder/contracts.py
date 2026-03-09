from pydantic import BaseModel
from typing import List


# ---------------------------------------------------------
# Request
# ---------------------------------------------------------
class ItineraryRequest(BaseModel):
    city: str
    theme: str
    days: int
    start_lat: float
    start_lon: float


# ---------------------------------------------------------
# POI (utilisé pour l'entrée)
# ---------------------------------------------------------
class POI(BaseModel):
    poi_id: str
    label: str
    lat: float
    lon: float
    themes: List[str]


# ---------------------------------------------------------
# Steps
# ---------------------------------------------------------
class StepPOI(BaseModel):
    type: str = "poi"
    poi_id: str
    label: str
    lat: float
    lon: float
    themes: List[str]
    distance_m: int


class StepEvent(BaseModel):
    type: str = "event"
    event_id: str
    label: str


Step = StepPOI | StepEvent


# ---------------------------------------------------------
# Day
# ---------------------------------------------------------
class Day(BaseModel):
    day: int
    steps: List[Step]


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------
class Summary(BaseModel):
    total_distance_m: int
    estimated_duration_s: int
    days_count: int
    poi_count: int
    steps_count: int


# ---------------------------------------------------------
# Response
# ---------------------------------------------------------
class ItineraryResponse(BaseModel):
    city: str
    theme: str
    summary: Summary
    days: List[Day]


