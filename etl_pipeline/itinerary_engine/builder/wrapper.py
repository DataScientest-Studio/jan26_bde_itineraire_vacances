from itinerary_engine.builder.contracts import (ItineraryRequest,ItineraryResponse,POI)
from itinerary_engine.builder.load_pois_for_city import load_pois_for_city
from itinerary_engine.builder.itinerary_builder import ItineraryBuilder


def generate_itinerary(req: ItineraryRequest) -> ItineraryResponse:
    """
    Wrapper métier : charge les POIs, appelle le builder,
    et renvoie un ItineraryResponse propre.
    """

    # 1. Charger les POIs depuis Postgres
    pois_raw = load_pois_for_city(req.city, req.theme)

    # 2. Convertir en objets POI (validation souple)
    pois = [POI(**p).dict() for p in pois_raw]

    # 3. Appeler le builder
    builder = ItineraryBuilder()
    itinerary_dict = builder.build_itinerary(
        city=req.city,
        theme=req.theme,
        pois=pois,
        nb_days=req.days,
        start_lat=req.start_lat,
        start_lon=req.start_lon
    )
    builder.close()

    # 4. Retourner un modèle Pydantic propre
    return ItineraryResponse(**itinerary_dict)

