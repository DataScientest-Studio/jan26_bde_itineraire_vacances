import os

# ---------------------------------------------------------
# Configuration Neo4j centralisée
# ---------------------------------------------------------
# Les valeurs par défaut correspondent à ton environnement local.
# En CI/CD, GitHub Actions écrasera ces variables via l'environnement.
# ---------------------------------------------------------

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Nassima94!!")
