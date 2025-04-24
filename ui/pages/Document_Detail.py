# ui/pages/Document_Detail.py (Version Minimale v3 - Lire ID Session + Syntaxe Corrigée)
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urljoin
import time # Gardé si besoin de pause debug

# Charger SEULEMENT l'URL du service document pour ce test
load_dotenv()
DOC_API_URL = os.getenv("DOCUMENT_SERVICE_API_URL")
# On aura besoin de LOAN_API_URL et GATEWAY_URL si on réactive le reste plus tard
LOAN_API_URL = os.getenv("LOAN_SERVICE_API_URL")
GATEWAY_URL = os.getenv("GATEWAY_STATIC_URL", "http://127.0.0.1:5000")


# Configuration simple de la page
st.set_page_config(page_title="Détail Document", layout="centered")
st.title("🔍 Détail du Document")

# --- 1. Vérification de Connexion (Robuste) ---
if not st.session_state.get('logged_in', False):
    st.warning("Veuillez vous connecter pour accéder à cette page.")
    st.page_link("pages/2_Login_Inscription.py", label="Se connecter / S'inscrire", icon="🔑")
    st.stop()

user_info = st.session_state.get('user_info')
if not user_info:
     st.error("Erreur : Informations utilisateur manquantes dans la session.")
     st.stop()

# --- 2. Récupérer l'ID du Document depuis l'état de session ---
doc_id = st.session_state.get("doc_id_to_view")

if not doc_id:
    st.error("Impossible de déterminer quel document afficher (ID manquant en session).")
    st.page_link("pages/1_Catalogue.py", label="Retour au Catalogue", icon="📖")
    st.stop()
# Pas besoin de conversion int ici si on s'assure de stocker un int

# --- 3. Appeler l'API Document Service ---
doc_data = None
api_error = None

if not DOC_API_URL:
    api_error = "L'URL du service documents n'est pas configurée dans l'environnement."
elif doc_id:
    try:
        api_url = f"{DOC_API_URL}/documents/{doc_id}"
        print(f"[Streamlit UI - Detail Session] Appel API: {api_url}")
        response = requests.get(api_url, timeout=5)

        if response.ok: # Si statut 2xx
            doc_data = response.json()
            print(f"[Streamlit UI - Detail Session] Données reçues: {doc_data}")
        elif response.status_code == 404:
            api_error = f"Le document avec l'ID {doc_id} n'a pas été trouvé."
            print(f"[Streamlit UI - Detail Session] Erreur 404 API doc {doc_id}")
        else: # Autre erreur API
             # CORRECTION SYNTAXE TRY/EXCEPT (Bloc ELSE Principal)
             error_msg = f"Erreur API documents (Code: {response.status_code})"
             try:
                 error_detail = response.json().get('error', response.text)
                 if error_detail : error_msg = f"Erreur API documents : {error_detail}"
             except: pass
             api_error = error_msg
             print(f"[Streamlit UI - Detail Session] Err API Détail Doc: {api_error}")
             # Fin de la correction

    except requests.exceptions.RequestException as e:
        api_error = f"Erreur de communication avec le service documents : {e}"
        print(f"[Streamlit UI - Detail Session] Erreur communication: {e}")

# --- 4. Affichage ---
st.divider()

if api_error: st.error(api_error)
elif doc_data:
    col1, col2 = st.columns([1, 2]) # Ratio colonnes
    with col1: # Colonne Image
        cover_filename = doc_data.get('cover_image_filename')
        placeholder_path = os.path.join("static", "images", "placeholder_cover.png")
        image_path_to_display = placeholder_path
        if cover_filename:
            potential_path = os.path.join("static", "uploads", "covers", cover_filename)
            if os.path.exists(potential_path):
                image_path_to_display = potential_path
            else:
                print(f"[Streamlit Detail] Image '{cover_filename}' (Doc ID {doc_id}) non trouvée localement à '{potential_path}', utilise placeholder.")
        st.image(image_path_to_display, use_container_width=True, output_format='auto')
    with col2: # Infos Texte
        st.title(doc_data.get('title', 'Titre inconnu'))
        st.subheader(f"par {doc_data.get('author', 'Auteur inconnu')}")
        st.caption(f"ID: {doc_data.get('id')}")
        st.markdown("**Formats :**"); formats_md = []
        if doc_data.get('is_physical'): formats_md.append("`Physique`")
        if doc_data.get('is_digital'): formats_md.append("`Numérique (PDF)`")
        st.markdown(" ".join(formats_md) if formats_md else "Aucun")
        if doc_data.get('is_physical'):
            status = doc_data.get('status', 'inconnu').capitalize(); color = "green" if status == "Disponible" else ("orange" if status == "Emprunte" else "grey")
            st.markdown(f"**Dispo. Physique :** :{color}[{status}]")
        with st.expander("Résumé"): st.write(doc_data.get('summary', 'Pas de résumé.'))

        # --- Actions Membre (Réactivées mais avec syntaxe erreur corrigée) ---
        if user_info.get('role') == 'membre':
            st.markdown("---")
            st.subheader("Vos Actions")
            user_id = user_info.get('id'); has_active_loan = False; has_active_reservation = False
            try: # Vérif prêt/résa
                if LOAN_API_URL and doc_data.get('is_digital'):
                    loan_resp = requests.get(f"{LOAN_API_URL}/users/{user_id}/loans/check?document_id={doc_id}", timeout=3)
                    if loan_resp.ok: has_active_loan = loan_resp.json().get('has_active_loan', False)
                if LOAN_API_URL and doc_data.get('is_physical') and doc_data.get('status') == 'emprunte':
                    resa_resp = requests.get(f"{LOAN_API_URL}/users/{user_id}/reservations/check?document_id={doc_id}", timeout=3)
                    if resa_resp.ok: has_active_reservation = resa_resp.json().get('has_active_reservation', False)
            except requests.exceptions.RequestException as e: st.caption(f"Err vérif prêt/résa: {e}")

            if doc_data.get('is_digital'): # Emprunt Num
                if has_active_loan: st.button("Déjà Emprunté (Num)", disabled=True, key="loan_disabled")
                else:
                    with st.form(key='borrow_form'):
                        st.caption("Emprunter PDF (14 jours)."); borrow_button = st.form_submit_button("Emprunter (Num)", type="primary")
                        if borrow_button:
                            # --- AJOUT DEBUG ---
                            st.info(f"Tentative d'emprunt par User ID: {user_id} pour Doc ID: {doc_id}")
                            print(f"[Streamlit UI] Tentative d'emprunt par User ID: {user_id} pour Doc ID: {doc_id}")
                            # --- FIN AJOUT DEBUG ---
                            api_url = f"{LOAN_API_URL}/loans/digital"; payload = {"user_id": user_id, "document_id": doc_id}
                            try:
                                response = requests.post(api_url, json=payload, timeout=5)
                                if response.status_code == 201: st.session_state['success_message'] = "Doc emprunté !"; st.rerun()
                                else: # CORRECTION SYNTAXE TRY/EXCEPT (Emprunt)
                                    error_detail = None; error_msg = f"Err API ({response.status_code})"
                                    try: error_detail = response.json().get('error')
                                    except: pass
                                    st.error(f"Erreur emprunt: {error_detail or error_msg}")
                                    print(f"[Streamlit UI] Err API Emprunt {response.status_code}: {response.text}")
                            except requests.exceptions.RequestException as e: st.error(f"Err comm prêt: {e}")
            if doc_data.get('is_physical'): # Résa Phys
                 if doc_data.get('status') == 'emprunte':
                     if has_active_reservation: st.button("Déjà Réservé (Phys)", disabled=True, key="resa_disabled")
                     else:
                         with st.form(key='reserve_form'):
                              st.caption("Réserver copie physique."); reserve_button = st.form_submit_button("Réserver (Phys)", type="secondary")
                              if reserve_button:
                                   api_url = f"{LOAN_API_URL}/reservations/physical"; payload = {"user_id": user_id, "document_id": doc_id}
                                   try:
                                        response = requests.post(api_url, json=payload, timeout=5)
                                        if response.status_code == 201: st.session_state['success_message'] = "Doc réservé !"; st.rerun()
                                        else: # CORRECTION SYNTAXE TRY/EXCEPT (Réservation)
                                             error_detail = None; error_msg = f"Err API ({response.status_code})"
                                             try: error_detail = response.json().get('error')
                                             except: pass
                                             st.error(f"Erreur résa: {error_detail or error_msg}")
                                             print(f"[Streamlit UI] Err API Résa {response.status_code}: {response.text}")
                                   except requests.exceptions.RequestException as e: st.error(f"Err comm résa: {e}")
                 elif doc_data.get('status') == 'disponible': st.success("Disponible en rayon.")
                 else: st.info(f"Statut physique : {doc_data.get('status','Inconnu')}")
else:
    st.warning("Aucune donnée de document à afficher.") # Si doc_data est None après appel API
st.divider()
st.page_link("pages/1_Catalogue.py", label="← Retour au Catalogue", icon="📖")

