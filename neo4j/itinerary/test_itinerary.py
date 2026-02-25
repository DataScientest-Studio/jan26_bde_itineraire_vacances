"""
test_itinerary.py
-----------------
Teste la génération d’un itinéraire et affiche les distances entre étapes.
"""

from itinerary_builder import ItineraryBuilder
from neo4j import GraphDatabase

# ---------------------------------------------------------
# Fonction utilitaire : calculer la distance entre deux POI
# ---------------------------------------------------------
def compute_distance(driver, poi_a, poi_b):
    with driver.session() as session:
        result = session.run(
            """
            WITH point({latitude: $lat1, longitude: $lon1}) AS p1,
                 point({latitude: $lat2, longitude: $lon2}) AS p2
            RETURN point.distance(p1, p2) AS d
            """,
            lat1=poi_a["lat"],
            lon1=poi_a["lon"],
            lat2=poi_b["lat"],
            lon2=poi_b["lon"]
        )
        return result.single()["d"]


# ---------------------------------------------------------
# Test principal
# ---------------------------------------------------------
if __name__ == "__main__":
    builder = ItineraryBuilder()

    # Point de départ (à adapter selon ton test)
    START_LAT = 48.8606
    START_LON = 2.3376

    itinerary = builder.build_itinerary(START_LAT, START_LON, max_stops=6)

    print("\n=== ITINÉRAIRE GÉNÉRÉ ===\n")

    for i, poi in enumerate(itinerary, start=1):
        print(f"Étape {i} — {poi['label']}")
        print(f"  ID : {poi['poi_id']}")
        print(f"  Coordonnées : ({poi['lat']}, {poi['lon']})")

        # Affichage de la distance depuis l’étape précédente
        if i > 1:
            d = compute_distance(builder.driver, itinerary[i-2], poi)
            print(f"  Distance depuis l'étape précédente : {round(d)} m")

        print()

    builder.close()
