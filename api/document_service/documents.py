import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import JSONResponse
from . import crud, models, schemas
from .database import get_db
from werkzeug.utils import secure_filename
try:
    from main import PDF_STORAGE_PATH_DOC_SERVICE
except ImportError:
    print("WARN: Impossible d'importer PDF_STORAGE_PATH_DOC_SERVICE depuis main.py dans documents.py")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    PDF_STORAGE_PATH_DOC_SERVICE = os.path.join(current_dir, '..', 'instance', 'uploads', 'pdfs') 
    os.makedirs(PDF_STORAGE_PATH_DOC_SERVICE, exist_ok=True)

router = APIRouter()

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

@router.get("/count", response_model=dict) 
def count_all_documents(db: Session = Depends(get_db)):
     count = crud.count_documents(db=db)
     return {"count": count}

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

@router.get("/{document_id}", response_model=schemas.DocumentOut)
def read_document(document_id: int, db: Session = Depends(get_db)):
    db_doc = crud.get_document(db, document_id=document_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    print(f"[Doc Service API] Détail doc demandé: ID {document_id}")
    return db_doc
    
@router.put("/{document_id}", response_model=schemas.DocumentOut) 
def update_existing_document(document_id: int, doc_update: schemas.DocumentUpdate, db: Session = Depends(get_db)): 
     update_data = doc_update.model_dump(exclude_unset=True)
     if update_data.get('is_digital') == False and 'file_path' in update_data and update_data['file_path'] is not None:
          pass
     if update_data.get('is_digital') == True and ('file_path' not in update_data or not update_data['file_path']):
         pass 

     updated_doc = crud.update_document(db=db, document_id=document_id, doc_update_data=doc_update)
     if updated_doc is None:
         raise HTTPException(status_code=404, detail="Document non trouvé pour mise à jour")
     print(f"[Doc Service API] Document mis à jour: ID {document_id}")
     return updated_doc

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_document(document_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return Response(status_code=status.HTTP_204_NO_CONTENT) 

@router.post("/upload_pdf", tags=["Uploads"]) 
async def upload_pdf_file(pdf_file: UploadFile = File(..., description="Le fichier PDF à uploader")):
    if not pdf_file.filename.lower().endswith('.pdf'):
         raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont autorisés.")
    original_filename = secure_filename(pdf_file.filename)
    unique_filename = f"{uuid.uuid4().hex}.pdf"
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

@router.post("/api/documents", response_model=schemas.DocumentOut, status_code=status.HTTP_201_CREATED, tags=["Documents CRUD"])
def create_new_document(doc_data: schemas.DocumentCreate, db: Session = Depends(get_db)):
    if doc_data.is_digital and not doc_data.file_path:
         raise HTTPException(status_code=400, detail="file_path (nom du fichier PDF uploadé) requis pour doc numérique")
    if not doc_data.is_physical and not doc_data.is_digital:
         raise HTTPException(status_code=400, detail="Au moins un format requis")
    try:
        created_doc = crud.create_document(db=db, doc_data=doc_data)
        print(f"[Doc Service API] Metadonnées Document créées: ID {created_doc.id}")
        return created_doc
    except Exception as e:
         print(f"[Doc Service API] Err interne création doc meta: {e}")
         raise HTTPException(status_code=500, detail="Erreur interne création document")


