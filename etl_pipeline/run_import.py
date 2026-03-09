import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
from etl.full.import_full import run_full_import
from etl.delta.import_delta import run_delta_import
from etl.neo4j_module.setup_indexes import setup_indexes


def main():
    parser = argparse.ArgumentParser(description="ETL Import Runner")
    parser.add_argument(
        "--mode",
        choices=["full", "delta"],
        required=True,
        help="Choisir le mode d'import : full ou delta"
    )
    parser.add_argument(
        "--setup-indexes",
        action="store_true",
        help="Créer les index Neo4j avant l'import"
    )

    args = parser.parse_args()

    # --- Optional: setup indexes ---
    if args.setup_indexes:
        print("[SETUP] Création des index Neo4j...")
        setup_indexes()

    # --- Run FULL or DELTA ---
    if args.mode == "full":
        print("[RUN] Import FULL démarré...")
        run_full_import()
        print("[RUN] Import FULL terminé.")

    elif args.mode == "delta":
        print("[RUN] Import DELTA démarré...")
        run_delta_import()
        print("[RUN] Import DELTA terminé.")


if __name__ == "__main__":
    main()
