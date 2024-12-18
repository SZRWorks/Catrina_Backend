from threading import Timer
from serial import Serial as NewSerial
from config import GlobalConfig
from raspberry import Switch
import time


global steppers
steppers = {}
global steppers_working
steppers_working: list = []
global servos
servos = {}


class Arduino():
    serial: NewSerial = None
    update_rate = 60  # Numero de veces por segundo en las que se comunicara con el arduino

    # Lista de metodos a ser llamados cuando se reciba un payload
    on_received_payload = []
    
    # Buffer de envio de payloads
    payload_buffer = []

    # Lista de metodos a ser llamados cuando se reciba un payload (Este payload contiene el ID del arduino emisor)
    on_received_complete_payload = []
    
    attached_servos = 0;
    attached_steppers = 0;
    

    I2C_id: int = 0

    def __init__(self, port, baudrate=9600):
        print("Abriendo puerto: " + port)

        # Verificar que el puerto exista y no este ocupado
        try:
            self.serial = NewSerial(port, baudrate)
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
        self.serial.close()

    def pin_mode(self, pin, output):
        pin = str(pin).zfill(2)
        pin_type = "O" if output else "I"

        payload = f"P:{pin}:{pin_type};"
        self.send_payload(payload)

    #def digital_read(self, pin):
    #    pin = str(pin).zfill(2)

    #    payload = f"R:{pin};"
    #    self.send_payload(payload)
    #    return str(self.serial.readline())[7] == "1"

    def digital_write(self, pin, high):
        pin = str(pin).zfill(2)
        value = '0255' if high else '0000'

        payload = f"W:{pin}:{value};"
        self.send_payload(payload)

    #def analog_read(self, pin):
    #    payload = f"R:A{pin};"
    #    self.send_payload(payload)

    #    received_payload = str(self.serial.readline(), 'utf-8')
    #    return int(received_payload.split(':')[2])

    def analog_write(self, pin, value):
        pin = str(pin).zfill(2)
        value = str(value).zfill(4)

        payload = f"W:{pin}:{value};"
        self.send_payload(payload)

    # Adjunta un servo al pin digital dado
    def attach_servo(self, pin):
        pin = str(pin).zfill(2)

        payload = f"P:{pin}:S;"
        self.send_payload(payload)

    # Aplica un angulo al servo dado
    def servo_write(self, servo_pin, angle):
        pin = str(servo_pin).zfill(2)
        angle = str(angle).zfill(4)

        payload = f"S:{pin}:{angle};"
        self.send_payload(payload)

    # Enviar un payload cualquiersea
    def send_payload(self, payload):
        payload = str(self.I2C_id) + payload;
        if (GlobalConfig.arduino_debug_payloads_level > 2): print(f"Buffering[{len(self.payload_buffer)}] -> " + payload)
        
        self.payload_buffer.insert(0, payload);

    def update(self):
        t = Timer(1/self.update_rate, self.update)
        t.start()

        if (self.serial.in_waiting > 2):
            received_payload = str(
                self.serial.readline(), 'utf-8').strip(" ").strip("\n")
            self._trigger_received_payload(received_payload)
        
        if (len(self.payload_buffer) > 0):
            payload = self.payload_buffer.pop()
            self.serial.write(bytes(payload, encoding='utf-8'))
            if (GlobalConfig.arduino_debug_payloads_level > 1): print(f"Sending -> " + payload)

    def _trigger_received_payload(self, payload):
        if (self.I2C_id != 0): return;
        
        if (len(payload) <= 0):
            return

        if (GlobalConfig.arduino_debug_payloads_level > 0):
            print("Receiving <- " + payload)

        for cll in self.on_received_complete_payload:
            cll(payload)
        
        self.check_received_payload(payload)
    
    def check_received_payload(self, payload: str):
        if not (payload[0] == str(self.I2C_id)):
            return
        
        for cll in self.on_received_payload:
            cll(payload[1:])

        # if (len(payload) > 0 and int(payload[0]) == 0):
        #    for cll in self.on_received_payload:
        #        cll(payload[1:])


class ArduinoSlave(Arduino):
    master: Arduino = None

    def __init__(self, _master: Arduino, _I2C_id: int):
        self.on_received_payload = []
        
        self.master = _master
        self.I2C_id = _I2C_id
        self.serial = self.master.serial

        self.master.on_received_complete_payload.append(
            self.check_received_payload)


class Servo:
    """
    Servo motor pwm
    """
    __id = 0
    __angle = 0
    __arduino: Arduino = None

    def __init__(self, arduino: Arduino, pwmPin, startAngle=0):
        self.__arduino = arduino

        # Obtener ID del servo
        self.__identifier = (self.__arduino.I2C_id, pwmPin)
        self.__id = pwmPin
        self.__arduino.attached_servos += 1;

        # Guardar el servo para futuras referencias
        if (self.__identifier in servos):
            raise ValueError(
                "Ya hay un servo asignado al pin " + str(self.__identifier))
            quit()
        servos[self.__id] = self

        # Settear puerto para servo en Arduino
        self.__arduino.attach_servo(pwmPin)
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
    working = False
    # Señal llamada cuando hemos terminado nuestros pasos objetivo
    on_steps_end = []

    # Señal llamada cuando se realiza un paso en el stepper
    on_step = []

    steps_per_rev: int = 4096
    step_time: int = 600
    min_step_time: int = 600
    max_step_time: int = 2000

    ready: bool = False

    last_target_steps = 0

    arduino: Arduino = None
    __arduino_id = 0
    __id = 0

    def __init__(self, arduino: Arduino, stepPin: int, dirPin: int, _steps_per_rev: int, _min_step_time: int, _max_step_time: int):
        self.on_step = []
        self.on_steps_end = []
        
        self.arduino = arduino

        stepPin = str(stepPin).zfill(2)
        dirPin = str(dirPin).zfill(2)

        # Configurar pin Enable
        #self.arduino.pin_mode(self.__enable_pin, True)

        # Obtener ID del motor
        self.__id = (self.arduino.I2C_id, stepPin, dirPin)
        self.__arduino_id = self.arduino.attached_steppers
        self.arduino.attached_steppers += 1;

        # Guardar el motor para futuras referencias
        if (self.__id in steppers):
            raise ValueError(
                "Ya hay un stepper asignado a los pines " + str(self.__id))
            quit()
        steppers[self.__id] = self

        # Settear puerto para servo en Arduino
        init_payload = f"M:{self.__arduino_id}:{stepPin}:{dirPin};"
        self.arduino.send_payload(init_payload)

        self.arduino.on_received_payload.append(self.__on_arduino_received_payload)

        self.configVelocities(_steps_per_rev, _min_step_time, _max_step_time)

    def configVelocities(self, _steps_per_rev: int, _min_step_time: int, _max_step_time: int):
        steps_per_rev = str(_steps_per_rev).zfill(5)
        min_step_time = str(_min_step_time).zfill(4)
        max_step_time = str(_max_step_time).zfill(4)

        config_payload = f"M:{self.__arduino_id}:{steps_per_rev}:{min_step_time}:{max_step_time};"
        self.arduino.send_payload(config_payload)

    def setVelocity(self, _velocity: int):
        _velocity = _velocity if _velocity >= 0 and _velocity <= 100 else (
            0 if _velocity < 0 else 100)

        velocity = str(_velocity).zfill(3)

        r = (self.max_step_time - self.min_step_time)
        self.step_time = int(self.max_step_time - (r * (_velocity/100.0)))

        velocity_payload = f"M:{self.__arduino_id}:{velocity};"
        self.arduino.send_payload(velocity_payload)

    def step(self, steps=1):
        if (steps == 0):
            return
        self.working = True

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
        # self.steps += steps * steps_mult

        # Activar enable de drivers
        if not self in steppers_working:
            steppers_working.append(self)

        # self.arduino.digital_write(self.__enable_pin, False)
        self.__on_step(0);

        # Convertir pasos a string con formato para payload
        steps = str(int(steps)).zfill(5)
        clockwise = 'T' if clockwise else 'F'

        # Decirle al arduino el numero de pasos a realizar
        payload = f"M:{self.__arduino_id}:{steps}:{clockwise};"
        self.arduino.send_payload(payload)

    def go_to(self, target: int):
        self.last_target_steps = target
        if (self.working):
            self.interrupt()
            return

        distanceSteps: int = int(target - self.steps)
        self.step(distanceSteps)

    def disable(self):
        #if (len(steppers_working) <= 0):
        #self.arduino.digital_write(self.__enable_pin, True)
        pass

    def interrupt(self):
        self.__check_disable()

        # Interrumpir pasos del stepper
        payload = f"M:{self.__arduino_id}:E;"
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
        if (payload[0] == str(self.__arduino_id)):
            self.__on_step(int(payload[1:]))
            return

        if not (payload[0] == "M"):
            return
        is_our_id: bool = payload[2] == str(self.__arduino_id)
        if not is_our_id:
            return

        # Señal de fin de pasos
        if (len(payload) > 4 and payload[4] == "E"):
            self.__on_steps_end()

    def __on_steps_end(self):
        print("STEPS ENDED: " + str(self.arduino.I2C_id) + "|" + str(self.__arduino_id))
        self.working = False
        self.__check_disable()
        self.__ensure_target()

        for cll in self.on_steps_end:
            cll()

    def __on_step(self, steps: int):
        self.steps += steps
        self.working = True

        for cll in self.on_step:
            cll(self, steps)

    def __ensure_target(self):
        if not (self.steps == self.last_target_steps):
            self.go_to(self.last_target_steps)

    def __check_disable(self):
        if (self in steppers_working):
            steppers_working.remove(self)

        # if (len(steppers_working) <= 0):
        #    self.arduino.digital_write(self.__enable_pin, True)
