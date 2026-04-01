# cli_tester.py
import argparse
from api.scripts.itinerary_engine.contracts import ItineraryRequest
from api.scripts.itinerary_engine.wrapper import generate_itinerary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--postalcodeinsee", required=True)
    parser.add_argument("--themeid", type=int, required=True)
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--use-neo4j", action="store_true")
    args = parser.parse_args()

    req = ItineraryRequest(
        postalcodeinsee=args.postalcodeinsee,
        themeid=args.themeid,
        days=args.days,
    )

    response = generate_itinerary(req, use_neo4j=args.use_neo4j)
    print(response.json(indent=4))


if __name__ == "__main__":
    main()
