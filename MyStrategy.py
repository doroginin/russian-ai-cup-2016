from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
import astar as pf
import canvas
from math import sqrt


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
    next_cell = None
    brain = None
    debug = None

    _me = _world = _game = _move = None

    def __init__(self):
        self.brain = Brain()
        self.brain.add_thought(lambda: self.go_to(1500, 1500))

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug is None:
            self.debug = canvas.Debug(world.width, world.width, 0.2, self.CELL)

        self._me = me
        self._world = world
        self._game = game
        self._move = move

        self.fill_obstacles()

        #print("x: {}, y: {}".format(me.x, me.y))

        self.brain.think()

        self.debug.draw(me, world, self.route, self.obstacles)

    def find_obstacles_in_route(self):
        for c in self.obstacles:
            for p in self.route:
                if p == c:
                    print("new obstacle detected!!!")
                    return True
        return False

    def go_to(self, x, y):
        if abs(x - self._me.x) < 0.1 and abs(y - self._me.y) < 0.1:
            self.brain.forget_current_thought()
            return
        self.brain.add_thought(self.go_to_next_cell)
        self.brain.add_thought(lambda: self.find_path(x, y))
        self.brain.think()

    def go_to_next_cell(self):
        if self.find_obstacles_in_route():
            self.brain.forget_current_thought()
            return

        if self.next_cell is None:
            if len(self.route) > 0:
                # self.next_cell = self.route[1]
                # del self.route[0]
                # del self.route[1]
                self.next_cell = self.route[0]
                del self.route[0]
                self.brain.add_thought(self.rotate)
                self.brain.think()
            else:
                self.brain.forget_current_thought()
        else:
            x, y = self.next_cell
            x = self.r(x)
            y = self.r(y)
            if abs(x - self._me.x) < 0.1 and abs(y - self._me.y) < 0.1:
                self._move.speed = 0
                self.next_cell = None
            else:
                self._move.speed = sqrt((x - self._me.x) ** 2 + (y - self._me.y) ** 2)

    def rotate(self):
        x, y = self.next_cell
        x = self.r(x)
        y = self.r(y)
        angle = self._me.get_angle_to(x, y)
        if abs(angle) > 0:
            self._move.turn = angle
        else:
            self.brain.forget_current_thought()
            self.brain.think()

    def find_path(self, end_x, end_y):
        w, h = self._world.width, self._world.height
        start_x, start_y = self._me.x, self._me.y
        current_position = self.c(start_x), self.c(start_y)
        go_to = self.c(end_x), self.c(end_y)
        a = pf.AStar()
        a.init_grid(self.c(w), self.c(h), self.obstacles,
                    current_position, go_to)
        self.route = a.solve()
        self.next_cell = None
        self.brain.forget_current_thought()
        self.brain.think()

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