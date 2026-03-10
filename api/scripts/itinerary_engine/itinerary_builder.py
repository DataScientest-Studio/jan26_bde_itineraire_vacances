import math

class ItineraryBuilder:
    def __init__(self):
        # Plus besoin de connexion Neo4j ici, le builder est 100% in-memory
        pass

    # ---------------------------------------------------------
    # Calcul de distance local (Haversine) - Remplace les appels DB
    # ---------------------------------------------------------
    def get_distance_between_point(self, lat1, lon1, lat2, lon2):
        if None in (lat1, lon1, lat2, lon2):
            return 0.0
            
        R = 6371000  # Rayon de la terre en mètres
        phi_1 = math.radians(lat1)
        phi_2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

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
    # Ordonner les POIs (Nearest Neighbor in-memory)
    # ---------------------------------------------------------
    def order_pois(self, pois, start_lat, start_lon):
        pois_copy = pois.copy()
        ordered = []

        if not pois_copy:
            return []

        # 1. Trouver le premier POI depuis la position utilisateur
        start_poi = self.find_closest_poi(pois_copy, start_lat, start_lon)
        if not start_poi:
            return []

        ordered.append(start_poi)
        pois_copy = [p for p in pois_copy if p["poi_id"] != start_poi["poi_id"]]

        # 2. Boucler sur les suivants sans JAMAIS appeler la base de données
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

    # ---------------------------------------------------------
    # Builder final (Logique originale conservée à 100%)
    # ---------------------------------------------------------
    def build_itinerary(self, postal_code_insee, theme, pois, nb_days, start_lat, start_lon):
        ordered = self.order_pois(pois, start_lat, start_lon)
        max_pois = nb_days * 4
        ordered = ordered[:max_pois]

        chunks = [ordered[i:i+4] for i in range(0, len(ordered), 4)]

        days_output = []
        total_distance = 0
        current_start_lat = start_lat
        current_start_lon = start_lon

        for day_index, day_pois in enumerate(chunks, start=1):
            steps = []
            
            # Matin
            for poi in day_pois[:2]:
                steps.append({"type": "poi", **poi})
            
            # Pause
            if len(day_pois) >= 2:
                steps.append({"type": "event", "event_id": "LUNCH_BREAK", "label": "Pause déjeuner"})
            
            # Après-midi
            for poi in day_pois[2:4]:
                steps.append({"type": "poi", **poi})

            # Distances
            prev = None
            for step in steps:
                if step["type"] == "poi":
                    if prev is None:
                        d = self.get_distance_between_point(current_start_lat, current_start_lon, step["lat"], step["lon"])
                    else:
                        d = self.get_distance_between_point(prev["lat"], prev["lon"], step["lat"], step["lon"])

                    step["distance_m"] = int(d)
                    total_distance += d
                    prev = step

            # Maj point de départ
            last_poi = next((s for s in reversed(steps) if s["type"] == "poi"), None)
            if last_poi:
                current_start_lat, current_start_lon = last_poi["lat"], last_poi["lon"]

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
        # Conservé pour la compatibilité avec le wrapper de ton collègue
        pass