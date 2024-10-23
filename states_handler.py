from arduino import Arduino, ArduinoSlave, Stepper, Servo
from config import GeneralTweaker


class StatesHandler():
    """
    Encargado de la gestion de el estado de cada stepper y servomotor 
    en el sistema
    """
    components = {}

    def __init__(self, master: Arduino):
        self.__parts_initializer = PartsInitializer(master)

        # configurar las partes
        for part_config in self.__parts_initializer.parts:
            self.components[part_config] = self.__parts_initializer.parts[part_config]['component']

    def apply_single_state(self, state):
        component = self.components[state['id']]
        
        isStepper: bool = type(component) is Stepper
        if (isStepper):
            pass
    


class PartsInitializer():
    def __init__(self, master: Arduino):
        arduinos = {
            'Head': master,
            'LeftArm': ArduinoSlave(master, 1),
            'RightArm': ArduinoSlave(master, 2)
        }
        self.arduinos = arduinos

        self.parts = {
            'Head/X': {
                'component': Stepper(
                    arduino=arduinos["Head"],
                    stepPin=2,
                    dirPin=3,
                    _steps_per_rev=GeneralTweaker.TB6600["steps_per_rev"],
                    _min_step_time=GeneralTweaker.TB6600["min_step_time"],
                    _max_step_time=GeneralTweaker.TB6600["max_step_time"]
                ),
                'low_limit': 0,
                'lhigh_limit': 7500
            },
            'Head/Y': {
                'component': Stepper(
                    arduino=arduinos["Head"],
                    stepPin=5,
                    dirPin=6,
                    _steps_per_rev=GeneralTweaker.TB6600["steps_per_rev"],
                    _min_step_time=GeneralTweaker.TB6600["min_step_time"],
                    _max_step_time=GeneralTweaker.TB6600["max_step_time"]
                ),
                'low_limit': 0,
                'lhigh_limit': 15000
            },
            'Head/Z': {
                'component': Stepper(
                    arduino=arduinos["Head"],
                    stepPin=9,
                    dirPin=10,
                    _steps_per_rev=GeneralTweaker.TB6600["steps_per_rev"],
                    _min_step_time=GeneralTweaker.TB6600["min_step_time"],
                    _max_step_time=GeneralTweaker.TB6600["max_step_time"]
                ),
                'low_limit': 0,
                'lhigh_limit': 7500
            },



            'LeftArm/Codo': {
                'component': Stepper(
                    arduino=arduinos["LeftArm"],
                    stepPin=7,
                    dirPin=8,
                    _steps_per_rev=GeneralTweaker.DM556["steps_per_rev"],
                    _min_step_time=GeneralTweaker.DM556["min_step_time"],
                    _max_step_time=GeneralTweaker.DM556["max_step_time"]
                ),
                'low_limit': 0,
                'lhigh_limit': 7500
            },
            'LeftArm/Muñeca': {
                'component': Stepper(
                    arduino=arduinos["LeftArm"],
                    stepPin=12,
                    dirPin=13,
                    _steps_per_rev=GeneralTweaker.TB6600["steps_per_rev"],
                    _min_step_time=GeneralTweaker.TB6600["min_step_time"],
                    _max_step_time=GeneralTweaker.TB6600["max_step_time"]
                ),
                'low_limit': 0,
                'high_limit': 7500
            },
            'LeftArm/Meñique': {
                'component': Servo(
                    arduino=arduinos["LeftArm"],
                    pwmPin=3,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'LeftArm/Anular': {
                'component': Servo(
                    arduino=arduinos["LeftArm"],
                    pwmPin=5,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'LeftArm/Medio': {
                'component': Servo(
                    arduino=arduinos["LeftArm"],
                    pwmPin=6,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'LeftArm/Indice': {
                'component': Servo(
                    arduino=arduinos["LeftArm"],
                    pwmPin=9,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'LeftArm/Pulgar': {
                'component': Servo(
                    arduino=arduinos["LeftArm"],
                    pwmPin=10,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'LeftArm/Pulgar2': {
                'component': Servo(
                    arduino=arduinos["LeftArm"],
                    pwmPin=11,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },




            'RightArm/Codo': {
                'component': Stepper(
                    arduino=arduinos["RightArm"],
                    stepPin=7,
                    dirPin=8,
                    _steps_per_rev=GeneralTweaker.DM556["steps_per_rev"],
                    _min_step_time=GeneralTweaker.DM556["min_step_time"],
                    _max_step_time=GeneralTweaker.DM556["max_step_time"]
                ),
                'low_limit': 0,
                'lhigh_limit': 7500
            },
            'RightArm/Muñeca': {
                'component': Stepper(
                    arduino=arduinos["RightArm"],
                    stepPin=12,
                    dirPin=13,
                    _steps_per_rev=GeneralTweaker.TB6600["steps_per_rev"],
                    _min_step_time=GeneralTweaker.TB6600["min_step_time"],
                    _max_step_time=GeneralTweaker.TB6600["max_step_time"]
                ),
                'low_limit': 0,
                'high_limit': 7500
            },
            'RightArm/Meñique': {
                'component': Servo(
                    arduino=arduinos["RightArm"],
                    pwmPin=3,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'RightArm/Anular': {
                'component': Servo(
                    arduino=arduinos["RightArm"],
                    pwmPin=5,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'RightArm/Medio': {
                'component': Servo(
                    arduino=arduinos["RightArm"],
                    pwmPin=6,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'RightArm/Indice': {
                'component': Servo(
                    arduino=arduinos["RightArm"],
                    pwmPin=9,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'RightArm/Pulgar': {
                'component': Servo(
                    arduino=arduinos["RightArm"],
                    pwmPin=10,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
            'RightArm/Pulgar2': {
                'component': Servo(
                    arduino=arduinos["RightArm"],
                    pwmPin=11,
                    startAngle=0
                ),
                'low_limit': 0,
                'high_limit': 180
            },
        }
