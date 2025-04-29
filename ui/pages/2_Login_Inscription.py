import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
USER_API = os.getenv("USER_SERVICE_API_URL")

st.set_page_config(page_title="Connexion / Inscription", layout="centered") 

if 'error_message' in st.session_state and st.session_state['error_message']:
    st.error(st.session_state['error_message'])
    st.session_state['error_message'] = None
if 'success_message' in st.session_state and st.session_state['success_message']:
    st.success(st.session_state['success_message'])
    st.session_state['success_message'] = None

if 'logged_in' in st.session_state and st.session_state['logged_in']:
    st.info("Vous êtes déjà connecté.")
    st.page_link("streamlit_app.py", label="Retour à l'accueil", icon="🏠")
    st.stop() 

tab1, tab2 = st.tabs(["Connexion", "Inscription Membre"])

with tab1:
    st.subheader("Connexion")
    with st.form("login_form"):
        login_username = st.text_input("Nom d'utilisateur", key="login_user")
        login_password = st.text_input("Mot de passe", type="password", key="login_pass")
        login_submitted = st.form_submit_button("Se Connecter")

        if login_submitted:
            if not login_username or not login_password:
                st.warning("Veuillez entrer un nom d'utilisateur et un mot de passe.")
            elif not USER_API:
                 st.error("L'URL du service utilisateur n'est pas configurée.")
            else:
                api_url = f"{USER_API}/auth/login"
                payload = {"username": login_username, "password": login_password}
                try:
                    response = requests.post(api_url, json=payload, timeout=5) 
                    if response.status_code == 200:
                        user_data = response.json()
                        st.session_state['logged_in'] = True
                        st.session_state['user_info'] = user_data
                        st.session_state['success_message'] = "Connexion réussie !"
                        print(f"[Streamlit UI] Login OK pour {login_username}")
                        st.rerun() 
                    elif response.status_code == 401:
                        st.error("Nom d'utilisateur ou mot de passe incorrect.")
                        print(f"[Streamlit UI] Login échoué 401 pour {login_username}")
                    else:
                        error_msg = f"Erreur API ({response.status_code})"
                        try: error_msg = response.json().get('error', error_msg)
                        except: pass
                        st.error(f"Erreur de connexion : {error_msg}")
                        print(f"[Streamlit UI] Erreur API Login {response.status_code}: {response.text}")
                except requests.exceptions.RequestException as e:
                     st.error("Erreur de communication avec le service d'authentification.")
                     print(f"[Streamlit UI] Err comm login: {e}")

with tab2:
    st.subheader("Créer un Compte Membre")
    with st.form("register_form"):
        reg_username = st.text_input("Nom d'utilisateur choisi", key="reg_user", help="Minimum 3 caractères")
        reg_email = st.text_input("Adresse Email (optionnel)", key="reg_email")
        reg_password = st.text_input("Mot de passe", type="password", key="reg_pass", help="Minimum 6 caractères")
        reg_confirm_password = st.text_input("Confirmer le mot de passe", type="password", key="reg_confirm")
        st.markdown("**Choisissez votre abonnement (Simulation) :**")
        reg_sub_type = st.radio(
            "Formule",
            options=['monthly', 'annual'],
            format_func=lambda x: "Mensuel (5€/mois)" if x == 'monthly' else "Annuel (50€/an)",
            key="reg_sub",
            horizontal=True, 
            label_visibility="collapsed" 
        )
        register_submitted = st.form_submit_button("S'inscrire")

        if register_submitted:
            if not reg_username or not reg_password or not reg_confirm_password or not reg_sub_type:
                st.warning("Veuillez remplir tous les champs obligatoires.")
            elif len(reg_username) < 3:
                 st.warning("Le nom d'utilisateur doit faire au moins 3 caractères.")
            elif len(reg_password) < 6:
                 st.warning("Le mot de passe doit faire au moins 6 caractères.")
            elif reg_password != reg_confirm_password:
                 st.warning("Les mots de passe ne correspondent pas.")
            elif not USER_API:
                 st.error("L'URL du service utilisateur n'est pas configurée.")
            else:
                api_url = f"{USER_API}/users"
                payload = {
                    "username": reg_username,
                    "password": reg_password,
                    "role": "membre",
                    "email": reg_email or None,
                    "subscription_type": reg_sub_type
                }
                try:
                    response = requests.post(api_url, json=payload, timeout=5)
                    if response.status_code == 201:
                         st.session_state['success_message'] = f"Compte '{reg_username}' créé ! Simulation de paiement réussie automatiquement pour cette démo. Vous pouvez maintenant vous connecter."
                         print(f"[Streamlit UI] Inscription simulée OK pour {reg_username}")
                         st.rerun() 
                    elif response.status_code == 409:  
                        error_msg = "Erreur API"
                        try:
                            error_msg = response.json().get('error', error_msg)
                        except:
                            pass
                        st.warning(f"{error_msg}")  

                    else:  
                        error_msg = f"Erreur API ({response.status_code})"
                        try:
                            error_detail = response.json().get('error')
                            error_msg = error_detail if error_detail else error_msg
                        except:
                            pass
                        st.error(f"Erreur inscription: {error_msg}")
                        print(f"[Streamlit UI] Err API Create User {response.status_code}: {response.text}")

                except requests.exceptions.RequestException as e:
                    st.error("Erreur de communication avec le service d'inscription.")
                    print(f"[Streamlit UI] Err comm register: {e}")
