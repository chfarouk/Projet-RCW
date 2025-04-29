import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime 

load_dotenv()
LOAN_API_URL = os.getenv("LOAN_SERVICE_API_URL")
DOC_API_URL = os.getenv("DOCUMENT_SERVICE_API_URL") 

st.set_page_config(page_title="Mon Compte", layout="wide")
st.title("👤 Mon Compte")

if not st.session_state.get('logged_in') or not st.session_state.get('user_info') or st.session_state['user_info'].get('role') != 'membre':
    st.warning("Veuillez vous connecter en tant que membre pour accéder à cette page.")
    st.page_link("pages/2_Login_Inscription.py", label="Se connecter / S'inscrire", icon="🔑")
    st.stop()

user_info = st.session_state['user_info']
user_id = user_info.get('id')

st.sidebar.success(f"Connecté: {user_info.get('username')} (Membre)")
if st.sidebar.button("Déconnexion", key="logout_membre"):
    st.session_state['logged_in'] = False; st.session_state['user_info'] = None
    st.session_state['success_message'] = "Déconnecté."; st.switch_page("streamlit_app.py")

if 'error_message' in st.session_state and st.session_state['error_message']:
    st.error(st.session_state['error_message']); st.session_state['error_message'] = None
if 'success_message' in st.session_state and st.session_state['success_message']:
    st.success(st.session_state['success_message']); st.session_state['success_message'] = None

loans_data = []
reservations_data = []
api_error = None

if not LOAN_API_URL or not DOC_API_URL or not user_id:
    api_error = "URLs API ou ID User manquants."
else:
    try:
        loan_api_url = f"{LOAN_API_URL}/users/{user_id}/loans?status=active"
        loan_resp = requests.get(loan_api_url, timeout=5)
        if loan_resp.ok:
            loans_raw = loan_resp.json()
            enriched_loans = []
            for loan in loans_raw:
                doc_id = loan.get('document_id')
                if doc_id:
                    doc_resp = requests.get(f"{DOC_API_URL}/documents/{doc_id}", timeout=2)
                    if doc_resp.ok:
                        doc_info = doc_resp.json()
                        loan['document_title'] = doc_info.get('title', f'Doc ID {doc_id}')
                        loan['file_path'] = doc_info.get('file_path')
                    else:
                        loan['document_title'] = f'Err titre Doc ID {doc_id}'
                        loan['file_path'] = None 
                    enriched_loans.append(loan)
            loans_data = enriched_loans
        else: print(f"[Streamlit UI] Err API prêts {loan_resp.status_code}")

        res_api_url = f"{LOAN_API_URL}/users/{user_id}/reservations?status=active"
        res_resp = requests.get(res_api_url, timeout=5)
        if res_resp.ok:
            res_raw = res_resp.json()
            for resa in res_raw:
                doc_id = resa.get('document_id')
                if doc_id:
                     doc_resp = requests.get(f"{DOC_API_URL}/documents/{doc_id}", timeout=2)
                     if doc_resp.ok:
                         resa['document_title'] = doc_resp.json().get('title', f'Doc ID {doc_id}')
                     else:
                          resa['document_title'] = f'Erreur titre Doc ID {doc_id}'
                else: resa['document_title'] = 'Document ID Manquant'
            reservations_data = res_raw
        else: print(f"[Streamlit UI] Err API résas {res_resp.status_code}")

    except requests.exceptions.RequestException as e:
        api_error = f"Erreur communication services: {e}"

tab_loans, tab_reservations, tab_profile = st.tabs(["Mes Emprunts Numériques", "Mes Réservations Physiques", "Mon Profil"])

with tab_loans:
    st.subheader("Emprunts Numériques Actifs")
    if api_error: st.error(api_error)
    elif not loans_data: st.info("Vous n'avez aucun emprunt numérique en cours.")
    else:
        today_date_obj = datetime.utcnow().date()
        for loan in loans_data:
            loan_id = loan.get('id') 
            doc_id = loan.get('document_id')
            doc_title = loan.get('document_title', f"Doc ID {doc_id}")
            pdf_filename = loan.get('file_path')
            due_date_str = loan.get('due_date', ''); due_date_obj = None; days_left_str = "-"

            with st.container(border=True):
                col_info, col_action = st.columns([3,1])
                with col_info:
                    st.markdown(f"**{doc_title}**")
                    st.caption(f"Retour prévu: {due_date_obj.strftime('%d/%m/%Y') if due_date_obj else 'N/A'} ({days_left_str})")
                with col_action:
                     if pdf_filename:
                         static_pdf_path = os.path.join("static", "uploads", "pdfs", pdf_filename)
                         if os.path.exists(static_pdf_path):

                              st.link_button("Lire", f"/{static_pdf_path.replace(os.sep, '/')}", 
                                             type="primary", use_container_width=True, target="_blank")
                         else:
                              st.caption("Fichier PDF non trouvé localement.")
                              print(f"[Streamlit UI] PDF non trouvé localement: {static_pdf_path}")
                     else:
                         st.caption("Pas de fichier PDF associé.")

                     with st.form(key=f"return_form_{loan_id}"):
                          return_submitted = st.form_submit_button("Retourner", type="secondary", use_container_width=True, help="Retourner ce document numérique")
                          if return_submitted:
                               return_api_url = f"{LOAN_API_URL}/loans/{loan_id}/return"
                               try:
                                    response = requests.post(return_api_url, json={"user_id": user_id}, timeout=5) # Envoyer user_id pour validation potentielle API
                                    if response.ok:
                                         st.session_state['success_message'] = f"'{doc_title}' retourné."
                                         st.rerun()
                                    else: st.error(f"Erreur retour: {response.json().get('error', 'Inconnue')}")
                               except requests.exceptions.RequestException as e: st.error(f"Err comm retour: {e}")

with tab_reservations:
    st.subheader("Réservations Physiques Actives")
    if api_error: st.error(api_error)
    elif not reservations_data: st.info("Vous n'avez aucune réservation physique en cours.")
    else:
         for resa in reservations_data:
            resa_id = resa.get('id') 
            doc_id = resa.get('document_id')
            doc_title = resa.get('document_title', f"Document ID {doc_id}")
            resa_date_str = resa.get('reservation_date', '')
            resa_date_formatted = ""
            if resa_date_str:
                 try: resa_date_formatted = datetime.fromisoformat(resa_date_str.replace('Z','+00:00')).strftime('%d/%m/%Y %H:%M')
                 except: pass

            with st.container(border=True):
                 col_info_res, col_action_res = st.columns([3,1])
                 with col_info_res:
                      st.markdown(f"**{doc_title}**")
                      st.caption(f"Réservé le: {resa_date_formatted or 'N/A'}")
                      st.page_link("pages/Document_Detail.py", label="Voir fiche", query_params={"doc_id": doc_id})
                 with col_action_res:  
                      with st.form(key=f"cancel_form_{resa_id}"):
                           cancel_submitted = st.form_submit_button("Annuler", type="secondary", use_container_width=True, help="Annuler cette réservation")
                           if cancel_submitted:
                                cancel_api_url = f"{LOAN_API_URL}/reservations/{resa_id}/cancel"
                                try:
                                     response = requests.post(cancel_api_url, json={"user_id": user_id}, timeout=5)
                                     if response.ok:
                                          st.session_state['success_message'] = f"Réservation pour '{doc_title}' annulée."
                                          st.rerun()
                                     else: st.error(f"Erreur annulation: {response.json().get('error', 'Inconnue')}")
                                except requests.exceptions.RequestException as e: st.error(f"Err comm annulation: {e}")

with tab_profile:
    st.subheader("Mon Profil")
    if user_info:
        st.write(f"**Nom d'utilisateur :** {user_info.get('username')}")
        st.write(f"**Email :** {user_info.get('email') or 'Non renseigné'}")
        st.write(f"**Rôle :** {user_info.get('role', '').capitalize()}")
        st.divider()
    else:
        st.error("Impossible de charger les informations du profil.")
