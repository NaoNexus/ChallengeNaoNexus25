# -*- coding: utf-8 -*-

'''
python3 64 bit
pip3 install -r requirements.txt
python3 main.py

versione Python 3.12.0 64 bit

NOTA BENE!!!  
Avviare prima server Nao: python2 main.py
Il server nao comunica con il Nao attraverso python2.
Questo server si interfaccia con l'utente, il database e AI attraverso python3.
''' 

# Modules
from pydub import AudioSegment
import nao
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, send_from_directory
from hashlib import md5, sha256
from datetime import datetime
from pathlib import Path
from openai import OpenAI
import requests
import time
import os
import csv
import cv2
import cv2.aruco as aruco
import numpy as np
import utilities
from helpers.config_helper import Config
from helpers.logging_helper import logger
from helpers.speech_recognition_helper import SpeechRecognition
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore
from flask_cors import CORS
import subprocess
import json


from firebase_helper import db

#from helpers.db_helper import DB


config_helper  = Config()
#db_helper      = DB(config_helper)

nao_ip         = config_helper.nao_ip
nao_port       = config_helper.nao_port
nao_user       = config_helper.nao_user
nao_password   = config_helper.nao_password
nao_api_openai = config_helper.nao_api_openai

face_detection = True
face_tracker   = True
local_db_dialog = []
local_rec       = []


app  = Flask(__name__)

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'
login_manager.session_protection = 'strong'


def make_md5(s):
    encoding = 'utf-8'
    return md5(s.encode(encoding)).hexdigest()


def make_sha256(s):
    encoding = 'utf-8'
    return sha256(s.encode(encoding)).hexdigest()


#################################
# FUNZIONI FLASK SERVER Python2 #
#################################
def detect_faces(frame):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')     # Carica il classificatore Haar per il rilevamento dei volti
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)                                                    # Converti il frame in scala di grigi
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))    # Rileva i volti nel frame
    for (x, y, w, h) in faces:                                                                              # Disegna un rettangolo attorno ai volti rilevati
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
    return frame

@app.route('/webcam', methods=['GET'])
def webcam():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_webcam/" + str(data) 
    response = requests.get(url, json=data, stream=True)

    # face detection
    def generate_frames():
        boundary     = b'--frame\r\n'
        content_type = b'Content-Type: image/jpeg\r\n\r\n'
        frame_data   = b''

        for chunk in response.iter_content(chunk_size=1024):
            frame_data += chunk
            if boundary in frame_data:
                # Estrai il frame
                parts = frame_data.split(boundary)
                for part in parts[:-1]:                    
                    if content_type in part:
                        frame_data = part.split(content_type)[-1]
                        # Decodifica il frame
                        np_frame = np.frombuffer(frame_data, dtype=np.uint8)
                        frame    = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
                        # Esegui il rilevamento facciale
                        if face_detection:
                            frame_with_faces = detect_faces(frame)
                            # Codifica di nuovo il frame con i volti rilevati come JPEG
                            _, buffer = cv2.imencode('.jpg', frame_with_faces)
                        else:
                            # Codifica di nuovo il frame 
                            _, buffer = cv2.imencode('.jpg', frame)
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                frame_data = parts[-1]

    return Response(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')


@app.route('/webcam_aruco', methods=['GET'])
def webcam_aruco():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_webcam/" + str(data) 
    response = requests.get(url, json=data, stream=True)

    # Inizializza il dizionario ArUco
    aruco_dict   = aruco.getPredefinedDictionary(aruco.DICT_4X4_1000)
    aruco_params = aruco.DetectorParameters()

    # Inizializza il rilevatore ArUco
    detector = aruco.ArucoDetector(aruco_dict, aruco_params)

    # aruco detection
    def generate_frames():
        boundary     = b'--frame\r\n'
        content_type = b'Content-Type: image/jpeg\r\n\r\n'
        frame_data   = b''

        for chunk in response.iter_content(chunk_size=1024):
            frame_data += chunk
            if boundary in frame_data:
                # Estrai il frame
                parts = frame_data.split(boundary)
                for part in parts[:-1]:                    
                    if content_type in part:
                        frame_data = part.split(content_type)[-1]
                        # Decodifica il frame
                        np_frame = np.frombuffer(frame_data, dtype=np.uint8)
                        frame    = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

                        # Conversione del frame in scala di grigi per migliorare il rilevamento dei marker
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        # Rileva i marker ArUco nel frame usando ArucoDetector
                        marker_corners, marker_ids, rejected_candidates = detector.detectMarkers(gray)

                        # Se vengono rilevati marker, disegnali sul frame
                        if marker_ids is not None:
                            # Disegna i marker rilevati sul frame
                            aruco.drawDetectedMarkers(frame, marker_corners, marker_ids)
                        
                        # Codifica di nuovo il frame 
                        _, buffer = cv2.imencode('.jpg', frame)
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                frame_data = parts[-1]

    return Response(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')


def nao_move_fast(angle):
    data     = {"nao_ip":nao_ip, "nao_port":nao_port, "angle":angle}
    url      = "http://127.0.0.1:5011/nao_move_fast/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))   


def nao_move_fast_stop():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_move_fast_stop/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))  


def nao_get_sensor_data():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_get_sensor_data/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))  
    return eval(str(response.text))['data']


nao_train_move_start = True
theta_speed = 0.0
def nao_train_move():
    duration   = 10
    filename   = 'nao_training_data.csv'
    start_time = time.time()
    data       = []

    #nao_move_fast(theta_speed)
    while nao_train_move_start:
        sensors = nao_get_sensor_data()
        x_speed = 1.0
        y_speed = 0.0
        data.append(sensors + [x_speed, y_speed, theta_speed])
        time.sleep(0.1)
    nao_move_fast_stop() 

    # Salva i dati in un file CSV
    with open(filename, mode='a') as file:
        writer = csv.writer(file)
        writer.writerow(['gyro_x', 'gyro_y', 'acc_x', 'acc_y', 'acc_z', 'x_speed', 'y_speed', 'theta_speed'])
        writer.writerows(data)



@app.route('/webcam_aruco_pose_estimate', methods=['GET'])
def webcam_aruco_pose_estimate():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_webcam/" + str(data) 
    response = requests.get(url, json=data, stream=True)

    # Ottieni le dimensioni del frame dalla webcam
    width    = 640
    height   = 480
    center_x = width  // 2
    center_y = height // 2

    # Inizializza il dizionario ArUco
    aruco_dict   = aruco.getPredefinedDictionary(aruco.DICT_4X4_1000)
    aruco_params = aruco.DetectorParameters()

    # Inizializza il rilevatore ArUco
    detector = aruco.ArucoDetector(aruco_dict, aruco_params)

    # Dimensione reale del marker in metri (ad esempio: 0.05 per 5 cm)
    marker_size = 0.025

    # Focale della camera in pixel (esempio, deve essere calibrata per la tua camera specifica)
    focal_length = 800

    # aruco detection
    def generate_frames():
        boundary     = b'--frame\r\n'
        content_type = b'Content-Type: image/jpeg\r\n\r\n'
        frame_data   = b''

        for chunk in response.iter_content(chunk_size=1024):
            frame_data += chunk
            if boundary in frame_data:
                # Estrai il frame
                parts = frame_data.split(boundary)
                for part in parts[:-1]:                    
                    if content_type in part:
                        frame_data = part.split(content_type)[-1]
                        # Decodifica il frame
                        np_frame = np.frombuffer(frame_data, dtype=np.uint8)
                        frame    = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

                        # Conversione del frame in scala di grigi per migliorare il rilevamento dei marker
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        # Rileva i marker ArUco nel frame usando ArucoDetector
                        marker_corners, marker_ids, rejected_candidates = detector.detectMarkers(gray)

                        # Se vengono rilevati marker, determina la posizione e la distanza
                        if marker_ids is not None:
                            for marker_id in marker_ids:
                                if marker_id == 449:
                                    for corners in marker_corners:
                                        # Calcola il centro del marker
                                        marker_center_x = int(corners[0][:, 0].mean())
                                        marker_center_y = int(corners[0][:, 1].mean())

                                        # Calcola la lunghezza apparente del marker in pixel
                                        pixel_size = cv2.norm(corners[0][0] - corners[0][1])

                                        # Calcola la distanza
                                        distance = (marker_size * focal_length) / pixel_size

                                        # Determina la deviazione dal centro dell'immagine
                                        deviation_x = marker_center_x - center_x
                                        deviation_y = marker_center_y - center_y

                                        # Stabilisci la direzione
                                        if distance > 0.20:
                                            nao_move_fast(0)
                                            
                                            if abs(deviation_x) < 10:  # Tolleranza per essere considerato "dritto"
                                                direction = "Dritto"
                                                nao_move_fast(0)
                                            elif deviation_x > 0:
                                                direction = "Storto a destra"
                                                nao_move_fast(10)
                                            else:
                                                direction = "Storto a sinistra"
                                                nao_move_fast(-10)
                                        else:
                                            nao_move_fast_stop()
                                            #pass

                                        print(f"Distanza dal marker: {distance:.2f} metri, Posizione marker: ({marker_center_x}, {marker_center_y}), Direzione: {direction}")

                                        # Disegna i marker rilevati sul frame
                                        aruco.drawDetectedMarkers(frame, marker_corners, marker_ids)

                                        # Disegna una linea tra il centro del frame e il centro del marker
                                        cv2.line(frame, (center_x, center_y), (marker_center_x, marker_center_y), (0, 255, 0), 2)
                        

                        # Disegna il centro del frame
                        cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)
                        
                        # Codifica di nuovo il frame 
                        _, buffer = cv2.imencode('.jpg', frame)
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                frame_data = parts[-1]

    return Response(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')



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


def nao_face_tracker():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_face_tracker/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))


def nao_stop_face_tracker():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_stop_face_tracker/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))


def nao_autonomous_life():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_autonomous_life/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))                                                     


def nao_wakeup():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_wakeup/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))                                                   


def nao_eye_white():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_eye_white/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))


def nao_animatedSayText(text_to_say):
    data     = {"nao_ip":nao_ip, "nao_port":nao_port, "text_to_say":text_to_say}
    url      = "http://127.0.0.1:5011/nao_animatedSayText/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))


def nao_standInit():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_standInit/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))                      


def nao_stand():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/nao_stand/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))


def nao_volume_sound(volume_level):
    data     = {"nao_ip":nao_ip, "nao_port":nao_port, "volume_level":volume_level}
    url      = "http://127.0.0.1:5011/nao_volume_sound/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))


def nao_tts_audiofile(filename): # FILE AUDIO NELLA CARTELLA tts_audio DI PY2
    data     = {"nao_ip":nao_ip, "nao_port":nao_port, "filename":filename, "nao_user":nao_user, "nao_password":nao_password}
    url      = "http://127.0.0.1:5011/nao_tts_audiofile/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))




# PAGINE WEB
# Per impedire all'utente di tornare indietro dopo aver fatto il logout
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

class User(UserMixin):
    def __init__(self, id = None, username = ''):
        self.id = id

users = {'1': {'id': '1', 'username': 'admin', 'password': '21232f297a57a5a743894a0e4a801fc3'}, #md5(admin)
         '2': {'id': '2', 'username': 'naonexus', 'password': '898d0dc0895b537fc1732a03cba7aff4'}} #md5(naonexus)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = make_md5(request.form["password"])

        # Verifica credenziali utente
        user = next((u for u in users.values() if u['username'] == username and u['password'] == password), None)
        if user:
            user_obj = User(user['id'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect('/')



# API
@app.route('/api', methods=['GET'])
def api():
    return render_template('api.html')


@app.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({'code': 200, 'status': 'online', 'elapsed time': utilities.getElapsedTime(startTime)}), 200


@app.route('/api/audio_rec', methods=['GET'])
def api_audio_rec():
    if request.method == 'GET':
        try:
            return jsonify({'code': 200, 'message': 'OK', 'recordings': local_rec}), 200
        except Exception as e:
            logger.error(str(e))
            return jsonify({'code': 500, 'message': str(e)}), 500


@app.route('/api/dialogo', methods=['GET'])
def api_dialogo():
    if request.method == 'GET':
        try:
            return jsonify({'code': 200, 'message': 'OK', 'data': local_db_dialog}), 200
        except Exception as e:
            logger.error(str(e))
            return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/data/<id>', methods=['POST'])
def api_data(id):
    if (id != None and id != ''):
        if request.method == 'POST':
            try:
                #{"id_player": value}
                json = request.json

                id_player = json["giocatore"]
                id_player = id_player.lower()

                nao.info_giocatore(id_player)
                return jsonify({'code': 200, 'message': 'OK', 'data': id_player}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
    else:
        logger.error('No id argument passed')
        return jsonify({'code': 500, 'message': 'No id was passed'}), 500

# MOVEMENTS
@app.route('/api/movement/init', methods=['GET'])
def api_movement_init():
    nao_autonomous_life()
    nao_eye_white()
    nao_wakeup()
    return redirect('/dashboard')

@app.route('/api/movement/start', methods=['GET'])
def api_movement_start():
    nao_move_fast(0)
    return redirect('/dashboard')

@app.route('/api/movement/stop', methods=['GET'])
def api_movement_stop():
    nao_move_fast_stop()
    return redirect('/dashboard')

@app.route('/api/movement/left', methods=['GET'])
def api_movement_left():
    global theta_speed
    theta_speed = 10
    #nao_move_fast(10)
    return redirect('/dashboard')

@app.route('/api/movement/right', methods=['GET'])
def api_movement_right():
    global theta_speed
    theta_speed = -10
    #nao_move_fast(-10)
    return redirect('/dashboard')

@app.route('/api/movement/stand', methods=['GET'])
def api_movement_stand():
    nao_stand()
    return redirect('/dashboard')

@app.route('/api/movement/standInit', methods=['GET'])
def api_movement_standInit():
    nao_standInit()
    return redirect('/dashboard')

@app.route('/api/movement/nao_train_move', methods=['GET'])
def api_movement_nao_train_move():
    global nao_train_move_start 
    nao_train_move_start = True
    nao_train_move()
    return redirect('/dashboard')

@app.route('/api/movement/nao_train_move_stop', methods=['GET'])
def api_movement_nao_train_move_stop():
    global nao_train_move_start 
    nao_train_move_start = False
    return redirect('/dashboard')


# SERVICES
@app.route('/services', methods=['GET'])
def services():
    return render_template('services.html')

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/database_interface')
@login_required  # Opzionale, se vuoi che sia accessibile solo agli utenti loggati
def serve_database_interface():
    return render_template('database_interface.html')

# TEXT-TO-SPEECH
@app.route('/tts_to_nao', methods=['POST'])
def tts_to_nao():
    if request.method == "POST":
        #text = request.form["message"]
        #nao_animatedSayText(text)

        text = request.form["message"]

        #collegamento a chatgpt
        client = OpenAI(api_key = nao_api_openai)
        speech_file_path = Path(__file__).parent.parent / "py2/tts_audio/speech.mp3"
        response = client.audio.speech.create(model="tts-1",voice="alloy",input=text)  
        response.stream_to_file(speech_file_path)
        nao_tts_audiofile("speech.mp3")

    return redirect('/dashboard')

# DATABASE
@app.route('/get_players')
def get_players():
    try:
        players = db.collection('players').stream()
        return jsonify([player.id for player in players])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_injuries')
def get_injuries():
    try:
        injuries = db.collection('injuries').stream()
        return jsonify([injury.id for injury in injuries])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_injury', methods=['POST'])
def add_injury():
    update_time()
    try:
        data = request.json
        injury_name = data.get('injury_name', '').strip().lower()
        recovery = data.get('recovery', '').strip().lower()
        recovery_time = data.get('recovery_time', 0)

        if not all([injury_name, recovery, recovery_time]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        doc_ref = db.collection('injuries').document(injury_name)
        if doc_ref.get().exists:
            return jsonify({'success': False, 'message': 'Injury already exists'}), 400

        doc_ref.set({
            'Recovery': recovery,
            'Time': int(recovery_time),
            'Created': datetime.now()
        })
        return jsonify({'success': True, 'message': 'Injury added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/add_player', methods=['POST'])
def add_player():
    update_time()
    try:
        data = request.json
        player_name = data.get('player_name', '').strip().lower()
        if not player_name:
            return jsonify({'success': False, 'message': 'Player name is required'}), 400

        doc_ref = db.collection('players').document(player_name)
        if doc_ref.get().exists:
            return jsonify({'success': False, 'message': 'Player already exists'}), 400

        doc_ref.set({
            'Injury list': [],
            'Time': 0,
            'Last date': datetime.now()
        })
        return jsonify({'success': True, 'message': 'Player added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/add_injury_to_player', methods=['POST'])
def add_injury_to_player():
    update_time()
    try:
        data = request.get_json()
        player_name = data.get('player_name', '').strip().lower()
        injury = data.get('injury', '').strip().lower()

        # Verifica esistenza giocatore
        player_ref = db.collection('players').document(player_name)
        player_doc = player_ref.get()
        if not player_doc.exists:
            return jsonify({'success': False, 'message': 'Player not found'}), 404

        # Verifica esistenza infortunio
        injury_doc = db.collection('injuries').document(injury).get()
        if not injury_doc.exists:
            return jsonify({'success': False, 'message': 'Injury not found'}), 404

        # MODIFICA QUI: Correggi l'accesso al campo Time
        injury_time = injury_doc.to_dict().get('Time', 0)  # Prima otteniamo il dict, poi usiamo .get()
        
        player_data = player_doc.to_dict()
        injury_list = player_data.get('Injury list', [])
        
        if injury not in injury_list:
            injury_list.append(injury)
            
            player_ref.update({
                'Injury list': injury_list,
                'Time': max(injury_time, player_data.get('Time', 0)),
                'Last date': datetime.now()
            })

        return jsonify({
            'success': True,
            'message': 'Injury added to player'
        })

    except Exception as e:
        print("ERRORE:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500

def update_time():
    players_ref = db.collection("players")
    now = datetime.now()

    for doc in players_ref.stream():
        data = doc.to_dict()
        last_date = data.get("Last date")
        time_value = data.get("Time", 0)

        if last_date:
            try:
                days_passed = (now.date() - last_date.replace(tzinfo=None).date()).days

                if days_passed > 0:
                    new_time = max(time_value - days_passed, 0)
                    update_data = {
                        "Time": new_time,
                        "Last date": now
                    }

                    # Se il tempo è a zero, svuota la Injury list
                    if new_time == 0:
                        update_data["Injury list"] = []

                    players_ref.document(doc.id).update(update_data)
                    print(f"{doc.id}: -{days_passed} giorni → Time = {new_time}")
                else:
                    print(f"{doc.id}: nessun giorno da scalare.")
            except Exception as e:
                print(f"Errore con {doc.id}: {e}")
        else:
            players_ref.document(doc.id).update({
                "Last date": now
            })
            print(f"{doc.id}: inizializzato con Last date.")

### EXERCISES ###

def ankle_circles():
    data = {"nao_ip": nao_ip, "nao_port": nao_port}
    json_data = json.dumps(data)
    url = "http://127.0.0.1:5011/ankle_circles/" + requests.utils.quote(json_data)
    response = requests.get(url)
    logger.info(response.text)
    return jsonify({"code": 200}), 200

def single_leg_balance():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/single_leg_balance/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def eccentric_calf_raises_on_step():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/eccentric_calf_raises_on_step/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def plantar_mobilization():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/plantar_mobilization/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def quadriceps_isometrics():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/quadriceps_isometrics/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def mini_squats():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/mini_squats/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def static_lunges():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/static_lunges/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def quad_set():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/quad_set/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def isometric_contraction():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/isometric_contraction/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def calf_raises():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/calf_raises/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def isometric_hip_adduction():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/isometric_hip_adduction/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

def bird_dog():
    data     = {"nao_ip":nao_ip, "nao_port":nao_port}
    url      = "http://127.0.0.1:5011/bird_dog/" + str(data) 
    response = requests.get(url, json=data)
    logger.info(str(response.text))
    return jsonify({"code": 200}), 200

'''
CODICI JSON
200 messaggio inviato
201 messaggio ricevuto
500 errore
'''

def nao_start():
    nao_volume_sound(80)
    nao_autonomous_life()
    nao_eye_white()
    nao_wakeup()
    
    nao_animatedSayText("Ciao sono Peara!")
    
    nao_stand()
    if face_tracker:
        nao_face_tracker()
    else:
        nao_stop_face_tracker()


if __name__ == "__main__":
    startTime  = time.time()
       
    #nao_start()

    nao_autonomous_life()
    nao_eye_white()
    nao_wakeup()
    nao_stand()

    #nao_tts_audiofile("speech01.mp3")
    #nao_touch_head_audiorecorder()
    #nao_audiorecorder(5)
    #nao_train_move()

    '''
    cred = credentials.Certificate("nao-basket-e5f9e-firebase-adminsdk-fbsvc-7feac96803.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    update_time()
    '''

    nao_volume_sound(100)
    update_time()

    #nao.principale()

    #nao.shortcut()

    #nao.info_giocatore_app("Nicola")

    app.secret_key = os.urandom(12)
    app.run(host=config_helper.srv_host, port=config_helper.srv_port, debug=config_helper.srv_debug)