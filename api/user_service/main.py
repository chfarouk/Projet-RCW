import os
from fastapi import FastAPI, Depends, HTTPException, status, Query 
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, or_
from sqlalchemy.orm import sessionmaker 
from werkzeug.security import generate_password_hash, check_password_hash 
from .shemas import UserCreate, UserOut, UserLogin, UserUpdate
from typing import Optional, List
from datetime import datetime, timedelta 

app = FastAPI(title="User Service API")

instance_path = os.path.join(os.path.dirname(__file__), 'instance') 
os.makedirs(instance_path, exist_ok=True) 
DATABASE_URL = f"sqlite:///{os.path.join(instance_path, 'user_service.db')}" 
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 
Base = declarative_base() 

class User(Base):
    __tablename__ = "users" 

    id = Column(Integer, primary_key=True, index=True) 
    username = Column(String(80), unique=True, index=True, nullable=False) 
    password = Column(String(255), nullable=False) 
    role = Column(String(50), nullable=False) 
    email = Column(String(120), unique=True, index=True, nullable=True) 
    subscription_status = Column(String(20), default='inactive', nullable=True)
    subscription_type = Column(String(20), nullable=True)
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'

def create_tables():
    print("Essai de création des tables pour User Service...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables User Service créées (si elles n'existaient pas).")
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")
        
create_tables()
    
def get_db():
    db = SessionLocal() 
    try:
        yield db 
    finally:
        db.close() 

@app.get("/") 
def read_root():
    return {"message": "Bienvenue sur l'API User Service de BiblioTech IA"}

@app.post("/api/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)  
def create_user_api(user_data: UserCreate, db: Session = Depends(get_db)):
    print(f"[User Service] Requête POST /api/users reçue pour username: {user_data.username}")
    if user_data.role not in ['membre', 'bibliothecaire', 'gerant']: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rôle '{user_data.role}' invalide")
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        print(f"[User Service] Conflit Username: {user_data.username}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nom d'utilisateur déjà pris")
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
             print(f"[User Service] Conflit Email: {user_data.email}")
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé")
    hashed_password = generate_password_hash(user_data.password) 
    try: 
        db_user = User( 
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
        return db_user 
    except Exception as e:
         db.rollback()
         print(f"[User Service] Erreur DB création: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne création")

@app.post("/api/auth/login", response_model=UserOut) 
def api_login(form_data:UserLogin, db: Session = Depends(get_db)):
    print(f"[User Service] Requête POST /api/auth/login reçue pour username: {form_data.username}")
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not check_password_hash(user.password, form_data.password):
        print(f"[User Service] Login échoué pour: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
        )
    print(f"[User Service] Login réussi pour: {user.username}")
    return user

@app.get("/api/users/{user_id}", response_model=UserOut) 
def read_user_api(user_id: int, db: Session = Depends(get_db)):
    print(f"[User Service] Requête GET /api/users/{user_id}")
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        print(f"[User Service] User ID {user_id} non trouvé.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    print(f"[User Service] Utilisateur trouvé: {db_user.username}, Rôle: {db_user.role}") 
    return db_user 

@app.get("/api/users", response_model=List[UserOut])
def read_users_api(
    role: Optional[str] = Query(None, enum=['membre', 'bibliothecaire', 'gerant'], description="Filtrer par rôle"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter (pagination)"), 
    limit: int = Query(100, ge=1, le=100, description="Nombre max d'éléments à retourner"), 
    db: Session = Depends(get_db)
):
    print(f"[User Service] Requête GET /api/users - Filtre Rôle: {role}, Skip: {skip}, Limit: {limit}")
    try:
        query = db.query(User) 
        if role:
            query = query.filter(User.role == role)

        users = query.order_by(User.username).offset(skip).limit(limit).all()

        print(f"[User Service] Renvoi de {len(users)} utilisateur(s).")
        return users
    except Exception as e:
         print(f"[User Service] Erreur DB listage utilisateurs: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne récupération utilisateurs")

@app.patch("/api/users/{user_id}", response_model=UserOut)
def update_user_api(user_id: int, user_update_data:UserUpdate, db: Session = Depends(get_db)):
    print(f"[User Service] Requête PATCH /api/users/{user_id} reçue")
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    update_data = user_update_data.model_dump(exclude_unset=True) 
    if "username" in update_data and update_data["username"] != db_user.username:
        existing_username = db.query(User).filter(User.username == update_data["username"]).first()
        if existing_username:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce nom d'utilisateur est déjà pris")
    if "email" in update_data and update_data["email"] != db_user.email:
         existing_email = db.query(User).filter(User.email == update_data["email"]).first()
         if existing_email:
              raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet email est déjà utilisé")
    for key, value in update_data.items():
        setattr(db_user, key, value) 
    try:
        db.commit()
        db.refresh(db_user) 
        print(f"[User Service] Utilisateur ID {user_id} mis à jour.")
        return db_user 
    except Exception as e:
         db.rollback()
         print(f"[User Service] Erreur DB MàJ User {user_id}: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne mise à jour utilisateur")

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT) 
def delete_user_api(user_id: int, db: Session = Depends(get_db)):
    print(f"[User Service] Requête DELETE /api/users/{user_id} reçue")
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    if db_user.role == 'gerant':
         print(f"[User Service] Tentative suppression Gérant ID {user_id} refusée.")
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suppression des gérants non autorisée")
    try:
        db.delete(db_user)
        db.commit()
        print(f"[User Service] Utilisateur ID {user_id} supprimé.")
        return None
    except Exception as e:
         db.rollback()
         print(f"[User Service] Erreur DB suppression User {user_id}: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne suppression utilisateur")

# @app.on_event("startup")
# def startup_event():
#     #  DECOMMENTEZ CE BLOC UNIQUEMENT POUR LA PREMIERE CREATION 
#     print("Vérification et ajout potentiel des utilisateurs de test au démarrage...")
#     db: Session = SessionLocal() 
#     try:
#         if not db.query(User).first():
#            print("Base User vide. Ajout utilisateurs test...")
#       
#            hashed_password_default = generate_password_hash('password') 
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
#          db.rollback() 
#     finally:
#          db.close() 
#     # RE-COMMENTEZ CE BLOC APRES LE PREMIER LANCEMENT REUSSI 
