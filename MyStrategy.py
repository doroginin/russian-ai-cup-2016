from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
import astar as pf
from enum import Enum
import canvas
from math import sqrt


class Action(Enum):
    idle = 1
    rotate = 2
    go = 3
    attack = 4


class MyStrategy:
    CELL = 70
    path = []
    current_destination_cell = None
    action = Action.idle

    debug = None

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug is None:
            self.debug = canvas.Debug(self.c(world.width), self.c(world.width))

        print("x: {}, y: {}".format(me.x, me.y))
        self.debug.clear()
        self.debug.draw_wizard((self.c(me.x), self.c(me.y)))

        action, action_args = self.what_to_do(me, world, game, move)
        self.do(me, world, game, move, action, action_args)

    def what_to_do(self, me: Wizard, world: World, game: Game, move: Move):
        target, found = self.find_target(me, world, game, move)
        if found:
            return Action.attack, target

        if self.action == Action.idle:
            return Action.go, (1000, 500)

        return self.action, {}

    def do(self, me: Wizard, world: World, game: Game, move: Move, action, action_args):
        self.action = action
        if action == Action.go:
            obstacles = self.find_obstacles(world)
            self.debug.draw_obstacles(obstacles)

            if len(action_args) > 0:
                self.path = self.find_path((world.width, world.height), (me.x, me.y), action_args, obstacles)
                self.current_destination_cell = None
            else:
                for c in obstacles:
                    for p in self.path:
                        if p == c:
                            print("obstacle detected")
                            end = self.path.pop()
                            self.path = self.find_path((world.width, world.height), (me.x, me.y),
                                                       (self.r(end[0]), self.r(end[1])), obstacles)
                            self.current_destination_cell = None

            self.debug.draw_path(self.path)

            if self.current_destination_cell is None and len(self.path) > 0:
                self.current_destination_cell = self.path[0]
                del self.path[0]

            if self.current_destination_cell:
                x, y = self.current_destination_cell
                x = self.r(x)
                y = self.r(y)
                if abs(x - me.x) == 0 and abs(y - me.y) == 0:
                    move.speed = 0
                    self.current_destination_cell = None
                else:
                    angle = me.get_angle_to(x, y)
                    if abs(angle) > 0:
                        self.do(me, world, game, move, Action.rotate, {})
                        return
                    move.speed = sqrt((x - me.x) ** 2 + (y - me.y) ** 2)

        if action == Action.rotate:
            if self.current_destination_cell:
                x, y = self.current_destination_cell
                x = self.r(x)
                y = self.r(y)
                angle = me.get_angle_to(x, y)
                if abs(angle) > 0:
                    move.turn = angle
                else:
                    move.turn = 0
                    move.speed = 0
                    self.do(me, world, game, move, Action.go, {})
            else:
                self.do(me, world, game, move, Action.idle, {})

    def find_path(self, size, start, end, unreachable_cells):
        w, h = size
        start_x, start_y = start
        current_position = self.c(start_x), self.c(start_y)
        end_x, end_y = end
        go_to = self.c(end_x), self.c(end_y)
        a = pf.AStar()
        a.init_grid(self.c(w), self.c(h), unreachable_cells,
                    current_position, go_to)
        path = a.solve()
        return path

    def find_target(self, me: Wizard, world: World, game: Game, move: Move):
        return False, {}

    def find_obstacles(self, world: World):
        obstacles = []
        for b in world.buildings:
            for x in range(self.c(b.x - b.radius), self.c(b.x + b.radius)):
                for y in range(self.c(b.y - b.radius), self.c(b.y + b.radius)):
                    obstacles.append((x, y))

        for t in world.trees:
            for x in range(self.c(t.x - t.radius), self.c(t.x + t.radius)):
                for y in range(self.c(t.y - t.radius), self.c(t.y + t.radius)):
                    obstacles.append((x, y))

        return obstacles

    def c(self, v):
        return int(v // self.CELL) + 1

    def r(self, v):
        return (v - 1) * self.CELL + self.CELL / 2