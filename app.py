import asyncio
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from animator import AnimationFrame, AnimatonsHelper
from main import LogicThread
from web_socket import Socket
from config import GlobalConfig
import random
import json


# Aplicaciones servidor
app = Flask(__name__)

app.config['SECRET_KEY'] = 'MaxEsPuto.secret'
app.config['DEBUG'] = GlobalConfig.log_socket
webSocket = SocketIO(app, cors_allowed_origins="*", logger=GlobalConfig.log_socket)

# Hilo logico principal
socket: Socket = Socket(webSocket);
logic_app: LogicThread = LogicThread();

# Valor semi-unico que identifica a la sesion
session_secret = random.randint(0, 10**10)


@webSocket.on("connect")
def on_socket_connection():
    pass


@webSocket.on("disconnect")
def on_socket_disconnection():
    pass


@webSocket.on_error()
def chat_error_handler(e):
    print('An error has occurred: ' + str(e))


@app.route('/')
def home():
    return '¿Que haces aqui wey? que pedo'

@app.route('/states', methods=['GET'])
def get_states():
    return logic_app.states_handler.get_formated_states()


@app.route('/auth', methods=['POST'])
def auth_sequence():
    sequence = request.get_json()
    
    return {'ok': GlobalConfig.admin_sequence == sequence}


@app.route('/animation', methods=['POST'])
def save_animation():
    # Obtener la data del request
    animation = request.get_json()
    
    return AnimatonsHelper.save_animation(animation);

@app.route('/animatios', methods=['PUT'])
def update_animation():
    # Obtener la data del request
    data = request.get_json()

@app.route('/animation/<id>', methods=['DELETE'])
def delete_animation(id: int):
    return {'ok': AnimatonsHelper.delete_animation(int(id))}

@app.route('/animation/<id>', methods=['GET'])
def get_animation(id: int):
    animation = AnimatonsHelper.get_animation_by_id(int(id))
    
    if not (animation):
        return jsonify({
            "success":  True,
            "error": 404,
            "message": "Resource not found"
        }), 404
    
    return animation.get_data_dict();
    
@app.route('/animations/<isAdmin>', methods=['GET'])
def get_animations(isAdmin: bool):
    return AnimatonsHelper.animations_to_dict(AnimatonsHelper.animations, bool(int(isAdmin)));


@app.route('/animator/frame', methods=['POST'])
def set_frame():
    frame = request.get_json()
    asyncio.run(logic_app.animator.apply_frame(AnimationFrame(frame)))
    
    return {'ok': True}
    
    
@app.route('/animator/play', methods=['POST'])
def play_animation():
    data = request.get_json()
    logic_app.animator.play(int(data['animation_id']))
    
    return {'ok': True}

@app.route('/system/abort', methods=['POST'])
def abort_system():
    # Obtener la data del request
    data = request.get_json()

    print("---- ABORTANDO OPERACIONES ----")

    logic_app.abort_system()

    print("ABORT")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True, use_reloader=False)
