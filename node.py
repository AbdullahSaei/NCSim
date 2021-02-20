from turtle import Turtle
import numpy as np


class Node(Turtle):

    def __init__(self, node_id, n_coverage, buf_size=1, place=(0, 0)):
        super().__init__()
        self.node_id = node_id
        self.coverage = n_coverage
        self.node_rgb = (np.random.rand(),
                         np.random.rand(),
                         np.random.rand())
        self.home = place
        self.place_node(place)
        self.helper = Turtle()
        self.setup_helper()
        self.buffer_size = buf_size
        self.neighbors = []
        self.avaliable_messages = []
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

    def sense_spectrum(self, packet_loss_percent, logger=None):
        # To simulate pathloss effect
        packet_loss_prob = packet_loss_percent/100
        weights = [1-packet_loss_prob, packet_loss_prob]
        # list of received messages after channel effect
        rx_msg = []
        if len(self.avaliable_messages) > 0:

            # There are messages in the channel
            for channel_msg in self.avaliable_messages:
                # Weighted random choice of success of fail
                success = np.random.choice([True, False], p=weights)
                if success:
                    rx_msg.append(channel_msg)
                else:
                    continue

        # discard other available messages
        self.avaliable_messages = []
        # not all received messages can fit into the buffer
        if len(rx_msg) > self.buffer_size:
            rx_msg = np.random.choice(rx_msg, size=(
                self.buffer_size), replace=False)
        # successful messages to the buffer
        self.rx_buffer = rx_msg

    def access_rx_buffer(self, new_packet):
        self.avaliable_messages.append(new_packet)

    def rx_packet(self, logger=None):
        # check if data in buffer
        log_msg = "Node {},rx,".format(self.node_id)
        if len(self.rx_buffer) > 0:
            log_msg += "msg "
            # decode or recode
            for data in self.rx_buffer:
                log_msg += "{} ".format(data)
            # Clear buffer
            self.rx_buffer = []
            logger.info(log_msg)
        else:
            log_msg +="no buffered packets"
            logger.warning(log_msg)

    def tx_packet(self, rx_node, tx_message):
        # Decode Message
        tx_packet = "IAM{}X".format(self.node_id) + tx_message
        # Send Packet, to current rx_node
        rx_node.access_rx_buffer(tx_packet)

    def broadcast_message(self, tx_message, logger=None):
        logger.info("Node {},tx,msg {},broadcast_to {}".format(
            self.node_id, tx_message, len(self.neighbors)))
        for node in self.neighbors:
            self.tx_packet(node, tx_message)
