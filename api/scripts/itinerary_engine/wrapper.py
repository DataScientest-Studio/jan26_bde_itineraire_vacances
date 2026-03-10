from scripts.itinerary_engine.contracts import ItineraryRequest, ItineraryResponse, POI
from scripts.itinerary_engine.load_pois_for_city import load_pois_for_city
from scripts.itinerary_engine.postgres_enricher import enrich_pois_with_postgres
from scripts.itinerary_engine.itinerary_builder import ItineraryBuilder

def generate_itinerary(req: ItineraryRequest) -> ItineraryResponse:
    pois_raw = load_pois_for_city(req.postal_code_insee, req.theme)
    pois = [POI(**p).model_dump() for p in pois_raw]

    # Construction de l'itinéraire (Logique Spatiale / Neo4j)
    builder = ItineraryBuilder()
    itinerary_dict = builder.build_itinerary(
        postal_code_insee=req.postal_code_insee,
        theme=req.theme,
        pois=pois,
        nb_days=req.days
    )
    builder.close()

    # --- ENRICHISSEMENT POSTGRES ---
    # 1. On liste uniquement les IDs des POIs qui ont été conservés dans le JSON
    kept_poi_ids = [
        step["poi_id"] 
        for day in itinerary_dict["days"] 
        for step in day["steps"] 
        if step["type"] == "poi"
    ]

    # 2. On récupère les données
    if kept_poi_ids:
        enriched_data = enrich_pois_with_postgres(kept_poi_ids)

        # 3. On injecte les données dans le dictionnaire final
        for day in itinerary_dict["days"]:
            for step in day["steps"]:
                if step["type"] == "poi":
                    poi_id = step["poi_id"]
                    if poi_id in enriched_data:
                        step.update(enriched_data[poi_id])

    return ItineraryResponse(**itinerary_dict)