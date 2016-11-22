from tkinter import *
from model.Wizard import Wizard
from model.World import World

class Debug:
    scale = 1
    calc_cell_size = 1

    def __init__(self, w, h, scale, calc_cell_size):
        self.scale = scale
        self.calc_cell_size = calc_cell_size
        self.window = Tk()
        self.canvas = Canvas(self.window, width=w * self.scale, height=h * self.scale, bg="white")
        self.canvas.pack()

    def clear(self):
        self.canvas.delete("all")

    def draw(self, wizard: Wizard, world: World, route, obstacles):
        self.clear()

        self.canvas.create_oval((wizard.x - wizard.radius) * self.scale,
                                (wizard.y - wizard.radius) * self.scale,
                                (wizard.x + wizard.radius) * self.scale,
                                (wizard.y + wizard.radius) * self.scale,
                                outline="blue", fill="blue")

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