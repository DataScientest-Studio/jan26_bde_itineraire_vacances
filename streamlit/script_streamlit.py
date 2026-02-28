import time
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from datetime import date
import os



# CONNEXION API & CACHE 3H
@st.cache_data(ttl=10800) # 10800 secondes = 3 heures
def get_cities_auto():
    try:
        # Obtenir le Token
        token_url = "http://api:8000/token"
        auth_data = {"username": "admin", "password": "Pwd_iv_26!@"}
        resp_token = requests.post(token_url, data=auth_data, timeout=3)
        
        if resp_token.status_code == 200:
            token = resp_token.json().get("access_token")
            
            # Recuperation des villes
            cities_url = "http://api:8000/cities"
            headers = {"Authorization": f"Bearer {token}"}
            resp_cities = requests.get(cities_url, headers=headers, timeout=3)
            
            if resp_cities.status_code == 200:
                rows = resp_cities.json()
                return [r["city"] for r in rows] # On garde juste les noms
                
    except:
        pass # ignore les erreurs silencieusement si l'API est éteinte
        
    # Liste de secours
    return ["Paris", "Bordeaux", "Lyon", "Marseille", "Biarritz"]




# Choix de structure et d'interface :
# 1. CONFIGURATION CENTRÉE : paramètres pour générer l'itinéraire de voyage
#       1) Recherche géographique : par 'ville' (endpoint API pour suggestions de villes)
#       2) Durée séjour : Durée du séjour (slider)
#       3) Choix de la thématique POIs : Sportif, Gastronomique, En famille, Culturel, Bien-être/Relaxation

# 2. Sidebar = menu de navigation : "Progressive Disclosure" avec Sommaire cliquable pour revenir sur chaque catégories
# 3. Design global : step by step, moderne et dynamique



# --- 1. INITIALISATION DES SESSIONS ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'ville' not in st.session_state:
    st.session_state.ville = ""
if 'duree' not in st.session_state:
    st.session_state.duree = 3



# 1. CONFIGURATION DE LA PAGE : CENTREE
st.set_page_config(page_title="Itinéraire de Vacances", layout="centered")



# --- (Initialisation) ---
if 'max_step' not in st.session_state:
    st.session_state.max_step = 1

# --- (Juste avant le code de la Sidebar) ---
st.session_state.max_step = max(st.session_state.max_step, st.session_state.step)

# 2. SIDEBAR : menu de navigation + indicateurs d'etapes + bouton de réinitialisation
with st.sidebar:
    st.title("Sommaire")
    st.write("---")

    # CSS : Alignement gauche et suppression du look bouton
    st.markdown("""
        <style>
        div[data-testid="stSidebar"] button {
            justify-content: flex-start !important;
            text-align: left !important;
            width: 100% !important;
            padding: 5px 0px !important;
            background-color: transparent !important;
            border: none !important;
        }
        /* Couleur Orange pour les étapes accessibles */
        div[data-testid="stSidebar"] button[kind="tertiary"]:enabled p {
            color: #FF4500 !important;
        }
        /* Couleur Grise pour le futur */
        div[data-testid="stSidebar"] button[kind="tertiary"]:disabled p {
            color: #CBD5E1 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialisation de la progression max
    if 'max_step' not in st.session_state: st.session_state.max_step = 1
    st.session_state.max_step = max(st.session_state.max_step, st.session_state.step)

    steps = [
        {"id": 1, "label": "Choix de destination", "icon": ":material/location_on:"},
        {"id": 2, "label": "Durée de mon séjour", "icon": ":material/tune:"},
        {"id": 3, "label": "Thématique de voyage", "icon": ":material/category:"},
        {"id": 4, "label": "Mon itinéraire", "icon": ":material/map:"}
    ]

    for s in steps:
        is_accessible = s['id'] <= st.session_state.max_step
        is_done = st.session_state.step > s['id']
        is_current = st.session_state.step == s['id']
        
        # Texte dynamique : Bold si actuel, Check si fini
        label = f"**{s['icon']} {s['label']}**" if is_current else (f":material/check_circle: {s['label']}" if is_done else f"{s['icon']} {s['label']}")

        if st.button(label, key=f"nav_{s['id']}", disabled=not is_accessible, type="tertiary"):
            st.session_state.step = s['id']
            st.rerun()

    st.write("---")
    if st.button("Recommencer", icon=":material/restart_alt:", use_container_width=True):
        st.session_state.clear()
        st.session_state.step = 1
        st.rerun()


# 3. DESIGN 
st.markdown("""
    <style>
                 
    /* Bandeau dégradé : Bleu -> Orange */
    .top-bar {
        height: 8px;
        background: linear-gradient(90deg, #4F46E5 0%, #FF694B 100%);
        border-radius: 10px;
        margin-bottom: 25px;
    }
            
    /* Style pour le label d'étape */
    .step-header-red {
        color: #FF4500; /* Rouge-Orangé vif */
        font-size: 2.5rem;
        font-weight: 900;
        margin-bottom: 5px;
        text-transform: uppercase;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }

    /* Liens sidebar */
    [data-testid="stSidebar"] a {
        text-decoration: none;
        color: #4B5563 !important;
    }
            
    /* Titres */
            h1 {
        font-family: 'Polymath', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -1px !important;
        color: #111827 !important;
    }

            
    /* 1. BOUTON PRINCIPAL (Dégradé Corail) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B4B 0%, #FF8E3C 100%) !important;
        border: none !important; color: white !important; font-weight: 700 !important;
        padding: 12px 30px !important; border-radius: 12px !important; transition: 0.3s !important;
    }

              
    .itinerary-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 20px; }
    .timeline { border-left: 2px solid #4F46E5; margin-left: 50px; padding-left: 30px; position: relative; }
    .timeline-item::before { content: ''; position: absolute; left: -41px; width: 20px; height: 20px; background: #FF694B; border: 3px solid white; border-radius: 50%; }
    .time-label { position: absolute; left: -105px; font-weight: 700; color: #4B5563; width: 60px; text-align: right; }
    </style>
    <div class="top-bar"></div>
    """, unsafe_allow_html=True)



# Titre page
st.title("Votre Assistant de Voyage Personnalisé")
st.write("Planifiez votre itinéraire de voyage en seulement quelques clics...")



# --- ÉTAPE 1 : DESTINATION --- "Ville" (input text + suggestions auto-complétion)
# Label "Étape 1"
st.markdown('<p style="color:#FF4500; font-weight:800; font-size:1.2rem; margin-bottom:0;">ÉTAPE 1</p>', unsafe_allow_html=True)
st.subheader("Choisissez votre destination :material/location_on:")
st.write("Indiquez la ville que vous souhaitez explorer :")

# Appel de la fonction (Instantané grâce au cache)
villes_db = get_cities_auto()

# Autocomplétion avec Selectbox (Affiche les suggestions au fur et à mesure de la frappe)
ville_temp = st.selectbox(
    "Destination", 
    options=villes_db,
    index=None,
    placeholder="Commencez à taper (ex: Paris...)",
    label_visibility="collapsed"
)

alerte_ville = st.empty()

st.write("##")

if st.button("Suivant :material/arrow_forward:", key="btn_etape1", type="primary"):
    if not ville_temp:
        alerte_ville.warning("Veuillez choisir une ville avant de passer à la suite. ⚠️")
    else:
        st.session_state.ville = ville_temp
        st.session_state.step = 2
        st.rerun()



# --- VERROUILLAGE (Le reste n'apparaît que si step >= 2) ---
if st.session_state.step >= 2:
    st.divider()
    # Cible HTML invisible
    st.markdown("<div id='cible-etape-2'></div>", unsafe_allow_html=True)
    # Automation : scroll la page en douceur
    if st.session_state.step == 2:
        components.html(
            "<script>window.parent.document.getElementById('cible-etape-2').scrollIntoView({behavior: 'smooth'});</script>", 
            height=0
        )
    
    
    # --- ETAPE 2 : DURÉE SEJOUR --- Slider pour selectionner la duree du séjour (1 à 7 jours)
    st.markdown('<p style="color:#FF4500; font-weight:800; font-size:1.2rem; margin-bottom:0;"> ÉTAPE 2</p>', unsafe_allow_html=True)
    st.subheader("Combien de temps souhaitez-vous partir ?")
    st.write("Indiquez le nombre de jours de votre voyage :")

    st.write("##")

    # Restriction de la largeur (Ratio 1/1 = prend la moitié de l'écran)
    col_slider, col_vide = st.columns([1, 1]) 

    with col_slider:
        # Le Select Slider (Affiche tous les jours en fixe en dessous)
        duree = st.select_slider(
            "Durée (jours)", 
            options=[1, 2, 3, 4, 5, 6, 7], 
            value=3,
            label_visibility="collapsed"
        )
    
    st.write(f"Vous avez choisi de partir : <span style='background-color:#FFF0ED; color:#FF4500; padding:4px 10px; border-radius:8px; font-size:0.9rem; font-weight:bold;'>{duree} {'jour' if duree == 1 else 'jours'}</span>", unsafe_allow_html=True)
    
    st.write("##")
    
    # ➡️ Bouton 
    if st.button("Suivant :material/arrow_forward:", key="btn_etape2", type="primary"):
        st.session_state.duree = duree
        st.session_state.step = 3
        st.rerun()


# --- ÉTAPE 3 : GÉNÉRATION DE L'ITINÉRAIRE ---
if st.session_state.step >= 3:
    st.divider()

    st.markdown("<div id='cible-etape-3'></div>", unsafe_allow_html=True)
    if st.session_state.step == 3:
        st.write("##")

        components.html(
            "<script>window.parent.document.getElementById('cible-etape-3').scrollIntoView({behavior: 'smooth'});</script>", 
            height=0
        )

    st.markdown('<p style="color:#FF4500; font-weight:800; font-size:1.2rem; margin-bottom:0;">ÉTAPE 3</p>', unsafe_allow_html=True)
    st.subheader("Quels sont vos centres d'intérêt ?")

    thematique = st.pills(
    label="Sélectionnez une thématique pour votre voyage :", 
    options=["Culture", "Sport", "Gastronomie", "En famille", "Bien-être/Relaxation"],
    selection_mode="single",
    default="Culture",
    )

    st.write("##")

    if st.button("Générer mon itinéraire de voyage :material/travel:", type="primary", key="gen_final"):
        
        # 1. Pipeline de chargement 
        st.session_state.thematique = thematique

        phrases = [
            "Localisation des meilleurs spots...",
            "Optimisation du trajet...",
            "Touche finale à votre itinéraire..."
        ]

        with st.spinner("Itinego s'occupe de tout..."):
            info_place = st.empty() 
            import time
            for p in phrases:
                info_place.write(f"_{p}_") 
                time.sleep(1.0)
                    
            info_place.empty()
            st.success("Votre itinéraire est prêt ! 🎉") 

            # LOGIQUE POUR TEST "PARIS2" vs RÉEL
            if st.session_state.ville.upper() == "PARIS2":
                # Données fictives structurées exactement comme le JSON attendu de Neo4j
                st.session_state.data_voyage = {
                    "metadata": {"city": "Paris2", "status": "test_mode"},
                    "points": [
                        {"h": "10:00", "n": "Tour Eiffel (Test)", "lat": 48.8584, "lon": 2.2945, "desc": "Matinée iconique au pied de la dame de fer."},
                        {"h": "11:30", "n": "Trocadéro (Test)", "lat": 48.8623, "lon": 2.2881, "desc": "Vue panoramique pour vos plus belles photos."},
                        {"h": "15:00", "n": "Musée du Louvre (Test)", "lat": 48.8606, "lon": 2.3376, "desc": "Après-midi culturelle avec la Joconde."},
                        {"h": "17:30", "n": "Jardin des Tuileries (Test)", "lat": 48.8635, "lon": 2.3275, "desc": "Balade relaxante avant la fin de journée."}
                    ]
                }
            else:
                # BRANCHEMENT FUTUR API ICI
                # payload = {"city": st.session_state.ville, "days": st.session_state.duree, "category": thematique}
                # response = requests.post("URL_API", json=payload)
                # st.session_state.data_voyage = response.json()
                
                # Message d'erreur si ce n'est pas Paris2 et que l'API n'est pas branchée
                st.warning("⚠️ Mode démo : Tapez 'Paris2' pour voir l'itinéraire de test.")
                st.stop()

        st.session_state.step = 4
        st.rerun()


# --- ÉTAPE 4 : RENDU FINAL ---

if st.session_state.step >= 4 and "data_voyage" in st.session_state:
    st.divider()
    st.markdown('<p class="step-header-red">VOTRE CARNET DE VOYAGE</p>', unsafe_allow_html=True)
    
    # 1. Extraction Data (Format attendu par st.map)
    df_map = pd.DataFrame(st.session_state.data_voyage["points"])
    
    # 2. Affichage Map
    st.subheader(f"Exploration de {st.session_state.ville}")
    st.map(df_map, size=70, color='#FF4500', zoom=12)

    st.write("##")

    # CHRONOLOGIE DE L'ITINÉRAIRE
    st.markdown("### Votre itinéraire personnalisé")
    st.write("##")

    # Boucle sur les points d'intérêt pour créer une timeline visuelle
    for pt in st.session_state.data_voyage["points"]:
        # Création d'une "Carte" visuelle 
        with st.container(border=True):
            col_h, col_desc = st.columns([1, 4])
            
            with col_h:
                # On affiche l'heure 
                st.markdown(f"## {pt['h']}")
                st.caption("Départ")
                
            with col_desc:
                # Le nom du lieu en gras et sa description
                st.markdown(f"#### :material/location_on: {pt['n']}")
                st.write(pt['desc'])
                
                # Petit badge optionnel pour le style
                st.markdown(f'<span style="background-color:#FFF0ED; color:#FF4500; padding:2px 8px; border-radius:5px; font-size:0.7rem; font-weight:bold;">VUE À NE PAS MANQUER</span>', unsafe_allow_html=True)

    st.success("Votre itinéraire personnalisé est prêt ! ✈️")

    st.write("##")


    # On place le bouton "Favoris" juste en dessous
    if st.button("❤️ Enregistrer dans mes favoris", use_container_width=True):
        # LOGIQUE DATA à faire : Enregistrer l'itinéraire dans une base de données ou via une API ??
        # payload_fav = {
        #    "user_id": "user_123",
        #    "itinerary_data": st.session_state.data_voyage
        # }
        # requests.post("TON_API/favorites", json=payload_fav)
        
        st.toast("Itinéraire ajouté à vos favoris ! ✨")