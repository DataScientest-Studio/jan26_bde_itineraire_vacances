import pandas as pd
import joblib
import os
import re
import unicodedata
from psycopg2 import extras
from scripts.utils.db_connect import get_pg_conn_api

print(f"predict_all_pois STARTED - PID: {os.getpid()}")

# --- MÊME CONFIGURATION QUE POUR L'EXTRACTION --- Liste non intelligible de types à ignorer, identique à get_sample_data.py
TYPES_TO_IGNORE = [
    "PointOfInterest", "PlaceOfInterest", "LocalBusiness", "Product", "ServiceProvider", 
    "Organization", "Agent", "CivicStructure", "BusinessPlace", "ConvenientService",
    "TouristInformationCenter", "LocalTouristOffice", "RegionalTourismCommittee", 
    "DepartementTourismCommittee", "ChamberOfCommerceAndIndustry", "IncomingTravelAgency", 
    "TourOperatorOrTravelAgency", "TourGuideAgency", "ProfessionalTourGuide", 
    "VolunteerTourGuideOrGreeter", "PublicLavatories", "ATM", "WifiHotSpot", 
    "LeftLuggage", "Practice", "TrainingWorkshop", "SchoolOrTrainingCentre",
    "Transport", "Parking", "BusStop", "BusStation", "TrainStation", "Airport", 
    "Airfield", "Seaport", "RiverPort", "Marina", "Pier", "TaxiStation", 
    "TaxiCompany", "CarpoolArea", "ElectricVehicleChargingPoint", 
    "ElectricBycicleChargingPoint", "GarageOrAirPump", "CarOrBikeWash", 
    "LaunchingRamp", "Lock", "CableCarStation", "TourismCableCar",
    "MedicalPlace", "Pharmacy", "HealthcareProfessional", "HealthcarePlace",
    "LodgingBusiness", "Accommodation", "Hotel", "HotelTrade", "Camping", 
    "CampingAndCaravanning", "ResidentialLeisurePark", "CampingPitch", "Bed", 
    "Suite", "HotelSuite", "Apartment", "House", "Bungalow", 
    "SelfCateringAccommodation", "HypermarketAndSupermarket", "Store", "Trader"
]

def clean_text(text):
    """Logique de nettoyage identique au script d'entraînement"""
    if not text or pd.isna(text):
        return ""
    text = str(text).lower()
    text = ''.join((c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'))
    text = text.replace("'", " ").replace("’", " ").replace("-", " ")
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def predict_all_themes():
    # 1. Chargement du Pipeline (qui contient le vectoriseur et le model)
    model_path = "scripts/ml/models/poi_theme_classifier.joblib" #ATTENTION PEUTETRE A REVOIR AVEC LES DOCKER.
    if not os.path.exists(model_path):
        print("❌ Modèle introuvable")
        return
    
    pipeline = joblib.load(model_path)
    conn = get_pg_conn_api()
    
    batch_size = 5000
    offset = 0
    
    print("🚀 Lancement de l'inférence massive sur les POI...")

    while True:
        # On utilise "shortdescription" en minuscule comme dans le script d'extraction
        query = """
            SELECT 
                p.uuid, 
                p.label, 
                p.description, 
                p.shortdescription,
                ARRAY_AGG(t.typeLabel) as types
            FROM poi p
            LEFT JOIN poiType pt ON p.uuid = pt.uuid
            LEFT JOIN type t ON pt.typeId = t.typeId
            -- On ajoute un LEFT JOIN vers la table des thèmes
            LEFT JOIN poiTheme pth ON p.uuid = pth.uuid
            -- On ne garde que les POI qui n'ont PAS de correspondance dans poiTheme
            WHERE pth.uuid IS NULL
            GROUP BY p.uuid, p.label, p.description, p.shortdescription
            LIMIT %s OFFSET %s;
        """
        df = pd.read_sql(query, conn, params=(batch_size, offset))
        
        if df.empty:
            break

        df = df.fillna("")

        # 2. Construction de l'input_text (Identique à l'extraction Gemini)
        def prepare_input(row):
            raw_types = row['types'] if isinstance(row['types'], list) else []
            valid_types = [t for t in raw_types if t not in TYPES_TO_IGNORE and t != ""]
            types_str = ", ".join(valid_types)
            
            # Priorité Longue > Courte comme dans le script
            description = row['description'] or row['shortdescription'] or ""
            
            # Formatage exact du texte
            text = f"NOM: {row['label']} | TYPES: {types_str} | DESC: {description}"
            return text.replace('\n', ' ').replace('\r', ' ').strip()

        df['input_raw'] = df.apply(prepare_input, axis=1)
        
        # 3. Nettoyage Regex (Identique à l'entraînement)
        df['input_clean'] = df['input_raw'].apply(clean_text)

        # 4. Prédiction
        # On prédit seulement si le texte n'est pas vide
        predictions = pipeline.predict(df['input_clean'])

        # 5. Insertion dans la DB
        results = list(zip(df['uuid'].tolist(), [int(p) for p in predictions]))
        
        with conn.cursor() as cur:
            # Cette requête vérifie si l'UUID existe. 
            # Si oui, elle écrase le themeId actuel avec la nouvelle prédiction.
            insert_query = """
                INSERT INTO poiTheme (uuid, themeId) 
                VALUES %s 
                ON CONFLICT (uuid) 
                DO UPDATE SET themeId = EXCLUDED.themeId;
            """
            extras.execute_values(cur, insert_query, results)
            conn.commit()

        offset += len(df)
        print(f"✅ {offset} POI traités...")

    conn.close()
    print("🏁 Inférence terminée. La table poiTheme est à jour.")

if __name__ == "__main__":
    predict_all_themes()