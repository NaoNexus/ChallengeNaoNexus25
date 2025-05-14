import speech_recognition as sr
from helpers.logging_helper import logger


class SpeechRecognition:
    r = sr.Recognizer()

    path = ""
    result = ""

    def __init__(self, path):
        self.r = sr.Recognizer()
        self.path = path

        self.recognise()

    '''
    def recognise(self):
        file = sr.AudioFile(self.path)

        with file as source:
            audio = self.r.record(source)

            self.result = self.r.recognize_google(audio, language="it-IT")
            logger.info(self.result)
    '''
    
    def recognise(self):
        try:
            file = sr.AudioFile(self.path)
            with file as source:
                audio = self.r.record(source)
                if len(audio.frame_data) == 0:
                    logger.warning("Audio vuoto.")
                    self.result = ""
                    return
                self.result = self.r.recognize_google(audio, language="it-IT")
                logger.info(self.result)
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition non ha capito l'audio.")
            self.result = ""
        except sr.RequestError as e:
            logger.error(f"Errore nella richiesta al servizio di riconoscimento: {e}")
            self.result = ""
        except Exception as e:
            logger.error(f"Errore imprevisto: {e}")
            self.result = ""
    