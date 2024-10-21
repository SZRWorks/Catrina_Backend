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
webSocket = SocketIO(app, cors_allowed_origins="*")

# Hilo logico principal
logic_app: LogicThread = LogicThread()
socket: Socket = Socket(webSocket);

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


@app.route('/testing', methods=['POST'])
def testSteps():
    # Obtener la data del request
    data = request.get_json()

    targetPosition = data["targetPosition"]

    logic_app.setToTarget(int(targetPosition))
    
    return {'xd':True}

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
