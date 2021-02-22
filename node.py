from turtle import Turtle
import numpy as np


class Node(Turtle):

    def __init__(self, node_id, n_coverage, buf_size=1, place=(0, 0)):
        super().__init__()
        self.node_id = node_id
        self.coverage = n_coverage
        self.node_color = "dark orange"
        self.home = place
        self.place_node(place)
        self.buffer_size = buf_size
        self.neighbors = []
        self.avaliable_messages = []
        self.rx_buffer = []

    def place_node(self, position, only_fd=None):
        self.shape("circle")
        self.penup()
        self.goto((0,0))
        self.color(self.node_color)
        self.pencolor("black")
        self.speed("fastest")
        self.clear()
        if only_fd:
            self.fd(position)
        else:
            self.goto(position)
        self.write(f"{self.node_id}  ", align="Right", font=("Calibri", 12, "bold"))

    def add_neighbor(self, new_neighbor):
        # To exclude duplications and adding self node to neighbors
        if (new_neighbor not in self.neighbors) and (new_neighbor != self):
            self.neighbors.append(new_neighbor)

    def get_neighbors(self):
        return self.neighbors

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
        log_msg = "Node {:2},rx,".format(self.node_id)
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
        tx_packet = "IAM{:02}X".format(self.node_id) + tx_message
        # Send Packet, to current rx_node
        rx_node.access_rx_buffer(tx_packet)

    def broadcast_message(self, tx_message, logger=None):
        logger.info("Node {:2},tx,msg {},broadcast_to {}".format(
            self.node_id, tx_message, len(self.neighbors)))
        for node in self.neighbors:
            self.tx_packet(node, tx_message)
