from arduino import Arduino, Stepper
from raspberry import Raspberry, Switch
from config import GlobalConfig
from threading import Timer
import time
import math


class LogicThread():
    """
    Encargado de inicializar la logica y mantener
    comunicada a cada una de las partes
    """

    arduino: Arduino = None

    goint = 0

    test_steppers: list = []
    def __init__(self):
        # Comenzar comunicacion con arduino RASP: /dev/ttyUSB0
        self.arduino = Arduino(
            GlobalConfig.arduino_serial_port,
            GlobalConfig.arduino_serial_baud_rate
        )

        # Comenzar raspberry
        Raspberry.init()
        
        self.target_steps = 400*4
        self.goint = self.target_steps
        for i in range(5):
            print(i)
            # Inicializar logica de funcionamiento
            self.test_steppers.append(Stepper(self.arduino, (2*i)+2, (2*i)+3, -1, -1))
            self.test_steppers[i].configVelocities(400, 500, 9999)

            self.test_steppers[i].setVelocity(0)
            self.test_steppers[i].step(self.target_steps)
            
            #if not (i == 0): continues
            self.test_steppers[i].on_step = [self.step]
            self.test_steppers[i].on_steps_end = [self.ended]

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
        return math.sin(t * math.pi)

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
