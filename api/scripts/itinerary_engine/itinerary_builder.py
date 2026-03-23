# itinerary_builder.py
from typing import List, Dict
from math import radians, sin, cos, sqrt, atan2


class ItineraryBuilder:
    def __init__(self, distances: Dict[tuple, float]):
        """
        distances : dict {(uuid1, uuid2): distance_m}
        Si distances est vide → fallback Haversine
        """
        self.distances = distances
        self.use_neo4j = len(distances) > 0

    def compute_distance(self, p1: Dict, p2: Dict) -> float:
        """
        Retourne la distance entre deux POI.
        - Si Neo4j est activé → utilise le dict distances
        - Sinon → fallback Haversine
        """
        if p1 is None or p2 is None:
            return 0

        if self.use_neo4j:
            return self.distances[(p1["uuid"], p2["uuid"])]

        # fallback Haversine (Postgres)
        R = 6371000
        dlat = radians(p2["latitude"] - p1["latitude"])
        dlon = radians(p2["longitude"] - p1["longitude"])
        a = sin(dlat/2)**2 + cos(radians(p1["latitude"])) * cos(radians(p2["latitude"])) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def _nearest_neighbour_order(self, pois: List[Dict]) -> List[Dict]:
        """
        Ordre des POI par plus proche voisin.
        """
        if not pois:
            return []

        unvisited = pois.copy()
        path = []

        current = unvisited.pop(0)
        path.append(current)

        while unvisited:
            nearest = min(
                unvisited,
                key=lambda p: self.compute_distance(current, p),
            )
            unvisited.remove(nearest)
            path.append(nearest)
            current = nearest

        return path

    def _select_best_pois(self, pois: List[Dict], nb_days: int) -> List[Dict]:
        """
        Sélectionne max 4 POI par jour.
        """
        max_poi = nb_days * 4
        if len(pois) <= max_poi:
            return pois

        ordered = self._nearest_neighbour_order(pois)
        return ordered[:max_poi]

    def build_itinerary(self, postalcodeinsee: str, themeid: int, pois: List[Dict], nb_days: int) -> Dict:
        """
        Construit l’itinéraire complet :
        - sélection POI
        - ordre nearest neighbour
        - découpage par jour
        - insertion pause déjeuner
        - calcul distances
        """
        if not pois:
            return {
                "postalcodeinsee": postalcodeinsee,
                "themeid": themeid,
                "summary": {
                    "total_distance_m": 0,
                    "estimated_duration_s": 0,
                    "days_count": nb_days,
                    "poi_count": 0,
                    "steps_count": 0,
                },
                "days": [],
            }

        # 1) Sélection
        pois = self._select_best_pois(pois, nb_days)

        # 2) Ordre
        ordered_pois = self._nearest_neighbour_order(pois)

        # 3) Découpage par jour
        pois_per_day = max(1, len(ordered_pois) // nb_days)
        days = []
        index = 0

        for day in range(1, nb_days + 1):
            day_pois = ordered_pois[index:index + pois_per_day]
            index += pois_per_day

            steps = []
            prev = None
            for poi in day_pois:
                dist = self.compute_distance(prev, poi) if prev else 0
                steps.append({
                    "type": "poi",
                    "uuid": poi["uuid"],
                    "label": poi["label"],
                    "latitude": poi["latitude"],
                    "longitude": poi["longitude"],
                    "themeid": themeid,
                    "distance_m": int(dist),
                })
                prev = poi

            # Pause déjeuner
            if steps:
                steps.insert(len(steps) // 2, {
                    "type": "event",
                    "event_id": "LUNCH_BREAK",
                    "label": "Pause déjeuner",
                })

            days.append({"day": day, "steps": steps})

        # 4) Résumé
        total_distance = sum(
            s["distance_m"]
            for d in days
            for s in d["steps"]
            if s["type"] == "poi"
        )

        summary = {
            "total_distance_m": int(total_distance),
            "estimated_duration_s": int(total_distance / 1.2),
            "days_count": nb_days,
            "poi_count": len(pois),
            "steps_count": sum(len(d["steps"]) for d in days),
        }

        return {
            "postalcodeinsee": postalcodeinsee,
            "themeid": themeid,
            "summary": summary,
            "days": days,
        }
