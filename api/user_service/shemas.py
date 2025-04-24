# api/user_service/schemas.py

# --- Imports ---
from pydantic import BaseModel, EmailStr, Field, ConfigDict # Outils de Pydantic pour la gestion des données de l'API
from typing import Optional # Outil pour indiquer qu'un champ peut être vide ou avoir une valeur
from datetime import datetime # Outil pour travailler avec des dates et heures
# --- Fin de Imports ---


# --- Schéma pour les données attendues lors de la CRÉATION d'un utilisateur ---
# C'est ce que l'API attend de recevoir dans la requête POST /api/users
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, description="Nom d'utilisateur unique (3 caractères min)")
    password: str = Field(..., min_length=6, description="Mot de passe (6 caractères min)")
    role: str = Field(..., description="Rôle de l'utilisateur (ex: membre, bibliothecaire, gerant)")
    email: Optional[EmailStr] = Field(None, description="Adresse email (optionnelle mais doit être valide si fournie)")
    # Pour un membre, on pourrait aussi attendre le type d'abonnement initial
    subscription_type: Optional[str] = Field(None, description="Type d'abonnement initial pour les membres (monthly/annual)")
# --- Fin ---


# --- Schéma pour les données renvoyées APRÈS création ou lors de la lecture ---
# On ne renvoie JAMAIS le mot de passe !
class UserOut(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[EmailStr] = None
    subscription_status: Optional[str] = None
    subscription_type: Optional[str] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) # Cette configuration permet à Pydantic de lire les données directement depuis un objet SQLAlchemy (comme notre modèle User)
# --- Fin ---


# --- Schéma pour les données attendues au login ---
class UserLogin(BaseModel):
    username: str
    password: str
# --- Fin ---


# --- Schéma pour la MISE À JOUR partielle d'un utilisateur ---
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, description="Nouveau nom d'utilisateur (optionnel, 3 caractères min)")
    email: Optional[EmailStr] = Field(None, description="Nouvel email (optionnel, doit être valide)")
# --- FIN AJOUT ---
