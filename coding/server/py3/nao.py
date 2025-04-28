'''
File di esecuzione del robot NAO
Contiene:
- Funzioni per IA;
- Funzioni per database;
- Funzioni 
'''

import main
from main import nao_audiorecorder
from main import nao_tts_audiofile
from openai import OpenAI
from pathlib import Path
from datetime import datetime


#--NAO AI
def nao_speak(text, voice="alloy"):
    
    # NON FINITO!
    api_key = "la_tua_chiave_api_openai"  # Sostituisci con la tua chiave

    try:
        # Inizializza il client OpenAI
        client = OpenAI(api_key=api_key)
        
        # Percorso del file audio (deve corrispondere alla cartella usata in main.py)
        speech_file_path = Path(__file__).parent.parent / "py2/tts_audio/speech.mp3"
        
        # Crea l'audio dal testo usando OpenAI
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Salva il file audio
        response.stream_to_file(speech_file_path)
        
        # Invia il file al NAO
        nao_tts_audiofile("speech.mp3")
        
        print("NAO ha pronunciato il testo con successo!")
        return True
    
    except Exception as e:
        print(f"Errore durante la sintesi vocale: {e}")
        return False

def nao_ai(self, user_input):
        """Genera una risposta AI usando OpenAI"""
        try:
            # Aggiungi l'input dell'utente alla cronologia
            self.add_to_history("user", user_input)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=133
            )
            
            ai_response = response.choices[0].message.content
            self.add_to_history("assistant", ai_response)
            
            return ai_response
            
        except Exception as e:
            print(f"Errore nella generazione della risposta: {e}")
            return "Mi dispiace, ho avuto un problema a generare una risposta."

#--DATABASE
def db_add_players(players_list, db):
    results = []

    for player_name in players_list:
        try:
            player_name = player_name.strip().lower()
            if not player_name:
                results.append({'success': False, 'message': 'Player name is required.'})
                continue

            doc_ref = db.collection('players').document(player_name)
            if doc_ref.get().exists:
                results.append({'success': False, 'message': f'Player "{player_name}" already exists.'})
                continue

            doc_ref.set({
                'Injury list': [],
                'Time': 0,
                'Last date': datetime.now()
            })
            results.append({'success': True, 'message': f'Player "{player_name}" added successfully.'})
        except Exception as e:
            results.append({'success': False, 'message': f'Error with player "{player_name}": {str(e)}'})

    for result in results:
        print(result)


#--PROCEDURE
def new_team():
    nao_tts_audiofile("") #--chiede di aggiungere tutti
                               #  i giocatori
    i = True
    giocatori = []

    while i:
        nao_tts_audiofile("") #--"giocatore"
        nome_giocatore = nao_audiorecorder(5)

        if nome_giocatore == "fine":
            break

        else:
            nome_giocatore = main.nao_audiorecorder(5)
            giocatori.append(nome_giocatore)
        
    #--Creazione stringa dei giocatori
    lista_giocatori = "I giocatori sono: "
        
    for p in giocatori:
        lista_giocatori += (giocatori[p] + ", ")

    lista_giocatori += "è corretto?"

    nao_speak(lista_giocatori)

    risposta = nao_tts_audiofile(5)

    if "si" in risposta:
        db_add_players()
    else:
        new_team()




#--MAIN
if __name__ == "__main__":

    #--AVVIAMENTO
    nao_tts_audiofile("") #--Il nao saluta

    nao_tts_audiofile("") #--Il nao chiede come può aiutare l'utente
                          #  Opzione 1: iniziare nuova squadra
                          #  Opzione 2: riconoscimento infortunio
                          #  Opzione 3: richiesta informazioni

                          # Utente deve dire il numero dell'opzione

    opzione = nao_audiorecorder(5)

    #--NUOVA SQUADRA
    if "uno" in opzione:
        print("Inzio creazione di una nuova squadra")
        new_team()
    
    if "due" in opzione:
        print("Inzio gestione giocatori")

    if "tre" in opzione:
        print("Informazioni sui giocatori")

    else:
        print("Opzione non riconosciuta")
        nao_tts_audiofile("") #--"Opzione non riconosciuta"

        
