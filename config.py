from decouple import config


class GlobalConfig:
    """
    Configurador global del backend y otros sistemas
    """
    # WINDOWS DEBUGGING
    # Permite compatibilidad de ejecucion con sistemas windows
    debug_mode = config("WINDOWS_DEBUGING").lower() == "true"

    admin_users = {
        "zau1": "231551244",
        "maxo": "toya300"
    }
    
    animations_file = 'animations.json'
    
    log_socket = False

    # Comenzar comunicacion con arduino RASP: /dev/ttyUSB0
    arduino_serial_port = config("SERIAL_PORT")
    arduino_serial_baud_rate = 500000
    # 0 no mostrar, 1 mostrar payloads recibidos, 2 mostrar payloads enviados y recibidos , 3 mostrar payloads enviados, en buffer y recibidos
    arduino_debug_payloads_level = 0
    arduino_max_steppers = 5;


class GeneralTweaker:
    """
    Configurador general de servos y steppers
    """

    DM556 = {
        "steps_per_rev": 400,
        "min_step_time": 500,
        "max_step_time": 6500,
    }

    TB6600 = {
        "steps_per_rev": 400,
        "min_step_time": 500,
        "max_step_time": 6500,
    }
