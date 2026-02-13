-- 1. Table de référence pour les types (Catalogue unique)
CREATE TABLE IF NOT EXISTS type (
    typeId SERIAL PRIMARY KEY,
    typeLabel VARCHAR(100) UNIQUE NOT NULL
);

-- 2. Table principale POI
CREATE TABLE IF NOT EXISTS poi (
    uuid UUID PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT,
    shortDescription TEXT,
    uri TEXT,
    legalName TEXT,
    telephone VARCHAR(50),
    email VARCHAR(255),
    homepage TEXT,
    lastUpdate DATE,
    lastUpdateDatatourisme TIMESTAMP
);

-- 3. Table de localisation (Relation 1:1 avec POI)
CREATE TABLE IF NOT EXISTS poiLocation (
    uuid UUID PRIMARY KEY REFERENCES poi(uuid) ON DELETE CASCADE,
    streetAddress TEXT,
    postalCode VARCHAR(50),
    postalCodeInsee VARCHAR(50),
    city TEXT,
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