# -*- coding: utf-8 -*-

'''
python2 64 bit
pip2 install -r requirements.txt
python2 main.py
''' 

# Modules
from naoqi import ALProxy
from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, send_file
import cv2
import time
import math
import numpy as np
import random
import paramiko
import utilities
from logging_helper import logger
import threading

app  = Flask(__name__)

nao_ip = "192.168.0.118"
nao_port=9559
motion = ALProxy("ALMotion", nao_ip, nao_port)
tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)


#################################
# FUNZIONI FLASK SERVER Python2 #
#################################
def nao_get_image(nao_ip, nao_port):
    video_proxy = ALProxy("ALVideoDevice", nao_ip, nao_port)            # NAO webcam

    # Set the camera parameters
    name_id          = "video_image_" + str(random.randint(0,100))      # The same Name could be used only six time
    camera_id        = 0                                                # Use the top camera (1 for bottom camera)
    resolution       = 1                                                # Image of 320*240px
    color_space      = 13                                               # RGB
    camera_fps       = 30                                               # fps
    brightness_value = 55                                               # default of 55
    video_proxy.setParameter(camera_id, 0, brightness_value)            # brightness

    # Subscribe to the video feed
    video_client = video_proxy.subscribeCamera(name_id, camera_id, resolution, color_space, camera_fps)
    try:
        while True:
            image          = video_proxy.getImageRemote(video_client)   # Capture a frame from the camera
            
            image_width    = image[0]
            image_height   = image[1]
            image_channels = 3
            image_data     = np.frombuffer(image[6], dtype=np.uint8).reshape((image_height, image_width, image_channels))

            desired_width  = 640
            desired_height = 480
            resized_image  = cv2.resize(image_data, (desired_width, desired_height))

            ret, buffer    = cv2.imencode('.jpg', resized_image)            
            frame          = buffer.tobytes()

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    except Exception as e:
        logger.error(str(e))
    finally:
        video_proxy.unsubscribe(video_client)

        
@app.route('/nao_webcam/<params>', methods=['GET'])
def nao_webcam(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json           = eval(params)
                nao_ip         = json['nao_ip']
                nao_port       = json['nao_port']

                return Response(nao_get_image(nao_ip, nao_port), mimetype='multipart/x-mixed-replace; boundary=frame')
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500 
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500


@app.route('/nao_audiorecorder/<params>', methods=['GET'])
def nao_get_audio(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "nao_user":value, "nao_password":value, "sec_sleep":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
                nao_user     = json['nao_user']
                nao_password = json['nao_password']
                sec_sleep    = json['sec_sleep']

                audio_device_proxy = ALProxy("ALAudioRecorder", nao_ip, nao_port)
                remote_path = "/data/home/nao/recordings/microphones/microphone_audio.wav" # sul nao
                sample_rate = 16000
                
                # Registra l'audio dal microfono del NAO per 'sec_sleep' secondi
                audio_data = audio_device_proxy.startMicrophonesRecording(remote_path, "wav", sample_rate, [0, 0, 1, 0])
                time.sleep(sec_sleep)
                audio_device_proxy.stopMicrophonesRecording()

                # Connessione SSH al Nao
                try:
                    transport = paramiko.Transport((nao_ip, 22))                 
                    transport.connect(username=nao_user, password=nao_password)  
                    scp = paramiko.SFTPClient.from_transport(transport)          
                    local_path  = "recordings/microphone_audio.wav"
                    scp.get(remote_path, local_path)
                except Exception as e:
                    logger.error(str(e))
                    return jsonify({'code': 500, 'message': str(e)}), 500
                finally:
                    scp.close()         
                    transport.close()   

                audio_device_proxy = None
                return send_file(local_path, as_attachment=True)
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500  
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500
    

service_active = False
@app.route('/nao_touch_head_audiorecorder/<params>', methods=['GET'])  
def nao_touch_head_audiorecorder(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "nao_user":value, "nao_password":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
                nao_user     = json['nao_user']
                nao_password = json['nao_password']

                memory_proxy       = ALProxy("ALMemory", nao_ip, nao_port)
                audio_device_proxy = ALProxy("ALAudioRecorder", nao_ip, nao_port)
                remote_path        = "/data/home/nao/recordings/microphones/microphone_audio.wav" # sul nao
                sample_rate        = 16000

                def on_middle_tactil_touched(value):
                    if value == 1.0:
                        print("Middle Tactil Touched - attivato.")

                        global service_active
                        if service_active:
                            print("stopMicrophonesRecording - Il servizio è stato disattivato.")
                            service_active = False
                            # Inserisci qui il codice per fermare il servizio
                            audio_device_proxy.stopMicrophonesRecording()
                            raise Exception("Sensore centrale toccato!") 
                        else:
                            print("startMicrophonesRecording - Il servizio è stato attivato.")
                            service_active = True
                            # Inserisci qui il codice per avviare il servizio
                            audio_data = audio_device_proxy.startMicrophonesRecording(remote_path, "wav", sample_rate, [0, 0, 1, 0])
                        
                try:
                    while True:
                        is_touched = memory_proxy.getData("MiddleTactilTouched")
                        on_middle_tactil_touched(is_touched)
                        time.sleep(0.1)
                except Exception as e:
                    print("Middle Tactil Touched - disattivato.")

                # Connessione SSH al Nao
                try:
                    transport = paramiko.Transport((nao_ip, 22))                 
                    transport.connect(username=nao_user, password=nao_password)  
                    scp = paramiko.SFTPClient.from_transport(transport)          
                    local_path  = "recordings/microphone_audio.wav"
                    scp.get(remote_path, local_path)
                except Exception as e:
                    logger.error(str(e))
                    return jsonify({'code': 500, 'message': str(e)}), 500
                finally:
                    scp.close()         
                    transport.close()   

                audio_device_proxy = None
                return send_file(local_path, as_attachment=True)
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500  
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500


@app.route('/nao_face_tracker/<params>', methods=['GET'])  
def nao_face_tracker(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json     = eval(params)
                nao_ip   = json['nao_ip']
                nao_port = json['nao_port']

                tracker_proxy = ALProxy("ALTracker", nao_ip, nao_port)
                targetName = "Face"
                faceWidth  = 0.1
                tracker_proxy.setMode("Head")
                tracker_proxy.registerTarget(targetName, faceWidth)
                tracker_proxy.track(targetName)
                return jsonify({'code': 200, 'function': 'nao_face_tracker(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500  
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500


@app.route('/nao_stop_face_tracker/<params>', methods=['GET'])  
def nao_stop_face_tracker(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json     = eval(params)
                nao_ip   = json['nao_ip']
                nao_port = json['nao_port']

                tracker_proxy = ALProxy("ALTracker", nao_ip, nao_port)
                tracker_proxy.stopTracker()
                tracker_proxy.unregisterAllTargets()
                return jsonify({'code': 200, 'function': 'nao_stop_face_tracker(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500 
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500 


@app.route('/nao_autonomous_life/<params>', methods=['GET'])  
def nao_autonomous_life(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json     = eval(params)
                nao_ip   = json['nao_ip']
                nao_port = json['nao_port']
                state    = "disabled"

                life_proxy = ALProxy("ALAutonomousLife", nao_ip, nao_port)              
                life_proxy.setState(state)                                              
                life_proxy = None                                                       
                return jsonify({'code': 200, 'function': 'nao_autonomous_life(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500  
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500
            

@app.route('/nao_wakeup/<params>', methods=['GET'])  
def nao_wakeup(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json     = eval(params)
                nao_ip   = json['nao_ip']
                nao_port = json['nao_port']

                motion_proxy = ALProxy("ALMotion", nao_ip, nao_port)                    
                motion_proxy.wakeUp()                                                   
                motion_proxy = None   
                return jsonify({'code': 200, 'function': 'nao_wakeup(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500   
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500                                                


@app.route('/nao_eye_white/<params>', methods=['GET'])  
def nao_eye_white(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json     = eval(params)
                nao_ip   = json['nao_ip']
                nao_port = json['nao_port']

                leds_proxy = ALProxy("ALLeds", nao_ip, nao_port)                        
                eye_group_name = "FaceLeds"                                             
                eye_color = [255, 255, 255]                                             # RGB values for white
                value_color = 256*256*eye_color[0] + 256*eye_color[1] + eye_color[2]
                leds_proxy.fadeRGB(eye_group_name, value_color, 0.5)                    # 0.5 is the duration in seconds
                leds_proxy = None
                return jsonify({'code': 200, 'function': 'nao_eye_white(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500  
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500                                                        


@app.route('/nao_animatedSayText/<params>', methods=['GET'])  
def nao_animatedSayText(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "text_to_say":value}
                json        = eval(params)
                nao_ip      = json['nao_ip']
                nao_port    = json['nao_port']
                text_to_say = json['text_to_say']

                tts_proxy = ALProxy("ALAnimatedSpeech", nao_ip, nao_port)                          
                animated_speech_config = {"bodyLanguageMode": "contextual"}             
                tts_proxy.say(text_to_say, animated_speech_config)                                                             
                tts_proxy = None
                return jsonify({'code': 200, 'function': 'nao_animatedSayText(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500   
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500  


@app.route('/nao_standInit/<params>', methods=['GET'])  
def nao_standInit(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json     = eval(params)
                nao_ip   = json['nao_ip']
                nao_port = json['nao_port']

                posture_proxy = ALProxy("ALRobotPosture", nao_ip, nao_port)                        
                posture_proxy.goToPosture("StandInit", 0.8)                             
                posture_proxy = None
                return jsonify({'code': 200, 'function': 'nao_standInit(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500                                                 


@app.route('/nao_stand/<params>', methods=['GET'])            
def nao_stand(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json     = eval(params)
                nao_ip   = json['nao_ip']
                nao_port = json['nao_port']

                posture_proxy = ALProxy("ALRobotPosture", nao_ip, nao_port)                        
                posture_proxy.goToPosture("Stand", 0.8)                                 
                posture_proxy = None  
                return jsonify({'code': 200, 'function': 'nao_stand(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500


@app.route('/nao_volume_sound/<params>', methods=['GET'])    
def nao_volume_sound(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "volume_level":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
                volume_level = json['volume_level']

                audio_proxy = ALProxy("ALAudioDevice", nao_ip, nao_port)
                audio_proxy.setOutputVolume(volume_level)
                audio_proxy = None
                return jsonify({'code': 200, 'function': 'nao_volume_sound(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500


@app.route('/nao_move_head/<params>', methods=['GET']) 
def nao_move_head(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "theta":value, "head_pitch_angle":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
                theta        = json["theta"]
                head_pitch_angle = json["head_pitch_angle"]

                motion_proxy = ALProxy("ALMotion", nao_ip, nao_port)
                motion_proxy.setAngles("HeadYaw", theta, 0.5)                           
                motion_proxy.setAngles("HeadPitch", head_pitch_angle, 0.5)
                motion_proxy = None
                return jsonify({'code': 200, 'function': 'nao_move_head(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500
    

@app.route('/nao_move_toward/<params>', methods=['GET'])  
def nao_move_toward(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "x":value, "y":value, "theta":value, "sec":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
                x            = json["x"]
                y            = json["y"]
                theta        = json["theta"]
                sec          = json["sec"]

                motion_proxy = ALProxy("ALMotion", nao_ip, nao_port)
                frequency = 1.0
                motion_proxy.moveToward(x, y, theta, [["Frequency", frequency]])
                time.sleep(sec)                                                         
                motion_proxy.stopMove()                                                 
                motion_proxy = None
                return jsonify({'code': 200, 'function': 'nao_move_toward(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500

    
@app.route('/nao_move_to/<params>', methods=['GET']) 
def nao_move_to(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "x":value, "y":value, "theta":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
                x            = json["x"]
                y            = json["y"]
                theta        = json["theta"]

                theta = math.radians(theta)
                motion_proxy = ALProxy("ALMotion", nao_ip, nao_port)
                motion_proxy.moveTo(x, y, theta)
                motion_proxy.stopMove()                                                 
                motion_proxy = None
                return jsonify({'code': 200, 'function': 'nao_move_to(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500

    
@app.route('/nao_move_fast/<params>', methods=['GET']) 
def nao_move_fast(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "angle":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
                angle        = json['angle']

                motion_proxy = ALProxy("ALMotion", nao_ip, nao_port)
                motion_proxy.move(1.0, 0.0, angle,  [ 
                                                    ["MaxStepX", 0.08],             # step of 2 cm in front
                                                    #["MaxStepY", 0.16],            # default value
                                                    #["MaxStepTheta", 0.4],         # default value
                                                    ["MaxStepFrequency", 1.0],      # low frequency
                                                    ["StepHeight", 0.01],           # step height of 1 cm
                                                    ["TorsoWx", 0.0],               # default value
                                                    #["TorsoWy", 0.1]               # torso bend 0.1 rad in front
                                                ])
                motion_proxy.move(1.0, 0.0, 0.0,  [ 
                                                    ["MaxStepX", 0.08],             # step of 2 cm in front
                                                    #["MaxStepY", 0.16],            # default value
                                                    #["MaxStepTheta", 0.4],         # default value
                                                    ["MaxStepFrequency", 1.0],      # low frequency
                                                    ["StepHeight", 0.01],           # step height of 1 cm
                                                    ["TorsoWx", 0.0],               # default value
                                                    #["TorsoWy", 0.1]               # torso bend 0.1 rad in front
                                                ])
                '''
                motion_proxy.moveToward(1.0, 0.0, angle, motion_proxy.getMoveConfig("Max"))
                time.sleep(10.0)
                motion_proxy.stopMove()
                '''
                return jsonify({'code': 200, 'function': 'nao_move_fast(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500
    

@app.route('/nao_move_fast_stop/<params>', methods=['GET']) 
def nao_move_fast_stop(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']

                motion_proxy = ALProxy("ALMotion", nao_ip, nao_port)
                motion_proxy.stopMove()
                motion_proxy = None
                return jsonify({'code': 200, 'function': 'nao_move_fast_stop(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500
    

@app.route('/nao_animations/<params>', methods=['GET']) 
def nao_animations(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
    
                behavior_manager = ALProxy("ALBehaviorManager", nao_ip, nao_port)
                behavior_name = "animations/Stand/Gestures/Hey_2"
                behavior_manager.runBehavior(behavior_name)

                return jsonify({'code': 200, 'function': 'nao_animations(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500


@app.route('/nao_tts_audiofile/<params>', methods=['GET'])  
def nao_tts_audiofile(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value, "filename":value, "nao_user":value, "nao_password":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']
                filename     = json['filename']
                nao_user     = json['nao_user']
                nao_password = json['nao_password']

                # Carico il filename sul Nao tramite SSH
                local_file_path  = "tts_audio/" + filename
                remote_file_path = "/data/home/nao/tts_audio/" + "audio.mp3"

                try:
                    transport = paramiko.Transport((nao_ip, 22))
                    transport.connect(username=nao_user, password=nao_password)
                    sftp = paramiko.SFTPClient.from_transport(transport)
                    sftp.put(local_file_path, remote_file_path)
                except Exception as e:
                    logger.error(str(e))
                    return jsonify({'code': 500, 'message': str(e)}), 500
                finally:
                    sftp.close()
                    transport.close()
                    
                # Riproduco file audio dal Nao
                audio_proxy            = ALProxy("ALAudioPlayer", nao_ip, nao_port)
                animated_speech_proxy  = ALProxy("ALAnimatedSpeech", nao_ip, nao_port)
                animated_speech_config = {"bodyLanguageMode": "contextual"}
                text = "\\pau=1000\\ "

                def bodyLanguageMode(stop_event):
                    while not stop_event.is_set():
                        animated_speech_proxy.say(text, animated_speech_config)

                # Crea e avvia il thread per i movimenti
                stop_event      = threading.Event()
                movement_thread = threading.Thread(target=bodyLanguageMode, args=(stop_event,))
                movement_thread.start()

                audio_proxy.playFile("/data/home/nao/tts_audio/" + "audio.mp3")
                stop_event.set()

                # Attende che il thread del movimento termini
                movement_thread.join()

                animated_speech_proxy = None
                audio_proxy = None
                return jsonify({'code': 200, 'function': 'nao_tts_audiofile(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500   
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500  


@app.route('/nao_standup/<params>', methods=['GET']) 
def nao_standup(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']

                posture_proxy = ALProxy("ALRobotPosture", nao_ip, nao_port)                        
                posture_proxy.goToPosture("Stand", 0.8)                                 
                posture_proxy = None 

                return jsonify({'code': 200, 'function': 'nao_standup(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500


@app.route('/nao_sitdown/<params>', methods=['GET']) 
def nao_sitdown(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']

                posture_proxy = ALProxy("ALRobotPosture", nao_ip, nao_port)                        
                posture_proxy.goToPosture("Sit", 0.8)                                 
                posture_proxy = None 
    
                return jsonify({'code': 200, 'function': 'nao_sitdown(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500


@app.route('/nao_crouch/<params>', methods=['GET']) 
def nao_crouch(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']

                posture_proxy = ALProxy("ALRobotPosture", nao_ip, nao_port)                        
                posture_proxy.goToPosture("Crouch", 0.8)                                 
                posture_proxy = None 
    
                return jsonify({'code': 200, 'function': 'nao_crouch(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK'}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500
    

@app.route('/nao_get_sensor_data/<params>', methods=['GET']) 
def nao_get_sensor_data(params):
    if (params != None and params != ''):
        if request.method == 'GET':
            try:
                #{"nao_ip":value, "nao_port":value}
                json         = eval(params)
                nao_ip       = json['nao_ip']
                nao_port     = json['nao_port']

                memory_proxy = ALProxy("ALMemory", nao_ip, nao_port)
                gyro_x = memory_proxy.getData("Device/SubDeviceList/InertialSensor/GyroscopeX/Sensor/Value")
                gyro_y = memory_proxy.getData("Device/SubDeviceList/InertialSensor/GyroscopeY/Sensor/Value")
                acc_x  = memory_proxy.getData("Device/SubDeviceList/InertialSensor/AccelerometerX/Sensor/Value")
                acc_y  = memory_proxy.getData("Device/SubDeviceList/InertialSensor/AccelerometerY/Sensor/Value")
                acc_z  = memory_proxy.getData("Device/SubDeviceList/InertialSensor/AccelerometerZ/Sensor/Value")
                data   = [gyro_x, gyro_y, acc_x, acc_y, acc_z]
                memory_proxy = None

                return jsonify({'code': 200, 'function': 'nao_get_sensor_data(ip:' + str(nao_ip) + ' port:' + str(nao_port) + ')', 'status':'OK', 'data':data}), 200
            except Exception as e:
                logger.error(str(e))
                return jsonify({'code': 500, 'message': str(e)}), 500
        else:
            return jsonify({'code': 500, 'message': 'methods error'}), 500
    else:
        return jsonify({'code': 500, 'message': 'params error'}), 500

### EXERCISES ###
     
@app.route('/ankle_circles_nao/<params>', methods=['GET'])
def ankle_circles_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)

        motion.setStiffnesses("RAnklePitch", 1.0)
        motion.setStiffnesses("RAnkleRoll", 1.0)
        motion.setAngles("RAnklePitch", 0.1, 0.5) # leggero sollevamento del piede
        time.sleep(1)
        tts.say("Rotazioni delle caviglie, 3 serie da 20")
        for set_num in range(3):
            # Senso orario
            tts.say("Set" + str(set_num + 1) + "in senso orario")
            for i in range(10):
                motion.setAngles("RAnkleRoll", 0.2, 0.5)
                time.sleep(0.5)
                motion.setAngles("RAnkleRoll", -0.2, 0.5)
                time.sleep(0.5)
            tts.say("Ora in senso antiorario")
            for i in range(10):
                motion.setAngles("RAnkleRoll", -0.2, 0.5)
                time.sleep(0.5)
                motion.setAngles("RAnkleRoll", 0.2, 0.5)
                time.sleep(0.5)
                
        return jsonify({"code" : 200}), 200
    except Exception as e:
        print(e)
        return jsonify({'code': 500, 'message': str(e)}), 500


@app.route('/single_leg_balance_nao/<params>', methods=['GET'])
def single_leg_balance_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        for set_num in range(3):
            tts.say("Set" + str(set_num + 1) + "bilanciamento su una gamba")
            motion.setAngles("LHipPitch", -0.2, 0.3)
            time.sleep(0.5)
            motion.setStiffnesses("LHipPitch", 0.0)
            time.sleep(30)
            motion.setAngles("LHipPitch", 0.0, 0.3)
            time.sleep(0.5)

        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    

@app.route('/eccentric_calf_raises_on_step_nao/<params>', methods=['GET'])
def eccentric_calf_raises_on_step_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        motion.setStiffnesses("RAnklePitch", 1.0)
        motion.setStiffnesses("RAnkleRoll", 1.0)
        motion.setAngles("RAnklePitch", 0.1, 0.5)
        time.sleep(1)

        for set_num in range(3):
            tts.say("Set" + (set_num + 1) + "di calf raises")
            for rep in range(15):
                motion.setAngles("LAnklePitch", -0.3, 0.2)  # salita
                motion.setAngles("RAnklePitch", -0.3, 0.2)
                time.sleep(0.5)
                motion.setAngles("LAnklePitch", 0.1, 0.1)   # discesa
                motion.setAngles("RAnklePitch", 0.1, 0.1)
                time.sleep(0.5)
            motion.setAngles(["LAnklePitch", "RAnklePitch"], [0.0, 0.0], 0.2)
            time.sleep(1)
        
        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@app.route('/plantar_mobilization_nao/<params>', methods=['GET'])
def plantar_mobilization_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)

        for set_num in range(3):
            tts.say("Set" + str(set_num + 1) + "mobilizzazione plantare")
            for rep in range(15):
                motion.setAngles(["LAnklePitch", "RAnklePitch"], [-0.1, -0.1], 0.2)  # punta
                time.sleep(0.3)
                motion.setAngles(["LAnklePitch", "RAnklePitch"], [0.1, 0.1], 0.2)   # tallone
                time.sleep(0.3)
            motion.setAngles(["LAnklePitch", "RAnklePitch"], [0.0, 0.0], 0.2)

        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    

@app.route('/quadriceps_isometrics_nao/<params>', methods=['GET'])
def quadriceps_isometrics_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        for set_num in range(3):
            tts.say("Set" + str(set_num + 1) + "isometrici quadricipite")
            for rep in range(10):
                motion.setAngles(["LKneePitch", "RKneePitch"], [0.0, 0.0], 0.1)  # ginocchio esteso
                time.sleep(1)

        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@app.route('/mini_squats_nao/<params>', methods=['GET'])
def mini_squats_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        tts.say("Mini-squat, 3 serie da 12")
        for set_num in range(3):
            tts.say("Serie" + str(set_num + 1))
            for rep in range(12):
                # Piegamento (circa 45°)
                motion.setAngles(["LKneePitch", "RKneePitch"], [0.5, 0.5], 0.2)
                time.sleep(0.8)
                # Ritorno in posizione eretta
                motion.setAngles(["LKneePitch", "RKneePitch"], [0.0, 0.0], 0.2)
                time.sleep(0.8)

        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/static_lunges_nao/<params>', methods=['GET'])
def static_lunges_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        tts.say("Static lunges, 3 serie da 10 per gamba")
        for set_num in range(3):
            tts.say("Serie" + str(set_num + 1))
            for leg in ["destra", "sinistra"]:
                tts.say("Gamba {leg}")
                for rep in range(10):
                    if leg == "destra":
                        motion.setAngles("RKneePitch", 0.4, 0.2)  # Piegamento
                        time.sleep(0.5)
                        motion.setAngles("RKneePitch", 0.0, 0.2)  # Ritorno
                        time.sleep(0.5)
                    else:
                        motion.setAngles("LKneePitch", 0.4, 0.2)
                        time.sleep(0.5)
                        motion.setAngles("LKneePitch", 0.0, 0.2)
                        time.sleep(0.5)
        
        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@app.route('/quad_set_nao/<params>', methods=['GET'])
def quad_set_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        tts.say("Quad Set, 3 serie da 10 contrazioni")
        for set_num in range(3):
            tts.say("Serie" + str(set_num + 1))
            for rep in range(10):
                motion.setAngles(["RKneePitch", "LKneePitch"], [0.0, 0.0], 0.2)
                time.sleep(1.0)
                motion.setAngles(["RKneePitch", "LKneePitch"], [0.1, 0.1], 0.2)
                time.sleep(0.5)
       
        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    

@app.route('/isometric_contraction_nao/<params>', methods=['GET'])
def isometric_contraction_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        tts.say("Isometric contraction, 3 serie da 10")
        for set_num in range(3):
            tts.say("Serie" + str(set_num + 1))
            for rep in range(10):
                # Posizione semiflessa mantenuta brevemente
                motion.setAngles(["RKneePitch", "LKneePitch"], [0.3, 0.3], 0.2)
                time.sleep(2.0)
                # Ritorno a posizione eretta
                motion.setAngles(["RKneePitch", "LKneePitch"], [0.0, 0.0], 0.2)
                time.sleep(0.5)
       
        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@app.route('/calf_raises_nao/<params>', methods=['GET'])
def calf_raises_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        tts.say("Calf raises, 3 serie da 15")
        for set_num in range(3):
            tts.say("Serie" + str(set_num + 1))
            for rep in range(15):
                # Solleva i talloni (spinta in punta di piedi)
                motion.setAngles(["LAnklePitch", "RAnklePitch"], [-0.3, -0.3], 0.2)
                time.sleep(0.8)
                # Ritorno in posizione neutra
                motion.setAngles(["LAnklePitch", "RAnklePitch"], [0.0, 0.0], 0.2)
                time.sleep(0.8)

        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
    

@app.route('/isometric_hip_adduction_nao/<params>', methods=['GET'])
def isometric_hip_adduction_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        tts.say("Isometric hip adduction, 3 serie da 15 contrazioni simulate")
        for set_num in range(3):
            tts.say("Serie" + str(set_num + 1))
            for rep in range(15):
                # Simula contrazione avvicinando le gambe
                motion.setAngles(["LHipRoll", "RHipRoll"], [-0.1, 0.1], 0.2)
                time.sleep(0.5)
                # Ritorno neutro
                motion.setAngles(["LHipRoll", "RHipRoll"], [0.0, 0.0], 0.2)
                time.sleep(0.5)

        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@app.route('/bird_dog_nao/<params>', methods=['GET'])
def bird_dog_nao(params):
    try:
        json         = eval(params)
        nao_ip       = json['nao_ip']
        nao_port     = json['nao_port']
        motion = ALProxy("ALMotion", nao_ip, nao_port)
        tts = ALProxy("ALTextToSpeech", nao_ip, nao_port)
        
        tts.say("Bird-dog simulato, 3 serie da 10 per lato")
        for set_num in range(3):
            tts.say("Serie" + str(set_num + 1))
            for rep in range(10):
                
                motion.setAngles(["LHipPitch", "RShoulderPitch"], [-0.3, -0.5], 0.2)
                time.sleep(1.0)
                motion.setAngles(["LHipPitch", "RShoulderPitch"], [0.0, 1.5], 0.2)
                time.sleep(0.5)

                motion.setAngles(["RHipPitch", "LShoulderPitch"], [-0.3, -0.5], 0.2)
                time.sleep(1.0)
                motion.setAngles(["RHipPitch", "LShoulderPitch"], [0.0, 1.5], 0.2)
                time.sleep(0.5)
        
        return jsonify({"code" : 200}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


# API
@app.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({'code': 200, 'status': 'online', 'elapsed time': utilities.getElapsedTime(startTime)}), 200


# INDEX
@app.route('/', methods=['GET'])
def services():
    return render_template('index.html')


'''
CODICI JSON
200 messaggio inviato
201 messaggio ricevuto
500 errore
'''


if __name__ == "__main__":
    startTime = time.time()
    app.run(host="0.0.0.0", port=5011, debug=False)