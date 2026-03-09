import pandas as pd
import os
from ...utils.db_connect import get_pg_conn

# On ignore tous ces types car ils ne sont pas intelligibles
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

def extract_data_for_ml(limit=100):
    """
    Extrait les données de Postgres, filtre les types nok
    et prépare le texte pour la labellisation Gemini.
    """
    conn = get_pg_conn()
    
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
        GROUP BY p.uuid
        ORDER BY RANDOM()
        LIMIT %s;
    """
    
    try:
        print(f"📡 Extraction de {limit} échantillons depuis Postgres...")
        df = pd.read_sql(query, conn, params=(limit,))
        df = df.fillna("")

        def prepare_text(row):
            # 1. Filtrage des types ignorés
            raw_types = row['types'] if isinstance(row['types'], list) else []
            valid_types = [t for t in raw_types if t not in TYPES_TO_IGNORE and t != ""]
            types_str = ", ".join(valid_types)
            
            # 2. Sélection de la description (Priorité Longue > Courte > Vide)
            # Grâce au fillna(""), si 'description' est vide, Python passe à 'shortdescription'
            description = row['description'] or row['shortdescription'] or ""
            
            # 3. Construction de la string
            text = f"NOM: {row['label']} | TYPES: {types_str} | DESC: {description}"
            
            # Nettoyage final des sauts de ligne pour le format CSV
            return text.replace('\n', ' ').replace('\r', ' ').strip()

        print("🪄  Préparation du texte d'entrée...")
        df['input_text'] = df.apply(prepare_text, axis=1)
        
        return df[['uuid', 'input_text']]

    except Exception as e:
        print(f"❌ Erreur lors de l'extraction : {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    # 1. Création du dossier de destination si inexistant
    os.makedirs("data/ml", exist_ok=True)
    
    # 2. Exécution de l'extraction
    samples = extract_data_for_ml(5000)
    
    if samples is not None:
        output_file = "data/ml/samples_to_label.csv"
        
        # 3. Sauvegarde
        samples.to_csv(output_file, index=False, encoding='utf-8')
        
        print("-" * 30)
        print(f"✅ Succès ! Fichier sauvegardé : {output_file}")
        print(f"📊 Nombre de lignes : {len(samples)}")
        print("-" * 30)