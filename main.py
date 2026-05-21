import sys, os
sys.path.insert(0, os.path.dirname(__file__))
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db, SessionLocal, User
from backend.services.auth import hash_password
from backend.routers import auth_router, employeur_router, employe_router

app = FastAPI(title='PaySlip Manager')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

app.include_router(auth_router)
app.include_router(employeur_router)
app.include_router(employe_router)

app.mount('/static', StaticFiles(directory='frontend'), name='static')

@app.get('/')
def root(): return FileResponse('frontend/index.html')

@app.get('/dashboard-employeur')
def dash_emp(): return FileResponse('frontend/pages/dashboard_employeur.html')

@app.get('/dashboard-employe')
def dash_employe(): return FileResponse('frontend/pages/dashboard_employe.html')

def _seed():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == 'admin@admin.com').first():
            admin = User(
                email='admin@admin.com',
                nom='Admin',
                prenom='Admin',
                hashed_password=hash_password('admin123'),
                role='employeur',
                actif=True
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

@app.on_event('startup')
def startup():
    init_db()
    _seed()