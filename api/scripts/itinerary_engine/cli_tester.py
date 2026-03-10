import argparse
from scripts.itinerary_engine.contracts import ItineraryRequest
from scripts.itinerary_engine.wrapper import generate_itinerary

def main():
    parser = argparse.ArgumentParser(description="Test du moteur d'itinéraire Neo4j")
    parser.add_argument("--postal_code_insee", required=True, help="Code INSEE de la ville (ex: 90010 pour Belfort)")
    parser.add_argument("--theme", required=True, help="Thème (ex: Gastronomique)")
    parser.add_argument("--days", type=int, default=1, help="Nombre de jours")

    args = parser.parse_args()

    req = ItineraryRequest(
        postal_code_insee=args.postal_code_insee,
        theme=args.theme,
        days=args.days
    )

    print(f"🔄 Génération de l'itinéraire pour le code {args.postal_code_insee} (Thème: {args.theme}, {args.days} jours)...")
    
    try:
        response = generate_itinerary(req)
        print(response.model_dump_json(indent=4))
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution : {e}")

if __name__ == "__main__":
    main()