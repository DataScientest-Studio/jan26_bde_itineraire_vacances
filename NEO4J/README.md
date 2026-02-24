1. Objectif du module
Ce module Neo4j gère la construction d’itinéraires touristiques à partir de POI (Points of Interest) déjà filtrés par le backend.
Il est totalement indépendant des autres briques du projet (backend, ML, PostgreSQL) et peut être testé en autonomie.

Neo4j sert uniquement à :

structurer les POI dans un graphe

stocker les relations de proximité (NEAR)

générer un itinéraire cohérent

Aucun filtrage métier n’est effectué dans Neo4j.

2. Structure du dossier
Code
neo4j/
│
├── schema/
│   ├── schema.cypher          # Structure logique du graphe
│   ├── constraints.cypher     # Contraintes d’unicité et d’existence
│   └── indexes.cypher         # Index pour optimiser les requêtes
│
├── import/
│   ├── import_poi.py          # Import des POI (depuis PostgreSQL ou dataset local)
│   └── create_near_relations.py # Calcul des distances + relations NEAR
│
├── itinerary/
│   ├── itinerary_builder.py   # Algorithme backend (greedy nearest-neighbor)
│   └── test_itinerary.py      # Script de test autonome
│
├── test_data/
│   └── poi_sample.json        # Dataset minimal pour tests indépendants
│
├── reset.py                   # Réinitialisation complète de Neo4j
│
└── README.md                  # Documentation du module

3. Installation
Prérequis
Neo4j Desktop ou Neo4j Server

Python 3

Driver Neo4j Python :

Code
pip install neo4j
(Optionnel) PostgreSQL si vous importez des POI réels

4. Réinitialiser Neo4j
Avant chaque test, on peut repartir d’une base propre :

Code
python neo4j/reset.py
Ce script :  
 - supprime tous les nœuds et relations

 - recharge les contraintes

 - recharge les index

5. Charger le schéma
Dans Neo4j Browser :

Ouvrir schema/schema.cypher

Exécuter le fichier

Ce fichier définit :

 - les labels

 - les relations

 - la structure logique du graphe

un exemple de POI

6. Importer les POI
Option A — Dataset minimal (recommandé pour tests)
Code
python neo4j/import/import_poi.py
Le script lit automatiquement :

Code
neo4j/test_data/poi_sample.json
Option B — Import réel depuis PostgreSQL
Configurer la connexion dans import_poi.py, puis :

Code
python neo4j/import/import_poi.py
🔗 7. Créer les relations NEAR
Une fois les POI importés :

Code
python neo4j/import/create_near_relations.py
Ce script :

calcule les distances Haversine

applique un seuil (par défaut : 1000 m)

crée les relations NEAR dans les deux sens

8. Générer un itinéraire
L’algorithme greedy est implémenté dans :

Code
neo4j/itinerary/itinerary_builder.py
Pour tester :

Code
python neo4j/itinerary/test_itinerary.py
Vous verrez un résultat du type :

Code
=== ITINÉRAIRE GÉNÉRÉ ===

Étape 1 — Musée du Louvre
Étape 2 — Pont des Arts
Étape 3 — Église Saint-Germain-l'Auxerrois
...
9. Workflow complet de test
Reset Neo4j

Code
python neo4j/reset.py
Charger le schéma

Exécuter schema.cypher dans Neo4j Browser

Importer les POI

Code
python neo4j/import/import_poi.py
Créer les relations NEAR

Code
python neo4j/import/create_near_relations.py
Tester l’itinéraire

Code
python neo4j/itinerary/test_itinerary.py
🧭 10. Notes importantes
Neo4j ne filtre rien : ville, thèmes, distance max → gérés par le backend.

Neo4j ne choisit pas les POI : il reçoit une liste déjà filtrée.

Neo4j ne calcule pas les distances en live : elles sont pré‑calculées.

L’algorithme greedy est simple, rapide, robuste pour une 1ere itération .

11. Prochaines étapes possibles
Ajouter un algorithme avancé (k-shortest paths)

Ajouter un scoring de POI

Intégrer une API de routage pour temps réel

Visualisation dans un notebook