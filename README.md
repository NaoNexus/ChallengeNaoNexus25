![logo_nao_darkblu_scritta](https://github.com/user-attachments/assets/42e0d805-979c-44e5-b074-5d3eaf8fa472)

# NaoRecovery

## Contents
* [NAO Challenge 2025](#nao-challenge-2025)
  * [Project](#project)
  * [Requirements](#requirements)
* [Coding](#coding)
  * [Server](#server)
  * [Dashboard](#dashboard)
  * [App](#app)
  * [Database](#database)
  * [AI](#ai)
* [Social](#social)
  * [Logo](#logo)
  * [Website](#website)
* [Linktree](#linktree)

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

The [Python 2](./coding/server/py2) component is responsible for direct communication with the robot, managing its sensors, actuators, and low-level controls. This choice is due to the fact that the NAOqi library, which is essential for interfacing with the NAO robot, is only available in Python 2.

The [Python 3](./coding/server/py3) component serves as the main environment for user interactions and hosts a Flask server that facilitates communication between the robot and the companion application.

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





### Dashboard
To support the development process and facilitate internal data management, we created NaoDashboard, a custom dashboard built with HTML, CSS, and JavaScript. This tool is intended for use by the coding team and provides a clear and organized view of the system’s data, helping us monitor performance, debug functionalities, and interact with the database more efficiently.

<img width="430" alt="image" src="https://github.com/user-attachments/assets/c328b4c3-2195-4cee-b834-f98733b08733" />





### App
Through the [companion app](./coding/app), players can track the status of their rehabilitation process and view the progress of assigned exercises. Additionally, they have the ability to call the NAO robot, which delivers a brief personalized update on their recovery status, offering encouragement and reinforcing engagement throughout the rehabilitation journey.

<img width="232" alt="image" src="https://github.com/user-attachments/assets/c9075545-c279-4c62-b244-6b6e9297085b" />





### Database
Our data is securely stored in Google Firebase’s Cloud Firestore, a scalable NoSQL cloud database designed for real-time synchronization and offline support. Utilizing Cloud Firestore allows us to efficiently manage and update rehabilitation data across multiple devices, ensuring that users and the system always have access to the most current information. This cloud-based approach also enhances data reliability, security, and accessibility, while simplifying backend maintenance and scalability as the project grows.

The database can be managed directly through our internal NaoDashboard, providing the coding team with real-time access and control over the stored data. Furthermore, the NAO robot communicates with the Cloud Firestore database via the Python 3 component, enabling seamless interaction between the robot and the cloud for updating and retrieving relevant information during the rehabilitation process.

Example of a db function:
```python
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
                'Exercise list': [],
                'Last date': datetime.now()
            })
            results.append({'success': True, 'message': f'Player "{player_name}" added successfully.'})
        except Exception as e:
            results.append({'success': False, 'message': f'Error with player "{player_name}": {str(e)}'})

    for result in results:
        print(result)
```





### AI
The NAO robot leverages [artificial intelligence](./coding/server/py3/nao_ai.py) both to process input data and to interact using a conversational prompt similar to those used in common AI chat interfaces. It also generates audio responses through text-to-speech synthesis, enabling natural and engaging communication with users. To achieve this, we utilize OpenAI’s APIs, including ChatGPT, allowing the robot to provide intelligent, context-aware interactions that enhance the rehabilitation experience.

Text generation funcion:
```python
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
```

Audio generation function:
```python
def audio_generator(testo, nome_file):
    """
    Genera un file audio da un testo usando OpenAI TTS
    e lo salva nella cartella specificata.
    """
    # Percorso di destinazione
    directory = "[percorso_file_audio]"
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
```

## Social
### Logo
The [logo](./social/loghi) is new, reflecting the complete renewal of our team. It features two stylized "N" letters representing our team name, NaoNexus — where "Nao" refers to the robot, and "Nexus," meaning "connection" in Latin, symbolizes the link between humans and machines. The overall shape of the logo is inspired by the stylized outline of the NAO robot’s head. The color palette consists of coral red and cyan, each presented in two different shades to convey dynamism and modernity.

![logo_nao_darkblue_definitivo](https://github.com/user-attachments/assets/8954b0d1-d563-4751-99ad-6a63bf0e4f55)


### Website
The website features a detailed description of the project, a presentation of our project partner, and an introduction to the development team. Additionally, it provides access to relevant resources such as documentation, updates on project milestones, and contact information to facilitate communication and collaboration with visitors.

## Linktree
https://linktr.ee/naonexus?utm_source=linktree_profile_share
