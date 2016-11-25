from tkinter import *
from math import *
import collections
from inspect import getsource
from Point import *
import MyStrategy


class Debug:
    scale = 1

    def __init__(self, w, h, scale):
        self.scale = scale
        self.window = Tk()
        self.canvas = Canvas(self.window, width=w * self.scale, height=h * self.scale, bg="white")
        self.canvas.pack()

    def draw(self, s: MyStrategy):
        self.canvas.delete("all")

        for i, t in enumerate(s.brain.processed):
            self.canvas.create_text(self.canvas.winfo_width() - 10, 10 + i * 10,
                                    text=getsource(t).strip().replace("self.brain.add_thought(lambda: self.", "")[:-1]
                                    if t.__name__ == "<lambda>" else t.__name__,
                                    fill="gray", font=("Helvectica", "10"), anchor="e")

        if s.brain.thoughts is not None:
            for i, t in enumerate(s.brain.thoughts):
                self.canvas.create_text(self.canvas.winfo_width() - 10,
                                        10 + (len(s.brain.thoughts) - i - 1 + len(s.brain.processed)) * 10,
                                        text=getsource(t).strip().replace(
                                            "self.brain.add_thought(lambda: self.", "")[:-1]
                                                if t.__name__ == "<lambda>" else t.__name__,
                                        fill="green" if i == len(s.brain.thoughts) - 1 else "blue",
                                        font=("Helvectica", "10"), anchor="e")

        self.canvas.create_text(self.canvas.winfo_width() / 2, 10,
                                text="Me.speed: {:.2f}".format(hypot(s.Me.speed_x, s.Me.speed_y)),
                                fill="red", font=("Helvectica", "10"))
        self.canvas.create_text(self.canvas.winfo_width() / 2, 20,
                                text="Move.speed: {:.2f}".format(s.Move.speed),
                                fill="red", font=("Helvectica", "10"))
        self.canvas.create_text(self.canvas.winfo_width() / 2, 30,
                                text="Move.strafe_speed: {:.2f}".format(s.Move.strafe_speed),
                                fill="red", font=("Helvectica", "10"))
        self.canvas.create_text(self.canvas.winfo_width() / 2, 40,
                                text="Me.angle: {:.2f}".format(s.Me.angle / pi * 180),
                                fill="red", font=("Helvectica", "10"))
        self.canvas.create_text(self.canvas.winfo_width() / 2, 50,
                                text="Move.turn: {:.2f}".format(s.Move.turn / pi * 180),
                                fill="red", font=("Helvectica", "10"))

        self.canvas.create_text(10, 10,
                                text="Tick: {:d}".format(s.tick_counter),
                                fill="red", font=("Helvectica", "10"), anchor="w")
        self.canvas.create_text(10, 20,
                                text="Position: {:.2f}, {:.2f}".format(s.Me.x, s.Me.y),
                                fill="red", font=("Helvectica", "10"), anchor="w")

        self.canvas.create_oval((s.Me.x - s.Me.radius) * self.scale,
                                (s.Me.y - s.Me.radius) * self.scale,
                                (s.Me.x + s.Me.radius) * self.scale,
                                (s.Me.y + s.Me.radius) * self.scale,
                                outline="blue")

        self.canvas.create_line(s.Me.x * self.scale, s.Me.y * self.scale,
                                (s.Me.x + s.Me.vision_range * cos(s.Me.angle)) * self.scale,
                                (s.Me.y + s.Me.vision_range * sin(s.Me.angle)) * self.scale,
                                fill="blue")

        self.canvas.create_line(s.Me.x * self.scale, s.Me.y * self.scale,
                                (s.Me.x + s.Move.speed * cos(s.Me.angle)) * self.scale,
                                (s.Me.y + s.Move.speed * sin(s.Me.angle)) * self.scale,
                                fill="red", width=2)

        for b in s.World.buildings:
            self.canvas.create_oval((b.x - b.radius) * self.scale,
                                    (b.y - b.radius) * self.scale,
                                    (b.x + b.radius) * self.scale,
                                    (b.y + b.radius) * self.scale,
                                    outline="black")

        for t in s.World.trees:
            self.canvas.create_oval((t.x - t.radius) * self.scale,
                                    (t.y - t.radius) * self.scale,
                                    (t.x + t.radius) * self.scale,
                                    (t.y + t.radius) * self.scale,
                                    outline="green")

        if isinstance(s.route, collections.Iterable):
            for i in s.route:
                x, y = i
                self.canvas.create_rectangle(x * CELL * self.scale,
                                             y * CELL * self.scale,
                                             (x + 1) * CELL * self.scale - 1,
                                             (y + 1) * CELL * self.scale - 1,
                                             outline="#FFEE15")

        for i in s.obstacles:
            x, y = i
            self.canvas.create_rectangle(x * CELL * self.scale,
                                         y * CELL * self.scale,
                                         (x + 1) * CELL * self.scale - 1,
                                         (y + 1) * CELL * self.scale - 1,
                                         outline="gray")

        for i in s.moving_obstacles:
            x, y = i
            self.canvas.create_rectangle(x * CELL * self.scale,
                                         y * CELL * self.scale,
                                         (x + 1) * CELL * self.scale - 1,
                                         (y + 1) * CELL * self.scale - 1,
                                         outline="#AA7505")

        if s.destination is not None and len(s.destination) == 2:
            x, y = s.destination
            rx, ry = to_real(to_calc(x)), to_real(to_calc(y))

            self.canvas.create_line((x - CELL / 3) * self.scale,
                                    (y - CELL / 3) * self.scale,
                                    (x + CELL / 3) * self.scale,
                                    (y + CELL / 3) * self.scale,
                                    fill='red')
            self.canvas.create_line((x - CELL / 3) * self.scale,
                                    (y + CELL / 3) * self.scale,
                                    (x + CELL / 3) * self.scale,
                                    (y - CELL / 3) * self.scale,
                                    fill='red')
            self.canvas.create_text(10, 30,
                                    text="destination: {:.2f}, {:.2f}".format(x, y),
                                    fill="red", font=("Helvectica", "10"), anchor="w")
            self.canvas.create_text(10, 40,
                                    text="calc destination: {:.2f}, {:.2f}".format(rx, ry),
                                    fill="red", font=("Helvectica", "10"), anchor="w")
            if s.first_cell is not None and len(s.first_cell) == 2:
                nx, ny = s.first_cell
                nx, ny = to_real(nx), to_real(ny)

                self.canvas.create_text(10, 50,
                                        text="next point: {:.2f}, {:.2f}".format(nx, ny),
                                        fill="red", font=("Helvectica", "10"), anchor="w")
                self.canvas.create_text(10, 60,
                                        text="distance to next point: {:.2f}".format(s.Me.get_distance_to(nx, ny)),
                                        fill="red", font=("Helvectica", "10"), anchor="w")
                self.canvas.create_text(10, 70,
                                        text="angle to next point: {:.2f}".format(
                                            s.Me.get_angle_to(nx, ny) / pi * 180),
                                        fill="red", font=("Helvectica", "10"), anchor="w")

        self.window.update()


            # First_x = -500;

            # for i in range(16000):
            #     if (i % 800 == 0):
            #         k = First_x + (1 / 16) * i
            #         canv.create_line(k + 500, -3 + 500, k + 500, 3 + 500, width=0.5, fill='black')
            #         canv.create_text(k + 515, -10 + 500, text=str(k), fill="purple", font=("Helvectica", "10"))
            #         if (k != 0):
            #             canv.create_line(-3 + 500, k + 500, 3 + 500, k + 500, width=0.5, fill='black')
            #             canv.create_text(20 + 500, k + 500, text=str(k), fill="purple", font=("Helvectica", "10"))
            #     try:
            #         x = First_x + (1 / 16) * i
            #         new_f = f.replace('x', str(x))
            #         y = -eval(new_f) + 500
            #         x += 500
            #         canv.create_oval(x, y, x + 1, y + 1, fill='black')
            #     except:
            #         pass

            # win.after(500, win.mainloop)
            # win.after(1000, win.update)
            # win.update()
