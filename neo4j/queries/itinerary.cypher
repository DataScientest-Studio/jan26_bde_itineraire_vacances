///////////////////////////////////////////////////////////////////////////
// itinerary.cypher
// Génération d’un itinéraire simple 
//
// Entrées :
//   $start_lat, $start_lon : point de départ
//   $max_stops : nombre d’étapes souhaitées
//
// Hypothèses :
//   - Les POI sont déjà filtrés (ville, thèmes, distance max)
//   - Les relations NEAR sont déjà créées
///////////////////////////////////////////////////////////////////////////


WITH point({latitude: 48.8606, longitude: 2.3376}) AS start_point
MATCH (p:POI)
WITH p,
     point.distance(
         start_point,
         point({latitude: p.lat, longitude: p.lon})
     ) AS d
ORDER BY d ASC
LIMIT 1
WITH [p] AS itinerary, p AS current

// 2. Trouver les POI suivants via les relations NEAR
CALL (itinerary, current) {
    WITH itinerary, current
    MATCH (current)-[r:NEAR]->(next:POI)
    WHERE NOT next IN itinerary
    RETURN next
    ORDER BY r.distance ASC
    LIMIT 1
} 
WITH itinerary + next AS itinerary, next AS current
WHERE size(itinerary) < 6
CALL (itinerary, current) {
    MATCH (current)-[r:NEAR]->(next:POI)
    WHERE NOT next IN itinerary
    RETURN next
    ORDER BY r.distance ASC
    LIMIT 1
}
WITH itinerary + next AS itinerary, next AS current
WHERE size(itinerary) < 6

// Répéter autant que nécessaire
// (dans Neo4j Browser, on peut copier/coller plusieurs blocs CALL)
// Dans le backend, on peut boucler en Python

RETURN itinerary;
