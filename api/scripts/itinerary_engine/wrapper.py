import time

from scripts.itinerary_engine.contracts import (
    ItineraryRequest,
    ItineraryResponse,
    POI,
)
from scripts.itinerary_engine.load_pois_for_city import load_pois_for_city
from scripts.itinerary_engine.postgres_enricher import enrich_pois_with_postgres
from scripts.itinerary_engine.itinerary_builder import ItineraryBuilder


def generate_itinerary(req: ItineraryRequest, use_neo4j: bool = False) -> ItineraryResponse:
    start = time.time()

    # 1) Charger les POI depuis Postgres
    pois_raw = load_pois_for_city(req.postalcodeinsee, req.themeid)

    # Limiter dès le début
    max_poi = req.days * 4
    pois_raw = pois_raw[:max_poi]

    # 2) Distances
    if use_neo4j:
        from scripts.itinerary_engine.neo4j_distance_loader import load_distances_from_neo4j
        distances = load_distances_from_neo4j(pois_raw)
        builder = ItineraryBuilder(distances=distances)
    else:
        builder = ItineraryBuilder(distances={})

    # 3) Normalisation
    pois = [POI(**p).dict() for p in pois_raw]

    # 4) Construire l’itinéraire
    itinerary_dict = builder.build_itinerary(
        postalcodeinsee=req.postalcodeinsee,
        themeid=req.themeid,
        pois=pois,
        nb_days=req.days,
    )

    # 5) Enrichissement Postgres
    kept_uuids = [
        step["uuid"]
        for day in itinerary_dict["days"]
        for step in day["steps"]
        if step["type"] == "poi"
    ]

    if kept_uuids:
        enriched_data = enrich_pois_with_postgres(kept_uuids)
        for day in itinerary_dict["days"]:
            for step in day["steps"]:
                if step["type"] == "poi":
                    uid = step["uuid"]
                    if uid in enriched_data:
                        step.update(enriched_data[uid])

    itinerary_dict["execution_time_seconds"] = round(time.time() - start, 3)

    return ItineraryResponse(**itinerary_dict)
