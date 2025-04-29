import streamlit as st
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()
DOC_API_URL = os.getenv("DOCUMENT_SERVICE_API_URL") 


st.set_page_config(page_title="Catalogue", layout="wide")
st.title("📖 Catalogue des Documents") 
st.divider()

if not st.session_state.get('logged_in', False):
    st.warning("Veuillez vous connecter pour accéder au catalogue.")
    st.page_link("pages/2_Login_Inscription.py", label="Se connecter / S'inscrire", icon="🔑")
    st.stop()

if 'error_message' in st.session_state and st.session_state['error_message']:
    st.error(st.session_state['error_message'])
    st.session_state['error_message'] = None
if 'success_message' in st.session_state and st.session_state['success_message']:
    st.success(st.session_state['success_message'])
    st.session_state['success_message'] = None

documents = []
api_error = None 

if not DOC_API_URL:
    api_error = "L'URL du service documents n'est pas configurée."
    st.error(api_error) 
else:
    try:
        api_endpoint = f"{DOC_API_URL}/documents"
        response = requests.get(api_endpoint,  timeout=5)

        if response.ok:
            documents = response.json()
        else:
            error_msg = f"Erreur API ({response.status_code})"
            try:
                error_detail = response.json().get('error', response.text)
                if error_detail: error_msg = f"Erreur API: {error_detail}"
            except: pass
            api_error = error_msg 
            print(f"[Streamlit UI] Err API Catalogue: {api_error}")

    except requests.exceptions.RequestException as e:
        api_error = f"Erreur de communication avec l'API : {e}"
        print(f"[Streamlit UI] Err comm catalogue: {e}")

if api_error:
    if DOC_API_URL: 
        st.error(api_error)
    st.info("Aucun document dans le catalogue pour le moment.")

else:
    num_columns = 3
    cols = st.columns(num_columns)
    for i, doc in enumerate(documents):
        col_index = i % num_columns 
        with cols[col_index]:
            with st.container(border=True, height=550): 
                doc_id = doc.get('id')
                if not doc_id: continue
                cover_filename = doc.get('cover_image_filename')
                placeholder_path = os.path.join("static", "images", "placeholder_cover.png")
                image_path = placeholder_path 

                if cover_filename:
                    potential_path = os.path.join("static", "uploads", "covers", cover_filename)
                    if os.path.exists(potential_path):
                        image_path = potential_path
                    else:
                        print(f"[Streamlit Catalogue] Image non trouvée: {potential_path}, utilise placeholder.")

                st.image(image_path, use_container_width=True, output_format='auto')

                detail_page_link = f"Document_Detail?doc_id={doc_id}" 

                st.markdown(f'<h5><a href="{detail_page_link}" target="_self" style="text-decoration: none; color: inherit;">{doc.get("title", "Titre inconnu")}</a></h5>', unsafe_allow_html=True)
                st.caption(f"par {doc.get('author', 'Auteur inconnu')} (ID: {doc_id})")

                formats = [];
                if doc.get('is_physical'): formats.append("Physique")
                if doc.get('is_digital'): formats.append("Numérique")
                st.write(f"**Formats:** {', '.join(formats) if formats else 'N/A'}")

                if doc.get('is_physical'):
                    status = doc.get('status', '?').capitalize(); color = "green" if status == "Disponible" else "orange" if status == "Emprunte" else "grey"
                    st.markdown(f"**Dispo. Physique:** :{color}[{status}]")

                st.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True)

                btn_cols = st.columns([2,1,1]) if st.session_state.get('user_info', {}).get('role') == 'bibliothecaire' else st.columns(1)

                with btn_cols[0]:
                 button_detail_key = f"detail_{doc_id}"
                 if st.button("Voir Détails", key=button_detail_key, use_container_width=True, type="primary"):
                     st.session_state['doc_id_to_view'] = doc_id 
                     st.switch_page("pages/Document_Detail.py")

                if st.session_state.get('user_info', {}).get('role') == 'bibliothecaire':
                    with btn_cols[1]: 
                        if st.button("✏️", key=f"edit_{doc_id}", use_container_width=True, help="Modifier"):
                            st.session_state['doc_id_to_edit'] = doc_id
                            st.switch_page("pages/Edit_Document.py")
                    with btn_cols[2]: 
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
                                        st.rerun() 
                                   except requests.exceptions.RequestException as e: st.session_state['error_message'] = f"Err comm suppression: {e}"; st.rerun()
