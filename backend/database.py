from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./payslip.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Table Users (employeurs et employés) :
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    nom = Column(String)
    prenom = Column(String)
    hashed_password = Column(String)
    role = Column(String, default='employe')
    poste = Column(String, nullable=True)
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    fiches = relationship('FicheDePaie', back_populates='employe', foreign_keys='FicheDePaie.employe_id')
    
class FicheDePaie(Base):
    __tablename__ = 'fiches_de_paie'
    id = Column(Integer, primary_key=True)
    employe_id = Column(Integer, ForeignKey('users.id'))
    employeur_id = Column(Integer, ForeignKey('users.id'))
    mois = Column(String)
    annee = Column(Integer)
    salaire_brut = Column(Float)
    salaire_net = Column(Float)
    cotisations = Column(Float)
    pdf_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    employe = relationship('User', foreign_keys=[employe_id], back_populates='fiches')
    employeur = relationship('User', foreign_keys=[employeur_id])

class HistoriqueEnvoi(Base):
    __tablename__ = 'historique_envois'
    id = Column(Integer, primary_key=True)
    fiche_id = Column(Integer, ForeignKey('fiches_de_paie.id'))
    date_envoi = Column(DateTime, default=datetime.utcnow)
    email_destinataire = Column(String)
    statut = Column(String)
    fiche = relationship('FicheDePaie')
    
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()