from turtle import Turtle
import random

class Node(Turtle):

    def __init__(self, node_range, place=(0,0)):
        super().__init__()
        self.coverage = node_range
        self.place_node(place)
        self.helper = self.clone()
        self.helper.hideturtle()
        self.packets = []

    def place_node(self, position):
        self.shape("circle")
        self.penup()
        self.color("blue")
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
        self.helper.clear()







