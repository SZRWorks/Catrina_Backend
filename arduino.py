from threading import Timer
from serial import Serial as NewSerial
from config import GlobalConfig
from raspberry import Switch
import time


global steppers
steppers = {}
global steppers_working
steppers_working = []
global servos
servos = {}


class Arduino():
    read_rate = 60  # Leer datos del buffer 60 veces por segundo

    # Lista de metodos a ser llamados cuando se reciba un payload
    on_received_payload = []

    def __init__(self, port, baudrate=9600):
        print("Abriendo puerto: " + port)

        # Verificar que el puerto exista y no este ocupado
        try:
            self.__serial = NewSerial(port, baudrate)
        except Exception as error:
            print(error)
            print("El puerto serial '" + port +
                  "' no existe o no esta disponible.")
            quit()

        # Esperar un momento a establecer la conexion serial
        time.sleep(3)

        # Comenzar a leer señales
        self.update()

    def kill(self):
        """
        Mata toda comunicacion con el arduino
        """
        self.__serial.close()

    def pin_mode(self, pin, output):
        pin = str(pin).zfill(2)
        pin_type = "O" if output else "I"

        payload = f"P:{pin}:{pin_type};"
        self.__serial.write(bytes(payload, encoding='utf-8'))

    def digital_read(self, pin):
        pin = str(pin).zfill(2)

        payload = f"R:{pin};"
        self.__serial.write(bytes(payload, encoding='utf-8'))
        return str(self.__serial.readline())[7] == "1"

    def digital_write(self, pin, high):
        pin = str(pin).zfill(2)
        value = '0255' if high else '0000'

        payload = f"W:{pin}:{value};"
        self.__serial.write(bytes(payload, encoding='utf-8'))

    def analog_read(self, pin):
        payload = f"R:A{pin};"
        self.__serial.write(bytes(payload, encoding='utf-8'))

        received_payload = str(self.__serial.readline(), 'utf-8')
        return int(received_payload.split(':')[2])

    def analog_write(self, pin, value):
        pin = str(pin).zfill(2)
        value = str(value).zfill(4)

        payload = f"W:{pin}:{value};"
        self.__serial.write(bytes(payload, encoding='utf-8'))

    # Adjunta un servo al pin digital dado
    def attach_servo(self, pin):
        pin = str(pin).zfill(2)

        payload = f"P:{pin}:S;"

        print(payload)
        self.__serial.write(bytes(payload, encoding='utf-8'))

    # Aplica un angulo al servo dado
    def servo_write(self, servo_pin, angle):
        pin = str(servo_pin).zfill(2)
        angle = str(angle).zfill(4)

        payload = f"S:{pin}:{angle};"
        print(payload)
        self.__serial.write(bytes(payload, encoding='utf-8'))

    # Aplica un angulo al servo dado
    def send_payload(self, payload):
        self.__serial.write(bytes(payload, encoding='utf-8'))

    def update(self):
        t = Timer(1/self.read_rate, self.update)
        t.start()

        if (self.__serial.in_waiting > 2):
            received_payload = str(
                self.__serial.readline(), 'utf-8').strip(" ").strip("\n")
            self.__trigger_received_payload(received_payload)

    def __trigger_received_payload(self, payload):
        for cll in self.on_received_payload:
            cll(payload)


class Servo:
    """
    Servo motor pwm
    """
    __id = 0
    __angle = 0

    def __init__(self, arduino, pwmPin, startAngle=0):
        self.__arduino = arduino

        # Obtener ID del servo
        self.__id = pwmPin

        # Guardar el servo para futuras referencias
        if (self.__id in servos):
            raise ValueError(
                "Ya hay un servo asignado al pin " + str(self.__id))
            quit()
        servos[pwmPin] = self

        # Settear puerto para servo en Arduino
        self.__arduino.attach_servo(self.__id)
        self.__arduino.servo_write(self.__id, startAngle)

    @property
    def angle(self):
        return self.__angle

    @angle.setter
    def angle(self, value):
        self.__angle = value
        self.__arduino.servo_write(self.__id, self.__angle)


class Stepper:
    """
    Motor a pasos de 2 pines, step y dir
    """

    __enable_pin = 11

    steps = 0
    # Señal llamada cuando hemos terminado nuestros pasos objetivo
    on_steps_end = []

    ready = False

    __origin_switch = None
    __end_switch = None

    __arduino_id = 0
    __id = 0

    def __init__(self, arduino: Arduino, stepPin: int, dirPin: int, origin_switch_pin: int, end_switch_pin: int):
        self.arduino = arduino

        stepPin = str(stepPin).zfill(2)
        dirPin = str(dirPin).zfill(2)

        # Configurar pin Enable
        self.arduino.pin_mode(self.__enable_pin, True)

        # Finales de carrera
        self.__origin_switch = Switch(origin_switch_pin)
        self.__end_switch = Switch(end_switch_pin)

        # Señales de finales de carrera
        self.__origin_switch.on_pressed = [self.__on_origin_reached]
        self.__end_switch.on_pressed = [self.__on_end_reached]

        # Obtener ID del motor
        self.__id = (stepPin, dirPin)
        self.__arduino_id = len(steppers)

        # Moverse indefinidamente al inicio hasta que lo alcancemos
        if (not self.__origin_switch.start_pressed) and (not GlobalConfig.debug_mode):
            print(str(self.__arduino_id) + " : " + "Go to origin")
            self.step(-10000)

        # Guardar el motor para futuras referencias
        if (self.__id in steppers):
            raise ValueError(
                "Ya hay un stepper asignado a los pines " + str(self.__id))
            quit()
        steppers[self.__id] = self

        # Settear puerto para servo en Arduino
        init_payload = f"M:{self.__arduino_id}:{stepPin}:{dirPin};"
        self.arduino.send_payload(init_payload)

        self.arduino.on_received_payload.append(
            self.__on_arduino_received_payload)

    def step(self, steps=1):
        clockwise = steps > 0
        if not (clockwise):
            steps = -steps

        # Si queremos hacer mas de este numero de pasos, diferir las llamdas en multiples
        maxSendSteps = 32767
        if (steps > maxSendSteps):
            self.step(steps - maxSendSteps)
            steps = maxSendSteps

        # Guardar los pasos dados
        steps_mult = -1
        if (clockwise):
            steps_mult = 1
        self.steps += steps * steps_mult

        # Activar enable de drivers
        if not self in steppers_working:
            steppers_working.append(self)

        self.arduino.digital_write(self.__enable_pin, False)

        # Convertir pasos a string con formato para payload
        steps = str(steps).zfill(5)
        clockwise = 'T' if clockwise else 'F'

        # Decirle al arduino el numero de pasos a realizar
        payload = f"M:{self.__arduino_id}:{steps}:{clockwise};"
        self.arduino.send_payload(payload)

    def disable(self):
        # if (len(steppers_working) <= 0):
        self.arduino.digital_write(self.__enable_pin, True)

    def interrupt(self):
        self.__check_disable()

        # Interrumpir pasos del stepper
        payload = f"M:{self.__arduino_id}:E;"
        print(payload)
        self.arduino.send_payload(payload)

    def __on_origin_reached(self, switch):
        if self.ready:
            return

        print("Origin reached : " + str(self.__arduino_id))
        self.ready = True
        self.steps = 0

        self.interrupt()

    def __on_end_reached(self, switch):
        pass  # self.ready = False

    def __on_arduino_received_payload(self, payload):
        if not (payload[0] == "M"):
            return
        if not (payload[2] == str(self.__arduino_id)):
            return

        # Señal de fin de pasos
        if (payload[4] == "E"):
            self.__on_steps_end()

    def __on_steps_end(self):
        self.__check_disable()

        for cll in self.on_steps_end:
            cll()

    def __check_disable(self):
        pass
        # if (self in steppers_working):
        #    steppers_working.remove(self)

        # if (len(steppers_working) <= 0):
        #    self.arduino.digital_write(self.__enable_pin, True)


# OBSOLETO, ARDUINO NO RESPONDE MAS A ESTOS PAYLOADS
class Stepper4:
    """
    CLASE OBSOLETA

    Motor a pasos de 4 entradas.
    """

    steps = 0
    # Señal llamada cuando hemos terminado nuestros pasos objetivo
    on_steps_end = []

    __arduino_id = 0
    __id = 0

    def __init__(self, arduino, in1, in2, in3, in4):
        self.arduino = arduino

        in1 = str(in1).zfill(2)
        in2 = str(in2).zfill(2)
        in3 = str(in3).zfill(2)
        in4 = str(in4).zfill(2)

        # Obtener ID del motor
        self.__id = (in1, in2, in3, in4)
        self.__arduino_id = len(steppers)

        # Guardar el motor para futuras referencias
        if (self.__id in steppers):
            raise ValueError(
                "Ya hay un stepper asignado a los pines " + str(self.__id))
            quit()
        steppers[self.__id] = self

        # Settear puerto para servo en Arduino
        init_payload = f"M:{self.__arduino_id}:{in1}:{in2}:{in3}:{in4};"
        self.arduino.send_payload(init_payload)

        self.arduino.on_received_payload.append(
            self.__on_arduino_received_payload)

    def step(self, steps=1):
        clockwise = steps > 0
        if not (clockwise):
            steps = -steps

        # Si queremos hacer mas de este numero de pasos, diferir las llamdas en multiples
        maxSendSteps = 32767
        if (steps > maxSendSteps):
            self.step(steps - maxSendSteps)
            steps = maxSendSteps

        # Guardar los pasos dados
        steps_mult = -1
        if (clockwise):
            steps_mult = 1
        self.steps += steps * steps_mult

        # Convertir pasos a string con formato para payload
        steps = str(steps).zfill(5)
        clockwise = 'T' if clockwise else 'F'

        # Decirle al arduino el numero de pasos a realizar
        payload = f"M:{self.__arduino_id}:{steps}:{clockwise};"
        self.arduino.send_payload(payload)

    def __on_arduino_received_payload(self, payload):
        if not (payload[0] == "M"):
            return
        if not (payload[2] == str(self.__arduino_id)):
            return

        # Señal de fin de pasos
        if (payload[4] == "E"):
            # print("END: " + payload)
            self.__on_steps_end()

    def __on_steps_end(self):
        for cll in self.on_steps_end:
            cll()
