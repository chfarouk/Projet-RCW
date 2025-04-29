from pydantic import BaseModel, EmailStr, Field, ConfigDict 
from typing import Optional
from datetime import datetime 

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, description="Nom d'utilisateur unique (3 caractères min)")
    password: str = Field(..., min_length=6, description="Mot de passe (6 caractères min)")
    role: str = Field(..., description="Rôle de l'utilisateur (ex: membre, bibliothecaire, gerant)")
    email: Optional[EmailStr] = Field(None, description="Adresse email (optionnelle mais doit être valide si fournie)")
    subscription_type: Optional[str] = Field(None, description="Type d'abonnement initial pour les membres (monthly/annual)")

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[EmailStr] = None
    subscription_status: Optional[str] = None
    subscription_type: Optional[str] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) 

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, description="Nouveau nom d'utilisateur (optionnel, 3 caractères min)")
    email: Optional[EmailStr] = Field(None, description="Nouvel email (optionnel, doit être valide)")
