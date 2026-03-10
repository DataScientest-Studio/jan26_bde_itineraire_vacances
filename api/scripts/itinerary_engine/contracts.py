from pydantic import BaseModel
from typing import List, Optional

class ItineraryRequest(BaseModel):
    postal_code_insee: str
    theme: str
    days: int

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
    # Nouveaux champs Postgres (Optionnels car certains POIs peuvent ne pas avoir ces infos)
    address: Optional[str] = None
    description: Optional[str] = None
    telephone: Optional[str] = None
    website: Optional[str] = None

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