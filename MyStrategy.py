from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
from model.Unit import Unit
from AStar import *
from Debug import *
from random import *
from math import *


class Brain:
    thoughts = []

    def add_thought(self, thought):
        self.thoughts.append(thought)

    def forget_current_thought(self):
        try:
            return self.thoughts.pop()
        except IndexError:
            return None

    def get_current_thought(self):
        return self.thoughts[len(self.thoughts) - 1] if len(self.thoughts) > 0 else None

    def think(self):
        thought = self.get_current_thought()
        if thought is not None and callable(thought):
            thought()


class MyStrategy:
    CELL = 70
    route = []
    obstacles = []
    first_cell = None
    second_cell = None
    brain = None
    debug = None
    destination = None

    _me = _world = _game = _move = None

    def __init__(self):
        self.brain = Brain()
        self.brain.add_thought(lambda: self.go_to(400, 3700))
        # self.brain.add_thought(lambda: self.go_to(0, 2700))

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug is None:
            self.debug = Debug(world.width, world.width, 0.16, self.CELL)

        self._me = me
        self._world = world
        self._game = game
        self._move = move

        self.fill_obstacles()

        self.brain.think()

        # if sqrt(move.speed) < 0.1 and hypot(me.speed_x, me.speed_y) < 0.1:
        #      print("speed_x+speed+y: {} | move.speed: {}, angle: {} | x: {} | y: {}".format(
        #          hypot(me.speed_x, me.speed_y),
        #          move.speed, me.angle, me.x, me.y))

        self.debug.draw(me, world, move, self.route, self.obstacles, self.destination)

    def find_obstacles_in_route(self):
        for c in self.obstacles:
            for p in self.route:
                if p == c:
                    print("new obstacle detected!!!")
                    return True
        return False

    def go_to(self, x, y):
        self.destination = (x, y)
        if self._me.get_distance_to(self.r(self.c(x)), self.r(self.c(y))) < self._game.wizard_forward_speed:
            self.brain.forget_current_thought()
            self.brain.add_thought(lambda: self.go_to(randint(0, 3989), randint(0, 3989)))
            self.brain.think()
            return
        self.brain.add_thought(self.go_to_next_cell)
        self.brain.add_thought(lambda: self.find_path(x, y))
        self.brain.think()
        return

    def go_to_next_cell(self):
        # if self.route is None or
        if self.find_obstacles_in_route():
            self.brain.forget_current_thought()
            self.brain.think()
            return

        if self.first_cell is None:
            if len(self.route) > 0:
                self.first_cell = self.route[0]
                if len(self.route) > 1:
                    self.second_cell = self.route[1]
                else:
                    self.second_cell = None
                self.brain.add_thought(self.rotate)
                self.brain.think()
                return
            else:
                self.brain.forget_current_thought()
        else:
            x1, y1 = self.first_cell
            x1, y1 = self.r(x1), self.r(y1)
            if self.second_cell is not None:
                x2, y2 = self.second_cell
                x2, y2 = self.r(x2), self.r(y2)
            else:
                x2, y2 = (None, None)
            if self._me.get_distance_to(x1, y1) < 0.1 or self.second_cell is not None\
                    and (min(x1, x2) < self._me.x < max(x1, x2) or min(y1, y2) < self._me.y < max(y1, y2)):
                del self.route[0]
                self.first_cell = None
                self.second_cell = None
                self.brain.think()
                return
            else:
                if self.second_cell is not None:
                    if abs(Point(x1, y1, self._me.angle).get_angle_to(x2, y2)) < pi / 360:  # pi / 360 rad == 0.5 deg
                        self._move.speed = self._game.wizard_forward_speed
                        return
                    else:
                        if self._me.get_distance_to(x1, y1) <= self._game.wizard_forward_speed:
                            self._move.turn = Point(x1, y1, self._me.angle).get_angle_to(x2, y2)

                self._move.speed = self._me.get_distance_to(x1, y1)

    def rotate(self):
        x, y = self.first_cell
        x = self.r(x)
        y = self.r(y)
        angle = self._me.get_angle_to(x, y)
        if abs(angle) > 0:
            self._move.turn = angle
        else:
            self.brain.forget_current_thought()
            self.brain.think()
            return

    def find_path(self, end_x, end_y):
        w, h = self._world.width, self._world.height
        start_x, start_y = self._me.x, self._me.y
        current_position = self.c(start_x), self.c(start_y)
        go_to = self.c(end_x), self.c(end_y)
        a = AStar(True)
        a.init_grid(self.c(w), self.c(h), self.obstacles,
                    current_position, go_to)
        self.route = a.solve()
        self.first_cell = None
        self.brain.forget_current_thought()
        self.brain.think()
        return

    def find_target(self, me: Wizard, world: World, game: Game, move: Move):
        return False, {}

    def fill_obstacles(self):
        self.obstacles = []
        for b in self._world.buildings:
            for x in range(self.c(b.x - b.radius), self.c(b.x + b.radius) + 1):
                for y in range(self.c(b.y - b.radius), self.c(b.y + b.radius) + 1):
                    self.obstacles.append((x, y))

        for t in self._world.trees:
            for x in range(self.c(t.x - t.radius), self.c(t.x + t.radius) + 1):
                for y in range(self.c(t.y - t.radius), self.c(t.y + t.radius) + 1):
                    self.obstacles.append((x, y))

    def c(self, v):
        return int(v // self.CELL)

    def r(self, v):
        return v * self.CELL + self.CELL / 2


class Point(Unit):
    def __init__(self, x, y, angle = 0):
        Unit.__init__(self, id=None, x=x, y=y, speed_x=None, speed_y=None, angle=angle, faction=None)