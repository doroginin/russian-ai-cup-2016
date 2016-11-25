from model.Unit import Unit


CELL = 72  # @todo decrease it


class Point(Unit):
    def __init__(self, x, y, angle = 0):
        Unit.__init__(self, id=None, x=x, y=y, speed_x=None, speed_y=None, angle=angle, faction=None)


def to_calc(v):
    return int(v // CELL)


def to_real(v):
    return v * CELL + CELL / 2# + 1
