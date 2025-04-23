from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

# Inizializzazione Flask
app = Flask(__name__)
CORS(app)  # Abilita CORS per tutte le route

# Configurazione Firebase
cred = credentials.Certificate("nao-basket-e5f9e-firebase-adminsdk-fbsvc-7feac96803.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Serve l'HTML
@app.route('/')
def serve_html():
    return send_from_directory(os.path.dirname(__file__), 'database_interface.html')  # Parentesi aggiunta qui

# API Endpoints
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
    try:
        data = request.json
        player_name = data.get('player_name', '').strip().lower()
        injury = data.get('injury', '').strip().lower()

        if not all([player_name, injury]):
            return jsonify({'success': False, 'message': 'Both fields are required'}), 400

        # Verifica esistenza giocatore
        player_ref = db.collection('players').document(player_name)
        player_doc = player_ref.get()
        if not player_doc.exists:
            return jsonify({'success': False, 'message': 'Player not found'}), 404

        # Verifica esistenza infortunio
        injury_doc = db.collection('injuries').document(injury).get()
        if not injury_doc.exists:
            return jsonify({'success': False, 'message': 'Injury not found'}), 404

        # Aggiorna dati giocatore
        injury_time = injury_doc.get('Time', 0)
        player_data = player_doc.to_dict()
        
        injury_list = player_data.get('Injury list', [])
        if injury not in injury_list:  # Evita duplicati
            injury_list.append(injury)

        player_ref.update({
            'Injury list': injury_list,
            'Time': max(injury_time, player_data.get('Time', 0)),
            'Last date': datetime.now()
        })
        return jsonify({'success': True, 'message': 'Injury added to player'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5012, debug=True)