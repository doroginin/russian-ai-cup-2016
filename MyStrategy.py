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
from Brain import *
from Point import *


class MyStrategy:
    CELL = 70
    route = None
    obstacles = []
    first_cell = None
    second_cell = None
    brain = None
    debug = None
    destination = None
    thoughts = []

    _me = _world = _game = _move = None

    def __init__(self):
        self.brain = Brain()
        #self.brain.add_thought(lambda: self.go_to(400, 3600))
        self.brain.add_thought(lambda: self.go_to(0, 3900))
        #self.brain.add_thought(lambda: self.go_random(500))

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug is None:
            self.debug = Debug(world.width, world.width, 0.1, self.CELL)

        self._me = me
        self._world = world
        self._game = game
        self._move = move

        self.fill_obstacles()

        #move.action = ActionType.HASTE

        self.brain.think()

        # if sqrt(move.speed) < 0.1 and hypot(me.speed_x, me.speed_y) < 0.1:
        #      print("speed_x+speed+y: {} | move.speed: {}, angle: {} | x: {} | y: {}".format(
        #          hypot(me.speed_x, me.speed_y),
        #          move.speed, me.angle, me.x, me.y))

        self.debug.draw(self.brain, me, world, move, self.route, self.obstacles, self.destination)

    def find_obstacles_in_route(self):
        for c in self.obstacles:
            for p in self.route:
                if p == c:
                    print("new obstacle detected!!!")
                    return True
        return False

    def go_random(self, radius):
        x = randint(self._me.x - radius, self._me.x + radius)
        y = randint(self._me.y - radius, self._me.y + radius)
        self.brain.forget_current_thought()
        self.brain.add_thought(lambda: self.go_to(min(3964, max(x, 0)), min(3964, max(y, 0))))
        return True

    def go_to(self, x, y):
        self.destination = (x, y)
        if self._me.get_distance_to(self.r(self.c(x)), self.r(self.c(y))) < self._game.wizard_forward_speed:
            self.brain.forget_current_thought()
            self.brain.add_thought(lambda: self.go_random(500))
            return True
        self.first_cell = None
        self.second_cell = None

        w, h = self._world.width, self._world.height
        start_x, start_y = self._me.x, self._me.y
        current_position = self.c(start_x), self.c(start_y)
        go_to = self.c(x), self.c(y)
        a = AStar(True)
        a.init_grid(self.c(w), self.c(h), self.obstacles,
                    current_position, go_to)
        self.route = a.solve()
        self.brain.forget_current_thought()
        if self.route is None:
            self.brain.add_thought(lambda: self.go_random(500))
        else:
            self.brain.add_thought(self.go_to_next_cell)
        return True

    def go_to_next_cell(self):
        # if self.route is None or
        if self.find_obstacles_in_route():
            self.brain.forget_current_thought()
            return True

        if self.first_cell is None:
            if len(self.route) > 0:
                self.first_cell = self.route[0]
                if len(self.route) > 1:
                    self.second_cell = self.route[1]
                else:
                    self.second_cell = None
                self.brain.add_thought(self.rotate)
                return True
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
                return True
            else:
                if self.second_cell is not None:
                    if abs(Point(x1, y1, self._me.angle).get_angle_to(x2, y2)) < pi / 360:  # pi / 360 rad == 0.5 deg
                        self._move.speed = self._game.wizard_forward_speed
                        return
                    else:
                        if self._me.get_distance_to(x1, y1) <= self._game.wizard_forward_speed:
                            #self._move.turn = Point(x1, y1, self._me.angle).get_angle_to(x2, y2)
                            print("PREROTATE")
                            self._move.speed = self._me.get_distance_to(x1, y1)
                            self.brain.add_thought(self.pre_rotate())
                            return True

                self._move.speed = self._me.get_distance_to(x1, y1)

    def rotate(self):
        x, y = self.first_cell
        x, y = self.r(x), self.r(y)
        angle = self._me.get_angle_to(x, y)
        if abs(angle) > 0:
            self._move.turn = angle
        else:
            self.brain.forget_current_thought()
            return True

    def pre_rotate(self):
        x1, y1 = self.first_cell
        x1, y1 = self.r(x1), self.r(y1)
        x2, y2 = self.second_cell
        x2, y2 = self.r(x2), self.r(y2)
        self._move.turn = Point(x1, y1, self._me.angle).get_angle_to(x2, y2)
        self.brain.forget_current_thought()

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

