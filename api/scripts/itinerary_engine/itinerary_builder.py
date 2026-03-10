import math
import random

class ItineraryBuilder:
    def __init__(self):
        pass

    def get_distance_between_point(self, lat1, lon1, lat2, lon2):
        if None in (lat1, lon1, lat2, lon2):
            return 0.0
            
        R = 6371000
        phi_1 = math.radians(lat1)
        phi_2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def order_pois(self, pois):
        pois_copy = pois.copy()
        ordered = []

        if not pois_copy:
            return []

        # Sélection aléatoire ("au pif") du premier point
        start_poi = random.choice(pois_copy)
        ordered.append(start_poi)
        pois_copy = [p for p in pois_copy if p["poi_id"] != start_poi["poi_id"]]

        current = start_poi
        while pois_copy:
            next_poi = min(
                pois_copy,
                key=lambda p: self.get_distance_between_point(
                    current["lat"], current["lon"], p["lat"], p["lon"]
                )
            )
            ordered.append(next_poi)
            pois_copy = [p for p in pois_copy if p["poi_id"] != next_poi["poi_id"]]
            current = next_poi

        return ordered

    def build_itinerary(self, postal_code_insee, theme, pois, nb_days):
        ordered = self.order_pois(pois)
        max_pois = nb_days * 4
        ordered = ordered[:max_pois]

        chunks = [ordered[i:i+4] for i in range(0, len(ordered), 4)]

        days_output = []
        total_distance = 0
        prev_global = None  # Sert à garder le dernier POI de la veille en mémoire

        for day_index, day_pois in enumerate(chunks, start=1):
            steps = []
            
            for poi in day_pois[:2]:
                steps.append({"type": "poi", **poi})
            
            if len(day_pois) >= 2:
                steps.append({"type": "event", "event_id": "LUNCH_BREAK", "label": "Pause déjeuner"})
            
            for poi in day_pois[2:4]:
                steps.append({"type": "poi", **poi})

            prev_step = None
            for step in steps:
                if step["type"] == "poi":
                    if prev_step is None and prev_global is None:
                        # Tout premier POI du voyage
                        d = 0.0
                    elif prev_step is None and prev_global is not None:
                        # Premier POI du jour (distance depuis le dernier de la veille)
                        d = self.get_distance_between_point(prev_global["lat"], prev_global["lon"], step["lat"], step["lon"])
                    else:
                        # POI suivant dans la même journée
                        d = self.get_distance_between_point(prev_step["lat"], prev_step["lon"], step["lat"], step["lon"])

                    step["distance_m"] = int(d)
                    total_distance += d
                    prev_step = step
                    prev_global = step

            days_output.append({"day": day_index, "steps": steps})

        summary = {
            "total_distance_m": int(total_distance),
            "estimated_duration_s": int(total_distance / 1.2),
            "days_count": len(days_output),
            "poi_count": len(ordered),
            "steps_count": sum(len(d["steps"]) for d in days_output)
        }

        return {
            "postal_code_insee": postal_code_insee,
            "theme": theme,
            "summary": summary,
            "days": days_output
        }

    def close(self):
        pass