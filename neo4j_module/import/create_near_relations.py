from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Nassima94!!"

MAX_DISTANCE_METERS = 2000  # rayon raisonnable pour un itinéraire urbain


class NearRelationBuilder:

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def get_city_ids(self):
        with self.driver.session() as session:
            result = session.run("MATCH (c:City) RETURN DISTINCT c.city_id AS city_id")
            return [record["city_id"] for record in result]

    def create_near_relations_for_city(self, city_id):
        print(f"Pré-calcul des distances pour la ville {city_id}...")

        with self.driver.session() as session:
            session.run(
                """
                MATCH (p1:POI {city_id: $city})
                MATCH (p2:POI {city_id: $city})
                WHERE p1 <> p2
                WITH p1, p2,
                     point.distance(
                         point({latitude: p1.lat, longitude: p1.lon}),
                         point({latitude: p2.lat, longitude: p2.lon})
                     ) AS d
                WHERE d <= $max_distance
                MERGE (p1)-[r:NEAR]->(p2)
                SET r.distance = d
                """,
                city=city_id,
                max_distance=MAX_DISTANCE_METERS
            )

        print(f"Relations NEAR créées pour {city_id}.")


if __name__ == "__main__":
    builder = NearRelationBuilder()

    city_ids = builder.get_city_ids()
    print(f"Villes trouvées : {city_ids}")

    for city in city_ids:
        builder.create_near_relations_for_city(city)

    builder.close()

