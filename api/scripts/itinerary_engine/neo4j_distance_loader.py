from typing import Dict, List
from scripts.utils.db_connect import get_neo4j_driver
import time


def load_distances_from_neo4j(pois: List[dict]) -> Dict[tuple, float]:
    slim_pois = [
        {
            "uuid": p["uuid"],
            "latitude": p["latitude"],
            "longitude": p["longitude"],
        }
        for p in pois
    ]

    driver = get_neo4j_driver()

    cypher = """
    UNWIND $pois AS p1
    UNWIND $pois AS p2
    WITH collect({
        from_uuid: p1.uuid,
        to_uuid: p2.uuid,
        dist: point.distance(
            point({latitude: p1.latitude, longitude: p1.longitude}),
            point({latitude: p2.latitude, longitude: p2.longitude})
        )
    }) AS distances
    RETURN distances
    """

    with driver.session() as session:

        print("[DEBUG] Neo4j reçoit", len(slim_pois), "POI")

        t0 = time.time()
        result = session.run(cypher, pois=slim_pois)
        row = result.single()  # 🔥 1 seule ligne
        print(f"[DEBUG] Neo4j driver time: {time.time() - t0:.3f} s")

        distances_list = row["distances"]

    driver.close()

    # Convertir la liste en dict
    distances = {
        (item["from_uuid"], item["to_uuid"]): item["dist"]
        for item in distances_list
    }

    return distances
