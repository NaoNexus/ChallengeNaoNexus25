import firebase_admin
from firebase_admin import credentials, firestore

# Evita doppia inizializzazione
if not firebase_admin._apps:
    cred = credentials.Certificate("nao-basket-e5f9e-firebase-adminsdk-fbsvc-929802554f.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()