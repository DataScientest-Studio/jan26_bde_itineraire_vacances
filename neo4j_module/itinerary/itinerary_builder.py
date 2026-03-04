from neo4j import GraphDatabase
import json
import os


class ItineraryBuilder:

    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Nassima94!!")
        )

    # ---------------------------------------------------------
    # Distance entre deux POI via Neo4j (point + distance)
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
    # Trouver le POI le plus proche du point de départ
    # (start_lat/start_lon ne sont pas un POI, on utilise point())
    # ---------------------------------------------------------
    def find_closest_poi(self, pois, lat, lon):
        poi_ids = [p["poi_id"] for p in pois]

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:POI)
                WHERE p.poi_id IN $poi_ids
                WITH p,
                    point({latitude: $lat, longitude: $lon}) AS start_point,
                    point({latitude: p.lat, longitude: p.lon}) AS poi_point
                RETURN p, point.distance(start_point, poi_point) AS d
                ORDER BY d ASC
                LIMIT 1
                """,
                poi_ids=poi_ids,
                lat=lat,
                lon=lon
            )

            record = result.single()
            if record:
                node = record["p"]
                return {
                    "poi_id": node["poi_id"],
                    "label": node["label"],
                    "lat": node["lat"],
                    "lon": node["lon"],
                    "themes": node["themes"]
                }
            return None


    # ---------------------------------------------------------
    # Construire l’itinéraire brut (sans pauses)
    # ---------------------------------------------------------
    def build_itinerary_from_pois(self, pois, days, start_lat, start_lon):
        pois_copy = pois.copy()
        itinerary = []

        # 1) Trouver le point de départ
        start_poi = self.find_closest_poi(pois_copy, start_lat, start_lon)
        itinerary.append(start_poi)
        pois_copy.remove(start_poi)

        # 2) Construire l'ordre complet des POI
        current = start_poi
        while pois_copy:
            next_poi = min(
                pois_copy,
                key=lambda p: self.get_distance_between(current["poi_id"], p["poi_id"])
            )
            itinerary.append(next_poi)
            pois_copy.remove(next_poi)
            current = next_poi

        # 3) Découper en jours
        per_day = len(itinerary) // days
        days_list = []
        index = 0
        for d in range(days):
            if d == days - 1:
                days_list.append(itinerary[index:])
            else:
                days_list.append(itinerary[index:index + per_day])
            index += per_day

        # 4) Insérer la pause déjeuner dans chaque jour
        final_days = []
        for i, day_steps in enumerate(days_list):
            final_days.append(
                self.insert_lunch_break(day_steps, is_first_day=(i == 0))
            )

        # 5) Format final
        return [
            {"day": i + 1, "steps": final_days[i]}
            for i in range(len(final_days))
        ]


    # ---------------------------------------------------------
    # Insérer pauses + séparer par jour
    # ---------------------------------------------------------
    def insert_lunch_break(self, steps, is_first_day=False):
        """
        Règle métier :
        - Jour 1 : 1 POI de départ + 2 activités + pause + 2 activités
        - Jour 2+ : 2 activités + pause + 2 activités
        """

        if is_first_day:
            # steps[0] = point de départ
            start = [steps[0]]
            activities = steps[1:]

            morning = activities[:2]
            afternoon = activities[2:4]  # max 2

            return start + morning + [{"poi_id": "LUNCH_BREAK", "label": "Pause déjeuner"}] + afternoon

        else:
            # Jour 2+
            morning = steps[:2]
            afternoon = steps[2:4]  # max 2

            return morning + [{"poi_id": "LUNCH_BREAK", "label": "Pause déjeuner"}] + afternoon


    # ---------------------------------------------------------
    # Export JSON structuré par jour
    # ---------------------------------------------------------
    def export_itinerary_to_json(self, days_itinerary, filename):
        export_data = {"days": []}

        for day_data in days_itinerary:
            export_data["days"].append({
                "day": day_data["day"],
                "steps": day_data["steps"]
            })

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=4, ensure_ascii=False)


    # ---------------------------------------------------------
    def close(self):
        self.driver.close()

