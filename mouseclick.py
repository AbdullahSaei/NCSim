import tkinter as tk
from turtle import Turtle


class MouseClick:
    def __init__(self, master, nodes):
        # store root
        self.root = master
        # create a popup menu
        self.aMenu = tk.Menu(master, tearoff=0)
        self.aMenu.add_command(label='Show coverage',
                               command=self.show_coverage)
        self.aMenu.add_command(label='Hide coverages',
                               command=self.hide_coverage)
        self.aMenu.add_command(label='Show neighbors', command=self.show_neighbors)
        self.aMenu.add_separator()
        self.aMenu.add_command(label='Exit Menu', command=self.ext_menu)

        self.bMenu = tk.Menu(master, tearoff=0)
        self.bMenu.add_command(label='Hide all coverages',
                               command=self.hide_all_coverages)
        self.bMenu.add_separator()
        self.bMenu.add_command(label='Exit Menu', command=self.ext_menu)

        self.nodes = nodes
        self.turs = [self.setup_turtles() for _ in range(len(self.nodes))]
        self.focus_node = None

    def setup_turtles(self):
        tur = Turtle()
        tur.pu()
        tur.ht()
        tur.color("saddle brown")
        return tur

    def show_coverage(self):
        # self.focus_node.show_coverage()
        i, n = self.focus_node
        tur = self.turs[i]
        tur.goto(n.xcor(), n.ycor() - n.coverage)
        tur.pendown()
        tur.circle(n.coverage)
        tur.penup()
        tur.goto(n.pos())

    def hide_coverage(self):
        # self.focus_node.hide_coverage()
        i, _ = self.focus_node
        tur = self.turs[i]
        tur.pendown()
        tur.clear()
        tur.penup()

    def hide_all_coverages(self):
        for tur in self.turs:
            tur.pendown()
            tur.clear()
            tur.penup()

    def show_neighbors(self):
        pass

    def ext_menu(self):
        pass

    def popup(self, x, y):
        # print("right click @ ({}, {})".format(x, y))
        x_root = self.root.winfo_pointerx()
        y_root = self.root.winfo_pointery()
        # print("(x, y) @ ({}, {})".format(x_root, y_root))
        if self.get_node((x, y)):
            self.aMenu.post(x_root, y_root)
        else:
            self.bMenu.post(x_root, y_root)

    def get_node(self, pos):
        dis = [n.distance(pos) for n in self.nodes]
        nearest_node = self.nodes[dis.index(min(dis))]
        self.focus_node = (dis.index(min(dis)), nearest_node) if min(
            dis) < 15 else None
        return self.focus_node

    def left_click(self, x, y):
        print("click @ ({}, {})".format(x, y))
