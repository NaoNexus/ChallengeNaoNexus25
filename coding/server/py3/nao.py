'''
File di esecuzione del robot NAO
Contiene:
- Funzioni per IA;
- Funzioni per database;
- Funzioni. 
'''

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from flask import jsonify, request
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import main
import nao_ai
from helpers.speech_recognition_helper import SpeechRecognition

from helpers.logging_helper import logger
from helpers.config_helper import Config

from firebase_helper import db

#import exercises

config_helper  = Config()
#db_helper      = DB(config_helper)

# Variabili globali per le connessioni e l'autenticazione del robot Nao
nao_ip         = config_helper.nao_ip
nao_port       = config_helper.nao_port
nao_user       = config_helper.nao_user
nao_password   = config_helper.nao_password
nao_api_openai = config_helper.nao_api_openai


#--db
api_key = "la_tua_chiave_api_openai"  # Sostituisci con la tua chiave

#--DATABASE
def delete_all_players():
    try:
        # Ottieni tutti i documenti nella collezione 'players'
        players_ref = db.collection('players')
        players = players_ref.stream()

        # Elimina ogni documento della collezione 'players'
        for player in players:
            player.reference.delete()
            print(f"Player {player.id} deleted successfully.")

    except Exception as e:
        print(f"Error deleting players: {str(e)}")


def db_add_players(players_list):
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

def get_all_injury_names():
    try:
        injuries = db.collection('injuries').stream()
        injury_names = [injury.id for injury in injuries]
        return injury_names                     #jsonify(injury_names)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def get_all_player_names():
    try:
        players = db.collection('players').stream()  # Ottieni tutti i documenti nella collezione 'players'
        player_names = [player.id for player in players]  # Estrai il nome di ogni giocatore (l'ID del documento)
        return player_names  # Restituisce la lista dei nomi
    except Exception as e:
        return {'error': str(e)}  # Restituisce l'errore in caso di problemi

def get_player_injuries_and_time(player_name):
    try:
        player_name = player_name.strip().lower()
        doc_ref = db.collection('players').document(player_name)
        doc = doc_ref.get()

        if not doc.exists:
            return {
                'success': False,
                'message': f'Giocatore "{player_name}" non trovato nel database.'
            }

        data = doc.to_dict()
        injury_list = data.get('Injury list', [])
        time_value = data.get('Time', 0)

        return {
            'success': True,
            'injury_list': injury_list,
            'time': time_value
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Errore nel recupero dei dati: {str(e)}'
        }

def add_injury_to_player(player_name, injury):
    try:
        player_name = player_name.strip().lower()
        injury = injury.strip().lower()

        # Verifica esistenza giocatore
        player_ref = db.collection('players').document(player_name)
        player_doc = player_ref.get()
        if not player_doc.exists:
            print(f"[ERRORE] Giocatore '{player_name}' non trovato.")
            return

        # Verifica esistenza infortunio
        injury_doc = db.collection('injuries').document(injury).get()
        if not injury_doc.exists:
            print(f"[ERRORE] Infortunio '{injury}' non trovato.")
            return

        # Ottieni tempo dell'infortunio
        injury_time = injury_doc.to_dict().get('Time', 0)

        player_data = player_doc.to_dict()
        injury_list = player_data.get('Injury list', [])

        if injury not in injury_list:
            injury_list.append(injury)

            player_ref.update({
                'Injury list': injury_list,
                'Time': max(injury_time, player_data.get('Time', 0)),
                'Last date': datetime.now()
            })

            print(f"[OK] Infortunio '{injury}' aggiunto al giocatore '{player_name}'.")
        else:
            print(f"[INFO] Il giocatore '{player_name}' ha già l'infortunio '{injury}'.")

    except Exception as e:
        print(f"[ECCEZIONE] {str(e)}")

def get_player_time(player_name):
    try:
        player_name = player_name.strip().lower()
        player_doc = db.collection('players').document(player_name).get()
        
        if not player_doc.exists:
            print(f"[ERRORE] Giocatore '{player_name}' non trovato.")
            return None
        
        player_data = player_doc.to_dict()
        time = player_data.get('Time', None)

        print(f"[OK] Tempo attuale per '{player_name}': {time}")
        return time

    except Exception as e:
        print(f"[ECCEZIONE] {str(e)}")
        return None

#--FUNZIONI
'''
def nao_audiorecorder(sec_sleep):
    data     = {"nao_ip":nao_ip, "nao_port":nao_port, "nao_user":nao_user, "nao_password":nao_password, "sec_sleep":sec_sleep}
    url      = "http://127.0.0.1:5011/nao_audiorecorder/" + str(data) 
    response = requests.get(url, json=data, stream=True)

    local_path = f'recordings/microphone_audio.wav'
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: 
                    f.write(chunk)   
        logger.info("File audio ricevuto: " + str(response.status_code))
    else:
        logger.error("File audio non ricevuto: " + str(response.status_code))

    while True:
        speech_recognition = SpeechRecognition(local_path)
        if (speech_recognition.result != None or speech_recognition.result != ''):
            break
    
    logger.info("nao_audiorecorder: " + str(speech_recognition.result))
    return str(speech_recognition.result)
'''


def nao_audiorecorder(sec_sleep):
    data = {
        "nao_ip": nao_ip,
        "nao_port": nao_port,
        "nao_user": nao_user,
        "nao_password": nao_password,
        "sec_sleep": sec_sleep
    }
    url = "http://127.0.0.1:5011/nao_audiorecorder/" + str(data)
    response = requests.get(url, json=data, stream=True)

    local_path = 'recordings/microphone_audio.wav'
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info("File audio ricevuto: " + str(response.status_code))
    else:
        logger.error("File audio non ricevuto: " + str(response.status_code))
        return None  # eventualmente interrompe se c'è un errore serio

    speech_recognition = SpeechRecognition(local_path)
    result = speech_recognition.result

    if result is not None and result.strip() != "":
        logger.info("nao_audiorecorder: " + str(result))
        return str(result)
    else:
        nao_tts_audiofile("non_ho_capito.mp3")
        return nao_audiorecorder(sec_sleep)


def nao_touch_head_audiorecorder():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port, "nao_user":nao_user, "nao_password":nao_password}
    url      = "http://127.0.0.1:5011/nao_touch_head_audiorecorder/" + str(data) 
    response = requests.get(url, json=data, stream=True)

    local_path = f'recordings/microphone_audio.wav'
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: 
                    f.write(chunk)   
        logger.info("File audio ricevuto: " + str(response.status_code))
    else:
        logger.error("File audio non ricevuto: " + str(response.status_code))

    while True:
        speech_recognition = SpeechRecognition(local_path)
        if (speech_recognition.result != None or speech_recognition.result != ''):
            break
    
    logger.info("nao_touch_head_audiorecorder: " + str(speech_recognition.result))
    return str(speech_recognition.result)

def nao_tts_audiofile(filename): # FILE AUDIO NELLA CARTELLA tts_audio DI PY2
    data     = {"nao_ip":nao_ip, "nao_port":nao_port, "filename":filename, "nao_user":nao_user, "nao_password":nao_password}
    url      = "http://127.0.0.1:5011/nao_tts_audiofile/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))


#--PROCEDURE
def new_team():
    nao_tts_audiofile("nuova_squadra.mp3") #--chiede di aggiungere tutti
                          #  i giocatori
    i = True
    giocatori = []
    
    c = 1

    
    while i:
        frase = "Giocatore " + str(c)
        nao_ai.audio_generator(frase, "giocatore")
        nao_tts_audiofile("giocatore.mp3") #--"giocatore"
        nome_giocatore = nao_audiorecorder(5)
        print("Nome giocatore: ", nome_giocatore)

        if "fine" in nome_giocatore or "Fine" in nome_giocatore:
            i = False
            break

        else:
            nome_giocatore_domanda = nome_giocatore + "è corretto?"
            nao_ai.audio_generator(nome_giocatore_domanda, "nome_giocatore")
            nao_tts_audiofile("nome_giocatore.mp3")
            risposta = nao_audiorecorder(5)

            if "sì" in risposta:
                nao_tts_audiofile("ho_aggiunto_giocatore.mp3")
                giocatori.append(nome_giocatore)
                print(giocatori)
                c+=1
                continue
            else:
                nao_tts_audiofile("riproviamo.mp3") #--riproviamo
                continue
    
    if len(giocatori) == 0:
        programma()

    #--Creazione stringa dei giocatori
    lista_giocatori = "I giocatori sono: "
        
    for j in range(0, len(giocatori) - 1):
        lista_giocatori += giocatori[j]
        lista_giocatori += ", "

    lista_giocatori += "è corretto?"

    print(lista_giocatori)

    nao_ai.audio_generator(lista_giocatori, "lista_giocatori")

    nao_tts_audiofile("lista_giocatori.mp3")

    risposta = nao_audiorecorder(5)

    if "sì" in risposta:
        delete_all_players()
        db_add_players(giocatori)
        nao_tts_audiofile("hai_creato_una_squadra.mp3")
        programma()
    else:
        new_team()


def gestione_giocatori():
    nao_tts_audiofile("opzionedue.mp3") #--"Gestione giocatori"

    nao_tts_audiofile("cometichiami.mp3") #--"come ti chiami?"
    
    nome_giocatore = nao_audiorecorder(4)

    print("Prima del minuscolo", nome_giocatore)
    nome_giocatore = str(nome_giocatore).lower()
    print("Dopo il minuscolo", nome_giocatore)

    player_list = get_all_player_names()
    print(player_list)

    if nome_giocatore not in player_list:
        nao_tts_audiofile("nonticonosco.mp3") #--"non ti conosco, sei nuovo?"
        answer = nao_audiorecorder(5)

        if "sì" in answer:
            nao_tts_audiofile("ora_ti_aggiungo.mp3") #--"Ok, adesso ti aggiungo alla squadra!"
            ng = [nome_giocatore]
            db_add_players(ng, db)

            nome_giocatore_domanda = nome_giocatore + "è corretto?"
            nao_ai.audio_generator(nome_giocatore_domanda, "nome_giocatore")
            nao_tts_audiofile("nome_giocatore.mp3")
            risposta = nao_audiorecorder(5)

            if "si" in risposta:
                nao_tts_audiofile("aggiungo_a_squadra.mp3") #--"Ok, adesso ti aggiungo alla squadra!"
                ng = [nome_giocatore]
                db_add_players(ng, db)   
            else:
                nao_tts_audiofile("riproviamo.mp3") #--riproviamo
                gestione_giocatori()
        
        else:
            nao_tts_audiofile("non_ho_capito_bene_ricominciamo.mp3") #--"Forse non ho capito bene, ricominciamo!"
            gestione_giocatori()
    
    else:
        nao_tts_audiofile("chiedo_sintomi.mp3") #--"Cosa ti senti? Premi la mia testa per iniziare
                              #   a descrivermi i tuoi sintomi. Premi di nuovo per terminare"

        #sintomi = nao_touch_head_audiorecorder()
        sintomi = nao_audiorecorder(10)

        stringa_infortuni = ""

        lista_infortuni = get_all_injury_names()

        stringa_infortuni = ", ".join(lista_infortuni)

        sintomi = "Sei un medico e devi capire cosa ha il paziente secondo i seguenti sintomi: " + sintomi
        sintomi += ". fai un discorso diretto con accento italiano che si rivolge direttamente al paziente(un giocatore di basket), senza istruzioni."
        sintomi += ("Scegli tra gli infortuni in questa lista: " + stringa_infortuni)

        print(sintomi)

        #--ChatGPT fa una breve diagnosi
        risposta = nao_ai.nao_ai(sintomi)
        print(risposta)
        nao_ai.audio_generator(risposta, "sintomi_risposta_ai")

        nao_tts_audiofile("sintomi_risposta_ai.mp3")
        
        #--Aggiunta dell'infortunio nel database.
        richiesta = "Tieni conto della tua risposta precedente: " + risposta
        richiesta += "Ora devi scegliere per il tuo paziente uno di questi infortuni: "
        richiesta += stringa_infortuni
        richiesta += ". La tua risposta deve contenere SOLO il numero dell'infortunio che hai scelto, puoi sceglierne solo 1. RICORDA CHE LA RISPOSTA DEVE CONTENERE SOLO IL NUMERO, il primo infortunio della lista è 0, il secondo è 1, ecc... Mi serve perchè mi devi dare la posizione nella lista così dopo posso estrarla"

        
        infortunio_scelto = nao_ai.nao_ai(richiesta)
        print(infortunio_scelto)
        indice = int(infortunio_scelto)
        print("Int: ", indice)
        infortunio = lista_infortuni[indice]

        parlato = "Per la descrizione che mi hai fornito, l'infortunio più probabile è: " + infortunio + ". Ora lo salverò nel mio database, così potremmo tenerne traccia."

        nao_ai.audio_generator(parlato, "ho_scelto_un_infortunio")
        nao_tts_audiofile("ho_scelto_un_infortunio.mp3")

        add_injury_to_player(nome_giocatore, infortunio)

        tempo = get_player_time(nome_giocatore)

        parlato2 = "Hai " + str(tempo) + "giorni di recupero rimanenti"
        nao_ai.audio_generator(parlato2, "giorni_rimanenti")
        nao_tts_audiofile("giorni_rimanenti.mp3")

        nao_tts_audiofile("ho_aggiunto_infortunio_successo.mp3")
        programma()
        


def stato_giocatore():
    nao_tts_audiofile("opzionetre.mp3")  #--"hai scelto l'opzione 3, ti posso dare informazioni sul tuo recupero"

    nao_tts_audiofile("cometichiami.mp3") #--"come ti chiami?"
    
    nome_giocatore = nao_audiorecorder(4)

    print("Prima del minuscolo", nome_giocatore)
    nome_giocatore = str(nome_giocatore).lower()
    print("Dopo il minuscolo", nome_giocatore)

    player_list = get_all_player_names()
    print(player_list)

    if nome_giocatore not in player_list:
        nao_tts_audiofile("nonticonosco.mp3") #--"non ti conosco, sei nuovo?"
        answer = nao_audiorecorder(5)

        if "sì" in answer:
            nao_tts_audiofile("ora_ti_aggiungo.mp3") #--"Ok, adesso ti aggiungo alla squadra!"
            ng = [nome_giocatore]
            db_add_players(ng, db)

            nome_giocatore_domanda = nome_giocatore + "è corretto?"
            nao_ai.audio_generator(nome_giocatore_domanda, "nome_giocatore")
            nao_tts_audiofile("nome_giocatore.mp3")
            risposta = nao_audiorecorder(5)

            if "si" in risposta:
                nao_tts_audiofile("aggiungo_a_squadra.mp3") #--"Ok, adesso ti aggiungo alla squadra!"
                ng = [nome_giocatore]
                db_add_players(ng, db)   
            else:
                nao_tts_audiofile("riproviamo.mp3") #--riproviamo
                gestione_giocatori()
        
        else:
            nao_tts_audiofile("non_ho_capito_bene_ricominciamo.mp3") #--"Forse non ho capito bene, ricominciamo!"
            gestione_giocatori()

    else:
        info_giocatore(nome_giocatore)
    programma()

def esercizi():
    nao_tts_audiofile("opzionequattro.mp3")
    lista_esercizi = ["ankle_circles", "single_leg_balance", "eccentric_calf_raises_on_step", "eccentric_calf_raises_on_step", "plantar_mobilization", "quadriceps_isometrics", "mini_squats", "static_lunges", "quad_set", "isometric_contraction", "calf_raises", "isometric_hip_adduction", "bird_dog"]
    stringa_esercizi = ", ".join(lista_esercizi)
    nao_tts_audiofile("cometichiami.mp3")
    
    programma()

#--FUNZIONI APP

def info_giocatore(giocatore):
    data = get_player_injuries_and_time(giocatore)
    print(data)

    if data.get("success"):
        injuries_list = data.get("injury_list", [])
        injuries_str = ", ".join(injuries_list) if injuries_list else "Nessun infortunio registrato."
        time_str = str(data.get("time", 0))
    else:
        injuries_str = "Nessun infortunio registrato."
        time_str = "0"

    stringa_input = "Sei un medico e devi rivolgerti con un discorso diretto al tuo paziente. Il tuo paziente ha questi infortuni (quando parli di tutto in italiano): "
    stringa_input += injuries_str
    stringa_input += ". Spiega il processo di cura. Ricordati di rimanere entro 133 token. Ricorda al tuo paziente che ha questi giorni di recupero mancanti: "
    stringa_input += time_str
    stringa_input += ". Spesso i discorsi che fai rimangono tagliati quindi stai attento a finire tutti i tuoi discorsi entro 133 token, circa 80 parole MASSIMO"

    risposta_ai = nao_ai.nao_ai(stringa_input)
    nao_ai.audio_generator(risposta_ai, "risposta_app")
    nao_tts_audiofile("risposta_app.mp3")



 #--AVVIAMENTO
def principale():
    print("Esecuzione iniziata")
    nao_tts_audiofile("accensione.mp3") #--Il nao saluta
    programma()

def shortcut():
    gestione_giocatori()

def programma():
    nao_tts_audiofile("opzioni.mp3") #--Il nao chiede come può aiutare l'utente
                          #  Opzione 1: iniziare nuova squadra
                          #  Opzione 2: riconoscimento infortunio
                          #  Opzione 3: richiesta informazioni

                          #  Fine per terminare l'esecuzione

                          # Utente deve dire il numero dell'opzione

    opzione = nao_audiorecorder(4)

    #--OPZIONI
    if "fine" in opzione or "Fine" in opzione:
        print("Fine esecuzione")
        nao_tts_audiofile("fine.mp3") #--"Grazie per avere utilizzato NAO"
        return

    if "1" in opzione or "uno" in opzione:
        print("Inzio creazione di una nuova squadra")
        new_team()
        programma()

    if "2" in opzione or "due" in opzione:
        print("Inzio gestione giocatori")
        gestione_giocatori()
        programma()

    if "3" in opzione or "tre" in opzione:
        print("Informazioni sui giocatori")
        stato_giocatore()
        programma()

    if "4" in opzione or "quattro" in opzione:
        print("Esercizi")
        #nao_tts_audiofile("opzione_non_disponibile.mp3")
        esercizi()
        programma()

    else:
        print("Opzione non riconosciuta")
        nao_tts_audiofile("opzione_non_riconosciuta.mp3") #--"Opzione non riconosciuta"
        programma()

