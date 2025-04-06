import firebase_admin
from firebase_admin import credentials, firestore

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

# Aggiunta utenti
def add_player():
    print("ADD A PLAYER:")
    while True:
        player_name = input("Player's name: ").strip()
        if player_name:
            break
        print("Try again.")

    doc_ref = db.collection('players').document(player_name)
    doc = doc_ref.get()

    if doc.exists:
        print('Player', player_name, 'already exists!')
    else:
        doc_ref.set({
            'Injury list': [], 'Time': 0,
        })
        print('Player', player_name, 'added successfully!')

# Aggiunta infortuni ad un giocatore
def add_injury_tap():
    time=0
    print("ADD AN INJURY:")
    player_name = str(input("Player's name: "))

    doc_ref = db.collection('players').document(player_name)
    doc = doc_ref.get()
    if doc.exists:
        injury_type = str(input("Add injury: "))
        player_data = doc.to_dict()
        injury_list = player_data.get('Injury list', [])
        if not isinstance(injury_list,list):   #controlla se injury_list è di tipo lista
            injury_list=[injury_list]
        injury_list.append(injury_type)

        doc_ref.update({
            'Injury list': injury_list, 'Time': time
        })
    else:
        print('Player', player_name, 'not found')

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
#add_injury --> da vedere come inserire nell'add_injury_tap?
add_player()
add_injury_tap()
