import os
from openai import OpenAI
from datetime import datetime

# Inserisci la tua API key qui
client = OpenAI(api_key="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")

# Cronologia della conversazione
conversation_history = []

def add_to_history(role, content):
    conversation_history.append({"role": role, "content": content})

def nao_ai(user_input):
    "Genera una risposta AI usando ChatGPT"
    try:
        add_to_history("user", user_input)

        response = client.chat.completions.create(
            model="gpt-4o",  # Usa un modello valido
            messages=conversation_history,
            temperature=0.7,
            max_tokens=133
        )

        ai_response = response.choices[0].message.content
        add_to_history("assistant", ai_response)

        return ai_response

    except Exception as e:
        print(f"Errore nella generazione della risposta: {e}")
        return "Mi dispiace, ho avuto un problema a generare una risposta."

def audio_generator(testo, nome_file):
    """
    Genera un file audio da un testo usando OpenAI TTS
    e lo salva nella cartella specificata.
    """
    # Percorso di destinazione
    directory = "/Users/nicolagiovannifaldi/Library/CloudStorage/OneDrive-Personale/3A SA/NaoNexus/ChallengeNaoNexus25/coding/server/py2/tts_audio"
    os.makedirs(directory, exist_ok=True)

    if not nome_file.endswith(".mp3"):
        nome_file += ".mp3"

    percorso = os.path.join(directory, nome_file)

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="fable",
            input=testo
        )

        with open(percorso, "wb") as f:
            f.write(response.content)

        print(f"Audio salvato in: {percorso}")
        return percorso
    except Exception as e:
        print(f"Errore nella generazione dell'audio: {e}")
        return None

# Esempio di utilizzo
if __name__ == "__main__":
    '''
    user_input = "Ho male alla gamba, cosa potrebbe essere? Parla italiano. Quello che generi sarà riprodotto su un audio quindi immaginati di fare un discorso diretto. Cerca di finire il discorso prima di 133 token. Usa un accento italiano. Hai massimo 100 parole a disposizione. non andare oltre"
    text = nao_ai(user_input)
    print(text)
    audio_generator(text)
    '''
    audio_generator("Forse non ho capito bene, ricominciamo!", "non_ho_capito_bene_ricominciamo")