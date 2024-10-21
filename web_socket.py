from flask_socketio import SocketIO


class Socket:
    __instance = None
    
    socket = None

    @staticmethod
    def get_instance():
        if Socket.__instance == None:
            Socket()
        return Socket.__instance

    @staticmethod
    def emit(event: str, value):
        Socket.socket.emit(event, value)

    def __init__(self, socket: SocketIO):
        Socket.socket = socket;
        
        """ Virtually private constructor. """
        if Socket.__instance != None:
            raise Exception("There is a socket already setted up!")
        else:
            Socket.__instance = self