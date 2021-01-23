from turtle import Screen
from node import Node
import time

screen = Screen()
screen.setup(width=600, height=600)
screen.bgcolor("black")
screen.title("Network Coding Simulator")
screen.tracer(0)

food = Node()

sim_is_on = True
while sim_is_on:
    screen.update()
    time.sleep(0.1)


screen.exitonclick()
