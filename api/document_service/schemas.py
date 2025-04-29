from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List 

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, description="Titre du document")
    author: Optional[str] = Field(None, description="Auteur du document")
    summary: Optional[str] = Field(None, description="Résumé du document")
    status: Optional[str] = Field("disponible", description="Statut physique (disponible, emprunte)")
    is_physical: bool = Field(True, description="Indique si une copie physique existe")
    is_digital: bool = Field(False, description="Indique si une version numérique existe")
    file_path: Optional[str] = Field(None, description="Nom du fichier PDF (si numérique)")
    cover_image_filename: Optional[str] = Field(None, description="Nom du fichier image de couverture")

class DocumentCreate(DocumentBase):
    pass 

class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None 
    is_physical: Optional[bool] = None
    is_digital: Optional[bool] = None
    file_path: Optional[str] = None
    cover_image_filename: Optional[str] = None 

class DocumentOut(DocumentBase):
    id: int
    cover_image_url: Optional[str] = Field(None, description="URL pour accéder à l'image de couverture")
    pdf_access_url: Optional[str] = Field(None, description="URL pour initier l'accès au PDF (via Loan Service)")

    model_config = ConfigDict(from_attributes=True) 
