import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()
USER_API = os.getenv("USER_SERVICE_API_URL")
DOC_API = os.getenv("DOCUMENT_SERVICE_API_URL")
LOAN_API = os.getenv("LOAN_SERVICE_API_URL")

st.set_page_config(
    page_title="BiblioTeccart",
    page_icon="📚", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'error_message' not in st.session_state:
    st.session_state['error_message'] = None
if 'success_message' not in st.session_state:
    st.session_state['success_message'] = None
    
if st.session_state['error_message']:
    st.error(st.session_state['error_message'])
    st.session_state['error_message'] = None 
if st.session_state['success_message']:
    st.success(st.session_state['success_message'])
    st.session_state['success_message'] = None 

st.title("📚 Bienvenue sur BiblioTeccart !")

st.markdown("""
Votre plateforme de gestion de bibliothèque intelligente.

*   Utilisez la barre latérale à gauche pour naviguer entre les sections.
*   Connectez-vous pour accéder au catalogue et à votre tableau de bord.
""")

if st.session_state['logged_in'] and st.session_state['user_info']:
     st.sidebar.success(f"Connecté en tant que : {st.session_state['user_info'].get('username', '')} ({st.session_state['user_info'].get('role', '')})")
     if st.sidebar.button("Déconnexion"):
         st.session_state['logged_in'] = False
         st.session_state['user_info'] = None
         st.session_state['success_message'] = "Vous avez été déconnecté."
         st.rerun() 
else:
    st.sidebar.info("Vous n'êtes pas connecté.")
    st.markdown("Veuillez vous connecter ou vous inscrire via la page 'Login / Inscription'.")

st.subheader("À propos")
st.write("Ce projet vise à créer une interface moderne pour une bibliothèque, en utilisant une architecture microservices avec FastAPI pour le backend et Streamlit pour cette interface utilisateur.")

st.markdown("---")
st.caption("© BiblioTeccart")
