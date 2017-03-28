from builtins import object
class Circle(object):
    """
    This is simple example of a class
    """
    pi=3.141592653589793
    def __init__(self,r):
        self.r=r
    def area(self):
        return 0.5*self.pi*self.r**2
    def circumference(self):
        return 2.*pi*self.r
