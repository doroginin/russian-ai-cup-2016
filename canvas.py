from math import *
from tkinter import *


class Debug:
    def __init__(self, w, h):
        self.window = Tk()
        self.canvas = Canvas(self.window, width=w, height=h, bg="white")
        self.canvas.create_line(5, 5, 100, 100, width=2, arrow=LAST)
        self.canvas.create_line(5, 100, 100, 5, width=2, arrow=LAST)
        self.canvas.pack()

    def update(self, ):
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