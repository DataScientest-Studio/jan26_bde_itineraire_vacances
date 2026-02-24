"""
create_near_relations.py
------------------------
Crée les relations NEAR entre POI en fonction de la distance géographique.

Compatible Neo4j 5 (utilise point.distance au lieu de distance()).
"""

from neo4j import GraphDatabase
import math

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Nassima94!!"  

MAX_DISTANCE_METERS = 1000  # seuil pour créer une relation NEAR


class NearRelationBuilder:

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def get_all_pois(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:POI)
                RETURN p.poi_id AS poi_id, p.lat AS lat, p.lon AS lon
            """)
            return list(result)

    def create_near_relations(self):
        pois = self.get_all_pois()
        print(f"{len(pois)} POI récupérés.")

        with self.driver.session() as session:
            for poi in pois:
                poi_id = poi["poi_id"]
                lat = poi["lat"]
                lon = poi["lon"]

                print(f"Recherche des voisins proches pour {poi_id}...")

                result = session.run(
                    """
                    WITH point({latitude: $lat, longitude: $lon}) AS start
                    MATCH (p:POI)
                    WHERE p.poi_id <> $poi_id
                    WITH p, start,
                         point.distance(
                             start,
                             point({latitude: p.lat, longitude: p.lon})
                         ) AS d
                    WHERE d <= $max_distance
                    RETURN p.poi_id AS poi_id, d
                    ORDER BY d ASC
                    """,
                    lat=lat,
                    lon=lon,
                    poi_id=poi_id,
                    max_distance=MAX_DISTANCE_METERS
                )

                neighbors = list(result)

                for n in neighbors:
                    session.run(
                        """
                        MATCH (a:POI {poi_id: $a})
                        MATCH (b:POI {poi_id: $b})
                        MERGE (a)-[:NEAR {distance: $d}]->(b)
                        """,
                        a=poi_id,
                        b=n["poi_id"],
                        d=n["d"]
                    )

                print(f"{len(neighbors)} relations NEAR créées pour {poi_id}.")

        print("Création des relations NEAR terminée.")


if __name__ == "__main__":
    builder = NearRelationBuilder()
    builder.create_near_relations()
    builder.close()
