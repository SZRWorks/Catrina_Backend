


class MathUtils():
    """
    Utilidades matematicas
    """
        
    @staticmethod
    def soft_in_out(t: float, softness: int=100) -> float:
        return (1 - ((2*t-1)**(100-(softness-2))))
        
    @staticmethod
    def max_value(t: float) -> float:
        return 1
          
    @staticmethod  
    def min_value(t: float) -> float:
        return 0
    