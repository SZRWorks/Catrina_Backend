from arduino import Arduino, ArduinoSlave, Stepper
from raspberry import Raspberry, Switch
from config import GlobalConfig
from threading import Timer
from web_socket import Socket
from states_handler import StatesHandler
from animator import AnimatonsHelper, Animator
import time
import math


class LogicThread():
    """
    Encargado de inicializar la logica y mantener
    comunicada a cada una de las partes
    """

    def __init__(self):
        self.master = Arduino(
            GlobalConfig.arduino_serial_port,
            GlobalConfig.arduino_serial_baud_rate
        )

        self.states_handler = StatesHandler(self.master)
        self.animator = Animator(self.states_handler)
        
        Socket.on('stateUpdated', self.states_handler.apply_single_state);
        

    def abort_system(self):
        """
        Aborta el sistema de manera repentina matando al programa,
        detiene toda peticion y conexion a otros sistemas.
        """
        # Detener los steppers
        self.master.digital_write(GlobalConfig.steppers_enable_pin, True)

        # Evitar que el arduino responda a mas ordenes
        self.master.kill()

        exit()
        quit()


"""
    steps: dict = {}
    def step(self, stepper: Stepper, elapsed_steps: int):
        if (not stepper in self.steps): self.steps[stepper] = 0
        self.steps[stepper] += elapsed_steps

        vel = int(self.soft_in_out(self.steps[stepper]/self.target_steps, 100)*100) #60
        stepper.setVelocity(vel)
        #print(vel)

    def ended(self):
        #self.steps = 0
        self.goint = -self.goint
        #self.test_stepper.step(self.goint)

    def ramp_ease(self, t):
        return (1-t**20) * 0.4 + 0.6
    
    def linear_ramp(self, t: float):
        return t

    def soft_in_out(self, t: float, softness: int):
        return (1 - ((2*t-1)**(100-(softness-2))))

    def sin_ease(self, t):
        return math.sin(t * math.pi)"""
