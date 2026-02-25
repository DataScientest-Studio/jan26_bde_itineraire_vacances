///////////////////////////////////////////////////////////////////////////
// schema.cypher
// Structure logique du graphe Neo4j pour le projet Itinéraires
// Auteur : Moussa
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// 1. Structure des nœuds
///////////////////////////////////////////////////////////////////////////

// Nœud :POI
// Propriétés attendues :
// - poi_id (string, unique)
// - label (string)
// - lat (float)
// - lon (float)
// - theme (string)
// - city_id (string)
// - short_description (string, optionnel)
// - type (string, optionnel)


// Nœud :City
// Propriétés :
// - city_id (string, unique)
// - name (string)
// - postal_code (string)
// - insee_code (string)


// Nœud :Theme
// Propriétés :
// - name (string, unique)


///////////////////////////////////////////////////////////////////////////
// 2. Relations
///////////////////////////////////////////////////////////////////////////

// POI → City
// (p:POI)-[:IN_CITY]->(c:City)

// POI → Theme
// (p:POI)-[:HAS_THEME]->(t:Theme)

// POI ↔ POI (distance en mètres)
// (p1:POI)-[:NEAR {distance: <meters>}]->(p2:POI)


///////////////////////////////////////////////////////////////////////////
// 3. Exemple de création d’un POI (documentation uniquement)
//
// Les POI réels sont créés par import_poi.py.
//
///////////////////////////////////////////////////////////////////////////

CREATE (p:POI {
    poi_id: "poi_12345",
    label: "Musée du Louvre",
    lat: 48.8606,
    lon: 2.3376,
    theme: "Culturel",
    city_id: "paris_75001",
    short_description: "Musée emblématique de Paris",
    type: "Museum"
});
