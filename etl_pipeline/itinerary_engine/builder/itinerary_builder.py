from neo4j import GraphDatabase
from neo4j_module.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class ItineraryBuilder:

    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    # ---------------------------------------------------------
    # Distance entre deux POI via Neo4j
    # ---------------------------------------------------------
    def get_distance_between(self, id1, id2):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:POI {poi_id: $id1})
                MATCH (q:POI {poi_id: $id2})
                WITH p, q,
                    point({latitude: p.lat, longitude: p.lon}) AS pa,
                    point({latitude: q.lat, longitude: q.lon}) AS pb
                RETURN point.distance(pa, pb) AS d
                """,
                id1=id1,
                id2=id2
            )
            record = result.single()
            return record["d"] if record else None

    # ---------------------------------------------------------
    # Distance entre un point libre et un POI
    # ---------------------------------------------------------
    def get_distance_between_point(self, lat1, lon1, lat2, lon2):
        with self.driver.session() as session:
            result = session.run(
                """
                WITH point({latitude: $lat1, longitude: $lon1}) AS a,
                     point({latitude: $lat2, longitude: $lon2}) AS b
                RETURN point.distance(a, b) AS d
                """,
                lat1=lat1,
                lon1=lon1,
                lat2=lat2,
                lon2=lon2
            )
            record = result.single()
            return record["d"] if record else None

    # ---------------------------------------------------------
    # Trouver le POI le plus proche du point de départ
    # ---------------------------------------------------------
    def find_closest_poi(self, pois, lat, lon):
        if not pois:
            return None

        distances = []
        for p in pois:
            d = self.get_distance_between_point(lat, lon, p["lat"], p["lon"])
            distances.append((d, p))

        distances.sort(key=lambda x: x[0])
        return distances[0][1]

    # ---------------------------------------------------------
    # Ordonner les POIs selon la distance (Nearest Neighbor)
    # ---------------------------------------------------------
    def order_pois(self, pois, start_lat, start_lon):
        pois_copy = pois.copy()
        ordered = []

        if not pois_copy:
            return []

        start_poi = self.find_closest_poi(pois_copy, start_lat, start_lon)
        if not start_poi:
            return []

        ordered.append(start_poi)
        pois_copy = [p for p in pois_copy if p["poi_id"] != start_poi["poi_id"]]

        current = start_poi
        while pois_copy:
            next_poi = min(
                pois_copy,
                key=lambda p: self.get_distance_between(current["poi_id"], p["poi_id"])
            )
            ordered.append(next_poi)
            pois_copy = [p for p in pois_copy if p["poi_id"] != next_poi["poi_id"]]
            current = next_poi

        return ordered

    # ---------------------------------------------------------
    # Builder final avec départ dynamique 
    # ---------------------------------------------------------
    def build_itinerary(self, city, theme, pois, nb_days, start_lat, start_lon):

        ordered = self.order_pois(pois, start_lat, start_lon)
        max_pois = nb_days * 4
        ordered = ordered[:max_pois]

        chunks = [ordered[i:i+4] for i in range(0, len(ordered), 4)]

        days_output = []
        total_distance = 0

        # Point de départ dynamique
        current_start_lat = start_lat
        current_start_lon = start_lon

        for day_index, day_pois in enumerate(chunks, start=1):
            steps = []

            # Matin
            morning = day_pois[:2]
            for poi in morning:
                steps.append({"type": "poi", **poi})

            # Pause
            if len(day_pois) >= 2:
                steps.append({
                    "type": "event",
                    "event_id": "LUNCH_BREAK",
                    "label": "Pause déjeuner"
                })

            # Après-midi
            afternoon = day_pois[2:4]
            for poi in afternoon:
                steps.append({"type": "poi", **poi})

            # Distances
            prev = None
            for step in steps:
                if step["type"] == "poi":
                    if prev is None:
                        d = self.get_distance_between_point(
                            current_start_lat, current_start_lon,
                            step["lat"], step["lon"]
                        )
                    else:
                        d = self.get_distance_between(prev["poi_id"], step["poi_id"])

                    step["distance_from_previous_m"] = int(d)
                    total_distance += d
                    prev = step

            # Mise à jour du point de départ pour le jour suivant
            last_poi = None
            for s in reversed(steps):
                if s["type"] == "poi":
                    last_poi = s
                    break

            if last_poi:
                current_start_lat = last_poi["lat"]
                current_start_lon = last_poi["lon"]

            days_output.append({
                "day": day_index,
                "steps": steps
            })

        summary = {
            "total_distance_m": int(total_distance),
            "estimated_duration_s": int(total_distance / 1.2),
            "days_count": len(days_output),
            "poi_count": len(ordered),
            "steps_count": sum(len(d["steps"]) for d in days_output)
        }

        return {
            "city": city,
            "theme": theme,
            "summary": summary,
            "days": days_output
        }

    def close(self):
        self.driver.close()


