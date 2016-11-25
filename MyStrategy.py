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


OBSTACLES_PADDING = 1


class MyStrategy:
    route = None
    obstacles = []
    moving_obstacles = []
    first_cell = None
    second_cell = None
    brain = None
    debug = None
    destination = None
    thoughts = []
    stuck_ticks = 0
    tick_counter = 0

    Me = World = Game = Move = None

    def __init__(self):
        self.brain = Brain()
        #self.brain.add_thought(lambda: self.go_random(500))
        #self.brain.add_thought(lambda: self.go_to(self._me.x + 300, self._me.y - 300))
        self.brain.add_thought(lambda: self.go_to(1188, 1188))


    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug is None:
            self.debug = Debug(world.width, world.width, 0.17)

        self.tick_counter += 1

        self.Me = me
        self.World = world
        self.Game = game
        self.Move = move

        self.fill_obstacles()

        self.brain\
            .think()\
            .add_thought(self.detect_stuck)\
            .think()

        self.debug.draw(self)

        self.brain.forget_processed_thoughts()

    def detect_stuck(self):
        if (self.Move.speed > 0 or self.Move.strafe_speed > 0) and self.Me.speed_x == 0 and self.Me.speed_y == 0:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks = 0
            self.moving_obstacles = []
        if self.stuck_ticks > 1:
            print("stuck detected")
            self.moving_obstacles = self.find_moving_obstacles_around_me(100)
            self.brain.forget_current_thought()  # forget go_to_next_cell

        self.brain.forget_current_thought()

    def find_obstacles_in_route(self):
        for c in self.obstacles:
            for p in self.route:
                if p == c:
                    print("new obstacle detected!!!")
                    return True
        return False

    def go_random(self, radius):
        x = randint(int(self.Me.x - radius), int(self.Me.x + radius))
        y = randint(int(self.Me.y - radius), int(self.Me.y + radius))
        self.brain.add_thought(lambda: self.go_to(x, y))
        return True

    def go_to(self, x, y):
        x = min(max(0, x), 3924)  # @todo it should depend on CELL
        y = min(max(0, y), 3924)
        self.destination = (x, y)
        if self.Me.get_distance_to(to_real(to_calc(x)), to_real(to_calc(y))) < self.Game.wizard_forward_speed:
            self.brain.forget_current_thought()
            return True
        self.first_cell = None
        self.second_cell = None

        w, h = self.World.width, self.World.height
        start_x, start_y = self.Me.x, self.Me.y
        current_position = to_calc(start_x), to_calc(start_y)
        go_to = to_calc(x), to_calc(y)
        a = AStar(True)
        a.init_grid(to_calc(w), to_calc(h), self.obstacles + self.moving_obstacles,
                    current_position, go_to)
        self.route = a.solve()
        if self.route is not None:
            self.brain.add_thought(self.go_to_next_cell)
        else:
            self.brain.forget_current_thought()
            nx, ny = x - CELL / 2 * (-1 if x < self.Me.x else 1), y - CELL / 2 * (-1 if y < self.Me.y else 1)
            print(x, y, "->", nx, ny)
            self.brain.add_thought(lambda: self.go_to(nx, ny))
        return True

    def go_to_next_cell(self):
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
            x1, y1 = to_real(x1), to_real(y1)
            if self.second_cell is not None:
                x2, y2 = self.second_cell
                x2, y2 = to_real(x2), to_real(y2)
            else:
                x2, y2 = (None, None)
            if self.Me.get_distance_to(x1, y1) < 0.1 or self.second_cell is not None\
                    and (min(x1, x2) < round(self.Me.x, 4) < max(x1, x2) or min(y1, y2) < round(self.Me.y, 4) < max(y1, y2)):
                del self.route[0]
                self.first_cell = None
                self.second_cell = None
                return True
            else:
                if self.second_cell is not None:
                    if abs(Point(x1, y1, self.Me.angle).get_angle_to(x2, y2)) < pi / 360:  # pi / 360 rad == 0.5 deg
                        self.Move.speed = self.Game.wizard_forward_speed
                        return
                    else:
                        if self.Me.get_distance_to(x1, y1) < self.Game.wizard_forward_speed:
                            self.Move.speed = self.Me.get_distance_to(x1, y1)
                            self.brain.add_thought(self.pre_rotate)
                            return True

                self.Move.speed = self.Me.get_distance_to(x1, y1)

    def rotate(self):
        x, y = self.first_cell
        x, y = to_real(x), to_real(y)
        angle = self.Me.get_angle_to(x, y)
        if abs(angle) > 0:
            self.Move.turn = angle
        else:
            self.brain.forget_current_thought()
            return True

    def pre_rotate(self):
        x1, y1 = self.first_cell
        x1, y1 = to_real(x1), to_real(y1)
        x2, y2 = self.second_cell
        x2, y2 = to_real(x2), to_real(y2)
        self.Move.turn = Point(x1, y1, self.Me.angle).get_angle_to(x2, y2)
        self.brain.forget_current_thought()

    def find_target(self, me: Wizard, world: World, game: Game, move: Move):
        return False, {}

    def fill_obstacles(self):
        padding = OBSTACLES_PADDING
        self.obstacles = []
        for b in self.World.buildings:
            for x in range(to_calc(b.x - b.radius - padding), to_calc(b.x + b.radius + padding) + 1):
                for y in range(to_calc(b.y - b.radius - padding), to_calc(b.y + b.radius + padding) + 1):
                    self.obstacles.append((x, y))

        for t in self.World.trees:
            for x in range(to_calc(t.x - t.radius - padding), to_calc(t.x + t.radius + padding) + 1):
                for y in range(to_calc(t.y - t.radius - padding), to_calc(t.y + t.radius + padding) + 1):
                    self.obstacles.append((x, y))

    def find_moving_obstacles_around_me(self, radius):
        padding = OBSTACLES_PADDING
        obstacles = []
        x1, x2 = self.Me.x - radius, self.Me.x + radius
        y1, y2 = self.Me.y - radius, self.Me.y + radius
        for w in self.World.wizards:
            if w.id == self.Me.id:
                continue
            w_x1, w_x2 = w.x - w.radius - padding, w.x + w.radius + padding
            w_y1, w_y2 = w.y - w.radius - padding, w.y + w.radius + padding
            if (x1 < w_x1 < x2 or x1 < w_x2 < x2) and (y1 < w_y1 < y2 or y1 < w_y2 < y2):
                for x in range(to_calc(w.x - w.radius - padding), to_calc(w.x + w.radius + padding) + 1):
                    for y in range(to_calc(w.y - w.radius - padding), to_calc(w.y + w.radius + padding) + 1):
                        obstacles.append((x, y))
        return obstacles
