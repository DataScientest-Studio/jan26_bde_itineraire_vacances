import argparse
from scripts.itinerary_engine.contracts import ItineraryRequest
from scripts.itinerary_engine.wrapper import generate_itinerary

def main():
    parser = argparse.ArgumentParser(description="Test du moteur d'itinéraire Neo4j")
    parser.add_argument("--postal_code_insee", required=True, help="Code postal insee de la ville (ex: 75056 pour Paris)")
    parser.add_argument("--theme", required=True, help="ID du thème dans Neo4j (ex: 123)")
    parser.add_argument("--days", type=int, default=1, help="Nombre de jours")
    parser.add_argument("--lat", type=float, required=True, help="Latitude de départ")
    parser.add_argument("--lon", type=float, required=True, help="Longitude de départ")

    args = parser.parse_args()

    # 1. Création de l'objet de requête (simule le body de l'API)
    req = ItineraryRequest(
        postal_code_insee=args.postal_code_insee,
        theme=args.theme,
        days=args.days,
        start_lat=args.lat,
        start_lon=args.lon
    )

    print(f"🔄 Génération de l'itinéraire pour {args.postal_code_insee} (Thème: {args.theme}, {args.days} jours)...")
    
    # 2. Appel du moteur
    try:
        response = generate_itinerary(req)
        # 3. Affichage du résultat JSON formaté (Pydantic V2)
        print(response.model_dump_json(indent=4))
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution : {e}")

if __name__ == "__main__":
    main()