import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pandas as pd 
import datetime

load_dotenv()
USER_API_URL = os.getenv("USER_SERVICE_API_URL")

st.set_page_config(page_title="Dashboard Gérant", layout="wide")
st.title("📊 Tableau de Bord Gérant")

if not st.session_state.get('logged_in') or not st.session_state.get('user_info') or st.session_state['user_info'].get('role') != 'gerant':
    st.error("Accès non autorisé."); st.page_link("pages/2_Login_Inscription.py", label="Connexion"); st.stop()

user_info_sidebar = st.session_state['user_info'] 
st.sidebar.success(f"Connecté: {user_info_sidebar.get('username')} (Gérant)")
if st.sidebar.button("Déconnexion", key="logout_gerant_dash"):
    st.session_state['logged_in'] = False; st.session_state['user_info'] = None
    st.session_state['success_message'] = "Déconnecté."; st.switch_page("streamlit_app.py")

if 'error_message' in st.session_state and st.session_state['error_message']:
    st.error(st.session_state['error_message']); st.session_state['error_message'] = None
if 'success_message' in st.session_state and st.session_state['success_message']:
    st.success(st.session_state['success_message']); st.session_state['success_message'] = None

tab_create, tab_manage = st.tabs(["➕ Ajouter Personnel", "👥 Gérer Utilisateurs"])

with tab_create:
    st.subheader("Ajouter un Nouveau Bibliothécaire")
    with st.form("create_librarian_form", clear_on_submit=True):
        biblio_username = st.text_input("Nom d'utilisateur*", key="biblio_user_create")
        biblio_email = st.text_input("Email (optionnel)", key="biblio_email_create")
        biblio_password = st.text_input("Mot de passe initial*", type="password", key="biblio_pass_create")
        submitted_create = st.form_submit_button("Créer le compte Bibliothécaire")

        if submitted_create:
            if not biblio_username or not biblio_password: st.warning("Username/Mot de passe requis.")
            elif len(biblio_password) < 6: st.warning("Mot de passe >= 6 caractères.")
            elif not USER_API_URL: st.error("URL service utilisateur non configurée.")
            else:
                payload = {"username": biblio_username, "password": biblio_password, "role": "bibliothecaire", "email": biblio_email or None}
                api_url = f"{USER_API_URL}/users"
                try:
                    response = requests.post(api_url, json=payload, timeout=5)
                    if response.status_code == 201: st.session_state['success_message'] = f"Compte '{biblio_username}' créé !"; st.rerun()
                    elif response.status_code == 409: error_msg = "Erreur"; 
                    try: error_msg = response.json().get('error', error_msg); 
                    except: pass; st.warning(f"{error_msg}")
                    else: error_msg = f"Err API ({response.status_code})"; 
                    try: error_detail = response.json().get('error'); error_msg = error_detail if error_detail else error_msg; 
                    except: pass; st.error(f"Erreur création: {error_msg}")
                except requests.exceptions.RequestException as e: st.error("Err comm service users."); print(f"[Streamlit UI] Err comm create biblio: {e}")

with tab_manage:
    st.subheader("Gérer les Comptes Utilisateurs")

    librarians = []
    members = []
    api_user_error = None

    if not USER_API_URL:
        api_user_error = "URL service utilisateur non configurée."
    else:
        try:
            resp_libs = requests.get(f"{USER_API_URL}/users", params={'role': 'bibliothecaire'}, timeout=5)
            if resp_libs.ok: librarians = resp_libs.json()
            else: api_user_error = f"Err récup biblios ({resp_libs.status_code})"; print(api_user_error)
            if not api_user_error:
                 resp_mems = requests.get(f"{USER_API_URL}/users", params={'role': 'membre'}, timeout=5)
                 if resp_mems.ok: members = resp_mems.json()
                 else: api_user_error = f"Err récup membres ({resp_mems.status_code})"; print(api_user_error)

        except requests.exceptions.RequestException as e:
            api_user_error = f"Err comm récupération users: {e}"; print(api_user_error)

    if api_user_error:
        st.error(api_user_error)

    st.markdown("##### Bibliothécaires")
    if librarians:
        df_libs = pd.DataFrame(librarians)
        df_libs_display = df_libs[['id', 'username', 'email']].rename(columns={'id': 'ID', 'username': 'Utilisateur', 'email': 'Email'})

        for index, user in df_libs.iterrows():
             col1, col2, col3, col4 = st.columns([1, 3, 4, 1]) 
             with col1: st.write(user['id'])
             with col2: st.write(user['username'])
             with col3: st.write(user['email'] or '-')
             with col4:
                  delete_key_lib = f"delete_lib_{user['id']}"
                  if st.button("🗑️", key=delete_key_lib, help=f"Supprimer {user['username']}"):
                       if user['id'] == st.session_state['user_info'].get('id'):
                            st.warning("Vous ne pouvez pas supprimer votre propre compte.")
                       else:
                            delete_api_url = f"{USER_API_URL}/users/{user['id']}" 
                            try:
                                 print(f"[Streamlit UI] Appel API Suppression User: DELETE {delete_api_url}")
                                 response = requests.delete(delete_api_url, timeout=5)
                                 if response.status_code == 204: 
                                      st.session_state['success_message'] = f"Utilisateur '{user['username']}' supprimé."
                                      st.rerun()
                                 elif response.status_code == 403: 
                                      st.error(f"Suppression non autorisée: {response.json().get('error', '')}")
                                 else:
                                    error_msg = f"Err API ({response.status_code})"; 
                                    try:
                                        error_detail = response.json().get('error'); error_msg = error_detail if error_detail else error_msg   
                                    except: pass
                                    st.error(f"Erreur suppression: {error_msg}")
                            except requests.exceptions.RequestException as e:
                                 st.error(f"Erreur communication suppression: {e}")
    else:
        st.caption("Aucun bibliothécaire trouvé.")

    st.divider()

    st.markdown("##### Membres")
    if members:
        df_mems = pd.DataFrame(members)
        df_mems_display = df_mems[['id', 'username', 'email', 'subscription_status', 'subscription_end_date']].rename(columns={
            'id': 'ID', 'username': 'Utilisateur', 'email': 'Email',
            'subscription_status': 'Statut Abo', 'subscription_end_date': 'Fin Abo'
        })
        
        for index, user in df_mems.iterrows():
             col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 4, 2, 2, 1])
             with col1: st.write(user['id'])
             with col2: st.write(user['username'])
             with col3: st.write(user['email'] or '-')
             with col4:
                status = user.get('subscription_status', 'N/A')
                st.markdown(f":{ 'green' if status == 'active' else 'orange' if status == 'pending' else 'red' if status == 'expired' else 'grey'}[{status.capitalize()}]")
             with col5:
                 end_date_str = user.get('subscription_end_date')
                 end_date_display = "-"
                 if end_date_str:
                     try: end_date_display = datetime.fromisoformat(end_date_str.replace('Z','+00:00')).strftime('%d/%m/%Y')
                     except: pass
                 st.write(end_date_display)
             with col6:
                 delete_key_mem = f"delete_mem_{user['id']}"
                 if st.button("🗑️", key=delete_key_mem, help=f"Supprimer {user['username']}"):
                       delete_api_url = f"{USER_API_URL}/users/{user['id']}"
                       try:
                            print(f"[Streamlit UI] Appel API Suppression User: DELETE {delete_api_url}")
                            response = requests.delete(delete_api_url, timeout=5)
                            if response.status_code == 204:
                                 st.session_state['success_message'] = f"Membre '{user['username']}' supprimé."
                                 st.rerun()
                            else:
                                 error_msg = f"Err API ({response.status_code})"; 
                                 try: error_detail = response.json().get('error'); error_msg = error_detail if error_detail else error_msg; 
                                 except: pass
                                 st.error(f"Erreur suppression: {error_msg}")
                       except requests.exceptions.RequestException as e:
                            st.error(f"Erreur communication suppression: {e}")
    else:
        st.caption("Aucun membre trouvé.")


