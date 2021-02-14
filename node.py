from turtle import Turtle
import random


class Node(Turtle):

    def __init__(self, n_coverage, place=(0, 0)):
        super().__init__()
        self.coverage = n_coverage
        self.node_rgb = (random.random(), random.random(), random.random())
        self.home = place
        self.place_node(place)
        self.helper = Turtle()
        self.setup_helper()
        self.set_buffer_size(1)
        self.neighbors = []
        self.rx_buffer = []

    def setup_helper(self):
        self.helper.hideturtle()
        self.helper.pu()
        self.helper.goto(self.pos())
        self.helper.color(self.node_rgb)

    def place_node(self, position):
        self.shape("circle")
        self.penup()
        self.color(self.node_rgb)
        self.speed("fastest")
        self.goto(position)

    def broadcast(self):
        pass

    def show_coverage(self):
        self.helper.goto(self.xcor(), self.ycor() - self.coverage)
        self.helper.pendown()
        self.helper.circle(self.coverage)
        self.helper.penup()
        self.helper.goto(self.pos())

    def hide_coverage(self):
        self.helper.pendown()
        self.helper.clear()
        self.helper.penup()

    def add_neighbor(self, new_neighbor):
        # To exclude duplications and adding self node to neighbors
        if new_neighbor not in self.neighbors and new_neighbor != self:
            self.neighbors.append(new_neighbor)

    def set_buffer_size(self, val):
        self.buffer_size = val

    def access_rx_buffer(self, new_msg):
        if len(self.rx_buffer) > self.buffer_size:
            self.rx_buffer.append(new_msg)

    def handle_receive(self):
        # check if data in buffer
        if len(self.rx_buffer) > 0:
            # decode or recode
            for data in self.rx_buffer:
                print("decode or recode {}".format(data))
            # Clear buffer
            self.rx_buffer = []
