import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT)

from neo4j_module.itinerary.itinerary_builder import ItineraryBuilder


def main():

    JSON_PATH = os.path.join(ROOT, "neo4j_module", "test_data", "poi_sample_Paris.json")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        pois = json.load(f)

    # --- Thème codé en dur pour ce test ---
    theme = "Nature"

    # --- Filtrage strict : un POI doit avoir exactement ce thème ---
    pois = [p for p in pois if theme in p.get("themes", [])]

    print(f"Thème sélectionné : {theme}")
    print(f"Nombre de POI correspondant : {len(pois)}")

    builder = ItineraryBuilder()

    nb_jours = 2
    start_lat = pois[0]["lat"]
    start_lon = pois[0]["lon"]

    itinerary = builder.build_itinerary_from_pois(
        pois=pois,
        days=nb_jours,
        start_lat=start_lat,
        start_lon=start_lon
    )

    days_itinerary = builder.insert_lunch_break(itinerary, nb_jours)

    builder.export_itinerary_to_json(days_itinerary, "itinerary_paris_nature.json")

    print(f"\n=== ITINÉRAIRE PARIS — THÈME {theme.upper()} ===\n")

    etape_num = 1

    for day, steps in days_itinerary.items():

        print(f"\n===== JOUR {day} =====\n")

        if day == 1:
            start = steps[0]
            print(f"Point de départ : {start['label']}")
            print(f"  ID : {start['poi_id']}")
            print(f"  Coordonnées : ({start['lat']}, {start['lon']})\n")
            start_index = 1
        else:
            start_index = 0

        for i in range(start_index, len(steps)):
            poi = steps[i]

            if poi["poi_id"] == "LUNCH_BREAK":
                print("---- Pause déjeuner ----\n")
                continue

            print(f"Étape {etape_num} — {poi['label']}")
            print(f"  ID : {poi['poi_id']}")
            print(f"  Coordonnées : ({poi['lat']}, {poi['lon']})")

            if i > start_index and steps[i-1]["poi_id"] != "LUNCH_BREAK":
                prev = steps[i-1]
                d = builder.get_distance_between(prev["poi_id"], poi["poi_id"])
                if d is not None:
                    print(f"  Distance depuis l'étape précédente : {round(d)} m")

            print()
            etape_num += 1

    builder.close()


if __name__ == "__main__":
    main()
