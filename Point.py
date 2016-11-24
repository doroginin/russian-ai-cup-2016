from model.Unit import Unit


class Point(Unit):
    def __init__(self, x, y, angle = 0):
        Unit.__init__(self, id=None, x=x, y=y, speed_x=None, speed_y=None, angle=angle, faction=None)