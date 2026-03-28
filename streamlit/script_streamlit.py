import os
import time
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from streamlit_local_storage import LocalStorage

BASE_URL = os.getenv("API_URL", "http://api:8000")

# Initialisation du module
localS = LocalStorage()


# Connexion à l'API et Cache 3h pour éviter les appels redondants

@st.cache_data(ttl=10800)
def get_cities_auto():
    # Liste de secours au cas où l'API est éteinte
    fallback_cities = [
        {"city": "Paris", "postalcodeinsee": "75056"},
        {"city": "Marseille", "postalcodeinsee": "13055"}
    ]
    
    try:
        token_url = "http://api:8000/token" 
        auth_data = {
            "username": os.getenv("API_USER"), 
            "password": os.getenv("API_PWD") 
        }
        resp_token = requests.post(token_url, data=auth_data, timeout=5)
        
        if resp_token.status_code == 200:
            token = resp_token.json().get("access_token")
            cities_url = "http://api:8000/cities"
            headers = {"Authorization": f"Bearer {token}"}
            
            # Interroge l'API et création "resp_cities"
            resp_cities = requests.get(cities_url, headers=headers, timeout=5)
            
            if resp_cities.status_code == 200:
                # On renvoie tout le JSON directement (qui contient {city, postal_code_insee})
                return resp_cities.json()
                
    except (requests.exceptions.RequestException, Exception):
        # En cas d'erreur API, on passe silencieusement à la suite
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

    


# 3. Design global CSS

st.markdown("""
    <style>
    .top-bar { height: 8px; background: linear-gradient(90deg, #4F46E5 0%, #FF694B 100%); border-radius: 10px; margin-bottom: 25px; }
    .step-header-red { color: #FF4500; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; text-transform: uppercase; }
    [data-testid="stSidebar"] { background-color: #F8FAFC; border-right: 1px solid #E2E8F0; }
    [data-testid="stSidebar"] a { text-decoration: none; color: #4B5563 !important; }
    button[kind="primary"] { background: linear-gradient(135deg, #FF6B4B 0%, #FF8E3C 100%) !important; border: none !important; color: white !important; font-weight: 700 !important; padding: 12px 30px !important; border-radius: 12px !important; transition: 0.3s !important; }
    </style>
    <div class="top-bar"></div>
    """, unsafe_allow_html=True)


# ÉTAPE 0 : Page d'accueil

if st.session_state.step == 0:
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>Itinégo</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4B5563; font-weight: 500; margin-top: -10px;'>Votre assistant de voyage personnalisé</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1rem; margin-top: 15px;'>Planifiez votre itinéraire de voyage en quelques clics seulement...</p>", unsafe_allow_html=True)
    
    
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
    # On utilise f-string pour combiner le NOM et les 2 premiers chiffres du CODE INSEE
    ville_temp = st.selectbox(
        "Destination", 
        options=villes_db, 
        format_func=lambda x: f"{x['city']} ({x['postalcodeinsee']})", 
        index=None, 
        placeholder="Tapez le nom d'une ville ou le code postal...", 
        label_visibility="collapsed"
    )
    alerte_ville = st.empty()
    st.write("##")

    if st.button("Suivant :material/arrow_forward:", key="btn_etape1", type="primary"):
        if not ville_temp:
            alerte_ville.warning("Veuillez choisir une ville avant de passer à la suite. ⚠️")
        else:
            # On stocke le CODE pour l'API
            st.session_state.ville = ville_temp["postalcodeinsee"] 
            # On stocke le NOM pour l'affichage à l'écran
            st.session_state.nom_ville_display = ville_temp["city"] 
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
        duree = st.select_slider("Durée (jours)", options=[1, 2, 3, 4, 5, 6], value=3, label_visibility="collapsed")

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
    st.subheader("Quel est le thème de votre voyage ?")

    thematique = st.pills("Sélectionnez une thématique pour votre voyage :", options=["Culture", "Sport", "Gastronomie", "En famille", "Bien-être/Relaxation"], selection_mode="single", default="Culture")
    st.write("##")

    if st.button("Générer mon itinéraire de voyage :material/travel:", type="primary", key="gen_final"):
        st.session_state.thematique = thematique

        with st.spinner("Itinégo calcule votre voyage..."):
            zone_animation = st.empty()
            
            messages_chargement = [
                ":material/search: **Localisation** des pépites locales...",
                ":material/architecture: **Calcul** de l'itinéraire optimal...",
                ":material/map: **Tracé** de votre carnet de voyage...",
                ":material/auto_awesome: **Personnalisation** de l'expérience..."
            ]

            for _ in range(2): 
                for msg in messages_chargement:
                    zone_animation.markdown(f"*{msg}*")
                    time.sleep(0.7) # Vitesse de l'alternance
            
            zone_animation.markdown(":material/sync: **Connexion** à l'intelligence Itinégo...")
            
            
            # API
            try:
                # Token d'authentification
                token_url = "http://api:8000/token"
                auth_data = {
                    "username": os.getenv("API_USER"), 
                    "password": os.getenv("API_PWD") 
                }
                resp_token = requests.post(token_url, data=auth_data, timeout=5)
                
                if resp_token.status_code == 200:
                    token = resp_token.json().get("access_token")
                    headers = {"Authorization": f"Bearer {token}"}

                    # Traduction de la thématique en numéro pour l'API
                    traduction_bdd = {
                        "Culture": "Culturel", 
                        "Sport": "Sportif", 
                        "Gastronomie": "Gastronomique", 
                        "En famille": "Familial", 
                        "Bien-être/Relaxation": "Détente & bien-être"
                    }
                    
                    category_pour_api = traduction_bdd.get(thematique, "Culturel")

                    parametres = {
                        "city": st.session_state.ville,
                        "days": st.session_state.duree,
                        "category": category_pour_api 
                    }
                
                    reponse = requests.get(
                        "http://api:8000/generer-itineraire", 
                        params=parametres,
                        headers=headers,
                        timeout=60
                    )

                    if reponse.status_code == 200:
                        data = reponse.json()
                        st.session_state.data_voyage = data 
                        st.session_state.step = 4
                        st.rerun()
                
                    else:
                        st.error(f"Erreur API : {reponse.status_code} - {reponse.text}")
                        st.stop()
                else:
                    st.error("Impossible d'obtenir l'autorisation de l'API (Token).")
                    st.stop()

            # GESTION DES ERREURS
            except requests.exceptions.RequestException as e:
                st.error(f"📡 **Erreur réseau** : Impossible de joindre l'API. ({e})")
                st.stop()
            except Exception as e:
                st.error(f"💥 **Erreur critique** : {e}")
                st.stop()

                # Mode démo : données de secours en cas d'erreur API ou pour les tests locaux
                st.session_state.data_voyage = {
                    "itinerary": [
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
        # st.rerun()




# ÉTAPE 4 : rendu de l'itinéraire

if st.session_state.step == 4 and "data_voyage" in st.session_state:
    st.divider()
    
    st.markdown('<p class="step-header-red">VOTRE CARNET DE VOYAGE</p>', unsafe_allow_html=True)
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">', unsafe_allow_html=True)
    
    theme_choisi = st.session_state.get("thematique", "Culture")
    st.markdown(f"<div style='margin-bottom: 20px;'><b>Thématique :</b> <span style='background-color:#FFF0ED; color:#FF4500; padding:4px 12px; border-radius:12px; font-size:0.85rem; font-weight:bold; margin-left: 10px;'>{theme_choisi}</span></div>", unsafe_allow_html=True)
    
    # Récupération de la liste "itinerary" du JSON pour afficher la carte et l'itinéraire détaillé
    itineraire = st.session_state.data_voyage.get("days", [])

    map_points = []
    for day in itineraire:
        for step in day.get("steps", []):
            if "latitude" in step and "longitude" in step:
                map_points.append({"lat": step["latitude"], "lon": step["longitude"], "label": step["label"]})
    
    if map_points:
        import pydeck as pdk # Import mis ici pour aller plus vite
        df_map = pd.DataFrame(map_points)
        st.subheader(f"Exploration de {st.session_state.get('nom_ville_display', 'votre destination')}")
        
        # Création des segments de lignes (Point A -> Point B)
        df_lines = pd.DataFrame({
            "start_lon": df_map["lon"].iloc[:-1].values,
            "start_lat": df_map["lat"].iloc[:-1].values,
            "end_lon": df_map["lon"].iloc[1:].values,
            "end_lat": df_map["lat"].iloc[1:].values,
        })

        # Affichage de la carte avancée PyDeck
        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=df_map["lat"].mean(),
                longitude=df_map["lon"].mean(),
                zoom=13,
                pitch=0,
            ),
            layers=[
                # Les lignes (Le tracé)
                pdk.Layer(
                    "LineLayer",
                    data=df_lines,
                    get_source_position='[start_lon, start_lat]',
                    get_target_position='[end_lon, end_lat]',
                    get_color='[255, 69, 0, 150]', # Orange transparent
                    get_width=4,
                ),
                # Les points (POI)
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df_map,
                    get_position='[lon, lat]',
                    get_color='[255, 69, 0, 255]', # Orange plein
                    get_radius=80,
                ),
            ],
        ))
        st.write("##")
        
    # Affichage de l'itinéraire détaillé
    st.markdown("<h3 style='margin-bottom: 30px;'>Votre itinéraire détaillé</h3>", unsafe_allow_html=True)
    
    # 1. On extrait UNIQUEMENT les vrais POIs pour avoir le compte exact
    toutes_activites = [s for d in itineraire for s in d.get("steps", []) if s.get("type") == "poi"]
    vrai_total_pois = len(toutes_activites)
    nb_jours_demandes = st.session_state.get('duree', 1)

    if vrai_total_pois == 0:
        st.warning("L'itinéraire a été généré, mais il est vide, 0 POI trouvés.")
        itineraire_a_afficher = []
    else:
        # LOGIQUE STRICTE : 1 jour = 4 POIs.
        # Si le total de POIs ne permet pas de remplir les jours demandés (4 par jour), on tasse .
        if vrai_total_pois < (nb_jours_demandes * 4):
            itineraire_a_afficher = []
            
            # On découpe TOUTE la liste brute en blocs stricts de 4 POIs
            for i in range(0, vrai_total_pois, 4):
                jour_index = (i // 4) + 1
                activites_jour = toutes_activites[i:i+4]
                
                steps_finaux = []
                if len(activites_jour) <= 2:

                    # 1 ou 2 POIs : Pas de pause dejeuner
                    steps_finaux = activites_jour
                else:
                    # 3 ou 4 POIs : On injecte la pause dejeuner au milieu (après le 2ème POI)
                    steps_finaux.append(activites_jour[0])
                    steps_finaux.append(activites_jour[1])
                    steps_finaux.append({"type": "pause", "label": "Pause déjeuner", "event_id": "LUNCH_BREAK"})
                    steps_finaux.extend(activites_jour[2:])
                    
                itineraire_a_afficher.append({"day": jour_index, "steps": steps_finaux})
            
            st.info(f"**Info** : Itinéraire généré avec succès. Cependant, nous n'avons trouvé que **{vrai_total_pois} activités** pour vos **{nb_jours_demandes} jours**. Nous les avons regroupées pour optimiser votre temps.", icon=":material/info:")
        else:
            itineraire_a_afficher = itineraire
            st.success("Votre itinéraire est prêt !", icon=":material/celebration:")
        
    total_days_4 = len(itineraire_a_afficher)
    for day_idx, day in enumerate(itineraire_a_afficher):
        jour_num = day.get("day", day_idx + 1)
        raw_steps = day.get("steps", [])
        if not raw_steps:
            continue

        # FILTRE : On extrait les POIs purs et on gère la pause/horaire
        pois_only = [pt for pt in raw_steps if pt.get("event_id") != "LUNCH_BREAK" and pt.get("type") != "pause"]
        
        if len(pois_only) == 1:
            steps_list = pois_only
            grille_horaire = ["10:00"]
        elif len(pois_only) == 2:
            steps_list = pois_only
            grille_horaire = ["08:00", "10:00"]
        else:
            steps_list = pois_only[:2] + [{"type": "pause", "label": "Pause déjeuner", "event_id": "LUNCH_BREAK"}] + pois_only[2:]
            grille_horaire = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00"]

        with st.expander(f"**JOUR {day.get('day', 1)}**", expanded=True, icon=":material/calendar_month:"):
            html_day = "<div style='padding-top: 40px;'>"

            for idx, pt in enumerate(steps_list):
                heure = grille_horaire[idx] if idx < len(grille_horaire) else "18:00"
                is_lunch = pt.get("event_id") == "LUNCH_BREAK" or pt.get("type") == "pause"
                is_last = (idx == len(steps_list) - 1)
                
                # Logique de distance pour les badges
                distance_badge = ""
                css_b = "position: absolute; left: 63px; top: -30px; transform: translateX(-50%); background-color: white; border-radius: 10px; padding: 2px 7px; font-size: 0.65rem; font-weight: bold; z-index: 10; white-space: nowrap;"
                
                if idx == 0:
                    # Badge de début ou "Itinéraire Jour X"
                    if day_idx == 0:
                        distance_badge = f"<div style='{css_b} border: 1px solid #4F46E5; color: #4F46E5;'>Début d'itinéraire</div>"
                    else:
                        distance_badge = f"<div style='{css_b} border: 1px solid #4F46E5; color: #4F46E5;'>Itinéraire Jour {jour_num}</div>"
                
                # Condition : Pas de badge si c'est un repas (is_lunch)
                elif not is_lunch and "distance_m" in pt:
                    dist_m = pt["distance_m"]
                    # Affichage même si 0m
                    txt = f"{dist_m / 1000:.1f} km" if dist_m >= 1000 else f"{int(dist_m)} m"
                    distance_badge = f"<div style='{css_b} border: 1px solid #E2E8F0; color: #6B7280;'>↓ {txt}</div>"

                line_html = "" if is_last else "<div style='position: absolute; left: 63px; top: 25px; bottom: 0px; width: 2px; background-color: #FF4500; opacity: 0.2;'></div>"
                
                if is_lunch:
                    icon_h = "<span class='material-icons-round' style='color: #FF4500; font-size: 1.2rem; margin-top: 2px;'>restaurant</span>"
                    desc_h = "" 
                else:
                    icon_h = "<div style='width: 12px; height: 12px; background-color: #FF4500; border-radius: 50%; margin: 8px auto 0 auto;'></div>"
                    adr, tel, web, desc = pt.get("address"), pt.get("phone") or pt.get("telephone"), pt.get("website"), pt.get("description")
                    
                    contact_elements = []
                    if adr and str(adr).lower() != "none":
                            adr_display = adr[:120] + "..." if len(adr) > 120 else adr
                            q = f"{pt.get('label','')} {adr} {st.session_state.get('nom_ville_display','')}".replace(" ", "+")
                            u = f"https://www.google.com/maps/search/?api=1&query={q}"
                            contact_elements.append(f"<a href='{u}' target='_blank' style='text-decoration: underline;'><span class='material-icons-round' style='font-size: 0.9rem; vertical-align: middle;'>place</span> {adr_display}</a>")
                    if tel and str(tel).lower() != "none": contact_elements.append(f"<span class='material-icons-round' style='font-size: 0.9rem; vertical-align: middle;'>call</span> {tel}")
                    if web and str(web).lower() != "none": contact_elements.append(f"<a href='{web}' target='_blank' style='color:#FF4500; text-decoration:none;'><span class='material-icons-round' style='font-size: 0.9rem; vertical-align: middle;'>language</span> Site Web</a>")
                    
                    info_l = f"<div style='font-size: 0.8rem; color: #6B7280; margin-top: 4px;'>{' • '.join(contact_elements)}</div>" if contact_elements else ""
                    det = f"<details open style='margin-top: 8px; cursor: pointer;'><summary style='font-size: 0.8rem; color: #6B7280;'>Description ...</summary><p style='font-size: 0.85rem; color: #4B5563; margin-top: 5px; line-height: 1.4;'>{desc}</p></details>" if desc and str(desc).lower() != "none" else ""
                    desc_h = f"{info_l}{det}<div style='margin-top: 2px;'><span style='color: #FF4500; font-weight: bold; font-size: 0.8rem;'>⏱ 2h</span></div>"
                
                margin_val = "30px" if is_lunch else "0px"
                html_day += f"<div style='display: flex; position: relative; margin-bottom: {margin_val};'>{line_html}{distance_badge}<div style='width: 45px; text-align: right; font-weight: bold; color: #4B5563; font-size: 0.95rem; padding-top: 3px;'>{heure}</div><div style='width: 30px; text-align: center; margin-left: 5px; margin-right: 5px;'>{icon_h}</div><div style='flex: 1; padding-bottom: 35px;'><div style='font-weight: bold; color: #111827; font-size: 1.05rem;'>{pt['label']}</div>{desc_h}</div></div>"
            
                # Pastille de fin pour le tout dernier POI du dernier jour
                if is_last and (day_idx == total_days_4 - 1):
                    html_day += f"<div style='position: relative; height: 30px;'><div style='position: absolute; left: 63px; top: -15px; transform: translateX(-50%); background-color: white; border-radius: 10px; padding: 2px 7px; font-size: 0.65rem; font-weight: bold; z-index: 10; white-space: nowrap; border: 1px solid #4F46E5; color: #4F46E5;'>Fin d'itinéraire</div></div>"

            html_day += "</div>"
            st.markdown(html_day, unsafe_allow_html=True)


    # Vérification si l'itinéraire actuel a déjà été sauvé durant cette vue
    if st.session_state.get('last_saved') == st.session_state.ville:
        st.markdown("<p style='font-weight: 800; margin-bottom: 0;'>Itinéraire enregistré !</p>", unsafe_allow_html=True)

        st.markdown("""
            <style>
            div.stButton > button[key="link_fav_button"] {
                color: black !important;
                text-decoration: none !important;
                background: transparent !important;
                border: none !important;
                padding: 0 !important;
                font-weight: normal !important;
                font-size: 1rem !important; /* Pour que ça ressemble à du texte */
                margin-top: 10px !important; /* Espacement après le texte "Itinéraire enregistré !" */
            }
            div.stButton > button[key="link_fav_button"]:hover {
                text-decoration: underline !important;
                color: black !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Lien clique acces aux favoris (avec clé unique pour le style)
        if st.button("Voir mes favoris", key="link_fav_button"):
            st.session_state.step = 5
            st.rerun()
    else:
        
        if st.button("❤️ Enregistrer dans mes favoris", use_container_width=True):
            mes_favoris = localS.getItem("mes_favoris_itinego") or []

            # Récupération du nom de la ville pour le titre
            # On utilise .get() pour sécuriser au cas où la variable n'est pas définie
            nom_ville = st.session_state.get('nom_ville_display', st.session_state.ville)

            nouveau_favori = {
                "id": int(time.time()),
                "nom": f"Itinéraire pour {nom_ville}",
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
        
        # Récupération des données
        fav = st.session_state.view_favori
        data_fav = fav["data"]
        itineraire_fav = data_fav.get("days", [])

        st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">', unsafe_allow_html=True)
        st.subheader(fav["nom"])
        st.write("---")
        
        # Affichage de l'itinéraire en colonne unique
        # Affichage de l'itinéraire avec la même logique métier que l'étape 4
        total_days_5 = len(itineraire_fav)
        for day_idx, day in enumerate(itineraire_fav):
            jour_num = day.get("day", day_idx + 1)
            raw_steps = day.get("steps", [])
            if not raw_steps:
                continue

            # FILTRE : On extrait les POIs purs et on gère la pause/horaire
            pois_only = [pt for pt in raw_steps if pt.get("event_id") != "LUNCH_BREAK" and pt.get("type") != "pause"]
            
            if len(pois_only) == 1:
                steps_list = pois_only
                grille_horaire = ["10:00"]
            else:
                steps_list = pois_only[:2] + [{"type": "pause", "label": "Pause déjeuner", "event_id": "LUNCH_BREAK"}] + pois_only[2:]
                grille_horaire = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00"]

            with st.expander(f"**JOUR {day.get('day', 1)}**", expanded=True, icon=":material/calendar_month:"):
                html_day = "<div style='padding-top: 40px;'>"

                for idx, pt in enumerate(steps_list):
                    heure = grille_horaire[idx] if idx < len(grille_horaire) else "18:00"
                    is_lunch = pt.get("event_id") == "LUNCH_BREAK" or pt.get("type") == "pause"
                    is_last = (idx == len(steps_list) - 1)
                    
                    # Logique de distance pour les badges
                    distance_badge = ""
                    css_b = "position: absolute; left: 63px; top: -30px; transform: translateX(-50%); background-color: white; border-radius: 10px; padding: 2px 7px; font-size: 0.65rem; font-weight: bold; z-index: 10; white-space: nowrap;"
                    
                    if idx == 0:
                        if day_idx == 0:
                            distance_badge = f"<div style='{css_b} border: 1px solid #4F46E5; color: #4F46E5;'>Début d'itinéraire</div>"
                        else:
                            distance_badge = f"<div style='{css_b} border: 1px solid #4F46E5; color: #4F46E5;'>Itinéraire Jour {jour_num}</div>"
                    elif not is_lunch and "distance_m" in pt:
                        dist_m = pt["distance_m"]
                        txt = f"{dist_m / 1000:.1f} km" if dist_m >= 1000 else f"{int(dist_m)} m"
                        distance_badge = f"<div style='{css_b} border: 1px solid #E2E8F0; color: #6B7280;'>↓ {txt}</div>"

                    line_html = "" if is_last else "<div style='position: absolute; left: 63px; top: 25px; bottom: 0px; width: 2px; background-color: #FF4500; opacity: 0.2;'></div>"
                    
                    if is_lunch:
                        icon_h = "<span class='material-icons-round' style='color: #FF4500; font-size: 1.2rem; margin-top: 2px;'>restaurant</span>"
                        desc_h = "" 
                    else:
                        icon_h = "<div style='width: 12px; height: 12px; background-color: #FF4500; border-radius: 50%; margin: 8px auto 0 auto;'></div>"
                        adr, tel, web, desc = pt.get("address"), pt.get("phone") or pt.get("telephone"), pt.get("website"), pt.get("description")
                        
                        contact_elements = []

                        if adr and str(adr).lower() != "none":
                            adr_display = adr[:120] + "..." if len(adr) > 120 else adr
                            q = f"{pt.get('label','')} {adr} {st.session_state.get('nom_ville_display','')}".replace(" ", "+")
                            u = f"https://www.google.com/maps/search/?api=1&query={q}"
                            contact_elements.append(f"<a href='{u}' target='_blank' style='text-decoration: underline;'><span class='material-icons-round' style='font-size: 0.9rem; vertical-align: middle;'>place</span> {adr_display}</a>")

                        if tel and str(tel).lower() != "none": 
                            contact_elements.append(f"<span class='material-icons-round' style='font-size: 0.9rem; vertical-align: middle;'>call</span> {tel}")
                        if web and str(web).lower() != "none": 
                            contact_elements.append(f"<a href='{web}' target='_blank' style='color:#FF4500; text-decoration:none;'><span class='material-icons-round' style='font-size: 0.9rem; vertical-align: middle;'>language</span> Site Web</a>")
                        
                        info_l = f"<div style='font-size: 0.8rem; color: #6B7280; margin-top: 4px;'>{' • '.join(contact_elements)}</div>" if contact_elements else ""
                        det = f"<details open style='margin-top: 8px; cursor: pointer;'><summary style='font-size: 0.8rem; color: #6B7280;'>Description ...</summary><p style='font-size: 0.85rem; color: #4B5563; margin-top: 5px; line-height: 1.4;'>{desc}</p></details>" if desc and str(desc).lower() != "none" else ""
                        desc_h = f"{info_l}{det}<div style='margin-top: 2px;'><span style='color: #FF4500; font-weight: bold; font-size: 0.8rem;'>⏱ 2h</span></div>"
                    
                    margin_val = "30px" if is_lunch else "0px"
                    html_day += f"<div style='display: flex; position: relative; margin-bottom: {margin_val};'>{line_html}{distance_badge}<div style='width: 45px; text-align: right; font-weight: bold; color: #4B5563; font-size: 0.95rem; padding-top: 3px;'>{heure}</div><div style='width: 30px; text-align: center; margin-left: 5px; margin-right: 5px;'>{icon_h}</div><div style='flex: 1; padding-bottom: 35px;'><div style='font-weight: bold; color: #111827; font-size: 1.05rem;'>{pt['label']}</div>{desc_h}</div></div>"
                
                    # Pastille de fin pour le tout dernier POI du dernier jour
                    if is_last and (day_idx == total_days_5 - 1):
                        html_day += f"<div style='position: relative; height: 30px;'><div style='position: absolute; left: 63px; top: -15px; transform: translateX(-50%); background-color: white; border-radius: 10px; padding: 2px 7px; font-size: 0.65rem; font-weight: bold; z-index: 10; white-space: nowrap; border: 1px solid #4F46E5; color: #4F46E5;'>Fin d'itinéraire</div></div>"

                html_day += "</div>"
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