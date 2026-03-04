import json
import os
import pytest

from neo4j_module.itinerary.itinerary_builder import ItineraryBuilder


DATA_FILE = os.path.join("data", "lyon_pois.json")


def load_pois():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_lyon_nature():
    # Charger les POI de Lyon
    pois = load_pois()

    # Filtrer uniquement les POI Nature
    nature_pois = [p for p in pois if "Nature" in p["themes"]]

    assert len(nature_pois) > 0, "Aucun POI nature trouvé dans lyon_pois.json"

    # Builder
    builder = ItineraryBuilder()

    # Construire l’itinéraire (2 jours, départ = Jardin du Luxembourg)
    itinerary = builder.build_itinerary_from_pois(
        pois=nature_pois,
        days=2,
        start_lat=48.8462,
        start_lon=2.3372
    )

    assert len(itinerary) > 0, "L’itinéraire nature est vide"

    # Ajouter les pauses + découpage par jour
    days_itinerary = itinerary

    # Vérifications simples
    assert any(day["day"] == 1 for day in days_itinerary), "Jour 1 manquant"
    assert any(day["day"] == 2 for day in days_itinerary), "Jour 2 manquant"
    assert len(days_itinerary[0]["steps"]) > 0, "Jour 1 vide"
    assert len(days_itinerary[1]["steps"]) > 0, "Jour 2 vide"

    # Export JSON
    builder.export_itinerary_to_json(days_itinerary, "lyon_nature_test.json")

    builder.close()

    print("\nItinéraire Lyon Nature généré avec succès.")
