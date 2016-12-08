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


# OBSTACLES_PADDING = 35 - CELL // 2 + 1  # 35 - Me radius
OBSTACLES_PADDING = 10
CHECKPOINT_INTERVAL = 15
CONTINUE_GOING = 10
WIZARD_CAST_RANGE_PADDING = 150

DEBUG = False


class MyStrategy:
    brain = None
    debug = None
    start_x = None
    start_y = None
    a_star = []

    Me = World = Game = Move = None

    tick = 0

    def __init__(self):
        if self.brain is None:
            self.brain = Brain()
        else:
            self.brain.thoughts = []
            self.brain.forget_processed_thoughts()

        self.stuck_ticks = 0
        self.move_to_bonus = False
        self.route = []
        self.processed_route = []
        self.obstacles = []
        self.moving_obstacles = []
        self.delayed_thoughts = []
        self.destination = None
        self.current_target = None
        self.current_point = None
        self.move_to_checkpoint = 0
        self.accurate_mode = False
        self.last_stuck_position = None
        self.last_stuck_tick = None
        self.i = -8
        self.idle = 0

        # case 1
        # self.brain.add(Thought(lambda: self.go_to(190, 3600), 'go_to'))
        # self.brain.add(Thought(lambda: self.go_to(190, 3750), 'go_to'))

        # case 2
        # self.brain.add(Thought(lambda: self.go_to(210, 3600), 'go_to'))
        # self.brain.add(Thought(lambda: self.go_to(210, 3700), 'go_to'))

        if DEBUG and self.debug is None:
            self.debug = Debug(800, 800, 0.17, a_star=False)
            # self.debug = Debug(800, 800, 1, 0, 3200, a_star=True)

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        self.a_star = []
        if self.start_x is None:
            self.start_x = me.x
            self.start_y = me.y

        self.brain.forget_processed_thoughts()
        self.processed_route = []

        self.Me = me
        self.World = world
        self.Game = game
        self.Move = move

        # death
        if self.World.tick_index - self.tick > 500:
            self.__init__()

        self.tick = self.World.tick_index

        self.brain\
            .add(Thought(self.check_delayed_thoughts))\
            .add(Thought(self.check_checkpoint))\
            .add(Thought(self.check_target))\
            .add(Thought(self.check_bonus))\
            .add(Thought(self.check_obstacles))\
            .think()\
            .add(Thought(self.check_stuck))\
            .think()

        if self.debug is not None:
            self.debug.draw(self)

    def schedule(self, delay: int, thought: Thought):
        self.delayed_thoughts.append({'after': (self.World.tick_index if self.World else 0) + delay, 'thought': thought})

    def check_delayed_thoughts(self):
        for t in self.delayed_thoughts:
            if self.World.tick_index >= t['after']:
                self.brain.add(t['thought'])
                self.delayed_thoughts.remove(t)
        return BrainState.done, BrainState.think

    def go_to_checkpoint(self):
        self.move_to_bonus = False
        x, y = 2000 + (150 if self.start_x < 2000 else -150) * self.i,\
            2000 + (150 if self.start_y < 2000 else -150) * self.i
        self.brain.add(Thought(lambda: self.stop_moving_to_checkpoint()))
        self.brain.add(Thought(lambda: self.go_to(x, y), "go_to"))

    def stop_moving_to_checkpoint(self):
        self.move_to_checkpoint = 0
        return BrainState.done, BrainState.think

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
        if distance <= self.Game.wizard_cast_range + WIZARD_CAST_RANGE_PADDING:
            self.current_target = target
            self.set_accurate_mode_on()
            angle = self.Me.get_angle_to_unit(target)
            self.Move.turn = angle

            if distance <= self.Game.wizard_cast_range:
                if not self.move_to_bonus and self.move_to_checkpoint >= 0:
                    self.brain.forget("go_to_next_cell")
                    self.brain.forget("go_to")
                if abs(angle) < self.Game.staff_sector / 2.0:
                    if distance <= self.Game.staff_range:
                        self.Move.action = ActionType.STAFF
                    else:
                        self.Move.action = ActionType.MAGIC_MISSILE
                        self.Move.cast_angle = angle
                        self.Move.min_cast_distance = distance - target.radius + self.Game.magic_missile_radius
        else:
            self.current_target = None
            self.set_accurate_mode_off()

        return BrainState.done, BrainState.think

    def check_bonus(self):
        d = self.Me.get_distance_to(1200, 1200)
        if not self.move_to_bonus and d / 4 < self.Game.bonus_appearance_interval_ticks\
                - self.World.tick_index % self.Game.bonus_appearance_interval_ticks < d / 2.5:
            self.move_to_bonus = True
            self.brain.add(Thought(self.wait_bonus))
            self.brain.add(Thought(lambda: self.go_to(1239, 1161), "go_near_bonus"))
        return BrainState.think, BrainState.done

    def wait_bonus(self):
        if len(self.World.bonuses) > 0:
            for b in self.World.bonuses:
                if b.x == 1200 and b.y == 1200:
                    self.brain.add(Thought(self.get_bonus))
                    return BrainState.done

        if 20 < self.World.tick_index % self.Game.bonus_appearance_interval_ticks < 500:
            self.go_to_checkpoint()
            return BrainState.done

    def get_bonus(self):
        if self.Me.get_distance_to(1200, 1200) > self.Me.radius + self.Game.bonus_radius:
            self.go_to(1200, 1200)
        else:
            self.go_to_checkpoint()
            return BrainState.done

    def check_checkpoint(self):
        if not self.move_to_bonus:
            if self.Me.life < self.Me.max_life * 0.60 and self.move_to_checkpoint >= 0\
                    and self.current_target is not None:
                self.brain.forget("go_to_next_cell")
                self.brain.forget("go_to")
                self.i -= 1
                self.go_to_checkpoint()
                self.move_to_checkpoint = -1
            if self.Me.life > self.Me.max_life * 0.60 and self.idle > CHECKPOINT_INTERVAL:
                self.i += 1
                self.go_to_checkpoint()
                self.idle = 0
                self.move_to_checkpoint = 1
            if self.Me.life > self.Me.max_life * 0.60 and self.idle > CONTINUE_GOING and self.destination is not None:
                self.brain.add(Thought(lambda: self.stop_moving_to_checkpoint()))
                self.go_to(*self.destination)
                self.idle = 0
                self.move_to_checkpoint = 1

        if (self.Move.action is None or self.Move.action == ActionType.NONE)\
                and self.Me.speed_x == 0 and self.Me.speed_y == 0 and self.Move.turn == 0:
            self.idle += 1
        else:
            self.idle = 0

        return BrainState.think, BrainState.done

    def check_stuck(self):
        if (abs(self.Move.speed) > 0 or abs(self.Move.strafe_speed) > 0)\
                and abs(self.Me.speed_x) < 0.1 and abs(self.Me.speed_y) < 0.1:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks = 0
            self.moving_obstacles = []
        if self.stuck_ticks > 1:
            self.brain.forget("go_to_next_cell")

            # if self.last_stuck_position is (self.Me.x, self.Me.y)\
            #     and self.World.tick_index - self.last_stuck_tick > 5:
            #     print("cancel this move")
            #     self.brain.forget("go_to")
            #     return BrainState.done

            self.last_stuck_position = (self.Me.x, self.Me.y)
            self.last_stuck_tick = self.World.tick_index

            if self.current_point is not None:
                # x, y = self.current_point
                # if to_cell(x) == to_cell(self.Me.x) and to_cell(y) == to_cell(self.Me.y):
                #     self.brain.forget("go_to")
                # else:
                self.moving_obstacles = self.find_moving_obstacles_around_me(100)

                # if self.accurate_mode:
                #     self.set_accurate_mode_off()
                # else:
                #     self.set_accurate_mode_on()

                # self.schedule(10, (Thought(self.set_accurate_mode_off)))
                return BrainState.done, BrainState.think

        return BrainState.done

    def set_accurate_mode_on(self):
        self.accurate_mode = True
        return BrainState.done, BrainState.think

    def set_accurate_mode_off(self):
        self.accurate_mode = False
        return BrainState.done, BrainState.think

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
        self.brain.add(Thought(lambda: self.go_to(x, y), "go_to", (x, y)))
        return BrainState.think

    def go_to(self, x, y):
        self.current_point = None
        self.destination = None
        w, h = self.World.width, self.World.height
        r = self.Me.radius
        x = min(max(r + 1, x), w - r - 1)
        y = min(max(r + 1, y), h - r - 1)
        distance = self.Me.get_distance_to(x, y)
        if distance > 0.1:
            self.destination = (x, y)
        else:
            return BrainState.done, BrainState.think
        start_x, start_y = self.Me.x, self.Me.y
        current_position = to_cell(start_x), to_cell(start_y)
        go_to = to_cell(x), to_cell(y)
        a = AStar()
        a.init_grid(to_cell(w), to_cell(h), self.obstacles + self.moving_obstacles,
                    current_position, go_to)
        self.route = a.solve(True, True)
        self.a_star = a.cells
        if len(self.route) > 0:
            if self.stuck_ticks < 5:
                del self.route[0]
            self.brain.add(Thought(self.go_to_next_cell))
            return BrainState.think
        else:
            self.route = []
            return BrainState.think, BrainState.done

    def get_next_point(self):
        while len(self.route) > 1:
            x1, y1 = self.route[0]
            x1, y1 = to_pixel(x1), to_pixel(y1)
            a1 = self.Me.get_angle_to(x1, y1)

            x2, y2 = self.route[1]
            x2, y2 = to_pixel(x2), to_pixel(y2)
            a2 = self.Me.get_angle_to(x2, y2)
            if abs(a1 - a2) < pi / 360:
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
    def go_to_next_cell(self):
        if self.find_obstacles_in_route():
            return BrainState.think, BrainState.done

        if self.current_point is None:
            self.get_next_point()
        if self.current_point is None:
            return BrainState.done, BrainState.think

        h = self.Me.get_distance_to(*self.current_point)
        if h > 0.1:
            a = self.Me.get_angle_to(*self.current_point)
            if self.accurate_mode and abs(a) > pi / 360:
                h = min(3, h)
            self.Move.speed = h * cos(a)
            self.Move.strafe_speed = h * sin(a)
            if self.current_target is None:
                self.Move.turn = a
            return
        else:
            self.current_point = None
            return BrainState.think

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
