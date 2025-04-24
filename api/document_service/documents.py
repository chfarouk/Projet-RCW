# api/document_service/api/endpoints/documents.py

# --- Imports --- 
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import JSONResponse
# Chemin relatif pour importer depuis le même service
from . import crud, models, schemas
from .database import get_db
from werkzeug.utils import secure_filename
try:
    from main import PDF_STORAGE_PATH_DOC_SERVICE
except ImportError:
    # Définir un chemin par défaut si l'import échoue (ex: pendant tests)
    print("WARN: Impossible d'importer PDF_STORAGE_PATH_DOC_SERVICE depuis main.py dans documents.py")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    PDF_STORAGE_PATH_DOC_SERVICE = os.path.join(current_dir, '..', 'instance', 'uploads', 'pdfs') # Chemin relatif par défaut
    os.makedirs(PDF_STORAGE_PATH_DOC_SERVICE, exist_ok=True)
# --- Fin Imports --- 


router = APIRouter()




# --- Endpoint pour LIRE les documents (avec filtres) ---
@router.get("/", response_model=List[schemas.DocumentOut])
def read_documents(
    q: Optional[str] = Query(None, alias="search", description="Terme de recherche (titre/auteur)"),
    is_physical: Optional[bool] = Query(None),
    is_digital: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db)
):
    documents = crud.get_documents(db, skip=skip, limit=limit, search=q,
    is_physical=is_physical, is_digital=is_digital, status=status)
    return documents
# --- Fin Endpoint pour LIRE les documents (avec filtres) ---


# --- Endpoint pour COMPTER les documents ---
@router.get("/count", response_model=dict) # Renvoie un simple dict {"count": N}
def count_all_documents(db: Session = Depends(get_db)):
     count = crud.count_documents(db=db)
     return {"count": count}
# --- Fin Endpoint pour COMPTER les documents ---


# --- Endpoint pour CRÉER un document ---
@router.post("/", response_model=schemas.DocumentOut, status_code=status.HTTP_201_CREATED)
def create_new_document(doc_data: schemas.DocumentCreate, db: Session = Depends(get_db)):
    if doc_data.is_digital and not doc_data.file_path:
         raise HTTPException(status_code=400, detail="file_path requis pour doc numérique")
    if not doc_data.is_physical and not doc_data.is_digital:
         raise HTTPException(status_code=400, detail="Au moins un format requis")
    try:
        created_doc = crud.create_document(db=db, doc_data=doc_data)
        print(f"[Doc Service API] Document créé: ID {created_doc.id}")
        return created_doc
    except Exception as e:
         print(f"[Doc Service API] Err interne création: {e}")
         raise HTTPException(status_code=500, detail="Erreur interne serveur")
# --- Fin Endpoint pour CRÉER un document ---


# --- Endpoint pour LIRE UN document ---
@router.get("/{document_id}", response_model=schemas.DocumentOut)
def read_document(document_id: int, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, document_id=document_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    print(f"[Doc Service API] Détail doc demandé: ID {document_id}")
     # Construire URLs avant de renvoyer
    # db_doc.cover_image_url = ...
    return db_doc
# --- Fin Endpoint pour LIRE UN document ---


# --- Endpoint pour METTRE À JOUR un document ---
@router.put("/{document_id}", response_model=schemas.DocumentOut) 
def update_existing_document(document_id: int, doc_update: schemas.DocumentUpdate, db: Session = Depends(get_db)): # Utiliser PUT pour l'instant
     # Validation cohérence
     update_data = doc_update.model_dump(exclude_unset=True)
     if update_data.get('is_digital') == False and 'file_path' in update_data and update_data['file_path'] is not None:
          pass
     if update_data.get('is_digital') == True and ('file_path' not in update_data or not update_data['file_path']):
         pass # La logique CRUD devrait gérer

     updated_doc = crud.update_document(db=db, document_id=document_id, doc_update_data=doc_update)
     if updated_doc is None:
         raise HTTPException(status_code=404, detail="Document non trouvé pour mise à jour")
     print(f"[Doc Service API] Document mis à jour: ID {document_id}")
     return updated_doc
# --- Fin Endpoint pour METTRE À JOUR un document ---


# --- Endpoint pour SUPPRIMER un document ---
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_document(document_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return Response(status_code=status.HTTP_204_NO_CONTENT) 
# --- Fin Endpoint pour SUPPRIMER un document ---

# --- Endpoint UPLOAD PDF (Chemin: "/upload_pdf") ---
# Deviendra POST /api/documents/upload_pdf
@router.post("/upload_pdf", tags=["Uploads"]) # Juste le chemin relatif ici
async def upload_pdf_file(pdf_file: UploadFile = File(..., description="Le fichier PDF à uploader")):
    if not pdf_file.filename.lower().endswith('.pdf'):
         raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont autorisés.")
    original_filename = secure_filename(pdf_file.filename)
    unique_filename = f"{uuid.uuid4().hex}.pdf"
    # Utiliser la variable importée
    save_path = os.path.join(PDF_STORAGE_PATH_DOC_SERVICE, unique_filename)
    try:
        with open(save_path, "wb") as buffer:
            content = await pdf_file.read()
            buffer.write(content)
        print(f"[Doc Service API] PDF sauvegardé: {unique_filename}")
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"filename": unique_filename})
    except Exception as e:
        print(f"[Doc Service API] Err sauvegarde PDF {unique_filename}: {e}")
        try: os.remove(save_path); 
        except OSError: pass
        raise HTTPException(status_code=500, detail=f"Err interne sauvegarde PDF: {e}")

# --- Endpoint CRÉER Document (POST /api/documents) ---
# Reste globalement le même, reçoit les métadonnées en JSON
@router.post("/api/documents", response_model=schemas.DocumentOut, status_code=status.HTTP_201_CREATED, tags=["Documents CRUD"])
def create_new_document(doc_data: schemas.DocumentCreate, db: Session = Depends(get_db)):
    # Validations (rôle, format, etc.)
    if doc_data.is_digital and not doc_data.file_path:
         raise HTTPException(status_code=400, detail="file_path (nom du fichier PDF uploadé) requis pour doc numérique")
    if not doc_data.is_physical and not doc_data.is_digital:
         raise HTTPException(status_code=400, detail="Au moins un format requis")

    # Vérifier que le fichier PDF mentionné existe (si numérique) ? Non, on fait confiance au nom fourni.
    # Vérifier que l'image mentionnée existe ? Non, géré par Gateway/UI.

    try:
        created_doc = crud.create_document(db=db, doc_data=doc_data)
        print(f"[Doc Service API] Metadonnées Document créées: ID {created_doc.id}")
        # Ajouter les URLs construites ici ou laisser Pydantic/Gateway ? Laisser Gateway pour flexibilité.
        return created_doc
    except Exception as e:
         print(f"[Doc Service API] Err interne création doc meta: {e}")
         raise HTTPException(status_code=500, detail="Erreur interne création document")


