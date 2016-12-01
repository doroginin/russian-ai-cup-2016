from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
from AStar import *
from Debug import *
from random import *
from math import *
from Brain import *
from BrainState import *
from Point import *
from model.Faction import Faction


OBSTACLES_PADDING = 35 - CELL // 2 + 1  # 35 - Me radius
CHECKPOINT_INTERVAL = 40
CONTINUE_GOING = 30

DEBUG = True


class MyStrategy:
    start_x = None
    start_y = None
    route = None
    processed_route = []
    obstacles = []
    moving_obstacles = []
    first_cell = None
    second_cell = None
    brain = None
    debug = None
    stuck_ticks = 0
    move_to_bonus = False

    destination = None
    current_target = None
    current_point = None
    move_to_checkpoint = 0

    i = -2
    idle = 0

    Me = World = Game = Move = None

    def __init__(self):
        self.brain = Brain()

        # self.brain.add(Thought(lambda: self.go_random2(500), "go_random({})", [500]))
        # self.brain.add(Thought(lambda: self.go_to(self.Me.x + 300, self.Me.y - 300)))
        # self.brain.add(Thought(lambda: self.go_to2(125, 3800), "go_to: 125, 3800"))
        # self.brain.add(Thought(lambda: self.go_to2(50, 3300), "go_to: 50, 3300"))
        # self.brain.add(Thought(lambda: self.go_to2(100, 3700), "go_to: 100, 3700"))
        # self.brain.add(Thought(lambda: self.go_to2(200, 4000), "go_to: 200, 4000"))
        # self.brain.add(Thought(lambda: self.go_to2(0, 3800), "go_to: 0, 3800"))
        # self.brain.add(Thought(lambda: self.go_to2(450, 3600), "go_to: 450, 3600"))
        # self.brain.add(Thought(lambda: self.go_to2(400, 3465), "go_to2({}, {})", (400, 3465)))

        if DEBUG:
            self.debug = Debug(800, 800, 0.17)
            # self.debug = Debug(600, 700, 1, 0, 3000)

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        if self.start_x is None:
            self.start_x = me.x
            self.start_y = me.y

        self.brain.forget_processed_thoughts()
        self.processed_route = []

        self.Me = me
        self.World = world
        self.Game = game
        self.Move = move

        self.brain\
            .add(Thought(self.check_checkpoint)) \
            .add(Thought(self.check_target))\
            .add(Thought(self.check_bonus))\
            .add(Thought(self.check_obstacles))\
            .think()\
            .add(Thought(self.check_stuck))\
            .think()

        if self.debug is not None:
            self.debug.draw(self)

    def go_to_checkpoint(self):
        x, y = 2000 + (200 if self.start_x < 2000 else -200) * self.i, 2000 + (200 if self.start_y < 2000 else -200) * self.i
        self.brain.add(Thought(lambda: self.go_to2(x, y), "go_to2({}, {})", (x, y)))
        return BrainState.done

    def check_target(self):
        targets = []
        targets += self.World.buildings
        targets += self.World.wizards
        targets += self.World.minions

        nearest_target = None
        nearest_target_distance = sys.float_info.max

        for t in targets:
            if t.faction == Faction.NEUTRAL or t.faction == self.Me.faction:
                continue

            distance = self.Me.get_distance_to(t.x, t.y)

            if distance < nearest_target_distance:
                nearest_target = t
                nearest_target_distance = distance

        if nearest_target is not None:
            self.brain.add(Thought(lambda: self.attack(nearest_target), "attack"))
        else:
            self.current_target = None

        return BrainState.think, BrainState.done

    def attack(self, target):
        distance = self.Me.get_distance_to_unit(target)
        if distance <= self.Game.wizard_cast_range:
            self.current_target = target
            if not self.move_to_bonus and self.move_to_checkpoint >= 0:
                self.brain.forget("go_to_next_cell")
                self.brain.forget("go_to({}, {})")
                self.brain.forget("go_to_next_cell2")
                self.brain.forget("go_to2({}, {})")
            angle = self.Me.get_angle_to_unit(target)
            self.Move.turn = angle

            if abs(angle) < self.Game.staff_sector / 2.0:
                self.Move.action = ActionType.MAGIC_MISSILE
                self.Move.cast_angle = angle
                self.Move.min_cast_distance = distance - target.radius + self.Game.magic_missile_radius
        else:
            self.current_target = None

        return BrainState.done

    def check_bonus(self):
        if not self.move_to_bonus and self.Me.get_distance_to(1200, 1200) / 2.5\
                > self.Game.bonus_appearance_interval_ticks\
                - self.World.tick_index % self.Game.bonus_appearance_interval_ticks:
            self.move_to_bonus = True
            self.brain.add(Thought(self.wait_bonus))
            self.brain.add(Thought(lambda: self.go_to2(1239, 1161), "go_near_bonus"))
        return BrainState.think, BrainState.done

    def wait_bonus(self):
        if len(self.World.bonuses) > 0:
            for b in self.World.bonuses:
                if b.x == 1200 and b.y == 1200:
                    self.brain.add(Thought(self.get_bonus))
                    return BrainState.done

        if 20 < self.Game.tick_count % self.Game.bonus_appearance_interval_ticks < 500:
            self.go_to_checkpoint()
            return BrainState.done

    def get_bonus(self):
        if self.Me.get_distance_to(1200, 1200) > self.Me.radius + self.Game.bonus_radius:
            self.go_to2(1200, 1200)
        else:
            self.move_to_bonus = False
            self.go_to_checkpoint()
            return BrainState.done

    def check_checkpoint(self):
        if not self.move_to_bonus:
            if self.Me.life < self.Me.max_life * 0.70 and self.move_to_checkpoint >= 0:
                self.brain.forget("go_to_next_cell2")
                self.brain.forget("go_to_next_cell")
                self.brain.forget("go_to2({}, {})")
                self.i -= 1
                self.go_to_checkpoint()
                self.move_to_checkpoint = -1
            if self.Me.life > self.Me.max_life * 0.50 and self.idle > CHECKPOINT_INTERVAL:
                self.i += 1
                self.go_to_checkpoint()
                self.idle = 0
                self.move_to_checkpoint = 1
            if self.Me.life > self.Me.max_life * 0.50 and self.idle > CONTINUE_GOING and self.destination is not None:
                self.go_to2(*self.destination)
                self.idle = 0
                self.move_to_checkpoint = 1

        if (self.Move.action is None or self.Move.action == ActionType.NONE)\
                and self.Me.speed_x == 0 and self.Me.speed_y == 0 and self.Move.turn == 0:
            self.idle += 1
        else:
            self.idle = 0

        if self.idle > 5:
            self.move_to_checkpoint = 0

        return BrainState.think, BrainState.done

    def check_stuck(self):
        if (self.Move.speed > 0 or self.Move.strafe_speed > 0) and self.Me.speed_x == 0 and self.Me.speed_y == 0:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks = 0
            self.moving_obstacles = []
        if self.stuck_ticks > 1:
            self.brain.forget("go_to_next_cell2")
            self.brain.forget("go_to_next_cell")
            if self.current_point is not None:
                x, y = self.current_point
                if to_cell(x) == to_cell(self.Me.x) and to_cell(y) == to_cell(self.Me.y):
                    self.brain.forget("go_to2({}, {})")
                else:
                    self.moving_obstacles = self.find_moving_obstacles_around_me(100)

        return BrainState.think, BrainState.done

    def find_obstacles_in_route(self):
        if len(self.route) > 0:
            for c in self.obstacles:
                for p in self.route:
                    if p == c:
                        if DEBUG:
                            print("new obstacle detected!!!")
                        return BrainState.think, BrainState.done
        return False

    def go_random(self, radius):
        x = randint(int(self.Me.x - radius), int(self.Me.x + radius))
        y = randint(int(self.Me.y - radius), int(self.Me.y + radius))
        self.brain.add(Thought(lambda: self.go_to(x, y, True), "go_to({}, {}, True)", (x, y)))
        return BrainState.think

    def go_random2(self, radius):
        x = randint(int(self.Me.x - radius), int(self.Me.x + radius))
        y = randint(int(self.Me.y - radius), int(self.Me.y + radius))
        self.brain.add(Thought(lambda: self.go_to2(x, y), "go_to2({}, {}, True)", (x, y)))
        return BrainState.think

    def go_to2(self, x, y):
        self.current_point = None
        self.destination = None
        w, h = self.World.width, self.World.height
        r = self.Me.radius
        x = min(max(r + 1, x), w - r - 1)
        y = min(max(r + 1, y), h - r - 1)
        if self.Me.get_distance_to(x, y) > 0.01:
            self.destination = (x, y)
        else:
            return BrainState.done, BrainState.think
        start_x, start_y = self.Me.x, self.Me.y
        current_position = to_cell(start_x), to_cell(start_y)
        go_to = to_cell(x), to_cell(y)
        a = AStar(True)
        a.init_grid(to_cell(w), to_cell(h), self.obstacles + self.moving_obstacles,
                    current_position, go_to)
        self.route = a.solve()
        if self.route is not None:
            del self.route[0]
            self.brain.add(Thought(self.go_to_next_cell2))
            return BrainState.think
        else:
            self.route = []
            # @todo remove this, astar should calc nearest point to the end by itself
            # nx, ny = x - CELL / 2 * (-1 if x < self.Me.x else 1), y - CELL / 2 * (-1 if y < self.Me.y else 1)
            # self.brain.add(Thought(lambda: self.go_to2(nx, ny), "go_to({}, {})", (nx, ny)))
            if DEBUG:
                print("Could not calculate route to {}, {}".format(x, y))
            return BrainState.think, BrainState.done

    def get_next_point(self):
        while len(self.route) > 1:
            x1, y1 = self.route[0]
            x1, y1 = to_pixel(x1), to_pixel(y1)
            a1 = self.Me.get_angle_to(x1, y1)

            x2, y2 = self.route[1]
            x2, y2 = to_pixel(x2), to_pixel(y2)
            a2 = self.Me.get_angle_to(x2, y2)
            if abs(a1 - a2) < pi / 380:
                self.processed_route.append(self.route[0])
                del self.route[0]
                continue
            else:
                self.current_point = x1, y1
                break

        if len(self.route) > 0:
            x1, y1 = self.route[0]
            x1, y1 = to_pixel(x1), to_pixel(y1)
            self.current_point = x1, y1
            self.processed_route.append(self.route[0])
            del self.route[0]
        else:
            if self.destination is not None:
                self.current_point = self.destination
                self.destination = None

    # @todo add pre_rotate
    def go_to_next_cell2(self):
        if self.find_obstacles_in_route():
            return BrainState.think, BrainState.done

        if self.current_point is None:
            self.get_next_point()
        if self.current_point is None:
            return BrainState.done, BrainState.think

        h = self.Me.get_distance_to(*self.current_point)

        if h > 0.01:
            a = self.Me.get_angle_to(*self.current_point)
            self.Move.speed = h * cos(a)
            self.Move.strafe_speed = h * sin(a)
            if self.current_target is None:
                self.Move.turn = a
            return
        else:
            self.current_point = None
            return BrainState.think

    def go_to(self, x, y, strict=False):
        x = min(max(36, x), 3924)  # @todo it should depend on CELL
        y = min(max(36, y), 3924)
        self.destination = (x, y)
        # if self.Me.get_distance_to(to_real(to_calc(x)), to_real(to_calc(y))) < self.Game.wizard_forward_speed:
        if to_cell(x) == to_cell(self.Me.x) and to_cell(y) == to_cell(self.Me.y):
            if not strict:
                self.destination = None
                return BrainState.think, BrainState.done
            h = self.Me.get_distance_to(x, y)
            if h > 0.1:  # @todo why not 0.1?
                a = self.Me.get_angle_to(x, y)
                self.Move.speed = h * cos(a)
                self.Move.strafe_speed = h * sin(a)
                return
            else:
                self.destination = None
                return BrainState.think, BrainState.done

        self.first_cell = None
        self.second_cell = None

        w, h = self.World.width, self.World.height
        start_x, start_y = self.Me.x, self.Me.y
        current_position = to_cell(start_x), to_cell(start_y)
        go_to = to_cell(x), to_cell(y)
        a = AStar(True)
        a.init_grid(to_cell(w), to_cell(h), self.obstacles + self.moving_obstacles,
                    current_position, go_to)
        self.route = a.solve()
        if self.route is not None:
            self.brain.add(Thought(self.go_to_next_cell))
            return BrainState.think
        else:
            self.route = []
            nx, ny = x - CELL / 2 * (-1 if x < self.Me.x else 1), y - CELL / 2 * (-1 if y < self.Me.y else 1)
            self.brain.add(Thought(lambda: self.go_to(nx, ny), "go_to({}, {})", (nx, ny)))
            return BrainState.think, BrainState.done

    def go_to_next_cell(self):
        if self.find_obstacles_in_route():
            return BrainState.think, BrainState.done

        if self.first_cell is None:
            if len(self.route) > 0:
                self.first_cell = self.route[0]
                if len(self.route) > 1:
                    self.second_cell = self.route[1]
                else:
                    self.second_cell = None
                self.brain.add(Thought(self.rotate))
                return BrainState.think
            else:
                return BrainState.done
        else:
            x1, y1 = self.first_cell
            x1, y1 = to_pixel(x1), to_pixel(y1)
            if self.second_cell is not None:
                x2, y2 = self.second_cell
                x2, y2 = to_pixel(x2), to_pixel(y2)
            else:
                x2, y2 = (None, None)
            if self.Me.get_distance_to(x1, y1) < 0.1 or self.second_cell is not None\
                    and (min(x1, x2) < round(self.Me.x, 4) < max(x1, x2) or min(y1, y2) < round(self.Me.y, 4) < max(y1, y2)):
                self.processed_route.append(self.route[0])
                del self.route[0]
                self.first_cell = None
                self.second_cell = None
                return BrainState.think
            else:
                if self.second_cell is not None:
                    if abs(Point(x1, y1, self.Me.angle).get_angle_to(x2, y2)) < pi / 360:  # pi / 360 rad == 0.5 deg
                        self.Move.speed = self.Game.wizard_forward_speed
                        return
                    else:
                        if self.Me.get_distance_to(x1, y1) < self.Game.wizard_forward_speed:
                            self.Move.speed = self.Me.get_distance_to(x1, y1)
                            self.brain.add(Thought(self.pre_rotate))
                            return BrainState.think

                self.Move.speed = self.Me.get_distance_to(x1, y1)

    def rotate(self, x=None, y=None):
        if x is None or y is None:
            x, y = self.first_cell
            x, y = to_pixel(x), to_pixel(y)
        angle = self.Me.get_angle_to(x, y)
        if abs(angle) > 0:
            self.Move.turn = angle
        else:
            return BrainState.think, BrainState.done

    def pre_rotate(self):
        x1, y1 = self.first_cell
        x1, y1 = to_pixel(x1), to_pixel(y1)
        x2, y2 = self.second_cell
        x2, y2 = to_pixel(x2), to_pixel(y2)
        self.Move.turn = Point(x1, y1, self.Me.angle).get_angle_to(x2, y2)
        return BrainState.done

    def check_obstacles(self):
        padding = OBSTACLES_PADDING
        self.obstacles = []
        for b in self.World.buildings:
            for x in range(to_cell(b.x - b.radius - padding), to_cell(b.x + b.radius + padding) + 1):
                for y in range(to_cell(b.y - b.radius - padding), to_cell(b.y + b.radius + padding) + 1):
                    self.obstacles.append((x, y))

        for t in self.World.trees:
            for x in range(to_cell(t.x - t.radius - padding), to_cell(t.x + t.radius + padding) + 1):
                for y in range(to_cell(t.y - t.radius - padding), to_cell(t.y + t.radius + padding) + 1):
                    self.obstacles.append((x, y))

        return BrainState.done, BrainState.think

        # for x in range(0, to_calc(self.World.width)):
        #     for y in range(0, to_calc(padding) + 1):
        #         self.obstacles.append((x, y))
        #
        # for x in range(0, to_calc(self.World.width)):
        #     for y in range(to_calc(self.World.height - padding), to_calc(self.World.height)):
        #         self.obstacles.append((x, y))
        #
        # for x in range(0, to_calc(padding) + 1):
        #     for y in range(0, to_calc(self.World.height)):
        #         self.obstacles.append((x, y))
        #
        # for x in range(to_calc(self.World.width - padding), to_calc(self.World.width)):
        #     for y in range(0, to_calc(self.World.height)):
        #         self.obstacles.append((x, y))

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
                for x in range(to_cell(w.x - w.radius - padding), to_cell(w.x + w.radius + padding) + 1):
                    for y in range(to_cell(w.y - w.radius - padding), to_cell(w.y + w.radius + padding) + 1):
                        obstacles.append((x, y))

        for m in self.World.minions:
            m_x1, m_x2 = m.x - m.radius - padding, m.x + m.radius + padding
            m_y1, m_y2 = m.y - m.radius - padding, m.y + m.radius + padding
            if (x1 < m_x1 < x2 or x1 < m_x2 < x2) and (y1 < m_y1 < y2 or y1 < m_y2 < y2):
                for x in range(to_cell(m.x - m.radius - padding), to_cell(m.x + m.radius + padding) + 1):
                    for y in range(to_cell(m.y - m.radius - padding), to_cell(m.y + m.radius + padding) + 1):
                        obstacles.append((x, y))
        return obstacles
