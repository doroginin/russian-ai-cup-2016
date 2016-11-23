from tkinter import *
from model.Wizard import Wizard
from model.World import World
from model.Move import Move
from math import *


class Debug:
    scale = 1
    calc_cell_size = 1

    def __init__(self, w, h, scale, calc_cell_size):
        self.scale = scale
        self.calc_cell_size = calc_cell_size
        self.window = Tk()
        self.canvas = Canvas(self.window, width=w * self.scale, height=h * self.scale, bg="white")
        self.canvas.pack()

    def draw(self, wizard: Wizard, world: World, move: Move, route, obstacles, destination):
        self.canvas.delete("all")

        self.canvas.create_text(self.canvas.winfo_width() / 2, 10, text=str(hypot(wizard.speed_x, wizard.speed_y)), fill="red", font=("Helvectica", "10"))

        self.canvas.create_oval((wizard.x - wizard.radius) * self.scale,
                                (wizard.y - wizard.radius) * self.scale,
                                (wizard.x + wizard.radius) * self.scale,
                                (wizard.y + wizard.radius) * self.scale,
                                outline="blue")

        self.canvas.create_line(wizard.x * self.scale, wizard.y * self.scale,
                                (wizard.x + wizard.vision_range * cos(wizard.angle)) * self.scale,
                                (wizard.y + wizard.vision_range * sin(wizard.angle)) * self.scale,
                                fill="blue")

        self.canvas.create_line(wizard.x * self.scale, wizard.y * self.scale,
                                (wizard.x + move.speed * cos(wizard.angle)) * self.scale,
                                (wizard.y + move.speed * sin(wizard.angle)) * self.scale,
                                fill="red", width=2)

        for b in world.buildings:
            self.canvas.create_oval((b.x - b.radius) * self.scale,
                                    (b.y - b.radius) * self.scale,
                                    (b.x + b.radius) * self.scale,
                                    (b.y + b.radius) * self.scale,
                                    outline="black")

        for t in world.trees:
            self.canvas.create_oval((t.x - t.radius) * self.scale,
                                    (t.y - t.radius) * self.scale,
                                    (t.x + t.radius) * self.scale,
                                    (t.y + t.radius) * self.scale,
                                    outline="green")

        for i in route:
            x, y = i
            self.canvas.create_rectangle(x * self.calc_cell_size * self.scale,
                                         y * self.calc_cell_size * self.scale,
                                         (x + 1) * self.calc_cell_size * self.scale - 1,
                                         (y + 1) * self.calc_cell_size * self.scale - 1,
                                         outline="#FFEE15")

        for i in obstacles:
            x, y = i
            self.canvas.create_rectangle(x * self.calc_cell_size * self.scale,
                                         y * self.calc_cell_size * self.scale,
                                         (x + 1) * self.calc_cell_size * self.scale - 1,
                                         (y + 1) * self.calc_cell_size * self.scale - 1,
                                         outline="gray")

        if len(destination) == 2:
            x, y = destination
            self.canvas.create_line((x - self.calc_cell_size / 3) * self.scale,
                                    (y - self.calc_cell_size / 3) * self.scale,
                                    (x + self.calc_cell_size / 3) * self.scale,
                                    (y + self.calc_cell_size / 3) * self.scale,
                                    fill='red')
            self.canvas.create_line((x - self.calc_cell_size / 3) * self.scale,
                                    (y + self.calc_cell_size / 3) * self.scale,
                                    (x + self.calc_cell_size / 3) * self.scale,
                                    (y - self.calc_cell_size / 3) * self.scale,
                                    fill='red')

        self.window.update()


    #First_x = -500;

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

    #win.after(500, win.mainloop)
    # win.after(1000, win.update)
    #win.update()