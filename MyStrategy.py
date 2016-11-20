from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
import astar as pf
import canvas as c


class MyStrategy:
    CELL_WIDTH = 35
    CELL_HEIGHT = 35
    debug = None
    path = []

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.debug is None:
            self.debug = c.Debug(int(world.width // self.CELL_WIDTH), int(world.width // self.CELL_HEIGHT))

        self.debug.update()

        if len(self.path) == 0:
            self.path = self.find_path(me, world, game, move)

        if len(self.path) > 0:
            cell = self.path.pop()
            x = cell[0] * self.CELL_WIDTH
            y = cell[1] * self.CELL_WIDTH
            angle = me.get_angle_to(x, y)
            move.turn = angle
            move.speed = game.wizard_forward_speed
        else:
            move.speed = 0

        #print(self.path)
        #print(self.path.pop())
        #next_cell = self.path.pop()
        #me.get_angle_to(x, y)
        # move.speed = game.wizard_forward_speed
        # move.strafe_speed = game.wizard_strafe_speed
        # move.turn = game.wizard_max_turn_angle
        # move.action = ActionType.MAGIC_MISSILE
        # self.go_to(me, move, game, 100, 3600)

    def find_path(self, me: Wizard, world: World, game: Game, move: Move):
        current_position = (int(me.x // self.CELL_WIDTH), int(me.y // self.CELL_HEIGHT))
        go_to = (int(3700 // self.CELL_WIDTH), int(100 // self.CELL_HEIGHT))
        a = pf.AStar()
        unreachable_cells = []
        for b in world.buildings:
            for x in range(int((b.x - b.radius / 2) // self.CELL_WIDTH), int((b.x + b.radius / 2) // self.CELL_WIDTH)):
                for y in range(int((b.y - b.radius / 2) // self.CELL_HEIGHT),
                               int((b.y + b.radius / 2) // self.CELL_HEIGHT)):
                    unreachable_cells.append((x, y))

        a.init_grid(int(world.width // self.CELL_WIDTH), int(world.height // self.CELL_HEIGHT), unreachable_cells,
                    current_position, go_to)
        path = a.solve()
        #self.debug(path, me, world, game, move)
        return path

    # def go_to(self, me: Wizard, move: Move, game: Game, x, y):
    #     self.going = True
    #     angle = me.get_angle_to(x, y)
    #     move.turn = angle
    #     if abs(angle) < game.staff_sector / 4.0:
    #         move.speed = game.wizard_forward_speed

