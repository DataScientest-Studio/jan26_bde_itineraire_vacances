from pydantic import BaseModel
from typing import List

class ItineraryRequest(BaseModel):
    postal_code_insee: str
    theme: str
    days: int
    start_lat: float
    start_lon: float

class POI(BaseModel):
    poi_id: str
    label: str
    lat: float
    lon: float
    theme: str

class StepPOI(BaseModel):
    type: str = "poi"
    poi_id: str
    label: str
    lat: float
    lon: float
    theme: str
    distance_m: int

class StepEvent(BaseModel):
    type: str = "event"
    event_id: str
    label: str

Step = StepPOI | StepEvent

class Day(BaseModel):
    day: int
    steps: List[Step]

class Summary(BaseModel):
    total_distance_m: int
    estimated_duration_s: int
    days_count: int
    poi_count: int
    steps_count: int

class ItineraryResponse(BaseModel):
    postal_code_insee: str
    theme: str
    summary: Summary
    days: List[Day]