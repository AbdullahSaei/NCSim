from turtle import Turtle
import random

class Node(Turtle):

    def __init__(self, node_range):
        super().__init__()
        self.shape("circle")
        self.penup()
        self.color("blue")
        self.speed("fastest")
        self.coverage = node_range
        self.refresh()

    def refresh(self):
        random_x = random.randint(-280, 280)
        random_y = random.randint(-280, 280)
        self.goto(random_x, random_y)

    def broadcast(self):
        pass



