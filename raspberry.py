from threading import Timer
from config import GlobalConfig
import time

debug_mode = GlobalConfig.debug_mode

if (not debug_mode):
    import RPi.GPIO as GPIO


class Raspberry:
    """
    Configuraciones principales a raspberry
    """

    update_rate = 75

    __start_time = time.time()
    __end_time = time.time()
    __elapsed_time = 0
    __last_time = time.time()

    on_update = []

    @staticmethod
    def init():
        on_update = []

        if not debug_mode:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)

        Raspberry.internal_update()

    @staticmethod
    def internal_update():
        t = Timer(1/Raspberry.update_rate, Raspberry.internal_update)
        t.start()

        Raspberry.update(Raspberry.__elapsed_time)

        Raspberry.__elapsed_time = time.time() - Raspberry.__last_time
        Raspberry.__last_time = time.time()

    @staticmethod
    def update(delta_time):
        for method in Raspberry.on_update:
            method(delta_time)


class Switch():
    """
    Switch a raspberry de uso general
    """
    on_pressed = []
    on_released = []

    start_pressed = False

    pressed = False

    false_pressed = False
    pressed_time = 0
    debounce_time = 20

    def __init__(self, pin, pull_down=True):
        self.on_pressed = []
        self.on_released = []

        self.pin = pin

        if (debug_mode):
            return

        # Aplicar configuraciones
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.start_pressed = GPIO.input(pin)
        if (self.start_pressed):
            self.pressed = True
            self.__on_pressed(self.pin)

        Raspberry.on_update.append(self.__update)

    def __update(self, delta_time):
        if (debug_mode):
            return

        if (GPIO.input(self.pin)):
            self.pressed_time += delta_time
            self.false_pressed = True

            if (self.pressed_time >= self.debounce_time / 1000 and not self.pressed):
                self.pressed = True
                self.__on_pressed(self.pin)
            return

        if self.pressed:
            self.__on_released(self.pin)
        self.pressed_time = 0
        self.pressed = False
        self.false_pressed = False

    def __on_pressed(self, channel):
        print("Pressed: " + str(channel) + " : " + str(self.pin))

        if (len(self.on_pressed) == 0):
            return
        self.on_pressed[0](self)

    def __on_released(self, channel):
        print("Released: " + str(channel) + " : " + str(self.pin))

        if (len(self.on_released) == 0):
            return
        self.on_released[0](self)
