from scripts.itinerary_engine.contracts import ItineraryRequest, ItineraryResponse, POI
from scripts.itinerary_engine.load_pois_for_city import load_pois_for_city
from scripts.itinerary_engine.itinerary_builder import ItineraryBuilder

def generate_itinerary(req: ItineraryRequest) -> ItineraryResponse:
    pois_raw = load_pois_for_city(req.postal_code_insee, req.theme)
    # model_dump() est préférable à dict() sous Pydantic V2
    pois = [POI(**p).model_dump() for p in pois_raw]

    builder = ItineraryBuilder()
    itinerary_dict = builder.build_itinerary(
        postal_code_insee=req.postal_code_insee,
        theme=req.theme,
        pois=pois,
        nb_days=req.days,
        start_lat=req.start_lat,
        start_lon=req.start_lon
    )
    builder.close()

    return ItineraryResponse(**itinerary_dict)