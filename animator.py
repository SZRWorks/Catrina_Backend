from states_handler import PartState, StatesHandler
from config import GlobalConfig
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
    


class Animator():
    """
    Encargado de la gestion de animaciones
    """
    animations: Animation = []
    next_id: int = None
    

    def __init__(self, states_handler: StatesHandler):
        self.__read_animations()
        
        print(self.animations)
    
    
    
    
    
    
    def __read_animations(self):
        with open(GlobalConfig.animations_file) as f:
            dat = (json.load(f))
            _animations = dat['animations']
            self.next_id = dat['next_id']
            
            for animation in _animations:
                self.animations.append(Animation(animation))
    
    
    def save_animation(self, animation: dict):
        if (self.get_animation_by_id(animation['id'])):
            return self.update_animation(animation)
        
        animation['id'] = self.next_id
        new_animation = Animation(animation)
        self.animations.append(new_animation)
        self.next_id += 1;
        
        self.__rewrite_file()
        
        return new_animation.get_data_dict()
    
    
    def update_animation(self, animation: dict):
        old = self.get_animation_by_id(animation['id'])
        self.animations.remove(old)
        
        new_animation = Animation(animation);
        self.animations.append(new_animation)
        
        self.__rewrite_file()
        
        return new_animation.get_data_dict()
    
    
    def delete_animation(self, animation_id: int):
        old = self.get_animation_by_id(animation_id)
        self.animations.remove(old)
        
        self.__rewrite_file()
        
        return True
        
    
    def __rewrite_file(self):
        with open(GlobalConfig.animations_file, 'w') as fp:
            json.dump({
                'animations': self.animations_to_dict(self.animations),
                'next_id': self.next_id
            }, fp)


    def animations_to_dict(self, animations: list[Animation]):
        _dict: list = []
        for animation in animations:
            _dict.append(animation.get_data_dict())
        
        return _dict
    
    def get_animation_by_id(self, animation_id: int) -> Animation:
        for animation in self.animations:
            animation: Animation = animation
            if (animation.id == animation_id):
                return animation
        
        return False