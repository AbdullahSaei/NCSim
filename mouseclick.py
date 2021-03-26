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
        self.aMenu.add_command(label='Show neighbours',
                               command=self.show_neighbors)
        self.aMenu.add_command(label='Show reachables',
                               command=self.show_tx_reachables)
        self.aMenu.add_separator()
        self.aMenu.add_command(label='Hide coverages',
                               command=self.hide_coverage)
        self.aMenu.add_command(label='Hide neighbors',
                               command=self.hide_neighbors)

        # reduced menu created for empty clicks
        self.bMenu = tk.Menu(master, tearoff=0)
        self.bMenu.add_command(label='Show all neighbours',
                               command=self.show_all_neighbors)
        self.bMenu.add_separator()
        self.bMenu.add_command(label='Clear all',
                               command=self.hide_all_coverages)

        self.nodes = nodes
        self.turs = [self.setup_turtles() for _ in range(len(self.nodes))]
        self.focus_node = None

    def setup_turtles(self):
        tur = Turtle()
        tur.pu()
        tur.ht()
        tur.color("saddle brown")
        tur.pensize(2)
        return tur

    def show_coverage(self):
        # self.focus_node.show_coverage()
        i, n = self.focus_node
        tur = self.turs[i]
        tur.goto(n.xcor(), n.ycor() - n.coverage)
        tur.setheading(0)
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
        _, tx_node = self.focus_node
        rx_nodes = tx_node.get_neighbors()
        # draw arrow for all neighbors
        for rx_node in rx_nodes:
            snd_pckt = self.turs[rx_node.node_id]
            snd_pckt.setposition(tx_node.pos())
            snd_pckt.setheading(snd_pckt.towards(rx_node.pos()))
            snd_pckt.fd(11)
            snd_pckt.pendown()
            snd_pckt.fd(rx_node.distance(snd_pckt) - 11)

            # Drawing arrow head
            snd_pckt.left(45)
            snd_pckt.backward(10)
            snd_pckt.forward(10)
            snd_pckt.right(90)
            snd_pckt.backward(10)
            snd_pckt.penup()

    def hide_neighbors(self):
        _, tx_node = self.focus_node
        rx_nodes = tx_node.get_neighbors()
        # draw arrow for all neighbors
        for rx_node in rx_nodes:
            self.turs[rx_node.node_id].clear()

    def show_all_neighbors(self):
        for n in self.nodes:
            self.focus_node = (n.node_id, n)
            self.show_neighbors()

    def show_tx_reachables(self):
        reachables = []
        for node in self.nodes:
            if self.focus_node[0] in [n.node_id for n in node.get_neighbors()]:
                reachables.append((node.node_id, node))

        i, node = self.focus_node
        for i_n, n in reachables:
            snd_pckt = self.turs[i_n]
            snd_pckt.setposition(n.pos())
            snd_pckt.setheading(snd_pckt.towards(node.pos()))
            snd_pckt.fd(11)
            snd_pckt.pendown()
            snd_pckt.fd(node.distance(snd_pckt) - 11)

            # Drawing arrow head
            snd_pckt.left(45)
            snd_pckt.backward(10)
            snd_pckt.forward(10)
            snd_pckt.right(90)
            snd_pckt.backward(10)
            snd_pckt.penup()

    def popup(self, x, y):
        # remove other menu lists
        self.aMenu.unpost()
        self.bMenu.unpost()

        # get curser tkk position
        x_root = self.root.winfo_pointerx()
        y_root = self.root.winfo_pointery()

        # if click on node
        if self.get_node((x, y)):
            self.aMenu.post(x_root, y_root)
        else:
            self.bMenu.post(x_root, y_root)

    def get_node(self, pos):
        dis = [n.distance(pos) for n in self.nodes]
        nearest_node = self.nodes[dis.index(min(dis))]
        self.focus_node = (dis.index(min(dis)), nearest_node) if (
            min(dis) < 15) else None
        return self.focus_node

    def left_click(self, x, y):
        self.aMenu.unpost()
        self.bMenu.unpost()
        x_root = self.root.winfo_pointerx()
        y_root = self.root.winfo_pointery()
        if self.get_node((x, y)):
            self.focus_node = self.get_node((x, y))
