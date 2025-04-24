# api/user_service/main.py

# --- Imports ---
import os
from fastapi import FastAPI, Depends, HTTPException, status, Query # Outils FastAPI
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, or_
from sqlalchemy.orm import sessionmaker # Session pour type hint et SessionLocal
from werkzeug.security import generate_password_hash, check_password_hash # Garder check_password_hash pour login futur
from .shemas import UserCreate, UserOut, UserLogin, UserUpdate
from typing import Optional, List
from datetime import datetime, timedelta # Outil pour les dates
# --- Fin Imports ---


# --- Créer une instance de l'application FastAPI ---
app = FastAPI(title="User Service API")
# --- Fin de la creation d'une instance de l'application FastAPI ---


# --- Configuration Base de Données ---
instance_path = os.path.join(os.path.dirname(__file__), 'instance') # Chemin vers le dossier 'instance'
os.makedirs(instance_path, exist_ok=True) # Crée le dossier si besoin
DATABASE_URL = f"sqlite:///{os.path.join(instance_path, 'user_service.db')}" # URL de connexion à la base de données SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # Créer une connexion à la base de données via SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Créer une "usine" à sessions pour parler à la base de données si necessaire
Base = declarative_base() # Créer une "Base" que nos modèles utiliseront pour définir les tables
# --- Fin de la Configuration Base de Données ---


# --- Définition du Modèle User ---
class User(Base):
    __tablename__ = "users" # Nom de la table dans la base de données

    id = Column(Integer, primary_key=True, index=True) # Clé primaire auto-incrémentée
    username = Column(String(80), unique=True, index=True, nullable=False) # Nom unique, non vide
    password = Column(String(255), nullable=False) # Hash du mot de passe, non vide
    role = Column(String(50), nullable=False) # Role (membre, etc.), non vide
    email = Column(String(120), unique=True, index=True, nullable=True) # Email unique, peut être vide
    # Champs abonnement (on garde nullable=True pour l'instant)
    subscription_status = Column(String(20), default='inactive', nullable=True)
    subscription_type = Column(String(20), nullable=True)
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'
# --- Fin de Définition du Modèle User ---


# --- Fonction pour créer les tables au démarrage ---
def create_tables():
    print("Essai de création des tables pour User Service...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables User Service créées (si elles n'existaient pas).")
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")
# --- Fin de la Fonction pour créer les tables au démarrage ---


# --- Creation de la base de donnee (si elle n'existe pas deja) et des tables (si ils n'existent pas deja) ---
create_tables()
# --- Fin de la Creation de la base de donnee (si elle n'existe pas deja) et des tables (si ils n'existent pas deja) ---
    

# Cette fonction sera appelée par FastAPI pour chaque requête nécessitant la DB
def get_db():
    db = SessionLocal() # Crée une nouvelle session
    try:
        yield db # Fournit la session à la fonction de la route
    finally:
        db.close() # Ferme la session après la fin de la requête
# --- Fin ---


# --- Créer une "porte d'entrée" (endpoint) ---
@app.get("/") # Quand quelqu'un accède à l'adresse racine ("/") de ce service on lui répond simplement avec un message de bienvenue
def read_root():
    return {"message": "Bienvenue sur l'API User Service de BiblioTech IA"}
# --- Fin de la Creation d'une "porte d'entrée" (endpoint) ---


# --- Créer une "porte d'entrée" (endpoint) pour créer un utilisateur ---
@app.post("/api/users", response_model=UserOut, status_code=status.HTTP_201_CREATED) # Indique le schéma de réponse et le statut succès 
def create_user_api(user_data: UserCreate, db: Session = Depends(get_db)):
    print(f"[User Service] Requête POST /api/users reçue pour username: {user_data.username}")
    # Vérifier si le rôle est valide (on peut le faire ici ou dans CRUD)
    if user_data.role not in ['membre', 'bibliothecaire', 'gerant']: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rôle '{user_data.role}' invalide")
      # 2. Vérifier si l'utilisateur ou l'email existe déjà (Logique directe)
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        print(f"[User Service] Conflit Username: {user_data.username}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nom d'utilisateur déjà pris")
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
             print(f"[User Service] Conflit Email: {user_data.email}")
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé")
    hashed_password = generate_password_hash(user_data.password) # Hacher le mot de passe
    try: # Créer l'objet et sauvegarder (Logique directe)
        db_user = User( # Utilise le modèle User défini dans ce fichier
            username=user_data.username,
            password=hashed_password,
            role=user_data.role,
            email=user_data.email,
            subscription_status='pending' if user_data.role == 'membre' else 'n/a',
            subscription_type=user_data.subscription_type if user_data.role == 'membre' else 'none'
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"[User Service] User créé: ID {db_user.id}")
        return db_user # Pydantic convertira db_user en UserOut grâce à response_model
    except Exception as e:
         db.rollback()
         print(f"[User Service] Erreur DB création: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne création")
# --- Fin Créer une "porte d'entrée" (endpoint) pour créer un utilisateur ---


# --- Créer une "porte d'entrée" (endpoint) pour l'authentification ---
@app.post("/api/auth/login", response_model=UserOut) # Renvoie UserOut si succès
def api_login(form_data:UserLogin, db: Session = Depends(get_db)):
    print(f"[User Service] Requête POST /api/auth/login reçue pour username: {form_data.username}")
    # 1. Chercher l'utilisateur par username
    user = db.query(User).filter(User.username == form_data.username).first()
    # 2. Vérifier si user existe ET si le mot de passe est correct
    if not user or not check_password_hash(user.password, form_data.password):
        # Si l'utilisateur n'existe pas OU si le mot de passe est incorrect
        print(f"[User Service] Login échoué pour: {form_data.username}")
        # Lever une exception HTTP 401 Unauthorized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            # headers={"WWW-Authenticate": "Bearer"}, # Standard pour API à token
        )
    # 3. Si on arrive ici, l'authentification a réussi
    print(f"[User Service] Login réussi pour: {user.username}")
    # Renvoyer l'objet utilisateur. FastAPI/Pydantic le convertira en UserOut.
    return user
# --- Fin Créer une "porte d'entrée" (endpoint) pour l'authentification ---


# --- Endpoint pour LIRE UN utilisateur par ID ---
@app.get("/api/users/{user_id}", response_model=UserOut) # L'ID est dans le chemin
def read_user_api(user_id: int, db: Session = Depends(get_db)):
    print(f"[User Service] Requête GET /api/users/{user_id}")
    # Requête directe dans la DB
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        print(f"[User Service] User ID {user_id} non trouvé.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    # Important: La conversion via response_model=schemas.UserOut se fait par FastAPI
    print(f"[User Service] Utilisateur trouvé: {db_user.username}, Rôle: {db_user.role}") # Log pour voir le rôle
    return db_user # Pydantic/FastAPI convertit en UserOut
# --- FIN AJOUT LIRE UN ---


# --- Endpoint pour LISTER les utilisateurs (avec filtre rôle optionnel) ---
# La réponse sera une LISTE d'objets UserOut
@app.get("/api/users", response_model=List[UserOut])
def read_users_api(
    role: Optional[str] = Query(None, enum=['membre', 'bibliothecaire', 'gerant'], description="Filtrer par rôle"), # Paramètre optionnel 'role' dans l'URL (?role=...)
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter (pagination)"), # Pour pagination future
    limit: int = Query(100, ge=1, le=100, description="Nombre max d'éléments à retourner"), # Pour pagination future
    db: Session = Depends(get_db)
):
    print(f"[User Service] Requête GET /api/users - Filtre Rôle: {role}, Skip: {skip}, Limit: {limit}")
    try:
        query = db.query(User) # Requête de base
        if role:
            # Appliquer le filtre si fourni (rôle est déjà validé par Query(enum=[...]))
            query = query.filter(User.role == role)

        # Appliquer tri, pagination (skip/limit) et récupérer les utilisateurs
        users = query.order_by(User.username).offset(skip).limit(limit).all()

        print(f"[User Service] Renvoi de {len(users)} utilisateur(s).")
        # Pydantic/FastAPI convertira chaque objet User de la liste en UserOut
        return users
    except Exception as e:
         print(f"[User Service] Erreur DB listage utilisateurs: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne récupération utilisateurs")
# --- FIN AJOUT LISTER ---


# --- Endpoint pour METTRE À JOUR un utilisateur par ID ---
@app.patch("/api/users/{user_id}", response_model=UserOut)
def update_user_api(user_id: int, user_update_data:UserUpdate, db: Session = Depends(get_db)):
    print(f"[User Service] Requête PATCH /api/users/{user_id} reçue")
    # 1. Récupérer l'utilisateur existant
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    # 2. Vérifier les conflits potentiels pour les champs uniques modifiés
    update_data = user_update_data.model_dump(exclude_unset=True) # Ne prend que les champs fournis
    if "username" in update_data and update_data["username"] != db_user.username:
        existing_username = db.query(User).filter(User.username == update_data["username"]).first()
        if existing_username:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce nom d'utilisateur est déjà pris")
    if "email" in update_data and update_data["email"] != db_user.email:
         existing_email = db.query(User).filter(User.email == update_data["email"]).first()
         if existing_email:
              raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet email est déjà utilisé")
    # 3. Appliquer les modifications à l'objet SQLAlchemy
    for key, value in update_data.items():
        setattr(db_user, key, value) # Met à jour les attributs correspondants
    # 4. Sauvegarder les changements
    try:
        db.commit()
        db.refresh(db_user) # Rafraîchir l'objet avec les données de la DB
        print(f"[User Service] Utilisateur ID {user_id} mis à jour.")
        return db_user # Pydantic convertit en UserOut
    except Exception as e:
         db.rollback()
         print(f"[User Service] Erreur DB MàJ User {user_id}: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne mise à jour utilisateur")
# --- FIN UPDATE USER API ---


# --- Endpoint pour SUPPRIMER un utilisateur par ID ---
@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT) # Statut succès pour DELETE
def delete_user_api(user_id: int, db: Session = Depends(get_db)):
    print(f"[User Service] Requête DELETE /api/users/{user_id} reçue")
    # 1. Récupérer l'utilisateur
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    # 2. Vérifier les règles métier (ex: ne pas supprimer un gérant)
    if db_user.role == 'gerant':
         print(f"[User Service] Tentative suppression Gérant ID {user_id} refusée.")
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suppression des gérants non autorisée")
    # 3. Supprimer de la base de données
    try:
        db.delete(db_user)
        db.commit()
        print(f"[User Service] Utilisateur ID {user_id} supprimé.")
        # Réponse vide avec statut 204 No Content (standard pour DELETE réussi)
        # On ne peut pas renvoyer de corps avec 204, donc on retourne None
        return None
    except Exception as e:
         db.rollback()
         print(f"[User Service] Erreur DB suppression User {user_id}: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne suppression utilisateur")
# --- FIN DELETE USER API ---

# @app.on_event("startup")
# def startup_event():
#     # !!! DÉCOMMENTEZ CE BLOC UNIQUEMENT POUR LA PREMIÈRE CRÉATION !!!
#     print("Vérification et ajout potentiel des utilisateurs de test au démarrage...")
#     db: Session = SessionLocal() 
#     try:
#         if not db.query(User).first():
#            print("Base User vide. Ajout utilisateurs test...")
#            # Importer le hashage ici
#            hashed_password_default = generate_password_hash('password') # Mot de passe par défaut
#            users_to_add = [
#                User(username='gerant', password=hashed_password_default, role='gerant', email='gerant@bibliotech.ia', subscription_status='n/a')
#            ]
#            db.add_all(users_to_add)
#            db.commit()
#            print("Utilisateur(s) de test ajouté(s).")
#         else:
#              print("Utilisateurs déjà présents.")
#     except Exception as e:
#          print(f"Erreur lors de l'ajout des données de test User: {e}")
#          db.rollback() # Annuler en cas d'erreur
#     finally:
#          db.close() # Fermer la session
#     # RE-COMMENTEZ CE BLOC APRÈS LE PREMIER LANCEMENT RÉUSSI 
    # --- FIN AJOUT DONNÉES TEST ---