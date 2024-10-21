

class GlobalConfig:
    """
    Configurador global del backend y otros sistemas
    """
    # WINDOWS DEBUGGING
    # Permite compatibilidad de ejecucion con sistemas windows
    debug_mode = True

    admin_users = {
        "zau1": "231551244",
        "maxo": "toya300"
    }

    # Comenzar comunicacion con arduino RASP: /dev/ttyUSB0
    arduino_serial_port = "COM6"
    arduino_serial_baud_rate = 500000
    arduino_debug_payloads_level = 0 # 0 no mostrar, 1 mostrar payloads recibidos, 2 mostrar payloads enviados y recibidos
