# api/loan-service/helpers.py
import requests
import os

# Récupérer les URLs depuis les variables d'environnement ou utiliser des défauts
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://127.0.0.1:8001')
DOCUMENT_SERVICE_URL = os.getenv('DOCUMENT_SERVICE_URL', 'http://127.0.0.1:8002')
SERVICE_TIMEOUT = 5

def get_user_data(user_id):
    """Appelle le user-service pour obtenir les détails d'un utilisateur."""
    try:
        api_url = f"{USER_SERVICE_URL}/api/users/{user_id}"
        response = requests.get(api_url, timeout=SERVICE_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Loan Service Helper] Erreur appel User Service ({user_id}): {e}")
        return None

def get_document_data(doc_id):
    """Appelle le document-service pour obtenir les détails d'un document."""
    try:
        api_url = f"{DOCUMENT_SERVICE_URL}/api/documents/{doc_id}"
        response = requests.get(api_url, timeout=SERVICE_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Loan Service Helper] Erreur appel Document Service ({doc_id}): {e}")
        return None