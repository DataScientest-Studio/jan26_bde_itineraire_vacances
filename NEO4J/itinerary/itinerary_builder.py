"""
itinerary_builder.py
--------------------
Construit un itinéraire à partir d'un point de départ en utilisant Neo4j.

Corrige le bug où le POI de départ réapparaissait en étape 2.
"""

from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Nassima94!!"  

MAX_DISTANCE_METERS = 1000  # seuil pour choisir le prochain POI


class ItineraryBuilder:

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    # ---------------------------------------------------------
    # Trouver le POI le plus proche du point de départ
    # ---------------------------------------------------------
    def find_start_poi(self, lat, lon):
        with self.driver.session() as session:
            result = session.run(
                """
                WITH point({latitude: $lat, longitude: $lon}) AS start
                MATCH (p:POI)
                WITH p,
                     point.distance(
                         start,
                         point({latitude: p.lat, longitude: p.lon})
                     ) AS d
                RETURN p, d
                ORDER BY d ASC
                LIMIT 1
                """,
                lat=lat,
                lon=lon
            )
            record = result.single()
            if record:
                return record["p"]
            return None

    # ---------------------------------------------------------
    # Trouver le prochain POI proche du POI courant
    # ---------------------------------------------------------
    def find_next_poi(self, current_poi_id, visited):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:POI {poi_id: $current})
                WITH c, point({latitude: c.lat, longitude: c.lon}) AS start
                MATCH (p:POI)
                WHERE p.poi_id <> $current
                  AND NOT p.poi_id IN $visited
                WITH p,
                     point.distance(
                         start,
                         point({latitude: p.lat, longitude: p.lon})
                     ) AS d
                WHERE d <= $max_distance
                RETURN p, d
                ORDER BY d ASC
                LIMIT 1
                """,
                current=current_poi_id,
                visited=list(visited),
                max_distance=MAX_DISTANCE_METERS
            )

            record = result.single()
            if record:
                return record["p"]
            return None

    # ---------------------------------------------------------
    # Construire l'itinéraire complet
    # ---------------------------------------------------------
    def build_itinerary(self, start_lat, start_lon, max_stops=6):
        itinerary = []
        visited = set()

        # Étape 1 : trouver le POI le plus proche du point de départ
        start_poi = self.find_start_poi(start_lat, start_lon)
        if not start_poi:
            print("Aucun POI trouvé.")
            return []

        itinerary.append(start_poi)
        visited.add(start_poi["poi_id"])  # <-- Correction essentielle

        current = start_poi

        # Étapes suivantes
        for _ in range(max_stops - 1):
            next_poi = self.find_next_poi(current["poi_id"], visited)
            if not next_poi:
                break

            itinerary.append(next_poi)
            visited.add(next_poi["poi_id"])
            current = next_poi

        return itinerary

    def compute_distance(self,driver, poi_a, poi_b):
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
# Exemple d'utilisation
# ---------------------------------------------------------
if __name__ == "__main__":
    builder = ItineraryBuilder()

    START_LAT = 48.8606
    START_LON = 2.3376

    itinerary = builder.build_itinerary(START_LAT, START_LON, max_stops=6)

    print("\n=== ITINÉRAIRE GÉNÉRÉ ===\n")
    for i, poi in enumerate(itinerary, start=1):
        print(f"Étape {i} — {poi['label']}")
        print(f"  ID : {poi['poi_id']}")
        print(f"  Coordonnées : ({poi['lat']}, {poi['lon']})\n")
        
        if i > 1:
            d = builder.compute_distance(builder.driver, itinerary[i-2], poi)
            print(f"  Distance depuis l'étape précédente : {round(d)} m")

        print()

    builder.close()
