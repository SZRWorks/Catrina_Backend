from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from main import LogicThread
from config import GlobalConfig
import random
import json


# Aplicaciones servidor
app = Flask(__name__)

app.config['SECRET_KEY'] = 'MaxEsPuto.secret'
socket = SocketIO(app, cors_allowed_origins="*")

# Hilo logico principal
logic_app = LogicThread()


# Usuarios admin
admin_users = GlobalConfig.admin_users
users = []
user_info = {}  # {"Username": [#pedidos, isAdmin], ...},

# Valor semi-unico que identifica a la sesion
session_secret = random.randint(0, 10**10)


@socket.on("connect")
def on_socket_connection():
    pass


@socket.on("disconnect")
def on_socket_disconnection():
    pass


@socket.on_error()
def chat_error_handler(e):
    print('An error has occurred: ' + str(e))


@app.route('/')
def home():
    return '¿Que haces aqui wey? que pedo'


@app.route('/users/kick', methods=['POST'])
def kick():
    # Obtener la data del request
    data = request.get_json()

    admin_name = data["adminUser"]
    user_to_kick = data["userToKick"]

    admin_name = admin_name.lower()
    user_to_kick = user_to_kick.lower()

    # Comprobar que el usuario intentando hacer el ban sea un administrador
    if ((user_to_kick in admin_users and user_to_kick != 'guest') or not admin_name in admin_users):
        return jsonify({
            "success":  True,
            "error": 403,
            "message": "No tienes los permisos para realizar esta accion"
        }), 403

    # Comprobar que el usuario este suscrito al bar
    if (not user_to_kick in users):
        return jsonify({
            "success":  True,
            "error": 403,
            "message": "El usuario no existe en el bar"
        }), 403

    users.remove(user_to_kick)
    del user_info[user_to_kick]
    print(user_to_kick + " ha sido expulsado del bar")

    return {"Ok": "Ok"}


@app.route('/users', methods=['GET'])
def getAll():
    _users = []
    for name, info in user_info.items():
        _users.append(
            {'name': name, 'numberOfOrders': info[0], 'isAdmin': info[1]}
        )

    return _users


@app.route('/users/validate', methods=['POST'])
def validate():
    # Obtener la data del request
    data = request.get_json()

    data['admin'] = False

    userName = data["name"]
    secret = data["secret"]
    userName = userName.lower()

    # Comprobar el secret de sesion
    if (not str(secret) == str(session_secret)):
        return jsonify({
            "success":  True,
            "error": 403,
            "message": "La sesion del usuario ha expirado"
        }), 403

    # Comprobar que el usuario este suscrito al bar
    if (not userName in users):
        return jsonify({
            "success":  True,
            "error": 403,
            "message": "El usuario no existe en el bar"
        }), 403

    return data


@app.route('/users/login', methods=['POST'])
def auth():
    # Obtener la data del request
    data = request.get_json()

    data['admin'] = False

    userName = data["name"]
    password = data["password"]
    userName = userName.lower()

    # El usuario ya está ocupado
    if (userName in users):
        return jsonify({
            "success":  True,
            "error": 406,
            "message": "Usuario ocupado"
        }), 406

    # Comprobar permisos de administrador
    if (userName in admin_users):
        if (not password == admin_users[userName]):
            return {'name': userName, 'password': None, 'admin': True}

        data['admin'] = True

    # Guardar el usuario
    users.append(userName)
    user_info[userName] = [0, data['admin']]
    print(userName + " ha entrado al bar!")

    # Enviar id secreto de sesion
    data['secret'] = session_secret
    data["name"] = userName.lower()

    return data


@app.route('/users/logout', methods=['POST'])
def logout():
    # Obtener la data del request
    data = request.get_json()

    userName = data["name"]
    userName = userName.lower()

    # El usuario ya está ocupado
    if not userName in users:
        return jsonify({
            "success":  True,
            "error": 404,
            "message": "No existe el usuario"
        }), 404

    # remover el usuario
    users.remove(userName)
    del user_info[userName]
    print(userName + " ha salido")

    return {"Ok": "Ok"}


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
