# api/document_service/models.

# --- Imports --- 
from sqlalchemy import Column, Integer, String, Boolean, Text # Importer depuis sqlalchemy
# from sqlalchemy.orm import declarative_base # On va utiliser la Base de database.py
from .database import Base # Importer la Base définie dans database.py
# --- Fin Imports --- 


class Document(Base):
    __tablename__ = "documents" # Nom de la table

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True) # Index sur titre pour recherche
    author = Column(String(150), nullable=True, index=True) # Index sur auteur
    summary = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='disponible') # Statut physique
    is_physical = Column(Boolean, default=True, nullable=False)
    is_digital = Column(Boolean, default=False, nullable=False)
    file_path = Column(String(300), nullable=True) # Nom fichier PDF
    cover_image_filename = Column(String(100), nullable=True) # Nom image

    def __repr__(self):
        fmts = ("P" if self.is_physical else "") + ("D" if self.is_digital else "")
        img = "I" if self.cover_image_filename else ""
        return f'<Doc {self.id} {self.title[:20]} ({fmts}{img})>'

