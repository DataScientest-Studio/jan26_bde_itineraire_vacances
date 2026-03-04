import json
import os
import pytest

from neo4j_module.itinerary.itinerary_builder import ItineraryBuilder


DATA_FILE = os.path.join("data", "paris_pois.json")


def load_pois():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_paris_culturel():
    # Charger les POI de Paris
    pois = load_pois()

    # Filtrer uniquement les POI Culturel
    culturel_pois = [p for p in pois if "Culturel" in p["themes"]]

    assert len(culturel_pois) > 0, "Aucun POI culturel trouvé dans paris_pois.json"

    # Builder
    builder = ItineraryBuilder()

    # Construire l’itinéraire (2 jours, départ = Notre-Dame)
    itinerary = builder.build_itinerary_from_pois(
        pois=culturel_pois,
        days=2,
        start_lat=48.852968,
        start_lon=2.349902
    )

    assert len(itinerary) > 0, "L’itinéraire culturel est vide"

    # Ajouter les pauses + découpage par jour
    days_itinerary = itinerary

    # Vérifications simples
    assert any(day["day"] == 1 for day in days_itinerary), "Jour 1 manquant"
    assert any(day["day"] == 2 for day in days_itinerary), "Jour 2 manquant"
    assert len(days_itinerary[0]["steps"]) > 0, "Jour 1 vide"
    assert len(days_itinerary[1]["steps"]) > 0, "Jour 2 vide"


    # Export JSON
    builder.export_itinerary_to_json(days_itinerary, "paris_culturel_test.json")

    builder.close()

    print("\nItinéraire Paris Culturel généré avec succès.")
