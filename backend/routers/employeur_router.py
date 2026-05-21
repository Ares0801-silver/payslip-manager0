from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.database import get_db, User, FicheDePaie, HistoriqueEnvoi
from backend.services.auth import require_employeur, hash_password
from backend.services.pdf_service import generer_fiche_pdf
from backend.services.email_service import envoyer_fiche_par_email

router = APIRouter(prefix='/api/employeur', tags=['Employeur'])

class EmployeCreate(BaseModel):
    email: str
    nom: str
    prenom: str
    poste: str = ''
    password: str

class FicheCreate(BaseModel):
    employe_id: int
    mois: str
    salaire_brut: float
    cotisations: float
    prime: float = 0.0
    heures: float = 151.67

@router.get('/employes')
def liste_employes(db=Depends(get_db), _=Depends(require_employeur)):
    employes = db.query(User).filter(User.role == 'employe').all()
    return [{'id':e.id,'nom':e.nom,'prenom':e.prenom,'email':e.email,
             'poste':e.poste,'actif':e.actif,'created_at':e.created_at.strftime('%d/%m/%Y')}
            for e in employes]

@router.post('/employes')
def ajouter_employe(data: EmployeCreate, db=Depends(get_db), _=Depends(require_employeur)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, 'Email deja utilise')
    emp = User(email=data.email, nom=data.nom, prenom=data.prenom,
               poste=data.poste, role='employe', hashed_password=hash_password(data.password))
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {'message': 'Employe ajoute', 'id': emp.id}

@router.delete('/employes/{employe_id}')
def retirer_employe(employe_id: int, db=Depends(get_db), _=Depends(require_employeur)):
    emp = db.query(User).filter(User.id == employe_id, User.role == 'employe').first()
    if not emp: raise HTTPException(404, 'Employe introuvable')
    emp.actif = False
    db.commit()
    return {'message': 'Employe desactive'}

@router.get('/fiches')
def liste_fiches(db=Depends(get_db), _=Depends(require_employeur)):
    fiches = db.query(FicheDePaie).all()
    result = []
    for f in fiches:
        emp = db.query(User).filter(User.id == f.employe_id).first()
        result.append({'id':f.id,'mois':f.mois,'employe_id':f.employe_id,
            'employe_nom':f'{emp.prenom} {emp.nom}' if emp else '---',
            'salaire_brut':f.salaire_brut,'salaire_net':f.salaire_net,
            'cotisations':f.cotisations,'prime':f.prime,
            'envoye':f.envoye,'envoye_le':f.envoye_le.strftime('%d/%m/%Y %H:%M') if f.envoye_le else None})
    return result

@router.post('/fiches')
def creer_fiche(data: FicheCreate, db=Depends(get_db), _=Depends(require_employeur)):
    emp = db.query(User).filter(User.id == data.employe_id, User.role == 'employe').first()
    if not emp: raise HTTPException(404, 'Employe introuvable')
    net = data.salaire_brut + data.prime - data.cotisations
    fiche = FicheDePaie(employe_id=data.employe_id, mois=data.mois,
        salaire_brut=data.salaire_brut, salaire_net=net,
        cotisations=data.cotisations, prime=data.prime, heures=data.heures)
    db.add(fiche)
    db.commit()
    db.refresh(fiche)
    try:
        fiche.pdf_path = generer_fiche_pdf(fiche, emp)
        db.commit()
    except: pass
    return {'message': 'Fiche creee', 'id': fiche.id}


@router.post('/fiches/{fiche_id}/envoyer')
def envoyer_fiche(fiche_id: int, db=Depends(get_db), employeur=Depends(require_employeur)):
    fiche = db.query(FicheDePaie).filter(FicheDePaie.id == fiche_id).first()
    if not fiche: raise HTTPException(404, 'Fiche introuvable')
    emp = db.query(User).filter(User.id == fiche.employe_id).first()
    pdf_path = generer_fiche_pdf(fiche, emp)
    fiche.pdf_path = pdf_path
    db.commit()
    result = envoyer_fiche_par_email(emp.email, emp.prenom, emp.nom, fiche.mois, pdf_path)
    if result['success']:
        fiche.envoye = True
        fiche.envoye_le = datetime.utcnow()
        db.commit()
    db.add(HistoriqueEnvoi(fiche_id=fiche.id, employe_id=emp.id,
        envoye_par=employeur.id, statut='success' if result['success'] else 'error',
        message=result.get('error', f'Envoye a {emp.email}')))
    db.commit()
    if not result['success']:
        raise HTTPException(500, f'PDF genere mais email non envoye : {result.get("error")}')
    return {'message': f'Fiche envoyee a {emp.email}', 'pdf': pdf_path}

@router.get('/fiches/{fiche_id}/pdf')
def telecharger_pdf(fiche_id: int, db=Depends(get_db), _=Depends(require_employeur)):
    fiche = db.query(FicheDePaie).filter(FicheDePaie.id == fiche_id).first()
    if not fiche or not fiche.pdf_path: raise HTTPException(404, 'PDF non disponible')
    return FileResponse(fiche.pdf_path, media_type='application/pdf', filename=f'fiche_{fiche.mois}.pdf')

@router.get('/historique')
def historique(db=Depends(get_db), _=Depends(require_employeur)):
    logs = db.query(HistoriqueEnvoi).order_by(HistoriqueEnvoi.date_envoi.desc()).all()
    result = []
    for log in logs:
        emp = db.query(User).filter(User.id == log.employe_id).first()
        fiche = db.query(FicheDePaie).filter(FicheDePaie.id == log.fiche_id).first()
        result.append({'id':log.id,'employe':f'{emp.prenom} {emp.nom}' if emp else '---',
            'mois':fiche.mois if fiche else '---',
            'date_envoi':log.date_envoi.strftime('%d/%m/%Y %H:%M'),
            'statut':log.statut,'message':log.message})
    return result

@router.get('/stats')
def stats(db=Depends(get_db), _=Depends(require_employeur)):
    return {'total_employes': db.query(User).filter(User.role=='employe', User.actif==True).count(),
            'total_fiches': db.query(FicheDePaie).count(),
            'fiches_envoyees': db.query(FicheDePaie).filter(FicheDePaie.envoye==True).count(),
            'fiches_en_attente': db.query(FicheDePaie).filter(FicheDePaie.envoye==False).count()}

