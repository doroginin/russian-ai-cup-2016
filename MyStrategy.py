from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
import astar as pf
from enum import Enum
import canvas


class Action(Enum):
    idle = 1
    going = 2
    attack = 3


class MyStrategy:
    CELL = 35
    path = []
    current_destination_cell = None
    action = Action.idle

    debug = None

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug is None:
            self.debug = canvas.Debug(self.c(world.width), self.c(world.width))
        self.debug.clear()
        self.debug.draw_wizard((self.c(me.x), self.c(me.y)))

        action, action_args = self.what_to_do(me, world, game, move)
        self.do(me, world, game, move, action, action_args)

    def what_to_do(self, me: Wizard, world: World, game: Game, move: Move):
        if self.action == Action.idle:
            target, found = self.find_target(me, world, game, move)
            if found:
                return Action.attack, target

            return Action.going, (3700, 100)

        if self.action == Action.going:
            target, found = self.find_target(me, world, game, move)
            if found:
                return Action.attack, target

            return Action.going, {}

    def do(self, me: Wizard, world: World, game: Game, move: Move, action, action_args):
        if action == Action.going:
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
                if abs(x - me.x) < me.radius and abs(y - me.y) < me.radius:
                    move.speed = 0
                    self.current_destination_cell = None
                else:
                    angle = me.get_angle_to(x, y)
                    move.turn = angle
                    move.speed = game.wizard_forward_speed

        self.action = action

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
            for x in range(self.c(b.x - b.radius / 2), self.c(b.x + b.radius / 2)):
                for y in range(self.c(b.y - b.radius / 2), self.c(b.y + b.radius / 2)):
                    obstacles.append((x, y))

        for t in world.trees:
            for x in range(self.c(t.x - t.radius / 2), self.c(t.x + t.radius / 2)):
                for y in range(self.c(t.y - t.radius / 2), self.c(t.y + t.radius / 2)):
                    obstacles.append((x, y))

        return obstacles

    def c(self, v):
        return int(v // self.CELL) + 1

    def r(self, v):
        return (v - 1) * self.CELL