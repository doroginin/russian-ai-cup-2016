from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Tree import Tree
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
from model.BuildingType import BuildingType
from model.MinionType import MinionType

# OBSTACLES_PADDING = 35 - CELL // 2 + 1  # 35 - Me radius
OBSTACLES_PADDING = 0
CHECKPOINT_INTERVAL = 1
WIZARD_CAST_RANGE_PADDING = 150
CHECKPOINT_STEP = 150
PENALTY_FOR_ENEMIES_ON_A_WAY_TO_BONUS = 2
AVOID_TOWER_FACTOR = 0
AVOID_FETISH_BLOWDART_FACTOR = 0
AVOID_WIZARD_FACTOR = 0

DEBUG = True

bonuses = {
    1: {'point': (1200.0, 1200.0), 'wait_point': (1239.0, 1161.0)},
    2: {'point': (2800.0, 2800.0), 'wait_point': (2761.0, 2839.0)}
}


class MyStrategy:
    brain = None
    debug = None
    start_x = None
    start_y = None
    a_star = []
    enemies_around_me = {
        'nw': {'count': 0, 'available_direction': False},
        'ne': {'count': 0, 'available_direction': False},
        'sw': {'count': 0, 'available_direction': False},
        'se': {'count': 0, 'available_direction': False},
    }

    me = world = game = mv = None

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
        self.last_stuck_position = (0, 0)
        self.last_stuck_tick = None
        self.last_stuck_angle = -180
        self.last_stuck_radius = 2

        self.idle = 0
        self.fight = False

        # case 1
        # self.brain.add(Thought(lambda: self.go_to(190, 3600)))
        # self.brain.add(Thought(lambda: self.go_to(190, 3750)))

        # case 2
        # self.brain.add(Thought(lambda: self.go_to(210, 3600), 'go_to'))
        # self.brain.add(Thought(lambda: self.go_to(210, 3700), 'go_to'))

        # self.brain.add(Thought(lambda: self.go_to(1000, 1000), "go_to"))
        # self.brain.add(Thought(lambda: self.go_to(2000, 2700), "go_to"))

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

        self.me = me
        self.world = world
        self.game = game
        self.mv = move

        # death
        if self.world.tick_index - self.tick > 500:
            self.__init__()

        self.tick = self.world.tick_index

        self.brain \
            .add(Thought(self.check_delayed_thoughts)) \
            .add(Thought(self.check_enemies)) \
            .add(Thought(self.check_bonus)) \
            .add(Thought(self.check_obstacles)) \
            .think() \
            .add(Thought(self.check_stuck)) \
            .add(Thought(self.check_checkpoint)) \
            .think()

        if self.debug is not None:
            self.debug.draw(self)

    def schedule(self, delay: int, thought: Thought):
        self.delayed_thoughts.append(
            {'after': (self.world.tick_index if self.world else 0) + delay, 'thought': thought})

    def check_delayed_thoughts(self):
        for t in self.delayed_thoughts:
            if self.world.tick_index >= t['after']:
                self.brain.add(t['thought'])
                self.delayed_thoughts.remove(t)
        return BrainState.done, BrainState.think

    def go_to_checkpoint(self):
        # @todo it's ugly
        if self.world.tick_index < 300:
            return

        if self.move_to_checkpoint == 0:
            return

        self.move_to_bonus = False

        destination = None
        if self.move_to_checkpoint < 0:
            count = sys.maxsize
            for d, c in self.enemies_around_me.items():
                if c["available_direction"] and c["count"] < count:
                    count = c["count"]
                    destination = d
            if destination is None:
                return

        if self.move_to_checkpoint > 0:
            count = 0
            destination = None
            for d, c in self.enemies_around_me.items():
                if c["available_direction"] and c["count"] > count:
                    count = c["count"]
                    destination = d

        if destination is None:
            # go to enemy base
            y = to_pixel(to_cell(self.start_x))
            x = to_pixel(to_cell(self.start_y))
        elif destination == "nw":
            x = to_pixel(to_cell(self.me.x - CHECKPOINT_STEP))
            y = x
        elif destination == "ne":
            x = to_pixel(to_cell(self.me.x + CHECKPOINT_STEP))
            y = 4000 - x
        elif destination == "se":
            x = to_pixel(to_cell(self.me.x + CHECKPOINT_STEP))
            y = x
        elif destination == "sw":
            x = to_pixel(to_cell(self.me.x - CHECKPOINT_STEP))
            y = 4000 - x

        self.brain.add(Thought(lambda: self.stop_moving_to_checkpoint()))
        self.brain.add(Thought(lambda: self.go_to(x, y), "go_to"))

    def pause_for_fight(self):
        if self.move_to_bonus or not self.current_target or \
                        self.me.get_distance_to(self.current_target.x,
                                                self.current_target.y) <= self.game.wizard_cast_range or \
                        self.move_to_checkpoint < 0:
            self.fight = False
            return BrainState.done, BrainState.think
        self.fight = True
        return

    def stop_moving_to_checkpoint(self):
        self.move_to_checkpoint = 0
        return BrainState.done, BrainState.think

    def check_enemies(self):
        self.enemies_around_me['nw'] = {'count': 0, 'available_direction': False}
        self.enemies_around_me['ne'] = {'count': 0, 'available_direction': False}
        self.enemies_around_me['se'] = {'count': 0, 'available_direction': False}
        self.enemies_around_me['sw'] = {'count': 0, 'available_direction': False}

        if self.me.x <= 2000 and self.me.y <= 2000 or self.me.x >= 2000 and self.me.y >= 2000:
            self.enemies_around_me['nw']['available_direction'] = True
            self.enemies_around_me['se']['available_direction'] = True

        if self.me.x <= 2000 and self.me.y >= 2000 or self.me.x >= 2000 and self.me.y <= 2000:
            self.enemies_around_me['sw']['available_direction'] = True
            self.enemies_around_me['ne']['available_direction'] = True

        if 1850 <= self.me.x <= 2150 and 1850 <= self.me.y <= 2150:
            self.enemies_around_me['nw']['available_direction'] = True
            self.enemies_around_me['ne']['available_direction'] = True
            self.enemies_around_me['sw']['available_direction'] = True
            self.enemies_around_me['se']['available_direction'] = True

        targets = []
        targets += self.world.buildings
        targets += self.world.wizards
        targets += self.world.minions
        if self.stuck_ticks > 0:
            for t in self.world.trees:
                if self.me.get_distance_to(t.x, t.y) <= self.me.radius + t.radius + 5:  # todo why 5, but not zero?
                    targets += [t]

        nearest_target = None
        nearest_target_distance = sys.float_info.max

        for t in targets:
            if (t.faction == Faction.NEUTRAL or t.faction == self.me.faction) and not isinstance(t, Tree):
                continue

            distance = self.me.get_distance_to(t.x, t.y)
            if distance > 2 * self.me.vision_range:
                continue

            if t.x <= self.me.x and t.y <= self.me.y:
                self.enemies_around_me['nw']['count'] += 1
            if t.x >= self.me.x and t.y <= self.me.y:
                self.enemies_around_me['ne']['count'] += 1
            if t.x >= self.me.x and t.y >= self.me.y:
                self.enemies_around_me['se']['count'] += 1
            if t.x <= self.me.x and t.y >= self.me.y:
                self.enemies_around_me['sw']['count'] += 1

            if distance < nearest_target_distance:
                nearest_target = t
                nearest_target_distance = distance

        if nearest_target is not None:
            self.brain.add(Thought(lambda: self.attack(nearest_target), "attack"))
        else:
            self.current_target = None

        return BrainState.think, BrainState.done

    def attack(self, target):
        distance = self.me.get_distance_to_unit(target)
        if distance <= self.game.wizard_cast_range + WIZARD_CAST_RANGE_PADDING:
            self.current_target = target
            self.set_accurate_mode_on()
            angle = self.me.get_angle_to_unit(target)
            self.mv.turn = angle

            if distance <= self.game.wizard_cast_range:
                if not self.move_to_bonus and self.move_to_checkpoint >= 0 \
                        and not isinstance(self.current_target, Tree):
                    self.brain.forget("go_to_next_cell")
                    self.brain.forget("go_to")
                    if not self.fight:
                        self.brain.add(Thought(self.pause_for_fight))
                if abs(angle) < self.game.staff_sector / 2.0:
                    if distance <= self.game.staff_range:
                        self.mv.action = ActionType.STAFF
                    else:
                        self.mv.action = ActionType.MAGIC_MISSILE
                        self.mv.cast_angle = angle
                        self.mv.min_cast_distance = distance - target.radius + self.game.magic_missile_radius
        else:
            self.current_target = None
            self.set_accurate_mode_off()

        return BrainState.done, BrainState.think

    def find_enemies_on_a_way_to_bonus(self):
        first = 0
        second = 0

        targets = []
        targets += self.world.buildings
        targets += self.world.wizards
        targets += self.world.minions

        for t in targets:
            if t.faction == Faction.NEUTRAL or t.faction == self.me.faction:
                continue

            if (bonuses[1]['point'][0] >= t.x >= self.me.x or self.me.x >= t.x >= bonuses[1]['point'][0]) and \
                    (bonuses[1]['point'][1] >= t.y >= self.me.y or self.me.y >= t.y >= bonuses[1]['point'][1]):
                first += 1

            if (bonuses[2]['point'][0] >= t.x >= self.me.x or self.me.x >= t.x >= bonuses[2]['point'][0]) and \
                    (bonuses[2]['point'][1] >= t.y >= self.me.y or self.me.y >= t.y >= bonuses[2]['point'][1]):
                second += 1

        return first, second

    def check_bonus(self):
        d1 = self.me.get_distance_to(*bonuses[1]['point'])
        d2 = self.me.get_distance_to(*bonuses[2]['point'])

        if not self.move_to_bonus and min(d1, d2) / 4 < self.game.bonus_appearance_interval_ticks \
                - self.world.tick_index % self.game.bonus_appearance_interval_ticks < min(d1, d2) / 2.5:
            w, h = self.world.width, self.world.height
            self.move_to_bonus = True
            self.check_obstacles()
            a = AStar()
            start = to_cell(self.me.x), to_cell(self.me.y)
            end1 = to_cell(bonuses[1]['point'][0]), to_cell(bonuses[1]['point'][1])
            end2 = to_cell(bonuses[2]['point'][0]), to_cell(bonuses[2]['point'][1])
            a.init_grid(to_cell(w), to_cell(h), self.obstacles + self.moving_obstacles,
                        start, end1)
            path1 = a.solve(True, True)
            a.init_grid(to_cell(w), to_cell(h), self.obstacles + self.moving_obstacles,
                        start, end2)
            path2 = a.solve(True, True)
            e1, e2 = self.find_enemies_on_a_way_to_bonus()
            e1 *= PENALTY_FOR_ENEMIES_ON_A_WAY_TO_BONUS
            e2 *= PENALTY_FOR_ENEMIES_ON_A_WAY_TO_BONUS
            self.move_to_bonus = 1 if len(path1) + e1 < len(path2) + e2 else 2
            self.brain.add(Thought(self.wait_bonus))
            self.brain.add(Thought(lambda: self.go_to(*bonuses[self.move_to_bonus]['wait_point']), "go_near_bonus"))
        return BrainState.think, BrainState.done

    def wait_bonus(self):
        if len(self.world.bonuses) > 0:
            for b in self.world.bonuses:
                d = Point(b.x, b.y).get_distance_to(*bonuses[self.move_to_bonus]['point'])
                if d < 5:
                    self.brain.add(Thought(self.get_bonus))
                    return BrainState.done

        if 5 < self.world.tick_index % self.game.bonus_appearance_interval_ticks \
                < self.game.bonus_appearance_interval_ticks / 2:
            self.move_to_checkpoint = 1
            self.go_to_checkpoint()
            return BrainState.done

    def get_bonus(self):
        if self.me.get_distance_to(*bonuses[self.move_to_bonus]['point']) > self.me.radius + self.game.bonus_radius:
            self.go_to(*bonuses[self.move_to_bonus]['point'])
        else:
            self.move_to_checkpoint = 1
            self.go_to_checkpoint()
            return BrainState.done

    def check_checkpoint(self):
        if not self.move_to_bonus:
            if self.move_to_checkpoint >= 0 \
                    and self.current_target is not None \
                    and (self.me.get_distance_to(self.current_target.x, self.current_target.y) <
                        self.game.wizard_cast_range / 2 or self.me.life < self.me.max_life * 0.70):
                self.brain.forget("go_to_next_cell")
                self.brain.forget("go_to")
                self.move_to_checkpoint = -1
                self.go_to_checkpoint()
            if self.me.life > self.me.max_life * 0.70 and self.idle > CHECKPOINT_INTERVAL:
                self.move_to_checkpoint = 1
                self.go_to_checkpoint()
                self.idle = 0
        if (self.stuck_ticks == 0 and self.mv.action is None or self.mv.action == ActionType.NONE) \
                and not self.fight and self.me.speed_x == 0 and self.me.speed_y == 0:
            self.idle += 1
        else:
            self.idle = 0

        return BrainState.think, BrainState.done

    def check_stuck(self):
        if (abs(self.mv.speed) > 0 or abs(self.mv.strafe_speed) > 0) \
                and abs(self.me.speed_x) < 0.1 and abs(self.me.speed_y) < 0.1:
            self.stuck_ticks += 1
        else:
            self.stuck_ticks = 0

        if self.stuck_ticks > 1:
            if isinstance(self.current_target, Tree):
                return BrainState.done

            if self.brain.exists('panic') or self.me.get_distance_to(*self.last_stuck_position) < 2 * self.me.radius:
                self.last_stuck_angle += pi / 180 * 45
                if self.last_stuck_angle > 2 * pi:
                    self.last_stuck_angle = 0
                    self.last_stuck_radius += 20
            else:
                self.last_stuck_angle = 0
                self.last_stuck_radius = 20

            x = self.me.x + self.last_stuck_radius * cos(self.last_stuck_angle)
            y = self.me.y + self.last_stuck_radius * sin(self.last_stuck_angle)
            self.brain.forget('panic', -1)
            self.brain.add(Thought(lambda: self.go_to(x, y), 'panic'))

            self.last_stuck_position = (self.me.x, self.me.y)
            self.last_stuck_tick = self.world.tick_index

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
                        return True
        return False

    def go_random(self, radius):
        x = randint(int(self.me.x - radius), int(self.me.x + radius))
        y = randint(int(self.me.y - radius), int(self.me.y + radius))
        self.brain.add(Thought(lambda: self.go_to(x, y), "go_to", (x, y)))
        return BrainState.think

    def go_to(self, x, y):
        self.current_point = None
        self.destination = None
        w, h = self.world.width, self.world.height
        r = self.me.radius
        x = min(max(r + 1, x), w - r - 1)
        y = min(max(r + 1, y), h - r - 1)
        distance = self.me.get_distance_to(x, y)
        if distance > 0.1:
            self.destination = (x, y)
        else:
            return BrainState.done, BrainState.think
        start_x, start_y = self.me.x, self.me.y
        current_position = to_cell(start_x), to_cell(start_y)
        go_to = to_cell(x), to_cell(y)
        a = AStar()
        a.init_grid(to_cell(w), to_cell(h), self.obstacles + self.moving_obstacles,
                    current_position, go_to)
        self.route = a.solve(True, True)
        self.a_star = a.cells
        if len(self.route) > 0:
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
            a1 = self.me.get_angle_to(x1, y1)

            x2, y2 = self.route[1]
            x2, y2 = to_pixel(x2), to_pixel(y2)
            a2 = self.me.get_angle_to(x2, y2)
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

    def go_to_next_cell(self):
        if self.find_obstacles_in_route():
            return BrainState.think, BrainState.done

        if self.current_point is None:
            self.get_next_point()
        if self.current_point is None:
            return BrainState.done, BrainState.think

        h = self.me.get_distance_to(*self.current_point)
        if h > 0.1:
            a = self.me.get_angle_to(*self.current_point)
            if self.accurate_mode and abs(a) > pi / 360:
                h = min(3, h)
            self.mv.speed = h * cos(a)
            self.mv.strafe_speed = h * sin(a)
            if self.current_target is None:
                self.mv.turn = a
            return
        else:
            self.current_point = None
            return BrainState.think

    def check_obstacles(self):
        self.obstacles = []
        for b in self.world.buildings:

            # if self.move_to_bonus and b.type == BuildingType.GUARDIAN_TOWER and b.faction != self.Me.faction:
            #     padding = self.Game.guardian_tower_attack_range * AVOID_TOWER_FACTOR
            # else:

            padding = OBSTACLES_PADDING

            for x in range(to_cell(b.x - b.radius - padding), to_cell(b.x + b.radius + padding) + 1):
                for y in range(to_cell(b.y - b.radius - padding), to_cell(b.y + b.radius + padding) + 1):
                    self.obstacles.append((x, y))

        for t in self.world.trees:
            if t.life > self.game.staff_damage / 2:
                for x in range(to_cell(t.x - t.radius - padding), to_cell(t.x + t.radius + padding) + 1):
                    for y in range(to_cell(t.y - t.radius - padding), to_cell(t.y + t.radius + padding) + 1):
                        self.obstacles.append((x, y))

        # if self.move_to_bonus:
        #     for t in self.World.wizards:
        #         if t.faction == Faction.NEUTRAL or t.faction == self.Me.faction:
        #             continue
        #         padding = self.Game.wizard_cast_range * AVOID_WIZARD_FACTOR
        #         for x in range(to_cell(t.x - t.radius - padding),
        #                        to_cell(t.x + t.radius + padding) + 1):
        #             for y in range(to_cell(t.y - t.radius - padding),
        #                            to_cell(t.y + t.radius + padding) + 1):
        #                 self.obstacles.append((x, y))
        #
        #     for t in self.World.minions:
        #         if t.faction == Faction.NEUTRAL or t.faction == self.Me.faction:
        #             continue
        #         if t.type == MinionType.FETISH_BLOWDART:
        #             padding = self.Game.fetish_blowdart_attack_range * AVOID_FETISH_BLOWDART_FACTOR
        #         else:
        #             padding = self.Me.radius * 3
        #         for x in range(to_cell(t.x - t.radius - padding),
        #                        to_cell(t.x + t.radius + padding) + 1):
        #             for y in range(to_cell(t.y - t.radius - padding),
        #                            to_cell(t.y + t.radius + padding) + 1):
        #                 self.obstacles.append((x, y))

        self.check_moving_obstacles_around_me(self.me.radius * 3)

        return BrainState.done, BrainState.think

    def check_moving_obstacles_around_me(self, radius):
        padding = OBSTACLES_PADDING
        obstacles = []
        x1, x2 = self.me.x - radius, self.me.x + radius
        y1, y2 = self.me.y - radius, self.me.y + radius
        for w in self.world.wizards:
            if w.id == self.me.id:
                continue
            w_x1, w_x2 = w.x - w.radius - padding, w.x + w.radius + padding
            w_y1, w_y2 = w.y - w.radius - padding, w.y + w.radius + padding
            if (x1 < w_x1 < x2 or x1 < w_x2 < x2) and (y1 < w_y1 < y2 or y1 < w_y2 < y2):
                for x in range(to_cell(w.x - w.radius - padding), to_cell(w.x + w.radius + padding) + 1):
                    for y in range(to_cell(w.y - w.radius - padding), to_cell(w.y + w.radius + padding) + 1):
                        obstacles.append((x, y))

        for m in self.world.minions:
            m_x1, m_x2 = m.x - m.radius - padding, m.x + m.radius + padding
            m_y1, m_y2 = m.y - m.radius - padding, m.y + m.radius + padding
            if (x1 < m_x1 < x2 or x1 < m_x2 < x2) and (y1 < m_y1 < y2 or y1 < m_y2 < y2):
                for x in range(to_cell(m.x - m.radius - padding), to_cell(m.x + m.radius + padding) + 1):
                    for y in range(to_cell(m.y - m.radius - padding), to_cell(m.y + m.radius + padding) + 1):
                        obstacles.append((x, y))

        self.moving_obstacles = obstacles
