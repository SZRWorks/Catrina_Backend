from flask import Flask, jsonify, request
from flask_socketio import SocketIO
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

# Usuarios admin
admin_users = GlobalConfig.admin_users
users = []
user_info = {}  # {"Username": [#pedidos, isAdmin], ...},

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



@app.route('/animations', methods=['POST'])
def save_animation():
    # Obtener la data del request
    animation = request.get_json()
    
    return logic_app.animator.save_animation(animation);

@app.route('/animations', methods=['PUT'])
def update_animation():
    # Obtener la data del request
    data = request.get_json()

@app.route('/animations/<id>', methods=['DELETE'])
def delete_animation(id: int):
    return {'ok': logic_app.animator.delete_animation(int(id))}

@app.route('/animations/<id>', methods=['GET'])
def get_animation(id: int):
    animation = logic_app.animator.get_animation_by_id(int(id))
    
    if not (animation):
        return jsonify({
            "success":  True,
            "error": 404,
            "message": "Resource not found"
        }), 404
    
    return animation.get_data_dict();
    
@app.route('/animations', methods=['GET'])
def get_animations():
    return logic_app.animator.animations_to_dict(logic_app.animator.animations);
    
    

@app.route('/system/abort', methods=['POST'])
def abort_system():
    # Obtener la data del request
    data = request.get_json()

    userName = data["name"]
    userName = userName.lower()

    if (not userName in admin_users):
        return jsonify({
            "success":  True,
            "error": 403,
            "message": "No tienes los permisos para realizar esta accion"
        }), 403

    print("---- ABORTANDO OPERACIONES ----")

    logic_app.abort_system()

    print("ABORT")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True, use_reloader=False)
