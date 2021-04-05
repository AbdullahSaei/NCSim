from turtle import Turtle
import numpy as np
import random


class Node(Turtle):
    def __init__(self, node_id, **kwargs):
        super().__init__()
        self.node_id = node_id
        self.coverage = int(kwargs.get("n_coverage", 100))
        self.node_color = "dark orange"
                
        # simulation configuration
        self.buffer_size = int(kwargs.get("buf_size", 100))
        self.neighbors = []
        self.avaliable_messages = []
        self.rx_buffer = []
        self.ch_num = int(kwargs.get("channels", 2))
        self.ts_num = int(kwargs.get("timeslots", 2))
        self.sending_channel = (0, 0)
        self.clear_counters()

    def clear_counters(self):
        self.aod = 0
        self.rank = 0
        self.missing = 0
        self.tx_count = 0
        self.total_rx_count = 0
        self.success_rx_count = 0
        self.collision_count = 0
        self.ig_msgs_count = 0
        self.packet_loss_count = 0

    def place_node(self, position, only_fd=None):
        self.shape("circle")
        self.penup()
        self.goto((0, 0))
        self.color(self.node_color)
        self.pencolor("black")
        self.speed("fastest")
        self.clear()
        if only_fd:
            self.fd(position)
        else:
            self.goto(position)
        self.write(f"{self.node_id}  ", align="right",
                   font=("Calibri", 12, "bold"))
        # Print AoD
        self.write(f"  0%", align="left",
                   font=("sans", 12))

    def add_neighbor(self, new_neighbor):
        # To exclude duplications and adding self node to neighbors
        if (new_neighbor not in self.neighbors) and (new_neighbor != self):
            self.neighbors.append(new_neighbor)

    def get_neighbors(self):
        return self.neighbors

    def update_tx_counter(self):
        self.tx_count = self.tx_count + len(self.neighbors) 

    def sense_spectrum(self, packet_loss_percent, logger=None):
        # To simulate pathloss effect
        packet_loss_prob = packet_loss_percent / 100
        weights = [1 - packet_loss_prob, packet_loss_prob]
        # list of received messages after channel effect
        rx_msg = []
        # if there is available message
        if len(self.avaliable_messages) > 0:
            # Total received messages
            self.total_rx_count = self.total_rx_count + len(self.avaliable_messages)
            logger.info(
                "node {:2} found {:2} msgs".format(
                    self.node_id, len(self.avaliable_messages)
                )
            )

            # remove collisions
            all_srcs = [src for _, _, src in self.avaliable_messages]
            # survivor msgs from collisions
            unq_msgs = []
            for i, m, src in self.avaliable_messages:
                freq = all_srcs.count(src)
                if freq == 1:
                    unq_msgs.append((i, m, src))
                else:
                    # number of collided msgs
                    self.collision_count = self.collision_count + 1
                    logger.warning(
                        "node {:2} collision @ {} discard msg".format(
                            self.node_id, src
                        )
                    )

            # There are non-collide messages in the channel
            for i, channel_msg, ch_ts in unq_msgs:
                # node cannot transmit and receive at the same time
                if ch_ts[1] == self.sending_channel[1]:
                    # update counter
                    self.ig_msgs_count = self.ig_msgs_count + 1
                    # log information
                    logger.warning(
                        "node {:2} tx on {} discard rx msg on {}".format(
                            self.node_id, self.sending_channel, ch_ts
                        )
                    )
                    continue

                # Weighted random choice of success of fail
                success = np.random.choice([True, False], p=weights)
                if success:
                    rx_msg.append((i, channel_msg))
                else:
                    self.packet_loss_count = self.packet_loss_count + 1 
                    logger.warning("node {:2} packet loss".format(self.node_id))
                    continue

            # log status of messages
            if len(rx_msg) <= 0:
                logger.critical(
                    "node {:2} no msgs survived".format(self.node_id))
            else:
                logger.info(
                    "node {:2} {:2} msgs to buffer size {}".format(
                        self.node_id, len(rx_msg), self.buffer_size
                    )
                )
        else:
            logger.critical("node {:2} No available msgs".format(self.node_id))

        # not all received messages can fit into the buffer
        if len(rx_msg) > self.buffer_size:
            rx_msg = random.choice(rx_msg, size=(
                self.buffer_size), replace=False)
        
        # update counter
        self.success_rx_count = self.success_rx_count + len(rx_msg)
        # successful messages to the buffer
        self.rx_buffer = rx_msg

    def access_rx_buffer(self, i, new_packet, on_channel):
        self.avaliable_messages.append((i, new_packet, on_channel))

    def get_rx_packets(self):
        if len(self.rx_buffer) > 0:
            packs = []
            s = ""
            for src, pack in self.rx_buffer: 
                s += "{:2} ".format(src)
                packs.append(pack)
            
            # print("node {:2} received from ".format(self.node_id) + s)
            return packs
        else:
            print("node {:2} no buffer".format(self.node_id))
            return None
    
    def print_aod_percentage(self, r_num, aod, ranks):
        self.aod = aod
        self.rank, *_, self.missing, _ = ranks
        self.undo()
        self.write(f"  {aod:3.0f}%", align="left",
                   font=("sans", 12))
        self.new_round_cleanup()
        return self.get_statistics(r_num)

    def new_round_cleanup(self):
        # discard other available messages
        # for next round clean startup
        self.avaliable_messages = []
        # Clear buffer
        self.rx_buffer = []

    def get_statistics(self, r):
        return {
            "round": r, 
            "node": self.node_id, 
            "AoD_%": self.aod, 
            "rank": self.rank, 
            "missing": self.missing,           
            "tx_total": self.tx_count, 
            "rx_total": self.total_rx_count,
            "rx_success": self.success_rx_count, 
            "rx_collisions": self.collision_count, 
            "rx_ignored": self.ig_msgs_count,
            "rx_FSPL": self.packet_loss_count
        }
