from arduino import Arduino, Stepper
from raspberry import Raspberry, Switch
from config import GlobalConfig


class LogicThread():
    """
    Encargado de inicializar la logica y mantener
    comunicada a cada una de las partes
    """
    
    arduino: Arduino = None
    

    def __init__(self):
        # Comenzar comunicacion con arduino RASP: /dev/ttyUSB0
        self.arduino = Arduino(
            GlobalConfig.arduino_serial_port,
            GlobalConfig.arduino_serial_baud_rate
        )

        # Comenzar raspberry
        Raspberry.init()

        # Inicializar logica de funcionamiento
        self.test_stepper = Stepper(self.arduino, 2, 3, -1, -1)
        self.test_stepper.configVelocities(400, 600, 9000)
        
        self.test_stepper.setVelocity(100)
        self.test_stepper.step(400)
        
    
    def abort_system(self):
        """
        Aborta el sistema de manera repentina matando al programa,
        detiene toda peticion y conexion a otros sistemas.
        """
        # Detener los steppers
        self.arduino.digital_write(GlobalConfig.steppers_enable_pin, True)
        
        # Evitar que el arduino responda a mas ordenes
        self.arduino.kill()
        
        exit()
        quit()

