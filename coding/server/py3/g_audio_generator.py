import os
from gtts import gTTS
from datetime import datetime

def audio_generator(testo):
    """
    Genera un file audio da un testo e lo salva nella cartella recordings/.
    
    Parametri:
        testo (str): Il testo da convertire in audio.
    
    Ritorna:
        str: Il percorso completo del file audio salvato.
    """
    # Assicurati che la cartella recordings esista
    os.makedirs("recordings", exist_ok=True)

    # Nome del file con timestamp per evitare sovrascrittura
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"audio_{timestamp}.mp3"
    percorso = os.path.join("recordings", nome_file)

    # Genera e salva l'audio
    tts = gTTS(text=testo, lang='it')
    tts.save(percorso)

    print(f"Audio salvato in: {percorso}")
    return percorso




audio = audio_generator("Prossimo giocatore")