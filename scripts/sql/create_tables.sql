-- 1. Table de référence pour les types (Catalogue unique)
CREATE TABLE IF NOT EXISTS type (
    typeId SERIAL PRIMARY KEY,
    typeLabel VARCHAR(100) UNIQUE NOT NULL
);

-- 2. Table principale POI
CREATE TABLE IF NOT EXISTS poi (
    uuid UUID PRIMARY KEY,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    shortDescription TEXT,
    uri VARCHAR(255),
    legalName VARCHAR(255),
    telephone VARCHAR(50),
    email VARCHAR(255),
    homepage VARCHAR(255),
    lastUpdate DATE,
    lastUpdateDatatourisme TIMESTAMP
);

-- 3. Table de localisation (Relation 1:1 avec POI)
CREATE TABLE IF NOT EXISTS poiLocation (
    uuid UUID PRIMARY KEY REFERENCES poi(uuid) ON DELETE CASCADE,
    streetAddress TEXT,
    postalCode VARCHAR(10),
    postalCodeInsee VARCHAR(10),
    city VARCHAR(100),
    cityInsee VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT
);

-- 4. Table de jointure pour les types (Relation N:N)
CREATE TABLE IF NOT EXISTS poiType (
    uuid UUID REFERENCES poi(uuid) ON DELETE CASCADE,
    typeId INT REFERENCES type(typeId) ON DELETE CASCADE,
    PRIMARY KEY (uuid, typeId)
);