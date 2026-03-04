from neo4j import GraphDatabase
import sys
import itertools


class PrecomputeDistances:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_city_pois(self, city):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:POI {city: $city})
                RETURN p.poi_id AS id, p.lat AS lat, p.lon AS lon
                """,
                city=city
            )
            return [record.data() for record in result]

    def compute_city_distances(self, city):
        with self.driver.session() as session:

            # Supprimer les anciennes relations NEAR de cette ville
            session.run(
                """
                MATCH (a:POI {city: $city})-[r:NEAR]->(b:POI {city: $city})
                DELETE r
                """,
                city=city
            )

            pois = self.get_city_pois(city)
            print(f"{len(pois)} POI trouvés pour {city}")

            # Calcul pairwise
            for p1, p2 in itertools.combinations(pois, 2):

                session.run(
                    """
                    MATCH (a:POI {poi_id: $id1})
                    MATCH (b:POI {poi_id: $id2})

                    WITH a, b,
                         point({latitude: a.lat, longitude: a.lon}) AS pa,
                         point({latitude: b.lat, longitude: b.lon}) AS pb

                    MERGE (a)-[:NEAR {distance: point.distance(pa, pb)}]->(b)
                    MERGE (b)-[:NEAR {distance: point.distance(pa, pb)}]->(a)
                    """,
                    id1=p1["id"],
                    id2=p2["id"]
                )


def main():
    if len(sys.argv) != 2:
        print("Usage: python precompute_distances.py <city_name>")
        return

    city = sys.argv[1]

    pre = PrecomputeDistances(
        "bolt://localhost:7687",
        "neo4j",
        "Nassima94!!"
    )

    pre.compute_city_distances(city)
    pre.close()

    print(f"Précalcul des distances NEAR terminé pour {city}.")


if __name__ == "__main__":
    main()
