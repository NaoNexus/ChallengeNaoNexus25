import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Carica le credenziali
cred = credentials.Certificate("nao-basket-e5f9e-firebase-adminsdk-fbsvc-7feac96803.json")
firebase_admin.initialize_app(cred)

# Inizializza il client Firestore
db = firestore.client()

# Aggiunge infortuni
def add_injury():

    injury_name = str(input("Nome infortunio: "))
    recovery = str(input("Metodo di recupero: "))
    recovery_time = int(input("Tempo di recupero(giorni): "))

    doc_ref = db.collection('injuries').document(injury_name)
    doc_ref.set({
        'Recovery': recovery,
        'Time': recovery_time
    })

# Creazione utenti
def add_players():
    player_name = str(input("Player's name: "))
    injury_list = ""
    now = datetime.now()
    last_date = now.strftime("%d/%m/%Y")

    doc_ref = db.collection('players').document(player_name)
    doc_ref.set({
        'Injury list': [],
        'Time': 0,
        'Last_date': last_date 
    })

# Modifica dati dei giocatori
def modify_players():
    player_name = str(input("Player's name: "))
    injury = str(input("Add_injury: "))

    # Riferimento al documento del giocatore
    player_ref = db.collection('players').document(player_name)
    player_doc = player_ref.get()

    # Calcolo del tempo rimanente
    time = player_doc.get('Time')
    last_date_str = player_doc.get('Last_date')  # Cambia qui
    now = datetime.now()
    current_date_str = now.strftime("%d/%m/%Y")

    last_date = datetime.strptime(last_date_str, "%d/%m/%Y")
    current_date = datetime.strptime(current_date_str, "%d/%m/%Y")

    # Calcola la differenza in giorni
    delta = current_date - last_date
    days = delta.days
    time -= days

    if time < 0:
        player_ref.update({
        'Injury list': []
        })
        time = 0 

    # Riferimento al documento dell'infortunio
    injury_ref = db.collection('injuries').document(injury)
    injury_doc = injury_ref.get()

    # Controlla se sia il giocatore che l'infortunio esistono
    if player_doc.exists and injury_doc.exists:
        # Aggiungi i giorni dell'infortunio
        time += injury_doc.get("Time")
        # Aggiungi il nuovo infortuno alla lista esistente del giocatore
        player_ref.update({
            'Injury list': firestore.ArrayUnion([injury]),  # Aggiunge l'infortunio all'array
            'Time': time,  # Aggiorna il campo "Time" (se necessario)
            'Last_date': current_date_str  # Cambia qui
        })
        print(f"Injury '{injury}' added to {player_name}'s injury list.")
    else:
        if not player_doc.exists:
            print(f"Player '{player_name}' does not exist.")
        if not injury_doc.exists:
            print(f"Injury '{injury}' does not exist.")

def get_player_info():
    # Chiedi il nome del giocatore
    player_name = str(input("Player's name: "))

    # Riferimento al documento del giocatore
    player_ref = db.collection('players').document(player_name)
    player_doc = player_ref.get()

    # Verifica se il giocatore esiste
    if not player_doc.exists:
        print(f"Player '{player_name}' does not exist.")
        return

    # Calcolo del tempo rimanente
    time = player_doc.get('Time')
    last_date_str = player_doc.get('Last_date')  # Cambia qui
    now = datetime.now()
    current_date_str = now.strftime("%d/%m/%Y")

    last_date = datetime.strptime(last_date_str, "%d/%m/%Y")
    current_date = datetime.strptime(current_date_str, "%d/%m/%Y")

    # Calcola la differenza in giorni
    delta = current_date - last_date
    days = delta.days
    time -= days

    if time < 0:
        player_ref.update({
        'Injury list': []
        })
        time = 0
    
    # Modifica Last_date e time
    player_ref.update({
            'Time': time,
            'Last_date': current_date_str
        })

    # Aggiorna la snapshot del documento dopo l'aggiornamento
    player_doc = player_ref.get()

    # Ottieni tutti i campi del documento
    player_data = player_doc.to_dict()

    # Stampa i dettagli del giocatore
    print(f"\nDetails for player '{player_name}':")
    for field, value in player_data.items():
        print(f"{field}: {value}")

# Esempio di lettura di un documento
def get_document():
    doc_ref = db.collection('users').document('userId')
    doc = doc_ref.get()
    
    if doc.exists:
        print('Document data:', doc.to_dict())
    else:
        print('No such document!')

# Esempio di lettura di tutti i documenti in una collezione
def get_all_documents():
    users_ref = db.collection('users')
    docs = users_ref.stream()
    
    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')

# Esegui le funzioni
#add_players()
#modify_players()
#get_player_info()

