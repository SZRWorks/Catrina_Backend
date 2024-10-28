from arduino import Arduino, ArduinoSlave, Stepper, Servo
from web_socket import Socket
from config import GeneralTweaker



class StatesHandler():
    """
    Encargado de la gestion de el estado de cada stepper y servomotor 
    en el sistema
    """
    __states = {}
    
    # True cuando el handler está ejecutando un frame de animacion
    executing_frame = False;


    def __init__(self, master: Arduino):
        self.__parts_initializer = PartsInitializer(master)

        # configurar los estados por defecto
        for part_id in self.__parts_initializer.parts:
            part_info = self.__parts_initializer.parts[part_id];
            component = part_info['component'];
            self.__states[part_id] = {
                'value': 0,
                'realValue': 0
            };
            
            isStepper: bool = type(component) is Stepper
            if (isStepper):
                component: Stepper = component
                component.on_step.append(lambda stepper, steps, _part_id=part_id: self.__local_stepper_step(_part_id, stepper, steps))
            #self.components[part_config] = self.__parts_initializer.parts[part_config]['component']
    
    def get_formated_states(self):
        formated_states = []
        for state in self.__states:
            formated_states.append({
                'id': state,
                'value': self.__states[state]['value'],
                'realValue': self.__states[state]['realValue'],
            })
        
        return formated_states

    def apply_single_state(self, state):
        part_info = self.__parts_initializer.parts[state['id']];
        new_value = state['value'];
        component = part_info['component'];
        low_limit = part_info['low_limit'];
        high_limit = part_info['high_limit'];
        
        target: int = int(((float(new_value)/100.0) * (high_limit - low_limit)) + low_limit)
        self.__states[state['id']]['value'] = new_value
        
        isStepper: bool = type(component) is Stepper
        if (isStepper):
            component: Stepper = component
            component.go_to(target)
            return;
        
        component: Servo = component
        component.angle = target
        
    
    def __local_stepper_step(self, part_id: str, stepper: Stepper, steps: int):
        part_info = self.__parts_initializer.parts[part_id];
        low_limit = part_info['low_limit'];
        high_limit = part_info['high_limit'];
        
        value_percentage = (stepper.steps/(high_limit - low_limit)) * 100;
        self.__states[part_id] = {
            'value': self.__states[part_id]['value'],
            'realValue': 0 if (value_percentage < 0) else (100 if (value_percentage > 100) else value_percentage)
        }
        self.__state_updated(part_id, self.__states[part_id])
    
    def __state_updated(self, part_id: str, state: dict):
        Socket.emit('stateUpdated', {
            'id': part_id,
            'value': state['value'],
            'realValue': state['realValue']
        })
    
    
class PartState():
    id: str = ""
    value: int = 0
    real_value: int = 0 
    
    def __init__(self, args: dict):
        self.id: str = args['id']
        self.value: int = args['value']
        self.real_value: int = args['realValue']
        
        self.dict_data = args
    
    def get_data_dict(self):
        return self.dict_data


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
                'high_limit': 7500
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
                'high_limit': 15000
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
                'high_limit': 7500
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
                'high_limit': 7500
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
                'high_limit': 7500
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
        
        """
        
        """
