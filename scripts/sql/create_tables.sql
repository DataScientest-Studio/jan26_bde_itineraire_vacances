-- 1. Table de référence pour les types (Catalogue unique)
CREATE TABLE IF NOT EXISTS type (
    typeId SERIAL PRIMARY KEY,
    typeLabel VARCHAR(100) UNIQUE NOT NULL
);

-- 2. Table de référence pour les Thèmes (Labels ML)
CREATE TABLE IF NOT EXISTS theme (
    themeId SERIAL PRIMARY KEY,
    themeLabel VARCHAR(100) UNIQUE NOT NULL
);

-- 3. Table des Villes (Normalisation de la localisation)
CREATE TABLE IF NOT EXISTS city (
    postalCodeInsee VARCHAR(50) PRIMARY KEY,
    postalCode VARCHAR(50),
    city TEXT,
    cityInsee VARCHAR(100)
);

-- 4. Table principale POI
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

-- 5. Table de localisation (Relation 1:1 avec POI)
CREATE TABLE IF NOT EXISTS poiLocation (
    uuid UUID PRIMARY KEY REFERENCES poi(uuid) ON DELETE CASCADE,
    streetAddress TEXT,
    postalCodeInsee VARCHAR(50) REFERENCES city(postalCodeInsee),
    latitude FLOAT,
    longitude FLOAT
);

-- 6. Table de jointure pour les types (Relation N:N)
CREATE TABLE IF NOT EXISTS poiType (
    uuid UUID REFERENCES poi(uuid) ON DELETE CASCADE,
    typeId INT REFERENCES type(typeId) ON DELETE CASCADE,
    PRIMARY KEY (uuid, typeId)
);

-- 7. Table de jointure pour les thèmes (Relation N:N - Alimentée par le ML)
CREATE TABLE IF NOT EXISTS poiTheme (
    uuid UUID PRIMARY KEY REFERENCES poi(uuid) ON DELETE CASCADE,
    themeId INT REFERENCES theme(themeId) ON DELETE CASCADE
);


-- 8. Insertion des thèmes prédéfinis
INSERT INTO theme (themeId, themeLabel) VALUES 
(1, 'Gastronomique'),
(2, 'Sportif'),
(3, 'Détente & bien-être'),
(4, 'Familial'),
(5, 'Culturel'),
(6, 'Autre')
ON CONFLICT (themeId) DO NOTHING;