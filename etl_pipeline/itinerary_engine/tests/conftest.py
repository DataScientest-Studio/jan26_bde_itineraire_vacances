import pytest
import subprocess
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def run(cmd):
    subprocess.run(cmd, check=True)

def prepare_city(city):
    city_lower = city.lower()

    # 1) Reset Neo4j
    run([sys.executable, os.path.join(BASE_DIR, "neo4j_module", "reset.py")])

    # 2) Import POIs
    run([
        sys.executable,
        os.path.join(BASE_DIR, "neo4j_module", "import", "import_city_pois.py"),
        city,
        os.path.join(BASE_DIR, "data", f"{city_lower}_pois.json")
    ])

    # 3) Precompute distances
    run([
        sys.executable,
        os.path.join(BASE_DIR, "neo4j_module", "precalc", "precompute_distances.py"),
        city
    ])

@pytest.fixture(autouse=True)
def setup_neo4j(request):
    test_name = request.node.name.lower()

    if "paris" in test_name:
        prepare_city("Paris")
    elif "lyon" in test_name:
        prepare_city("Lyon")
    elif "limoux" in test_name:
        prepare_city("Limoux")
