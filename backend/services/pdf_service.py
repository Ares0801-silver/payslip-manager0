import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

PDF_DIR = 'pdfs'
os.makedirs(PDF_DIR, exist_ok=True)

BLEU = colors.HexColor('#0F1F3D')
CYAN = colors.HexColor('#00A8E8')
GRIS = colors.HexColor('#8FA3B1')

def generer_fiche_pdf(fiche, employe) -> str:
    filename = f'fiche_{employe.id}_{fiche.mois}.pdf'
    filepath = os.path.join(PDF_DIR, filename)
    doc = SimpleDocTemplate(filepath, pagesize=A4,
          leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph('BULLETIN DE PAIE', ParagraphStyle('t', fontSize=20,
        textColor=BLEU, alignment=TA_CENTER, fontName='Helvetica-Bold')))
    story.append(Paragraph(f'Periode : {fiche.mois}', ParagraphStyle('s', fontSize=12,
        textColor=GRIS, alignment=TA_CENTER)))
    story.append(HRFlowable(width='100%', thickness=2, color=CYAN))
    story.append(Spacer(1, 12))
    data = [
        ['Employe', f'{employe.prenom} {employe.nom}'],
        ['Poste', employe.poste or '---'],
        ['Salaire Brut', f'{fiche.salaire_brut:.2f} MAD'],
        ['Prime', f'{fiche.prime:.2f} MAD'],
        ['Cotisations', f'- {fiche.cotisations:.2f} MAD'],
        ['NET A PAYER', f'{fiche.salaire_net:.2f} MAD'],
    ]
    t = Table(data, colWidths=[6*cm, 11*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLEU),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.HexColor('#F0F8FF'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, GRIS),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph('Document confidentiel - PaySlip Manager',
        ParagraphStyle('f', fontSize=8, textColor=GRIS, alignment=TA_CENTER)))
    doc.build(story)
    return filepath
