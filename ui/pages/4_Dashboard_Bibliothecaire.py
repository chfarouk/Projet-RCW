import streamlit as st
import requests
import os
from dotenv import load_dotenv
import uuid 
from werkzeug.utils import secure_filename 

load_dotenv()
DOC_API_URL = os.getenv("DOCUMENT_SERVICE_API_URL")

COVER_SAVE_PATH_UI = os.path.join('static', 'uploads', 'covers')
os.makedirs(COVER_SAVE_PATH_UI, exist_ok=True)


ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'} 

def allowed_file(filename):
    """Vérifie si l'extension du fichier est dans la liste autorisée."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

st.set_page_config(page_title="Dashboard Bibliothécaire", layout="wide")
st.title("📖 Tableau de Bord Bibliothécaire")

if not st.session_state.get('logged_in') or not st.session_state.get('user_info') or st.session_state['user_info'].get('role') != 'bibliothecaire':
    st.error("Accès réservé aux bibliothécaires."); st.page_link("pages/2_Login_Inscription.py", label="Connexion"); st.stop()

st.sidebar.success(f"Connecté: {st.session_state['user_info']['username']} (Bibliothécaire)")
if st.sidebar.button("Déconnexion", key="logout_biblio"):
    st.session_state['logged_in'] = False; st.session_state['user_info'] = None; st.session_state['success_message'] = "Déconnecté."; st.switch_page("streamlit_app.py")

if 'error_message' in st.session_state and st.session_state['error_message']: st.error(st.session_state['error_message']); st.session_state['error_message'] = None
if 'success_message' in st.session_state and st.session_state['success_message']: st.success(st.session_state['success_message']); st.session_state['success_message'] = None

st.subheader("Ajouter un Nouveau Document")

with st.form("add_document_form_v2", clear_on_submit=False): 
    title = st.text_input("Titre*", key="doc_title_add")
    author = st.text_input("Auteur", key="doc_author_add")
    summary = st.text_area("Résumé", key="doc_summary_add")

    st.write("**Formats Disponibles***")
    col1, col2 = st.columns(2)
    with col1: is_physical = st.checkbox("Version Physique", key="doc_phys_add", value=True)
    with col2: is_digital = st.checkbox("Version Numérique (PDF)", key="doc_digi_add")

    pdf_file_to_upload = None
    if is_digital:
         pdf_file_to_upload = st.file_uploader(
             "Choisir le fichier PDF*", type=["pdf"], key="doc_pdf_upload",
             help="Le fichier PDF du document numérique."
        )

    cover_image_to_upload = st.file_uploader(
        "Choisir l'image de couverture (optionnel)", type=["png", "jpg", "jpeg", "gif", "webp"],
        key="doc_cover_upload", help="Image qui sera affichée dans le catalogue."
    )

    submitted = st.form_submit_button("Ajouter le Document")

    if submitted:
        if not title: st.warning("Titre requis.")
        elif not is_physical and not is_digital: st.warning("Format requis.")
        elif is_digital and not pdf_file_to_upload: st.warning("Fichier PDF requis si Numérique coché.")
        elif not DOC_API_URL: st.error("URL service documents non configurée.")
        else:
            saved_pdf_filename = None
            saved_cover_filename = None
            api_error_occurred = False

            if is_digital and pdf_file_to_upload:
                pdf_upload_url = f"{DOC_API_URL}/documents/upload_pdf"
                files = {'pdf_file': (pdf_file_to_upload.name, pdf_file_to_upload.getvalue(), pdf_file_to_upload.type)}
                try:
                    print(f"[Streamlit UI] Upload PDF vers: {pdf_upload_url}")
                    response_pdf = requests.post(pdf_upload_url, files=files, timeout=15) 
                    if response_pdf.ok: 
                        saved_pdf_filename = response_pdf.json().get("filename")
                        print(f"[Streamlit UI] Upload PDF OK. Nom fichier: {saved_pdf_filename}")
                        if not saved_pdf_filename:
                             st.error("Erreur: L'API d'upload PDF n'a pas renvoyé de nom de fichier.")
                             api_error_occurred = True
                    else:
                        error_msg="Err API Upload PDF"; 
                        try: error_msg=response_pdf.json().get('detail', error_msg); 
                        except: pass
                        st.error(f"Erreur upload PDF: {error_msg} ({response_pdf.status_code})")
                        print(f"[Streamlit UI] Err API Upload PDF {response_pdf.status_code}: {response_pdf.text}")
                        api_error_occurred = True
                except requests.exceptions.RequestException as e:
                     st.error(f"Erreur communication upload PDF: {e}")
                     print(f"[Streamlit UI] Err comm upload PDF: {e}")
                     api_error_occurred = True

            if not api_error_occurred and cover_image_to_upload:
                 if allowed_file(cover_image_to_upload.name): 
                     original_filename = secure_filename(cover_image_to_upload.name)
                     extension = original_filename.rsplit('.', 1)[1].lower()
                     saved_image_name = f"{uuid.uuid4().hex}.{extension}"
                     save_path = os.path.join(COVER_SAVE_PATH_UI, saved_image_name)
                     try:
                         with open(save_path, "wb") as f:
                             f.write(cover_image_to_upload.getvalue())
                         saved_cover_filename = saved_image_name
                         print(f"[Streamlit UI] Image couverture sauvegardée localement: {saved_image_name}")
                     except Exception as e:
                          st.warning(f"Erreur sauvegarde image couverture locale: {e}")
                 else:
                      st.warning("Format d'image de couverture non autorisé.")

            if not api_error_occurred:
                payload = {
                    "title": title, "author": author or None, "summary": summary or None,
                    "is_physical": is_physical, "is_digital": is_digital,
                    "file_path": saved_pdf_filename if is_digital else None, 
                    "cover_image_filename": saved_cover_filename, 
                    "status": "disponible"
                }
                create_doc_api_url = f"{DOC_API_URL}/documents"
                try:
                    print(f"[Streamlit UI] Appel API Création Metadonnées Doc: {create_doc_api_url}")
                    response_create = requests.post(create_doc_api_url, json=payload, timeout=5)
                    if response_create.status_code == 201:
                         st.session_state['success_message'] = f"Document '{title}' ajouté avec succès !"
                         print(f"[Streamlit UI] Création Metadonnées Doc OK: {response_create.json()}")
                         st.rerun()
                    else:
                         error_msg = "Err API Créa Doc"; 
                         try: error_msg = response_create.json().get('error', error_msg); 
                         except: pass
                         st.error(f"Erreur création document: {error_msg} ({response_create.status_code})")
                         print(f"[Streamlit UI] Err API Create Doc Meta {response_create.status_code}: {response_create.text}")
                except requests.exceptions.RequestException as e:
                     st.error(f"Erreur communication création document: {e}")
                     print(f"[Streamlit UI] Err comm create doc meta: {e}")

st.markdown("---")
st.info("La modification/suppression se fait via le Catalogue.")
