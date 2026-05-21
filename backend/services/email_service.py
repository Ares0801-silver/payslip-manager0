import os
import resend

resend.api_key = os.getenv('RESEND_API_KEY', '')
FROM_ADDRESS = os.getenv('FROM_ADDRESS', 'onboarding@resend.dev')
FROM_NAME = os.getenv('FROM_NAME', 'PaySlip Manager')

def envoyer_fiche_par_email(employe_email, employe_prenom, employe_nom, mois, pdf_path):
    if not resend.api_key:
        return {'success': False, 'error': 'Cle API Resend manquante (RESEND_API_KEY)'}
    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        corps = f'<p>Bonjour {employe_prenom} {employe_nom},</p>'
        corps += f'<p>Votre bulletin de paie pour <b>{mois}</b> est en piece jointe.</p>'
        corps += '<p>Cordialement, Le Service RH via PaySlip Manager</p>'
        params = {
            'from': f'{FROM_NAME} <{FROM_ADDRESS}>',
            'to': [employe_email],
            'subject': f'Votre bulletin de paie - {mois}',
            'html': corps,
            'attachments': [{'filename': f'bulletin_{mois}.pdf', 'content': list(pdf_bytes)}]
        }
        response = resend.Emails.send(params)
        if response and response.get('id'):
            return {'success': True}
        return {'success': False, 'error': 'Pas de reponse de Resend'}
    except FileNotFoundError:
        return {'success': False, 'error': 'PDF introuvable'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
