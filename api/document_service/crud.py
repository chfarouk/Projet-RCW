# api/document_service/crud.py

# --- Imports ---
from sqlalchemy.orm import Session
from sqlalchemy import or_, func # Importer pour recherche et count
from . import models, schemas # Import local
from typing import Optional, List
import os # Pour basename lors de l'update
# --- Fin Imports ---


# --- Lire les documents ---
def get_document(db: Session, document_id: int) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.id == document_id).first()

def get_documents(db: Session, skip: int = 0, limit: int = 100,
                   search: Optional[str] = None,
                   is_physical: Optional[bool] = None,
                   is_digital: Optional[bool] = None,
                   status: Optional[str] = None) -> List[models.Document]:
    query = db.query(models.Document)
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(models.Document.title.ilike(search_term), models.Document.author.ilike(search_term)))
    if is_physical is not None:
         query = query.filter(models.Document.is_physical == is_physical)
    if is_digital is not None:
         query = query.filter(models.Document.is_digital == is_digital)
    if status:
         query = query.filter(models.Document.status == status)

    return query.order_by(models.Document.title).offset(skip).limit(limit).all()

def count_documents(db: Session) -> int:
     return db.query(func.count(models.Document.id)).scalar() or 0
# --- Fin Lire les documents ---


# --- Créer un document ---
def create_document(db: Session, doc_data: schemas.DocumentCreate) -> models.Document:
    # Nettoyer les chemins de fichiers avant de créer l'objet modèle
    clean_file_path = os.path.basename(doc_data.file_path) if doc_data.file_path else None
    clean_cover_filename = os.path.basename(doc_data.cover_image_filename) if doc_data.cover_image_filename else None

    db_doc = models.Document(
        title=doc_data.title,
        author=doc_data.author,
        summary=doc_data.summary,
        status=doc_data.status or 'disponible',
        is_physical=doc_data.is_physical,
        is_digital=doc_data.is_digital,
        file_path=clean_file_path if doc_data.is_digital else None, # S'assurer que path est null si pas digital
        cover_image_filename=clean_cover_filename
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc
# --- Fin Créer un document ---


# --- Mettre à jour un document ---
def update_document(db: Session, document_id: int, doc_update_data: schemas.DocumentUpdate) -> Optional[models.Document]:
    db_doc = get_document(db, document_id)
    if not db_doc:
        return None

    update_data = doc_update_data.model_dump(exclude_unset=True) # Seulement les champs fournis

    for key, value in update_data.items():
        # Nettoyer les chemins si présents dans l'update
        if key == 'file_path' and value is not None:
            value = os.path.basename(value)
        if key == 'cover_image_filename' and value is not None:
             value = os.path.basename(value)
        setattr(db_doc, key, value)

    # Assurer la cohérence : pas de file_path si pas digital
    if not db_doc.is_digital:
         db_doc.file_path = None

    db.commit()
    db.refresh(db_doc)
    return db_doc
# --- Fin Mettre à jour un document ---


# --- Supprimer un document ---
def delete_document(db: Session, document_id: int) -> bool:
     db_doc = get_document(db, document_id)
     if db_doc:
         db.delete(db_doc)
         db.commit()
         return True
     return False
# --- Fin Supprimer un document ---