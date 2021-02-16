from turtle import Turtle
import random


class Node(Turtle):

    def __init__(self, n_coverage, buf_size=1, place=(0, 0)):
        super().__init__()
        self.coverage = n_coverage
        self.node_rgb = (random.random(), random.random(), random.random())
        self.home = place
        self.place_node(place)
        self.helper = Turtle()
        self.setup_helper()
        self.buffer_size = buf_size
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
        if (new_neighbor not in self.neighbors) and (new_neighbor != self):
            self.neighbors.append(new_neighbor)

    def access_rx_buffer(self, new_packet):
        # Set Packet-loss Coefficient Randomly, from 0 up to configured value

        if len(self.rx_buffer) > self.buffer_size:
            # Set the rx_Node Buffer with the sent packet
            self.rx_buffer.append(new_packet)

    def rx_packet(self):
        # check if data in buffer
        if len(self.rx_buffer) > 0:
            # decode or recode
            for data in self.rx_buffer:
                print("decode or recode {}".format(data))
            # Clear buffer
            self.rx_buffer = []

    def tx_packet(self, rx_node, tx_message):
        # Decode Message
        tx_packet = tx_message
        # Send Packet, to current rx_node
        rx_node.access_rx_buffer(tx_packet)

    def broadcast_message(self, tx_message):
        for node in self.neighbors:
            self.tx_packet(node, tx_message)
