# ui/streamlit_app.py
import streamlit as st
import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement (URLs des API)
load_dotenv()
USER_API = os.getenv("USER_SERVICE_API_URL")
DOC_API = os.getenv("DOCUMENT_SERVICE_API_URL")
LOAN_API = os.getenv("LOAN_SERVICE_API_URL")

# --- Configuration de la Page Streamlit ---
st.set_page_config(
    page_title="BiblioTeccart",
    page_icon="📚", # Ou un emoji/lien vers favicon
    layout="wide", # Utiliser toute la largeur
    initial_sidebar_state="collapsed" # Afficher la barre latérale par défaut
)

# --- Initialisation ROBUSTE de l'État de Session ---
# Vérifier chaque clé nécessaire individuellement
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'error_message' not in st.session_state:
    st.session_state['error_message'] = None
if 'success_message' not in st.session_state:
    st.session_state['success_message'] = None
# --- FIN Initialisation Robuste ---


# --- Affichage des Messages Flash (Simulé) ---
# Maintenant, on peut vérifier la valeur en toute sécurité
if st.session_state['error_message']:
    st.error(st.session_state['error_message'])
    st.session_state['error_message'] = None # Effacer après affichage
if st.session_state['success_message']:
    st.success(st.session_state['success_message'])
    st.session_state['success_message'] = None # Effacer après affichage

# --- Contenu de la Page d'Accueil (streamlit_app.py) ---
st.title("📚 Bienvenue sur BiblioTeccart !")

st.markdown("""
Votre plateforme de gestion de bibliothèque intelligente.

*   Utilisez la barre latérale à gauche pour naviguer entre les sections.
*   Connectez-vous pour accéder au catalogue et à votre tableau de bord.
""")

# Afficher des infos différentes si connecté ou non
if st.session_state['logged_in'] and st.session_state['user_info']:
     st.sidebar.success(f"Connecté en tant que : {st.session_state['user_info'].get('username', '')} ({st.session_state['user_info'].get('role', '')})")
     # Ajouter un bouton de déconnexion dans la barre latérale
     if st.sidebar.button("Déconnexion"):
         # Effacer les informations de session
         st.session_state['logged_in'] = False
         st.session_state['user_info'] = None
         st.session_state['success_message'] = "Vous avez été déconnecté."
         st.rerun() # Forcer le rechargement de la page pour refléter la déconnexion
else:
    st.sidebar.info("Vous n'êtes pas connecté.")
    st.markdown("Veuillez vous connecter ou vous inscrire via la page 'Login / Inscription'.")


st.subheader("À propos")
st.write("Ce projet vise à créer une interface moderne pour une bibliothèque, en utilisant une architecture microservices avec FastAPI pour le backend et Streamlit pour cette interface utilisateur.")

# On pourrait afficher ici des nouveautés ou stats publiques si on avait une API pour ça

# --- Pied de page simple ---
st.markdown("---")
st.caption("© BiblioTeccart")