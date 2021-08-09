from turtle import Turtle
import typing
import numpy as np


def choose_random_from_list(id_msg_list):
    arr = np.array(id_msg_list, dtype=object)
    output = arr[np.random.choice(arr.shape[0])]
    selected = (output[0], output[1])
    return selected


class Node(Turtle):
    def __init__(self, node_id, **kwargs):
        super().__init__()
        self.node_id = node_id
        self.coverage = int(kwargs.get("n_coverage", 100))
        self.node_color = "dark orange"

        # simulation configuration
        self.buffer_size = int(kwargs.get("buf_size", 100))
        self.neighbors: typing.List[Node] = []
        self.available_messages: typing.List[tuple] = []
        self.rx_buffer: list = []
        self.ch_num = int(kwargs.get("channels", 2))
        self.ts_num = int(kwargs.get("timeslots", 2))
        self.sending_channel = (0, 0)

        # set modes as configured
        self.duplex = kwargs.get("duplex", False)
        self.rx_multi = kwargs.get("rx_multi", True)

        # init counters
        self.last_aod = (0, 0, 0)
        self.tx_count = 0
        self.total_rx_count = 0
        self.success_rx_count = 0
        self.collision_count = 0
        self.rx_missed_count = 0
        self.ig_msgs_count = 0
        self.packet_loss_count = 0
        self.is_node_sleeping = False
        self.is_node_done = False

        # additive Overhead
        self.additive_overhead = [0, 0, 0]

    def clear_counters(self):
        self.last_aod = (0, 0, 0)
        self.tx_count = 0
        self.total_rx_count = 0
        self.success_rx_count = 0
        self.collision_count = 0
        self.rx_missed_count = 0
        self.ig_msgs_count = 0
        self.packet_loss_count = 0
        self.additive_overhead = [0, 0, 0]
        self.is_node_sleeping = False
        self.is_node_done = False
        self.node_reset()

    def node_reset(self):
        # reset node
        self.fillcolor(self.node_color)
        self.pencolor("black")
        self.shapesize(outline=2)
        self.clear()
        # node number
        self.write(f"{self.node_id}  ", align="right",
                   font=("Calibri", 12, "bold"))
        # Print AoD
        self.write("  0%", align="left",
                   font=("sans", 12, "normal"))

    def place_node(self, position, only_fd=None):
        self.shape("circle")
        self.penup()
        self.goto((0, 0))
        self.speed("fastest")
        if only_fd:
            self.fd(position)
        else:
            self.goto(position)
        self.node_reset()

    def add_neighbor(self, new_neighbor):
        # To exclude duplications and adding self node to neighbors
        if (new_neighbor not in self.neighbors) and (new_neighbor != self):
            self.neighbors.append(new_neighbor)

    def get_neighbors(self):
        return self.neighbors

    def update_tx_counter(self):
        self.tx_count = self.tx_count + len(self.neighbors)

    def sense_spectrum(self, packet_loss_percent, logger=None):
        # To simulate path loss effect
        packet_loss_prob = packet_loss_percent / 100
        weights = [1 - packet_loss_prob, packet_loss_prob]
        # list of received messages after channel effect
        rx_msg = []
        # if there is available message
        if len(self.available_messages) > 0:
            # Total received messages
            self.total_rx_count += len(self.available_messages)
            logger.info(
                "node {:2} found {:2} msgs".format(
                    self.node_id, len(self.available_messages)
                )
            )

            # remove collisions
            all_srcs = [src for _, _, src in self.available_messages]
            heu_srcs = [src for _, m, src in self.available_messages if m[-1]]

            # survivor msgs from collisions
            unq_msgs = []
            for i, m, src in self.available_messages:
                freq = all_srcs.count(src)
                h_freq = heu_srcs.count(src)

                if freq == 1:
                    unq_msgs.append((i, m, src))
                elif h_freq == 1:
                    # smpl, grdy, hrst = m
                    logger.warning(
                        "node {:2} heuristic survived collision @ {}".format(
                            self.node_id, src
                        )
                    )
                    unq_msgs.append((i, (None, None, m[-1]), src))
                else:
                    # number of collided msgs
                    self.collision_count = self.collision_count + 1
                    logger.warning(
                        "node {:2} collision @ {} discard msg".format(
                            self.node_id, src
                        )
                    )

            # filter ig messages due to: tx_mode and packet loss
            # survivors
            multi_rx_msg: typing.List[tuple] = []
            for i, channel_msg, ch_ts in unq_msgs:
                # node cannot transmit and receive at the same time
                if not self.duplex and ch_ts[1] == self.sending_channel[1]:
                    # update counter
                    self.ig_msgs_count += 1
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
                    multi_rx_msg.append((i, channel_msg, ch_ts))
                else:
                    self.packet_loss_count = self.packet_loss_count + 1
                    logger.warning(
                        "node {:2} packet loss".format(self.node_id))

            # filter msgs received at same time
            if not self.rx_multi and len(multi_rx_msg) > 1:
                # also remove collided ones
                unq_srcs = [src for _, _, src in multi_rx_msg]
                timeslots = set(map(lambda x: x[1], unq_srcs))

                # node cannot receive on multi-channels at the same time
                grouped_msgs = [[m for m in multi_rx_msg if m[2][1] == t]
                                for t in timeslots]

                # number of missed messages at same time
                for gmsg in grouped_msgs:
                    if len(gmsg) > 1:
                        msgs_s_nonzeros = [
                            (i, m) for i, m, ch in gmsg if m[0] and not m[-1]]
                        msgs_h_nonzeros = [
                            (i, m) for i, m, ch in gmsg if m[-1] and not m[0]]
                        skipped_msgs = len(gmsg) - 1

                        selected = choose_random_from_list(gmsg)

                        # heuristic place is empty
                        if msgs_h_nonzeros and not selected[1][-1]:
                            rx_msg.append(selected)
                            selected = choose_random_from_list(
                                msgs_h_nonzeros)
                            skipped_msgs -= 1
                        # simple place is empty
                        elif msgs_s_nonzeros and not selected[1][0]:
                            rx_msg.append(selected)
                            selected = choose_random_from_list(
                                msgs_s_nonzeros)
                            skipped_msgs -= 1

                        rx_msg.append(selected)
                        logger.warning("node {:2} multi rx msgs {} discard msg".format(
                            self.node_id, skipped_msgs))
                        self.rx_missed_count += skipped_msgs
                    else:
                        rx_msg.append((gmsg[0][0], gmsg[0][1]))
            # either only one msg or full-duplex
            else:
                for i, m, _ in multi_rx_msg:
                    rx_msg.append((i, m))

            # log status of messages
            if len(rx_msg) == 0:
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
            arr = np.array(rx_msg, dtype=object)
            selected = arr[np.random.choice(
                arr.shape[0], size=self.buffer_size, replace=False)]
            rx_msg = selected.tolist()

        # update counter
        self.success_rx_count += len(rx_msg)
        # successful messages to the buffer
        self.rx_buffer = rx_msg

    def access_rx_buffer(self, i, new_packet, on_channel):
        self.available_messages.append((i, new_packet, on_channel))

    def add_to_overhead(self, vals):
        self.additive_overhead = [cur + neu for cur,
                                  neu in zip(self.additive_overhead, vals)]

    def get_additive_oh(self):
        return self.additive_overhead

    def get_rx_packets(self):
        if len(self.rx_buffer) > 0:
            # packs = []
            s = ""
            for src, _ in self.rx_buffer:
                s += "{:2} ".format(src)
                # packs.append(pack)

            # print("node {:2} received from ".format(self.node_id) + s)
            return self.rx_buffer

        print("node {:2} no buffer".format(self.node_id))
        return None

    def set_sending_channel(self, freq, timeslot):
        self.sending_channel = (freq, timeslot)

    def node_sleep(self):
        if not self.is_node_sleeping:
            self.undo()
            self.is_node_sleeping = True
            self.fillcolor("gray")
            msg = f"  {self.last_aod[0]:3.0f}%"
            self.write(msg, align="left",
                       font=("sans", 12, "normal"))

    def print_aod_percentage(self, r_num, aods, ranks):
        if self.last_aod != aods:
            self.last_aod = aods
            self.undo()
            if self.last_aod[0] == 100:
                self.is_node_done = True
                self.pencolor("green")
            self.write(f"  {aods[0]:3.0f}%", align="left",
                       font=("sans", 12, "normal"))

        self.new_round_cleanup()
        return self.get_statistics(r_num, aods, ranks)

    def new_round_cleanup(self):
        # discard other available messages
        # for next round clean startup
        self.available_messages = []
        # Clear buffer
        self.rx_buffer = []

    def get_statistics(self, r=0, aod=(0, 0, 0), rank=(0, 0, 0)):
        return {
            "round": r,
            "node": self.node_id,
            "S_AoD_%": aod[0],
            "H_AoD_%": aod[1],
            "G_AoD_%": aod[2],
            "S_rank": rank[0],
            "G_rank": rank[1],
            "H_rank": rank[2],
            "tx_total": self.tx_count,
            "rx_total": self.total_rx_count,
            "rx_success": self.success_rx_count,
            "rx_collisions": self.collision_count,
            "rx_ignored": self.ig_msgs_count,
            "rx_missed": self.rx_missed_count
        }
