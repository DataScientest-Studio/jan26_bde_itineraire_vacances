import json
import argparse

from itinerary_engine.builder.itinerary_builder import ItineraryBuilder
from itinerary_engine.builder.load_pois_for_city import load_pois_for_city


def main():
    parser = argparse.ArgumentParser(description="Build itinerary for a given city and theme.")
    parser.add_argument("--city", required=True, help="City name (ex: paris)")
    parser.add_argument("--theme", required=True, help="Theme (ex: culturel)")
    parser.add_argument("--days", type=int, default=2, help="Number of days (1, 2, 3...)")
    parser.add_argument("--start-lat", type=float, required=True, help="Starting latitude")
    parser.add_argument("--start-lon", type=float, required=True, help="Starting longitude")

    args = parser.parse_args()

    # 1. Charger les POIs depuis Postgres
    pois = load_pois_for_city(args.city, args.theme)

    # 2. Construire l’itinéraire
    builder = ItineraryBuilder()
    itinerary = builder.build_itinerary(
        city=args.city,
        theme=args.theme,
        pois=pois,
        nb_days=args.days,
        start_lat=args.start_lat,
        start_lon=args.start_lon
    )
    builder.close()

    # 3. Afficher le JSON final
    print(json.dumps(itinerary, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()

