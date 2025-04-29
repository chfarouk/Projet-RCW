import streamlit as st
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()
DOC_API_URL = os.getenv("DOCUMENT_SERVICE_API_URL")
GATEWAY_URL = os.getenv("GATEWAY_STATIC_URL", "http://127.0.0.1:5000") 

st.set_page_config(page_title="Modifier Document", layout="wide")

st.title("📝 Modifier le Document")

if not st.session_state.get('logged_in') or not st.session_state.get('user_info') or st.session_state['user_info'].get('role') != 'bibliothecaire':
    st.error("Accès réservé aux bibliothécaires.")
    st.page_link("streamlit_app.py", label="Retour à l'accueil", icon="🏠")
    st.stop()

doc_id_to_edit = st.session_state.get("doc_id_to_edit")
if not doc_id_to_edit:
    st.error("Aucun document sélectionné pour l'édition."); st.page_link("pages/1_Catalogue.py", label="Retour Catalogue"); st.stop()

st.info(f"Modification du Document ID : {doc_id_to_edit}")

doc_data = None; api_error = None
if not DOC_API_URL: api_error = "URL service documents non configurée."
else:
    try:
        api_url = f"{DOC_API_URL}/documents/{doc_id_to_edit}"
        response = requests.get(api_url, timeout=5)
        if response.ok: doc_data = response.json()
        elif response.status_code == 404: api_error = "Document non trouvé."
        else: api_error = f"Erreur API ({response.status_code})"; 
        try: api_error += f": {response.json().get('error', response.text)}"; 
        except: pass
    except requests.exceptions.RequestException as e: api_error = f"Erreur comm service docs: {e}"

if api_error: st.error(api_error); st.stop()
if not doc_data: st.error("Impossible de charger les données du document."); st.stop()

with st.form("edit_document_form"): 
    st.subheader("Informations du Document")
    title = st.text_input("Titre*", key="edit_title", value=doc_data.get('title', ''))
    author = st.text_input("Auteur", key="edit_author", value=doc_data.get('author', ''))
    summary = st.text_area("Résumé", key="edit_summary", value=doc_data.get('summary', ''))

    current_status = doc_data.get('status', 'disponible') 
    status_to_send = current_status 
    if doc_data.get('is_physical'):
        st.write("**Statut Physique Actuel :** ", current_status.capitalize())
        st.caption("Le statut physique est géré via les enregistrements de prêt/retour.")
    else:
         status_to_send = 'disponible' 

    st.write("**Formats Disponibles***")
    col1_fmt, col2_fmt = st.columns(2)
    with col1_fmt:
        is_physical = st.checkbox("Version Physique", key="edit_phys", value=doc_data.get('is_physical', True))
    with col2_fmt:
        is_digital = st.checkbox("Version Numérique (PDF)", key="edit_digi", value=doc_data.get('is_digital', False))

    pdf_file_name = None
    if is_digital:
         pdf_file_name = st.text_input("Nom du fichier PDF*", key="edit_pdf_name", value=doc_data.get('file_path', ''), placeholder="ex: livre.pdf")

    st.write("**Image de Couverture**")
    current_image_filename = doc_data.get('cover_image_filename')
    if current_image_filename:
        img_url = urljoin(GATEWAY_URL, f"/static/uploads/covers/{current_image_filename}")
        st.image(img_url, width=100, caption="Image actuelle")
        remove_cover = st.checkbox("Supprimer l'image actuelle", key="edit_remove_cover")
    else:
         st.caption("Aucune image de couverture actuellement.")
         remove_cover = False
    cover_image_name_to_send = current_image_filename
    if remove_cover: cover_image_name_to_send = None

    submitted = st.form_submit_button("Enregistrer les Modifications")

    if submitted:
        st.write("Formulaire soumis ! Tentative d'enregistrement...") 
        if not title: st.warning("Titre requis.")
        elif not is_physical and not is_digital: st.warning("Format requis.")
        elif is_digital and not pdf_file_name: st.warning("Nom PDF requis.")
        elif not DOC_API_URL: st.error("URL service docs non configurée.")
        else:
            payload = {
                "title": title, "author": author or None, "summary": summary or None,
                "is_physical": is_physical, "is_digital": is_digital,
                "file_path": pdf_file_name if is_digital else None,
                "cover_image_filename": cover_image_name_to_send,
                "status": status_to_send
            }
            api_url_put = f"{DOC_API_URL}/documents/{doc_id_to_edit}"

            try:
                print(f"[Streamlit UI] Appel API Modif Doc: PUT {api_url_put}")
                response = requests.put(api_url_put, json=payload, timeout=5)

                if response.ok:
                    st.session_state['success_message'] = f"Document '{title}' modifié !"
                    if 'doc_id_to_edit' in st.session_state: del st.session_state['doc_id_to_edit']
                    st.switch_page("pages/1_Catalogue.py")
                else:
                     error_msg = f"Err API ({response.status_code})"; 
                     try: error_detail = response.json().get('error'); error_msg = error_detail if error_detail else error_msg; 
                     except: pass
                     st.error(f"Erreur modification: {error_msg}")
                     print(f"[Streamlit UI] Err API Edit Doc {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                 st.error(f"Err comm service docs: {e}")
                 print(f"[Streamlit UI] Err comm edit doc: {e}")


st.divider()
st.page_link("pages/1_Catalogue.py", label="Annuler et Retourner au Catalogue", icon="📖")
