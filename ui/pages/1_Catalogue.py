# ui/pages/1_Catalogue.py (Version avec Boutons Admin fonctionnels)
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urljoin

# --- Configuration initiale ---
load_dotenv()
DOC_API_URL = os.getenv("DOCUMENT_SERVICE_API_URL") # Ex: http://127.0.0.1:8002/api


st.set_page_config(page_title="Catalogue", layout="wide")
st.title("📖 Catalogue des Documents") # Emoji ajouté
st.divider()

# --- Vérification Connexion ---
if not st.session_state.get('logged_in', False):
    st.warning("Veuillez vous connecter pour accéder au catalogue.")
    st.page_link("pages/2_Login_Inscription.py", label="Se connecter / S'inscrire", icon="🔑")
    st.stop()

# --- Affichage Messages Flash (Simulé) ---
# Important de les afficher ici aussi car on revient sur cette page après certaines actions
if 'error_message' in st.session_state and st.session_state['error_message']:
    st.error(st.session_state['error_message'])
    st.session_state['error_message'] = None
if 'success_message' in st.session_state and st.session_state['success_message']:
    st.success(st.session_state['success_message'])
    st.session_state['success_message'] = None

# --- Récupération des documents depuis l'API (CORRIGÉ) ---
documents = []
api_error = None # Initialiser à None au début

if not DOC_API_URL:
    # Assigner à la variable globale au script
    api_error = "L'URL du service documents n'est pas configurée."
    st.error(api_error) # Afficher l'erreur immédiatement ici
else:
    try:
        api_endpoint = f"{DOC_API_URL}/documents"
        response = requests.get(api_endpoint,  timeout=5)

        if response.ok:
            documents = response.json()
        else:
            # Assigner à la variable globale au script
            error_msg = f"Erreur API ({response.status_code})"
            try:
                error_detail = response.json().get('error', response.text)
                if error_detail: error_msg = f"Erreur API: {error_detail}"
            except: pass
            api_error = error_msg # Mettre à jour api_error ici
            print(f"[Streamlit UI] Err API Catalogue: {api_error}")

    except requests.exceptions.RequestException as e:
        # Assigner à la variable globale au script
        api_error = f"Erreur de communication avec l'API : {e}"
        print(f"[Streamlit UI] Err comm catalogue: {e}")

# --- Affichage du contenu ---
# La variable api_error existera toujours (soit None, soit avec une erreur)
if api_error:
    # Afficher l'erreur si elle n'a pas déjà été affichée (cas de l'URL manquante)
    if DOC_API_URL: # N'afficher que si ce n'est pas l'erreur d'URL
        st.error(api_error)
    st.info("Aucun document dans le catalogue pour le moment.")

else:
    # --- Affichage des documents (le code de la boucle reste le même) ---
    num_columns = 3
    cols = st.columns(num_columns)
    for i, doc in enumerate(documents):
        col_index = i % num_columns # Répartir dans les colonnes 0, 1, 2, 0, 1, 2...
        with cols[col_index]:
            # Utiliser un container pour chaque carte de document
            with st.container(border=True, height=550): # Hauteur fixe optionnelle
                doc_id = doc.get('id')
                if not doc_id: continue

                # --- Affichage Image (Chemin Local) ---
                cover_filename = doc.get('cover_image_filename')
                placeholder_path = os.path.join("static", "images", "placeholder_cover.png")
                image_path = placeholder_path # Défaut

                if cover_filename:
                    potential_path = os.path.join("static", "uploads", "covers", cover_filename)
                    if os.path.exists(potential_path):
                        image_path = potential_path
                    else:
                        print(f"[Streamlit Catalogue] Image non trouvée: {potential_path}, utilise placeholder.")

                # Afficher l'image (non cliquable directement avec st.image)
                st.image(image_path, use_container_width=True, output_format='auto')

                # --- Informations document ---
                # Construire l'URL de la page détail
                detail_page_link = f"Document_Detail?doc_id={doc_id}" # Chemin relatif pour st.page_link

                # Titre cliquable (utiliser markdown pour le lien)
                st.markdown(f'<h5><a href="{detail_page_link}" target="_self" style="text-decoration: none; color: inherit;">{doc.get("title", "Titre inconnu")}</a></h5>', unsafe_allow_html=True)
                st.caption(f"par {doc.get('author', 'Auteur inconnu')} (ID: {doc_id})")

                formats = [];
                if doc.get('is_physical'): formats.append("Physique")
                if doc.get('is_digital'): formats.append("Numérique")
                st.write(f"**Formats:** {', '.join(formats) if formats else 'N/A'}")

                # --- Statut Physique ---
                if doc.get('is_physical'):
                    status = doc.get('status', '?').capitalize(); color = "green" if status == "Disponible" else "orange" if status == "Emprunte" else "grey"
                    st.markdown(f"**Dispo. Physique:** :{color}[{status}]")

                # Espace pour pousser les boutons vers le bas si hauteur fixe
                st.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True)

                # --- Boutons ---
                btn_cols = st.columns([2,1,1]) if st.session_state.get('user_info', {}).get('role') == 'bibliothecaire' else st.columns(1)

                with btn_cols[0]:
                 # --- REMPLACER st.page_link PAR CECI ---
                 # Utiliser st.button qui stocke l'ID et change de page
                 button_detail_key = f"detail_{doc_id}"
                 if st.button("Voir Détails", key=button_detail_key, use_container_width=True, type="primary"):
                     st.session_state['doc_id_to_view'] = doc_id # Stocker l'ID à voir
                     st.switch_page("pages/Document_Detail.py") # Changer de page


                # --- Boutons Admin (Bibliothécaire) ---
                if st.session_state.get('user_info', {}).get('role') == 'bibliothecaire':
                    with btn_cols[1]: # Modifier
                        if st.button("✏️", key=f"edit_{doc_id}", use_container_width=True, help="Modifier"):
                            st.session_state['doc_id_to_edit'] = doc_id
                            st.switch_page("pages/Edit_Document.py")
                    with btn_cols[2]: # Supprimer
                         with st.popover("🗑️", use_container_width=True):
                              st.markdown(f"**Supprimer '{doc.get('title', '')}' ?**")
                              st.warning("Action irréversible !")
                              if st.button("Confirmer Suppression", key=f"confirm_delete_{doc_id}", type="primary"):
                                   delete_api_url = f"{DOC_API_URL}/documents/{doc_id}"
                                   try:
                                        response = requests.delete(delete_api_url, timeout=5)
                                        if response.status_code == 204: st.session_state['success_message'] = f"Doc ID {doc_id} supprimé."; st.rerun()
                                        elif response.status_code == 404: st.session_state['error_message'] = "Doc non trouvé (API)."
                                        else: error_msg="Err API"; 
                                        try: error_msg=response.json().get('error', f'Code {response.status_code}'); 
                                        except: pass; st.session_state['error_message'] = f"Erreur suppression: {error_msg}"
                                        st.rerun() # Recharger même si erreur pour afficher message
                                   except requests.exceptions.RequestException as e: st.session_state['error_message'] = f"Err comm suppression: {e}"; st.rerun()