import firebase_admin
from firebase_admin import credentials, firestore

# Carica le credenziali
cred = credentials.Certificate("nao-basket-e5f9e-firebase-adminsdk-fbsvc-7feac96803.json")
firebase_admin.initialize_app(cred)

# Inizializza il client Firestore
db = firestore.client()

# Aggiunge infortuni
def add_injury():

    while True:
        injury_name = str(input("Injury name: ")).strip().lower()
        if injury_name:
            break
        else:
            print("Try again.")


    while True:
        recovery = str(input("Recovery method: ")).strip().lower()
        if recovery:
            break
        else:
            print("Try again.")
    
    while True:
        recovery_time = int(input("Recovery time: "))
        if recovery_time:
            break
        else:
            print("Try again.")
    
    doc_ref = db.collection('injuries').document(injury_name)
    doc = doc_ref.get()

    if doc.exists:
        print("Injury already exists")

    
    doc_ref.set({
        'Recovery': recovery,
        'Time': recovery_time
    })

# Creazione utenti
def add_players():

    while True:
        player_name = str(input("Player's name: ")).strip().lower()
        if player_name:
            break
        else:
            print("Try again.")


    doc_ref = db.collection('players').document(player_name)
    doc = doc_ref.get()

    if doc.exists:
        print("Player already exists")
    else:
        doc_ref.set({
            'Injury list': "",
            'Time': 0,
            'Last date': 0
        })
        print("Player added successfully")

# Modifica utenti
def add_injury_tap():
    
    player_name = str(input("Player's name: "))

    doc_ref = db.collection('players').document(player_name)
    doc = doc_ref.get()

    if doc.exists:
        
        injury = str(input("Add_injury: "))
        doc_ref_i = db.collection('injuries').document(injury)
        doc_i = doc_ref_i.get()

        if doc_i.exists:
            
            injury_time = doc_ref_i.get("Time") #--!! Errore qui !!
            time = doc_ref.get("Time") #--!! Errore qui !!

            if injury_time >= time:
                time = injury_time

            player_data = doc.to_dict()
            injury_list = player_data.get('Injury list', [])
            if not isinstance(injury_list,list):   #controlla se injury_list è di tipo lista
                injury_list=[injury_list]
            injury_list.append(injury)

            doc_ref.update({
                'Injury list': injury_list, 
                'Time': time
            })
        
        else:
            print("Injury does not exist.")
            add_injury_tap()
    else:
        print("Player does not exist.")
        add_injury_tap()

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
add_injury_tap()
