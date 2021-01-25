from turtle import Turtle
import random

class Node(Turtle):

    def __init__(self, node_range, place=(0,0)):
        super().__init__()
        self.coverage = node_range
        self.node_rgb = (random.random(),random.random(),random.random())
        self.home = place
        self.place_node(place)
        self.helper = Turtle()
        self.setup_helper()
        self.packets = []

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
        self.helper.goto(self.xcor(),self.ycor()-self.coverage)
        self.helper.pendown()
        self.helper.circle(self.coverage)
        self.helper.penup()
        self.helper.goto(self.pos())

    def hide_coverage(self):
        self.helper.pendown()
        self.helper.clear()
        self.helper.penup()

    def discover_neighbours(self):
        pass








