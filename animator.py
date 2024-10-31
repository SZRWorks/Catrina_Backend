from arduino import Stepper
from states_handler import PartState, StatesHandler
from math_utils import MathUtils
from config import GlobalConfig
from web_socket import Socket
import asyncio
import json


class AnimationFrame():
    """
    Guarda toda la informacion de una animacion
    """
    id: int = -1
    min_velocity: int = 0
    max_velocity: int = 100
    velocity_curve: str = 'Min velocity'
    start_delay: int = 0
    end_delay: int = 0
    data: list[PartState] = []
    dict_data: dict = {}
    
    def __init__(self, args: dict):
        self.id = args['id']
        self.min_velocity = args['minVelocity']
        self.max_velocity = args['maxVelocity']
        self.velocity_curve = args['velocityCurve']
        self.start_delay = args['startDelay']
        self.end_delay = args['endDelay']
        
        self.data = []
        for state in args['data']:
            self.data.append(PartState(state))
        
        self.dict_data = args

    def get_data_dict(self):
        return self.dict_data

class Animation():
    """
    Guarda toda la informacion de una animacion
    """
    id: int = -1
    title: str = ''
    is_public: bool = False
    frames: list[AnimationFrame] = []
    __dict_data: dict = {}
    
    def __init__(self, args: dict):
        self.id = args['id']
        self.title = args['title']
        self.is_public = args['isPublic']
        
        self.frames = []
        for frame in args['frames']:
            self.frames.append(AnimationFrame(frame))
        
        self.__dict_data = args
    
    def get_data_dict(self):
        return self.__dict_data
    

class AnimatonsHelper():
    """
    Encargado de la gestion de animaciones
    """
    animations: Animation = []
    next_id: int = None
        
    @staticmethod
    def read_animations():
        with open(GlobalConfig.animations_file) as f:
            dat = (json.load(f))
            _animations = dat['animations']
            AnimatonsHelper.next_id = dat['next_id']
            
            for animation in _animations:
                AnimatonsHelper.animations.append(Animation(animation))
    
    @staticmethod
    def save_animation(animation: dict):
        if (AnimatonsHelper.get_animation_by_id(animation['id'])):
            return AnimatonsHelper.update_animation(animation)
        
        animation['id'] = AnimatonsHelper.next_id
        new_animation = Animation(animation)
        AnimatonsHelper.animations.append(new_animation)
        AnimatonsHelper.next_id += 1;
        
        AnimatonsHelper.__rewrite_file()
        
        return new_animation.get_data_dict()
    
    @staticmethod
    def update_animation(animation: dict):
        old = AnimatonsHelper.get_animation_by_id(animation['id'])
        AnimatonsHelper.animations.remove(old)
        
        new_animation = Animation(animation);
        AnimatonsHelper.animations.append(new_animation)
        
        AnimatonsHelper.__rewrite_file()
        
        return new_animation.get_data_dict()
    
    @staticmethod
    def delete_animation(animation_id: int):
        old = AnimatonsHelper.get_animation_by_id(animation_id)
        AnimatonsHelper.animations.remove(old)
        
        AnimatonsHelper.__rewrite_file()
        
        return True
        
    @staticmethod
    def __rewrite_file():
        with open(GlobalConfig.animations_file, 'w') as fp:
            json.dump({
                'animations': AnimatonsHelper.animations_to_dict(AnimatonsHelper.animations),
                'next_id': AnimatonsHelper.next_id
            }, fp)

    @staticmethod
    def animations_to_dict(animations: list[Animation], include_private: bool = True):
        _dict: list = []
        for animation in animations:
            if (not include_private and not animation.is_public): continue
            _dict.append(animation.get_data_dict())
        
        return _dict
    
    @staticmethod
    def get_animation_by_id(animation_id: int) -> Animation:
        for animation in AnimatonsHelper.animations:
            animation: Animation = animation
            if (animation.id == animation_id):
                return animation
        
        return False
    
    
    
    


class Animator():
    playing: bool = False
    
    __actual_animation: Animation = None
    __frames_queue: list[AnimationFrame] = None
    __actual_frame: AnimationFrame = None
    __frame_velocity_curve = None
    
    states_handler: StatesHandler = None
    
    
    
    def __init__(self, states_handler: StatesHandler):
        self.states_handler = states_handler
        self.states_handler.on_stepper_update.append(self.__handle_stepper_velocity_curve)
        
        # Load animations
        AnimatonsHelper.read_animations()
    
    def play(self, animation_id: int):
        print("Trying to play: ", animation_id)
        if self.playing: return;
        
        animation: Animation = AnimatonsHelper.get_animation_by_id(animation_id);
        if (not animation or animation == None):
            print("Animation id:", animation_id, " not found")
            return;
        
        for frame in animation.frames:
            if (frame.data == None or len(frame.data) <= 0):
                print("Some animation frames has empty data")
                return;
        
        self.playing = True
        print("PLAY!")
        
        self.__actual_animation = animation
        self.__actual_frames = animation.frames.copy()
        self.__check_next_frame();
        
        # notifica al fronend de los cambios
        Socket.emit('animationStatusUpdated', {
            'playing': True,
            'animation_id': self.__actual_animation.id,
            'left_frames': len(self.__actual_frames),
            'animation_percentage': 0
        })
    
    
    async def apply_frame(self, frame: AnimationFrame, apply_delays: bool = False):
        self.__actual_frame = frame
        self.__frame_velocity_curve = self.__get_velocity_function(self.__actual_frame.velocity_curve)
        
        if (apply_delays):
            await asyncio.sleep(frame.start_delay)
        
        self.states_handler.on_every_work_ended.append(lambda : asyncio.run(self.on_frame_work_ended(apply_delays)))
        for state in self.__actual_frame.data:
            self.states_handler.apply_single_state(state.get_data_dict());
        
        
    async def on_frame_work_ended(self, apply_delays: bool = False):
        self.states_handler.on_every_work_ended = []
        if (apply_delays):
            await asyncio.sleep(self.__actual_frame.end_delay)
        
        self.__check_next_frame();
    
    
    def __check_next_frame(self):
        if (len(self.__actual_frames) <= 0):
            self.__animation_frames_ended()
            return;
        
        asyncio.run(self.apply_frame(self.__actual_frames.pop(), True))
    
    def __animation_frames_ended(self):
        self.playing = False;
        self.__actual_animation = None
        self.__actual_frame = None
        self.__actual_frames = None
        
        # notifica al fronend de los cambios
        Socket.emit('animationStatusUpdated', {
            'playing': False,
            'animation_id': -1,
            'left_frames': 0,
            'animation_percentage': 100
        })
    
    
    def __handle_stepper_velocity_curve(self, stepper: Stepper, elapsed_steps: int):
        if (self.__frame_velocity_curve == None): return
        
        curve = self.__frame_velocity_curve(stepper.steps/stepper.last_target_steps)
        af = self.__actual_frame;
        vel = int(((af.max_velocity - af.min_velocity) * curve) + af.min_velocity)
        
        stepper.setVelocity(vel)
    
    
    def __get_velocity_function(self, curve_name: str):
        #if (curve_name == 'Soft in-out'):
        return MathUtils.max_value
        