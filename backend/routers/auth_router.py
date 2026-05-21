from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db, User
from backend.services.auth import hash_password, verify_password, create_token

router = APIRouter(prefix='/api/auth', tags=['Auth'])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    nom: str
    prenom: str
    password: str
    poste: str = ''
    role: str = 'employe'

@router.post('/login')
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Email ou mot de passe incorrect')
    if not user.actif:
        raise HTTPException(status_code=403, detail='Compte desactive')
    token = create_token({'user_id': user.id, 'role': user.role})
    return {'token': token, 'role': user.role, 'nom': user.nom, 'prenom': user.prenom, 'id': user.id}

@router.post('/register')
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail='Email deja utilise')
    user = User(email=data.email, nom=data.nom, prenom=data.prenom,
               poste=data.poste, role=data.role, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({'user_id': user.id, 'role': user.role})
    return {'token': token, 'role': user.role, 'nom': user.nom, 'prenom': user.prenom, 'id': user.id}

