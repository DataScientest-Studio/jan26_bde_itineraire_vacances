import time
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from streamlit_local_storage import LocalStorage

# Initialisation du module
localS = LocalStorage()


# Connexion à l'API et Cache 3h pour éviter les appels redondants

@st.cache_data(ttl=10800)
def get_cities_auto():
    # Liste de secours automatique (Fallback)
    fallback_cities = ["Paris", "Paris2","Bordeaux", "Lyon", "Marseille", "Biarritz"]
    
    try:
        # Réduction du timeout à 1s pour ne pas bloquer l'utilisateur
        token_url = "http://api:8000/token"
        auth_data = {"username": "admin", "password": "Pwd_iv_26!@"}
        resp_token = requests.post(token_url, data=auth_data, timeout=1)
        
        if resp_token.status_code == 200:
            token = resp_token.json().get("access_token")
            cities_url = "http://api:8000/cities"
            headers = {"Authorization": f"Bearer {token}"}
            resp_cities = requests.get(cities_url, headers=headers, timeout=1)
            
            if resp_cities.status_code == 200:
                return [r["city"] for r in resp_cities.json()] 
                
    except (requests.exceptions.RequestException, Exception):
        # En cas d'erreur API, on utilise silencieusement les données de secours
        pass 
        
    return fallback_cities


# 1. Initialisation de la session et configuration de la page

st.set_page_config(page_title="Itinéraire de Vacances", layout="centered")

if 'step' not in st.session_state: st.session_state.step = 0
if 'ville' not in st.session_state: st.session_state.ville = ""
if 'duree' not in st.session_state: st.session_state.duree = 3
if 'max_step' not in st.session_state: st.session_state.max_step = 1

st.session_state.max_step = max(st.session_state.max_step, st.session_state.step)


# 2. SIDEBAR : Menu de navigation 

with st.sidebar:
    st.title("Sommaire")
    st.write("---")

    st.markdown("""
        <style>
        div[data-testid="stSidebar"] button {
            justify-content: flex-start !important; text-align: left !important;
            width: 100% !important; padding: 5px 0px !important;
            background-color: transparent !important; border: none !important;
        }
        div[data-testid="stSidebar"] button[kind="tertiary"]:enabled p { color: #FF4500 !important; }
        div[data-testid="stSidebar"] button[kind="tertiary"]:disabled p { color: #CBD5E1 !important; }
        </style>
    """, unsafe_allow_html=True)

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
        
        label = f"**{s['icon']} {s['label']}**" if is_current else (f":material/check_circle: {s['label']}" if is_done else f"{s['icon']} {s['label']}")

        if st.button(label, key=f"nav_{s['id']}", disabled=not is_accessible, type="tertiary"):
            st.session_state.step = s['id']
            st.rerun()

    st.write("---")
    # Existence de favoris pour appliquer un style différent
    favoris_nav = localS.getItem("mes_favoris_itinego") or []
    is_empty = len(favoris_nav) == 0

    # Bouton favoris style sidebar
    fav_label = "**:material/star: Mes itinéraires favoris**" if st.session_state.step == 5 else ":material/star: Mes itinéraires favoris"
    
    if st.button(fav_label, key="nav_fav", type="tertiary", disabled=is_empty):
        st.session_state.step = 5
        st.rerun()

    if st.button("Recommencer", icon=":material/restart_alt:", use_container_width=True):
        st.session_state.clear()
        st.session_state.step = 1
        st.rerun()

    


# 3. Design global (CSS)

st.markdown("""
    <style>
    .top-bar { height: 8px; background: linear-gradient(90deg, #4F46E5 0%, #FF694B 100%); border-radius: 10px; margin-bottom: 25px; }
    .step-header-red { color: #FF4500; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; text-transform: uppercase; }
    [data-testid="stSidebar"] { background-color: #F8FAFC; border-right: 1px solid #E2E8F0; }
    [data-testid="stSidebar"] a { text-decoration: none; color: #4B5563 !important; }
    h1 { font-family: 'Polymath', sans-serif !important; font-weight: 800 !important; letter-spacing: -1px !important; color: #111827 !important; }
    button[kind="primary"] { background: linear-gradient(135deg, #FF6B4B 0%, #FF8E3C 100%) !important; border: none !important; color: white !important; font-weight: 700 !important; padding: 12px 30px !important; border-radius: 12px !important; transition: 0.3s !important; }
    </style>
    <div class="top-bar"></div>
    """, unsafe_allow_html=True)


# ÉTAPE 0 : Page d'accueil

if st.session_state.step == 0:
    st.markdown("<h1 style='text-align: center; font-size: 4rem;'>Itinégo</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4B5563;'>Votre assistant de voyage personnalisé</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Planifiez votre itinéraire de voyage en seulement quelques clics...</p>", unsafe_allow_html=True)
    
    st.write("##")
    st.write("##")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("Trouver mon itinéraire de voyage", type="primary", use_container_width=True):
            st.session_state.step = 1
            st.session_state.max_step = 1
            st.rerun()


# ÉTAPE 1 : Choix de la destination

if st.session_state.step >= 1 and st.session_state.step != 5:
    
    st.markdown("""
        <style>
        @keyframes slideFade {
            0% { opacity: 0; transform: translateY(40px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .block-container { animation: slideFade 0.6s ease-out; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Itinégo")
    st.subheader("Votre assistant de voyage personnalisé")
    
    st.write("---")

    st.markdown('<p style="color:#FF4500; font-weight:800; font-size:1.2rem; margin-bottom:0;">ÉTAPE 1</p>', unsafe_allow_html=True)
    st.subheader("Choisissez votre destination :material/location_on:")

    villes_db = get_cities_auto()
    ville_temp = st.selectbox("Destination", options=villes_db, index=None, placeholder="Commencez à taper (ex: Paris...)", label_visibility="collapsed")

    alerte_ville = st.empty()
    st.write("##")

    if st.button("Suivant :material/arrow_forward:", key="btn_etape1", type="primary"):
        if not ville_temp:
            alerte_ville.warning("Veuillez choisir une ville avant de passer à la suite. ⚠️")
        else:
            st.session_state.ville = ville_temp
            st.session_state.step = 2
            st.rerun()


# ETAPE 2 : Durée du séjour

if st.session_state.step >= 2 and st.session_state.step != 5:
    st.divider()
    st.markdown("<div id='cible-etape-2'></div>", unsafe_allow_html=True)
    
    if st.session_state.step == 2:
        components.html("<script>window.parent.document.getElementById('cible-etape-2').scrollIntoView({behavior: 'smooth'});</script>", height=0)
    
    st.markdown('<p style="color:#FF4500; font-weight:800; font-size:1.2rem; margin-bottom:0;"> ÉTAPE 2</p>', unsafe_allow_html=True)
    st.subheader("Combien de temps souhaitez-vous partir ?")
    
    col_slider, col_vide = st.columns([1, 1]) 
    with col_slider:
        duree = st.select_slider("Durée (jours)", options=[1, 2, 3, 4, 5, 6, 7], value=3, label_visibility="collapsed")
    
    st.write(f"Vous avez choisi de partir : <span style='background-color:#FFF0ED; color:#FF4500; padding:4px 10px; border-radius:8px; font-size:0.9rem; font-weight:bold;'>{duree} {'jour' if duree == 1 else 'jours'}</span>", unsafe_allow_html=True)
    st.write("##")
    
    if st.button("Suivant :material/arrow_forward:", key="btn_etape2", type="primary"):
        st.session_state.duree = duree
        st.session_state.step = 3
        st.rerun()


# ÉTAPE 3 : Génération de l'itinéraire

if st.session_state.step >= 3 and st.session_state.step != 5:

    st.divider()
    st.markdown("<div id='cible-etape-3'></div>", unsafe_allow_html=True)
    
    if st.session_state.step == 3:
        components.html("<script>window.parent.document.getElementById('cible-etape-3').scrollIntoView({behavior: 'smooth'});</script>", height=0)

    st.markdown('<p style="color:#FF4500; font-weight:800; font-size:1.2rem; margin-bottom:0;">ÉTAPE 3</p>', unsafe_allow_html=True)
    st.subheader("Quels sont vos centres d'intérêt ?")

    thematique = st.pills("Sélectionnez une thématique pour votre voyage :", options=["Culture", "Sport", "Gastronomie", "En famille", "Bien-être/Relaxation"], selection_mode="single", default="Culture")
    st.write("##")

    if st.button("Générer mon itinéraire de voyage :material/travel:", type="primary", key="gen_final"):
        st.session_state.thematique = thematique

        with st.spinner("Itinego s'occupe de tout..."):
            info_place = st.empty() 
            for p in ["Localisation des meilleurs spots...", "Optimisation du trajet...", "Touche finale..."]:
                info_place.write(f"_{p}_") 
                time.sleep(1.0)
            info_place.empty()
            
            # --- TENTATIVE API ---
            try:
                payload = {"city": st.session_state.ville, "days": st.session_state.duree, "theme": thematique}
                
                # MODE PRODUCTION : Quand l'API sera prête dans le Docker :
                # 1. DÉCOMMENTER les 4 lignes ci-dessous pour activer l'appel à l'API
                # response = requests.post("http://api:8000/generate", json=payload, timeout=5) 
                # if response.status_code == 200:
                #     st.session_state.data_voyage = response.json()
                # else:
                
                # 2. Supprimer (ou commenter) cette ligne raise ConnectionError
                raise ConnectionError 

            except (requests.exceptions.RequestException, ConnectionError):
                # Mode démo : données de secours en cas d'erreur API ou pour les tests locaux
                st.session_state.data_voyage = {
                    "days": [
                        {"day": 1, "steps": [
                            {"time": "08:00", "poi_id": "PAR002", "label": "Cathédrale Notre-Dame", "lat": 48.8529, "lon": 2.3499, "themes": ["Culturel"]},
                            {"time": "10:00", "poi_id": "PAR010", "label": "Sainte-Chapelle", "lat": 48.8554, "lon": 2.345, "themes": ["Culturel"]},
                            {"time": "12:00", "poi_id": "LUNCH_BREAK", "label": "Pause déjeuner (12h-14h)"},
                            {"time": "14:00", "poi_id": "PAR008", "label": "Centre Pompidou", "lat": 48.8606, "lon": 2.3522, "themes": ["Culturel"]},
                            {"time": "16:00", "poi_id": "PAR001", "label": "Musée du Louvre", "lat": 48.8606, "lon": 2.3376, "themes": ["Culturel"]}
                        ]},
                        {"day": 2, "steps": [
                            {"time": "08:00", "poi_id": "PAR009", "label": "Musée Rodin", "lat": 48.8556, "lon": 2.3151, "themes": ["Culturel"]},
                            {"time": "10:00", "poi_id": "PAR003", "label": "Tour Eiffel", "lat": 48.8584, "lon": 2.2945, "themes": ["Culturel"]},
                            {"time": "12:00", "poi_id": "LUNCH_BREAK", "label": "Pause déjeuner (12h-14h)"},
                            {"time": "14:00", "poi_id": "PAR004", "label": "Arc de Triomphe", "lat": 48.8738, "lon": 2.295, "themes": ["Culturel"]},
                            {"time": "16:00", "poi_id": "PAR007", "label": "Opéra Garnier", "lat": 48.8719, "lon": 2.3316, "themes": ["Culturel"]}
                        ]}
                    ]
                }
                st.toast("Affichage des données de secours", icon="⚠️")

        # Sortie du spinner et passage direct à l'étape 4
        st.session_state.step = 4
        st.rerun()




# ÉTAPE 4 : rendu de l'itinéraire

if st.session_state.step == 4 and "data_voyage" in st.session_state:
    st.divider()
    
    st.markdown('<p class="step-header-red">VOTRE CARNET DE VOYAGE</p>', unsafe_allow_html=True)
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">', unsafe_allow_html=True)
    
    theme_choisi = st.session_state.get("thematique", "Culture")
    st.markdown(f"<div style='margin-bottom: 20px;'><b>Thématique :</b> <span style='background-color:#FFF0ED; color:#FF4500; padding:4px 12px; border-radius:12px; font-size:0.85rem; font-weight:bold; margin-left: 10px;'>{theme_choisi}</span></div>", unsafe_allow_html=True)
    
    map_points = []
    for day in st.session_state.data_voyage.get("days", []):
        for step in day.get("steps", []):
            if "lat" in step and "lon" in step:
                map_points.append({"lat": step["lat"], "lon": step["lon"], "name": step["label"]})
    
    if map_points:
        df_map = pd.DataFrame(map_points)
        st.subheader(f"Exploration de {st.session_state.ville}")
        st.map(df_map, size=70, color='#FF4500', zoom=12)
        st.write("##")

    st.markdown("### Votre itinéraire détaillé")
    
    for day in st.session_state.data_voyage.get("days", []):
        with st.container(border=True):
            html_day = f"<h4 style='color:#111827; margin-bottom: 20px; display: flex; align-items: center;'><span class='material-icons-round' style='margin-right: 8px; color:#FF4500;'>calendar_month</span> JOUR {day['day']}</h4>"
            
            steps_list = day.get("steps", [])
            for idx, pt in enumerate(steps_list):
                heure = pt.get("time", "08:00")
                is_lunch = pt.get("poi_id") == "LUNCH_BREAK"
                is_last = (idx == len(steps_list) - 1)
                
                line_html = "" if is_last else "<div style='position: absolute; left: 63px; top: 25px; bottom: 0px; width: 2px; background-color: #FF4500; opacity: 0.2;'></div>"
                time_display = "" if is_lunch else f"{heure}"
                icon_name = "restaurant" if is_lunch else "location_on"
                icon = f"<span class='material-icons-round' style='color: #FF4500; font-size: 1.3rem;'>{icon_name}</span>"
                
                if is_lunch:
                    desc_html = "<p style='color: #6B7280; font-size: 0.85rem; margin: 0;'>Temps libre (2h)</p>"
                else:
                    desc_html = f"<div style='margin-top: 4px;'><span style='color: #6B7280; font-size: 0.85rem;'>Visite (2h)</span></div>"
                
                html_day += f"<div style='display: flex; position: relative; margin-bottom: 0px;'>{line_html}<div style='width: 45px; text-align: right; font-weight: bold; color: #4B5563; font-size: 0.95rem; padding-top: 3px;'>{time_display}</div><div style='width: 30px; text-align: center; margin-left: 5px; margin-right: 5px;'>{icon}</div><div style='flex: 1; padding-bottom: 25px;'><div style='font-weight: bold; color: #111827; font-size: 1.05rem;'>{pt['label']}</div>{desc_html}</div></div>"
            
            st.markdown(html_day, unsafe_allow_html=True)

    st.success("Votre itinéraire personnalisé est prêt !")
    st.write("##")

    # Vérification si l'itinéraire actuel a déjà été sauvé durant cette vue
    if st.session_state.get('last_saved') == st.session_state.ville:
        st.markdown("<p style='font-weight: 800; margin-bottom: 0;'>Itinéraire enregistré !</p>", unsafe_allow_html=True)
        
        # Lien clique acces aux favoris
        if st.button("Voir mes favoris", type="tertiary"):
            st.session_state.step = 5
            st.rerun()
    else:
        
        if st.button("❤️ Enregistrer dans mes favoris", use_container_width=True):
            mes_favoris = localS.getItem("mes_favoris_itinego") or []
            nouveau_favori = {
                "id": int(time.time()),
                "nom": f"Itinéraire pour {st.session_state.ville}",
                "data": st.session_state.data_voyage
            }
            mes_favoris.append(nouveau_favori)
            localS.setItem("mes_favoris_itinego", mes_favoris)
            
            # Mémorise que c'est sauvé pour changer l'affichage
            st.session_state.last_saved = st.session_state.ville
            
            # Petit délai pour laisser le LocalStorage respirer
            time.sleep(0.4)
            st.rerun()



# ÉTAPE 5 : Gestion des favoris
st.write("##")
st.write("##")

if st.session_state.step == 5:
    
    # Ancre et le script de défilement automatique
    st.markdown("<div id='cible-etape-5'></div>", unsafe_allow_html=True)
    components.html("<script>window.parent.document.getElementById('cible-etape-5').scrollIntoView({behavior: 'smooth'});</script>", height=0)

    st.markdown('<p class="step-header-red">Mes favoris</p>', unsafe_allow_html=True)
    favoris = localS.getItem("mes_favoris_itinego") or []

    # Sous-étape : Affichage d'un favori sélectionné
    if "view_favori" in st.session_state:
        if st.button(":material/arrow_back: Retour à la liste", type="tertiary"):
            del st.session_state.view_favori
            st.rerun()
        
        fav = st.session_state.view_favori
        data_fav = fav["data"]
        
        st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">', unsafe_allow_html=True)
        st.subheader(fav["nom"])
        st.write("---")
        
        # 1. Carte du favori
        map_points = []
        for day in data_fav.get("days", []):
            for step_point in day.get("steps", []):
                if "lat" in step_point and "lon" in step_point:
                    map_points.append({"lat": step_point["lat"], "lon": step_point["lon"], "name": step_point["label"]})
        
        if map_points:
            df_map = pd.DataFrame(map_points)
            st.map(df_map, size=70, color='#FF4500', zoom=12)
            st.write("##")

        # 2. Itinéraire Timeline du favori
        for day in data_fav.get("days", []):
            with st.container(border=True):
                html_day = f"<h4 style='color:#111827; margin-bottom: 20px; display: flex; align-items: center;'><span class='material-icons-round' style='margin-right: 8px; color:#FF4500;'>calendar_month</span> JOUR {day['day']}</h4>"
                
                steps_list = day.get("steps", [])
                for idx, pt in enumerate(steps_list):
                    heure = pt.get("time", "08:00")
                    is_lunch = pt.get("poi_id") == "LUNCH_BREAK"
                    is_last = (idx == len(steps_list) - 1)
                    
                    line_html = "" if is_last else "<div style='position: absolute; left: 63px; top: 25px; bottom: 0px; width: 2px; background-color: #FF4500; opacity: 0.2;'></div>"
                    time_display = "" if is_lunch else f"{heure}"
                    icon_name = "restaurant" if is_lunch else "location_on"
                    icon = f"<span class='material-icons-round' style='color: #FF4500; font-size: 1.3rem;'>{icon_name}</span>"
                    
                    if is_lunch:
                        desc_html = "<p style='color: #6B7280; font-size: 0.85rem; margin: 0;'>Temps libre (2h)</p>"
                    else:
                        desc_html = f"<div style='margin-top: 4px;'><span style='color: #6B7280; font-size: 0.85rem;'>Visite (2h)</span></div>"
                    
                    html_day += f"<div style='display: flex; position: relative; margin-bottom: 0px;'>{line_html}<div style='width: 45px; text-align: right; font-weight: bold; color: #4B5563; font-size: 0.95rem; padding-top: 3px;'>{time_display}</div><div style='width: 30px; text-align: center; margin-left: 5px; margin-right: 5px;'>{icon}</div><div style='flex: 1; padding-bottom: 25px;'><div style='font-weight: bold; color: #111827; font-size: 1.05rem;'>{pt['label']}</div>{desc_html}</div></div>"
                
                st.markdown(html_day, unsafe_allow_html=True)

    # Sous-étape : Liste des favoris
    else:
        if not favoris:
            st.info("Vous n'avez pas encore d'itinéraires enregistrés.")
            if st.button("Explorer des destinations"):
                st.session_state.step = 1
                st.rerun()
        else:
            st.write("Sélectionnez un voyage pour voir les détails :")
            
            # CSS pour l'effet au survol
            st.markdown("""
                <style>
                .stButton button[kind="secondary"] {
                    border: 1px solid #E2E8F0 !important;
                    justify-content: flex-start !important;
                    height: 60px !important;
                }
                .stButton button[kind="secondary"]:hover {
                    border-color: #FF4500 !important;
                    background-color: #FFF0ED !important;
                    color: #FF4500 !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # Algorithme pour ajouter (n°X) aux favoris avec noms en doublon
            nom_counts = {}
            for f in favoris:
                nom_counts[f['nom']] = nom_counts.get(f['nom'], 0) + 1
                
            nom_tracker = {nom: 0 for nom in nom_counts}

            for i, fav in enumerate(favoris):
                nom_base = fav['nom']
                
                # Ajout de (n°X) UNIQUEMENT s'il y a des doublons
                if nom_counts[nom_base] > 1:
                    nom_tracker[nom_base] += 1
                    display_name = f"{nom_base} (n°{nom_tracker[nom_base]})"
                else:
                    display_name = nom_base

                col_link, col_del = st.columns([8, 1])
                
                with col_link:
                    if st.button(display_name, key=f"fav_{fav['id']}", use_container_width=True, icon=":material/visibility:"):
                        st.session_state.view_favori = fav
                        st.rerun()
                
                with col_del:
                    if st.button(":material/delete:", key=f"del_{fav['id']}", help="Supprimer ce favori"):
                        
                        # Filtrage pour supprimer le favori sélectionné
                        favoris = [f for f in favoris if f['id'] != fav['id']]
                        
                        # Sauvegarde de la nouvelle liste de favoris dans le localStorage
                        localS.setItem("mes_favoris_itinego", favoris)
                        
                        # Pause pour laisser le temps au toast de s'afficher avant le rechargement
                        time.sleep(0.5)
                        
                        # Rechargement de la page pour mettre à jour la liste des favoris
                        st.toast("Favori supprimé !")
                        st.rerun()
