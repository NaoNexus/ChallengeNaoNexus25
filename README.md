# NaoRecovery

## Contents
* [NAO Challenge 2025](#naochallenge2025)
    * [Descrizione](#descrizione)
    * [Requirements](#requirements)
* [Coding](#coding)
* [Social](#social)
* [Authors](#authors)

## NAO Challenge 2025
The NaoChallenge offers students the opportunity to tackle real-world issues through the use of robotics and innovation. This year, the NaoNexus team has focused on Sports Rehabilitation, specifically supporting basketball players in their recovery from injuries and helping them safely return to peak performance.

### Project
For the NaoChallenge 2025, NaoNexus has developed the NaoRecovery ecosystem, composed of the NAO robot and a companion app. NaoRecovery uses the robot to provide players with a rapid preliminary assessment of their injury and to interact with them in a natural and engaging way. The app is designed as an extension of the system, allowing users to monitor and manage their rehabilitation progress efficiently.

NaoRecovery is intended to serve as a valuable support tool for basketball teams, assisting medical staff and coaches in tracking recovery timelines, improving communication with athletes, and promoting a smoother, data-driven return to play.

#### REQUIREMENTS
> [!IMPORTANT]


## Coding
### Server
The NAO robot is programmed using the Python programming language, with the codebase divided into two components: one written in Python 2 and the other in Python 3.

The Python 2 component is responsible for direct communication with the robot, managing its sensors, actuators, and low-level controls. This choice is due to the fact that the NAOqi library, which is essential for interfacing with the NAO robot, is only available in Python 2.

The Python 3 component serves as the main environment for user interactions and hosts a Flask server that facilitates communication between the robot and the companion application.

Both components are executed concurrently on a local server. The Python 3 module invokes specific functions defined in the Python 2 module, which in turn handle real-time communication with the NAO robot. This architecture ensures a modular and efficient system capable of responsive interaction and control.

A function in py3:
```python
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
```

The same funcion communicates with the robot NAO in py2:
```python
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
```

## Social


## Authors
