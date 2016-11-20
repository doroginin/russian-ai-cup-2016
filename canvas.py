from tkinter import *


class Debug:
    CELL = 3

    def __init__(self, w, h):
        self.window = Tk()
        self.canvas = Canvas(self.window, width=w * self.CELL, height=h * self.CELL, bg="white")
        self.canvas.pack()

    def clear(self):
        self.canvas.delete("all")

    def draw_wizard(self, wizard):
        x, y = wizard
        # draw wizard
        self.canvas.create_rectangle(x * self.CELL, y * self.CELL,
                                     (x + 1) * self.CELL - 1, (y + 1) * self.CELL - 1,
                                     outline="blue", fill="blue")
        self.window.update()

    def draw_path(self, path):
        # draw path
        for i in path:
            x, y = i
            self.canvas.create_rectangle(x * self.CELL, y * self.CELL,
                                         (x + 1) * self.CELL - 1, (y + 1) * self.CELL - 1,
                                         outline="green", fill="green")
        self.window.update()

    def draw_obstacles(self, obstacles):
        # draw obstacles
        for i in obstacles:
            x, y = i
            self.canvas.create_rectangle(x * self.CELL, y * self.CELL,
                                         (x + 1) * self.CELL - 1, (y + 1) * self.CELL - 1,
                                         outline="black", fill="black")
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