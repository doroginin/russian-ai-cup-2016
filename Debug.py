from tkinter import *
from math import *
import collections
from Point import *
import MyStrategy
from model.Faction import Faction


class Debug:
    def x(self, x):
        return (x - self.start_x) * self.scale

    def y(self, y):
        return (y - self.start_y) * self.scale

    def __init__(self, w, h, scale, start_x=0, start_y=0, a_star=False):
        self.scale = scale
        self.start_x = start_x
        self.start_y = start_y
        self.window = Tk()
        self.canvas = Canvas(self.window, width=w, height=h, bg="white")
        self.canvas.pack()
        self.a_star = a_star

    def draw(self, s: MyStrategy):
        self.canvas.delete("all")

        if self.a_star:
            for c in s.a_star:
                self.canvas.create_text(self.x(to_pixel(c.x)), self.y(to_pixel(c.y) - CELL / 3),
                                        text=c.g,
                                        fill="green", font=("Helvectica", "5"))
                self.canvas.create_text(self.x(to_pixel(c.x)), self.y(to_pixel(c.y)),
                                        text=c.h,
                                        fill="blue", font=("Helvectica", "5"))
                self.canvas.create_text(self.x(to_pixel(c.x)), self.y(to_pixel(c.y) + CELL / 3),
                                        text=c.f,
                                        fill="red", font=("Helvectica", "5"))

        for i, t in enumerate(s.brain.processed):
            self.canvas.create_text(self.canvas.winfo_width() - 10, 10 + i * 10,
                                    text=t.name.format(*t.args),
                                    fill="gray", font=("Helvectica", "10"), anchor="e")

        if s.brain.thoughts is not None:
            for i, t in enumerate(s.brain.thoughts):
                self.canvas.create_text(self.canvas.winfo_width() - 10,
                                        10 + (len(s.brain.thoughts) - i - 1 + len(s.brain.processed)) * 10,
                                        text=t.name.format(*t.args),
                                        fill="green" if i == len(s.brain.thoughts) - 1 else "blue",
                                        font=("Helvectica", "10"), anchor="e")

        self.canvas.create_text(self.canvas.winfo_width() / 2, 10,
                                text="Me.speed: {:.2f}".format(hypot(s.me.speed_x, s.me.speed_y)),
                                fill="red", font=("Helvectica", "10"))
        self.canvas.create_text(self.canvas.winfo_width() / 2, 20,
                                text="Move.speed: {:.2f}".format(s.mv.speed),
                                fill="red", font=("Helvectica", "10"))
        self.canvas.create_text(self.canvas.winfo_width() / 2, 30,
                                text="Move.strafe_speed: {:.2f}".format(s.mv.strafe_speed),
                                fill="red", font=("Helvectica", "10"))
        self.canvas.create_text(self.canvas.winfo_width() / 2, 40,
                                text="Me.angle: {:.2f}".format(s.me.angle / pi * 180),
                                fill="red", font=("Helvectica", "10"))
        self.canvas.create_text(self.canvas.winfo_width() / 2, 50,
                                text="Move.turn: {:.2f}".format(s.mv.turn / pi * 180),
                                fill="red", font=("Helvectica", "10"))

        self.canvas.create_text(10, 10,
                                text="Tick: {:d}, idle: {:d}, move_to_checkpoint: {:d}, stuck: {:d}".format(s.world.tick_index, s.idle, s.move_to_checkpoint, s.stuck_ticks),
                                fill="red", font=("Helvectica", "10"), anchor="w")
        self.canvas.create_text(10, 20,
                                text="Position: {:.2f}, {:.2f} / {:d}, {:d}".format(s.me.x, s.me.y, to_cell(s.me.x), to_cell(s.me.y)),
                                fill="red", font=("Helvectica", "10"), anchor="w")

        self.canvas.create_oval(self.x(s.me.x - s.me.radius),
                                self.y(s.me.y - s.me.radius),
                                self.x(s.me.x + s.me.radius),
                                self.y(s.me.y + s.me.radius),
                                outline=self.get_my_color(s))

        self.canvas.create_rectangle(self.x(to_cell(s.me.x) * CELL),
                                     self.y(to_cell(s.me.y) * CELL),
                                     self.x((to_cell(s.me.x) + 1) * CELL) - 1,
                                     self.y((to_cell(s.me.y) + 1) * CELL) - 1,
                                     outline="blue")

        self.canvas.create_text(self.x(s.me.x - 2 * s.me.radius), self.y(s.me.y - 2 * s.me.radius),
                                text="{:d}".format(s.enemies_around_me["nw"]["count"]),
                                fill="red" if s.enemies_around_me["nw"]["available_direction"] else "gray",
                                font=("Helvectica", "10"))
        self.canvas.create_text(self.x(s.me.x + 2 * s.me.radius), self.y(s.me.y - 2 * s.me.radius),
                                text="{:d}".format(s.enemies_around_me["ne"]["count"]),
                                fill="red" if s.enemies_around_me["ne"]["available_direction"] else "gray",
                                font=("Helvectica", "10"))
        self.canvas.create_text(self.x(s.me.x + 2 * s.me.radius), self.y(s.me.y + 2 * s.me.radius),
                                text="{:d}".format(s.enemies_around_me["se"]["count"]),
                                fill="red" if s.enemies_around_me["se"]["available_direction"] else "gray",
                                font=("Helvectica", "10"))
        self.canvas.create_text(self.x(s.me.x - 2 * s.me.radius), self.y(s.me.y + 2 * s.me.radius),
                                text="{:d}".format(s.enemies_around_me["sw"]["count"]),
                                fill="red" if s.enemies_around_me["sw"]["available_direction"] else "gray",
                                font=("Helvectica", "10"))

        self.canvas.create_line(self.x(s.me.x), self.y(s.me.y),
                                self.x(s.me.x + s.me.vision_range * cos(s.me.angle)),
                                self.y(s.me.y + s.me.vision_range * sin(s.me.angle)),
                                fill="blue")

        for b in s.world.buildings:
            self.canvas.create_oval(self.x(b.x - b.radius),
                                    self.y(b.y - b.radius),
                                    self.x(b.x + b.radius),
                                    self.y(b.y + b.radius),
                                    outline="black")

        for t in s.world.trees:
            self.canvas.create_oval(self.x(t.x - t.radius),
                                    self.y(t.y - t.radius),
                                    self.x(t.x + t.radius),
                                    self.y(t.y + t.radius),
                                    outline="green")

        targets = []
        targets += s.world.wizards
        targets += s.world.minions

        for t in targets:
            if s.me.id == t.id:
                continue
            if t.faction == Faction.NEUTRAL or t.faction == s.me.faction:
                self.canvas.create_oval(self.x(t.x - t.radius),
                                        self.y(t.y - t.radius),
                                        self.x(t.x + t.radius),
                                        self.y(t.y + t.radius),
                                        outline="#43AA53")
                continue
            self.canvas.create_oval(self.x(t.x - t.radius),
                                    self.y(t.y - t.radius),
                                    self.x(t.x + t.radius),
                                    self.y(t.y + t.radius),
                                    outline="red")

        for i in s.obstacles:
            x, y = i
            self.canvas.create_rectangle(self.x(x * CELL),
                                         self.y(y * CELL),
                                         self.x((x + 1) * CELL) - 1,
                                         self.y((y + 1) * CELL) - 1,
                                         outline="gray")

        for i in s.moving_obstacles:
            x, y = i
            self.canvas.create_rectangle(self.x(x * CELL),
                                         self.y(y * CELL),
                                         self.x((x + 1) * CELL) - 1,
                                         self.y((y + 1) * CELL) - 1,
                                         outline="gray")
            # self.canvas.create_text(self.x(to_pixel(x)), self.y(to_pixel(y)),
            #                         text="{},{}".format(x, y),
            #                         fill="gray", font=("Helvectica", "8"))

        if isinstance(s.processed_route, collections.Iterable):
            for i in s.processed_route:
                x, y = i
                self.canvas.create_rectangle(self.x(x * CELL),
                                             self.y(y * CELL),
                                             self.x((x + 1) * CELL) - 1,
                                             self.y((y + 1) * CELL) - 1,
                                             outline="#C0A260")
        if isinstance(s.route, collections.Iterable):
            for i in s.route:
                x, y = i
                self.canvas.create_rectangle(self.x(x * CELL),
                                             self.y(y * CELL),
                                             self.x((x + 1) * CELL) - 1,
                                             self.y((y + 1) * CELL) - 1,
                                             outline="#AA7505")

        if s.current_point is not None and len(s.current_point) == 2:
            x, y = s.current_point

            self.canvas.create_line(self.x(x),
                                    self.y(y - s.me.radius / 2),
                                    self.x(x),
                                    self.y(y + s.me.radius / 2),
                                    fill='green')
            self.canvas.create_line(self.x(x - s.me.radius / 2),
                                    self.y(y),
                                    self.x(x + s.me.radius / 2),
                                    self.y(y),
                                    fill='green')

            self.canvas.create_text(10, 50,
                                    text="next point: {:.2f}, {:.2f}".format(x, y),
                                    fill="green", font=("Helvectica", "10"), anchor="w")
            self.canvas.create_text(10, 60,
                                    text="distance to next point: {:.2f}".format(s.me.get_distance_to(x, y)),
                                    fill="green", font=("Helvectica", "10"), anchor="w")
            self.canvas.create_text(10, 70,
                                    text="angle to next point: {:.2f}".format(
                                        s.me.get_angle_to(x, y) / pi * 180),
                                    fill="green", font=("Helvectica", "10"), anchor="w")

        if s.destination is not None and len(s.destination) == 2:
            x, y = s.destination
            rx, ry = to_pixel(to_cell(x)), to_pixel(to_cell(y))

            self.canvas.create_line(self.x(x - s.me.radius / 2),
                                    self.y(y - s.me.radius / 2),
                                    self.x(x + s.me.radius / 2),
                                    self.y(y + s.me.radius / 2),
                                    fill='blue')
            self.canvas.create_line(self.x(x - s.me.radius / 2),
                                    self.y(y + s.me.radius / 2),
                                    self.x(x + s.me.radius / 2),
                                    self.y(y - s.me.radius / 2),
                                    fill='blue')
            self.canvas.create_text(10, 30,
                                    text="destination: {:.2f}, {:.2f}".format(x, y),
                                    fill="blue", font=("Helvectica", "10"), anchor="w")
            self.canvas.create_text(10, 40,
                                    text="calc destination: {:.2f}, {:.2f}".format(rx, ry),
                                    fill="blue", font=("Helvectica", "10"), anchor="w")
        if s.current_target is not None:
            x, y = s.current_target.x, s.current_target.y
            r = s.current_target.radius

            self.canvas.create_line(self.x(x),
                                    self.y(y - r),
                                    self.x(x),
                                    self.y(y + r),
                                    fill='red')
            self.canvas.create_line(self.x(x - r),
                                    self.y(y),
                                    self.x(x + r),
                                    self.y(y),
                                    fill='red')


        self.window.update()
        # self.window.after(500, self.window.mainloop)
        # self.window.after(500, self.window.update)

    @staticmethod
    def get_my_color(s: MyStrategy):
        if s.move_to_bonus:
            return "blue"
        if s.move_to_checkpoint > 1:
            return "red"
        if s.move_to_checkpoint == 0:
            return "gray"
        if s.move_to_checkpoint < 0:
            return "yellow"
