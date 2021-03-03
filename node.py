from turtle import Turtle
import numpy as np
import kodo

class Node(Turtle):

    def __init__(self, node_id, **kwargs):
        super().__init__()
        self.node_id = node_id
        self.coverage = int(kwargs.get("n_coverage",100))
        self.node_color = "dark orange"
        self.buffer_size = int(kwargs.get("buf_size",100))
        self.neighbors = []
        self.avaliable_messages = []
        self.rx_buffer = []

        # KODO CODE
        def fifi(i):
            switcher={
                    "binary16":kodo.field.binary16,
                    "binary8":kodo.field.binary8,
                    "binary4":kodo.field.binary4,
                    "binary":kodo.field.binary
                }
            return switcher.get(i,kodo.field.binary)
        # Choose the finite field, the number of symbols (i.e. generation size)
        # and the symbol size in bytes
        field = fifi(kwargs.get("fifi"))
        symbols = int(kwargs.get("num_of_nodes",5))
        symbol_size = int(kwargs.get("packet_size",100))

        # Create an encoder and a decoder
        self.encoder = kodo.RLNCEncoder(field, symbols, symbol_size)
        self.decoder = kodo.RLNCDecoder(field, symbols, symbol_size)

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
            # Define the data_out bytearray where the symbols should be decoded
            # This bytearray must not go out of scope while the encoder exists!
            data_out = bytearray(self.decoder.block_size())
            self.decoder.set_symbols_storage(data_out)
            
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
        # Generate some random data to encode. We create a bytearray of the same
        # size as the encoder's block size and assign it to the encoder.
        # This bytearray must not go out of scope while the encoder exists!
        data_in = bytearray(tx_packet, encoding="utf-8")
        self.encoder.set_symbols_storage(data_in)
        # Send Packet, to current rx_node
        rx_node.access_rx_buffer(tx_packet)

    def broadcast_message(self, tx_message, logger=None):
        logger.info("Node {:2},tx,msg {},broadcast_to {}".format(
            self.node_id, tx_message, len(self.neighbors)))
        for node in self.neighbors:
            self.tx_packet(node, tx_message)
