from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db, User

SECRET_KEY = 'payslip-secret-key-change-in-production'
ALGORITHM = 'HS256'
TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
bearer_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = data.copy()
    payload['exp'] = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials=Depends(bearer_scheme), db: Session=Depends(get_db)):
    if not credentials:
        raise HTTPException(status_code=401, detail='Non authentifie')
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.id == payload.get('user_id')).first()
        if not user or not user.actif:
            raise HTTPException(status_code=401, detail='Utilisateur introuvable')
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail='Token invalide')

def require_employeur(user=Depends(get_current_user)):
    if user.role != 'employeur':
        raise HTTPException(status_code=403, detail='Acces refuse')
    return user
