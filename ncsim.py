from turtle import Turtle
import typing
from platform import system as os_type
from glob import glob
import os
import time
import logging
import re
import numpy as np
import pandas as pd
import cde
from node import Node
from controller import MouseClick, Controller
import ncsim_visualizer as ncsv

CFG_OS = os_type()
# Get values from ncs visualizer

# Fetch Simulation Dictionary
CFG_SIM = ncsv.CFG_SIM
# Fetch Parameters Dictionary
CFG_PARAM = ncsv.CFG_PARAM

# Fetch RUN related Configurations, or set default values.
RUN_ALL = bool(CFG_SIM.get('auto_run_all', False))
AUTO_RUN_TO_FULL = bool(CFG_SIM.get('auto_full_aod', False))

# Fetch Nodes related Configurations, or set default values.
TOPOLOGY_TYPE = ncsv.TOPOLOGY_TYPE
NUM_OF_NODES = cde.NUM_OF_NODES
SEED_VALUE = cde.SEED_VALUE
MIN_DIST_NODES = int(CFG_PARAM.get('min_dist_between_nodes', 20))
NODE_COVERAGE = int(CFG_PARAM.get("nodes_coverage", '100'))
NODE_BUFFER_SIZE = int(CFG_PARAM.get('node_buffer_size', 1))

# Fetch simulation parameters
PACKET_LOSS = int(CFG_PARAM.get("packet_loss_percent", 0))
CHANNEL_NUM = int(CFG_PARAM.get("channels", 2))
TIMESLOT_NUM = int(CFG_PARAM.get("timeslots", 2))
TX_MODE = CFG_PARAM.get("tx_mode", "half_duplex")
RX_MODE = CFG_PARAM.get("rx_mode", "multi")

# Kodo configuration
CFG_KODO = {
    "n_coverage": NODE_COVERAGE,
    "buf_size": NODE_BUFFER_SIZE,
    "fifi": cde.FINITE_FIELD,
    "gen_size": cde.NUM_OF_NODES,
    "packet_size": cde.PACKET_SIZE,
    "channels": CHANNEL_NUM,
    "timeslots": TIMESLOT_NUM,
    "seed": cde.SEED_VALUE,
    "duplex": True if re.match("full", TX_MODE) else False,
    "rx_multi": True if re.match("multi", RX_MODE) else False
}

# Fetch Logger related Configurations, or set default values.
LOG_PATH = CFG_SIM.get('log_path', "")
EXP_NAME = CFG_SIM.get('name', "test")
EXP_ID = int(CFG_SIM.get('id', 0))

# Create two Loggers .log for traces and .csv for KPIs
# create loggers
trace = logging.getLogger('trace')
kpi = logging.getLogger('kpi')
kodo_log = logging.getLogger('kodo')

LOG_FILES_NAME = f"{LOG_PATH}/{TOPOLOGY_TYPE}_{NUM_OF_NODES}_{EXP_NAME}_{EXP_ID}"

# Start clean
for filename in glob(f"{LOG_FILES_NAME}*"):
    os.remove(filename)

# add a file handler
log_fh = logging.FileHandler(f'{LOG_FILES_NAME}.log', 'w+')
kpi_fh = logging.FileHandler(f'{LOG_FILES_NAME}.csv', 'w+')
kodo_fh = logging.FileHandler(f'{LOG_FILES_NAME}.txt', 'w+')
# create a formatter and set the formatter for the handler.
log_frmt = logging.Formatter('%(asctime)s:%(levelname)-10s: %(funcName)-16s: %(message)s',
                             datefmt="%Y-%m-%d %H.%M.%S")
kpi_frmt = logging.Formatter('%(asctime)s,%(msecs)-3d,%(funcName)-17s,%(message)s',
                             datefmt="%Y-%m-%d %H:%M:%S")
kodo_frmt = logging.Formatter('%(asctime)s\t%(funcName)-17s\t%(message)s',
                              datefmt="%Y-%m-%d %H:%M:%S")
log_fh.setFormatter(log_frmt)
kpi_fh.setFormatter(kpi_frmt)
kodo_fh.setFormatter(kodo_frmt)


def fmt_filter(record):
    record.levelname = '[%s]' % record.levelname
    return True


# add the Handler to the logger
trace.addHandler(log_fh)
trace.setLevel(logging.DEBUG)
trace.addFilter(fmt_filter)
kpi.addHandler(kpi_fh)
kpi.setLevel(logging.DEBUG)
kodo_log.addHandler(kodo_fh)
kodo_log.setLevel(logging.DEBUG)

# For Generations
GENERATIONS = int(CFG_PARAM.get("generations_num", '5'))
GEN_TIME = int(CFG_PARAM.get("generation_time_ms", '1000'))
ACT_TIME = int(CFG_PARAM.get("action_time_ms", '40'))
ROUNDS = int(GEN_TIME/ACT_TIME)
EXTRA_RNDS = 0


def get_configs():
    return {
        "num_nodes": NUM_OF_NODES,
        "num_rounds": ROUNDS,
        "seed_value": SEED_VALUE,
        "generation_time_ms": GEN_TIME,
        "action_time_ms": ACT_TIME,
        "topology": TOPOLOGY_TYPE,
        "packet_size_bytes": cde.PACKET_SIZE,
        "finite_field": cde.FINITE_FIELD,
        "SINR_loss_%": PACKET_LOSS,
        "channels": CHANNEL_NUM,
        "timeslots": TIMESLOT_NUM,
        "tx_mode": TX_MODE,
        "rx_mode": RX_MODE
    }


class NCSim:
    def __init__(self):
        # Call to NCSimVisualizer create Screen
        self.screen = ncsv.NCSimVisualizer(CFG_OS)
        # Log operating system
        trace.info(f"running on {CFG_OS.lower()}")
        # Create place holder of the data per gen
        self.data_in = ""
        # Create List of Nodes Variable
        self.nodes: typing.List[Node] = []
        # Call Nodes Init Method
        self.create_nodes()
        # store AoDs
        self.full_AoD: typing.List[float] = []

        # create right click listener
        self.mclick = MouseClick(self.screen.root, self.nodes)
        # attach popup to window
        ncsv.set_click_listener(
            fun=self.mclick.left_click, btn=1, add=True)
        # attach left click
        ncsv.set_click_listener(fun=self.mclick.popup, btn=3, add=True)
        summ_header = [*self.nodes[0].get_statistics()]
        # Init controller window
        self.ctrl = Controller(
            self.screen.root, summ_header, auto_run=RUN_ALL,
            auto_full=AUTO_RUN_TO_FULL, **get_configs())

        self.statistics_df = pd.DataFrame(columns=['Generation', *summ_header])
        self.at_done_df = pd.DataFrame(
            columns=['Generation', 'Round', 'Node', 'Algorithm', 'added_s_overhead', 'added_g_overhead', 'added_h_overhead'])
        self.logged = [[False, False, False] for _ in range(NUM_OF_NODES)]

        self.current_gen = 0
        print("init done")

    def create_nodes(self):
        # LOGGING:
        self.screen.visual_output_msg(
            f"Set {NUM_OF_NODES} nodes to {TOPOLOGY_TYPE} topology")
        trace.info(f"creating {NUM_OF_NODES} node(s)")

        # Loop over #no. of nodes to create its objects
        for index in range(NUM_OF_NODES):
            # Append the created node to list of nodes
            self.nodes.append(Node(index, **CFG_KODO))
        # LOGGING:
        trace.info(f"setting topology to {TOPOLOGY_TYPE}")
        # Adjust Nodes Co-ordinates according to topology
        self.draw_network(TOPOLOGY_TYPE)
        # Update Screen Changes
        self.screen.screen_refresh()

    def draw_network(self, topology):
        # for case insensitivity
        topology = topology.lower()
        draw_cursor = Turtle()                  # Create A Drawing Cursor
        draw_cursor.color("black")
        draw_cursor.ht()                        # Hide the Cursor
        draw_cursor.penup()                     # Hide Cursor pen movements

        # IF RING TOPOLOGY
        if topology == "ring":
            ring_radius = ncsv.SCREEN_HEIGHT/4                           # Set the Ring Radius
            # Adjust Cursor starting position
            draw_cursor.setposition(0, int(-ring_radius-50))
            node_spacing = 360/NUM_OF_NODES                         # Set Node Spacing
            # Loop over the Nodes and Set Positions
            for index in range(NUM_OF_NODES):
                # Move Cursor in circle shape by node spacing angle
                draw_cursor.circle(ring_radius, node_spacing)
                node_position = draw_cursor.position()              # fetch Cursor Position
                # Locate Node where Cursor Stops
                self.nodes[index].place_node(node_position)

        # IF CHAIN TOPOLOGY
        elif topology == "chain":
            # Set the Chain Length
            chain_length = ncsv.SCREEN_WIDTH
            # Adjust Cursor starting position
            draw_cursor.setposition(-(chain_length/2) + ncsv.SCREEN_MARGIN,
                                    -(chain_length/2) + ncsv.SCREEN_MARGIN)
            # To draw diagonally
            draw_cursor.left(45)
            # Loop over the Nodes and Set Positions
            for node in self.nodes:
                # Move Cursor forward by node spacing value
                draw_cursor.fd(chain_length/NUM_OF_NODES)
                node_position = draw_cursor.position()     # fetch Cursor Position
                # Locate Node where Cursor Stops
                node.place_node(node_position)

        # IF RANDOM TOPOLOGY
        elif topology == "random":
            # Constants
            LOW_VALUE = 0
            HIGH_VALUE = 1

            # divides the screen to 4 quarters
            def create_quarters(mutate=0.0):
                # for the linear equation
                a = 0.03 + mutate
                b = 0.55

                # Create linear equation for mapping num of nodes
                # 5   nodes -> 0.7
                # 100 nodes -> 3.5

                FACTOR = a * NUM_OF_NODES + b
                # Set the Quarter Size
                quarter_size = int(NODE_COVERAGE*FACTOR)
                # Set the Quarter Areas in list Variable, X and Y Lower and Higher values
                return [{"X_RANGE": [-quarter_size, 0],
                         "Y_RANGE": [0, quarter_size]},      # Q1
                        {"X_RANGE": [0, quarter_size],
                         "Y_RANGE": [0, quarter_size]},      # Q2
                        {"X_RANGE": [-quarter_size, 0],
                         "Y_RANGE": [-quarter_size, 0]},     # Q3
                        {"X_RANGE": [0, quarter_size],
                         "Y_RANGE": [-quarter_size, 0]}]     # Q4

            # distributes the nodes inside the 4 quarters
            def distribute_nodes(quarters_areas):
                # Loop over the Nodes and Set Positions
                for ix, nx in enumerate(self.nodes):
                    _success = False
                    counter = 0
                    while not _success:
                        _success = True
                        counter = counter + 1
                        # Randomly Set the Node X Position, in specific Quarter
                        x_position = np.random.randint(
                            quarters_areas[ix % 4]["X_RANGE"][LOW_VALUE],
                            quarters_areas[ix % 4]["X_RANGE"][HIGH_VALUE])
                        # Randomly Set the Node Y Position, in specific Quarter
                        y_position = np.random.randint(
                            quarters_areas[ix % 4]["Y_RANGE"][LOW_VALUE],
                            quarters_areas[ix % 4]["Y_RANGE"][HIGH_VALUE])
                        # Locate Node where Cursor Stops
                        nx.place_node((x_position, y_position))
                        # Check if there is overlapping nodes
                        for _neighbor in self.nodes:
                            # Check until reaching node index
                            if _neighbor == nx:
                                break
                            if nx.distance(_neighbor) < MIN_DIST_NODES:
                                trace.warning(
                                    f"node {nx.node_id} was overlapping node {_neighbor.node_id}")
                                _success = False
                        if counter == 1000:
                            trace.warning(
                                "failed to create topology")
                            return False
                return True

            # Try to place the nodes correctly
            done = False
            # for mutations if distribution failed
            c = 0.0
            # try until successful
            while not done:
                Q_s = create_quarters(c)
                c += 0.01
                done = distribute_nodes(Q_s)

        # IF GRID TOPOLOGY
        elif topology == "grid":
            # Get nearest root + 1
            def nearest_square(limit):
                answer = 0
                while (answer+1)**2 < limit:
                    answer += 1
                return answer+1

            # Set the Chain Length
            chain_v_length = ncsv.SCREEN_HEIGHT - ncsv.HEAD_MARGIN - ncsv.MESSAGE_MARGIN
            chain_h_length = ncsv.SCREEN_WIDTH - ncsv.SCREEN_MARGIN * 2
            chains = np.array_split(self.nodes, nearest_square(NUM_OF_NODES))
            for index, chain in enumerate(chains):
                v_move = (chain_v_length/len(chains)) * index
                # Adjust Cursor starting position
                draw_cursor.setposition(-(chain_h_length/2 + ncsv.SCREEN_MARGIN),
                                        (chain_v_length/2) - v_move - ncsv.MESSAGE_MARGIN)
                # Loop over the Nodes and Set Positions
                for node in chain:
                    # Move Cursor forward by node spacing value
                    draw_cursor.fd(chain_h_length/len(chain))
                    node_position = draw_cursor.position()     # fetch Cursor Position
                    # Locate Node where Cursor Stops
                    node.place_node(node_position)

        # IF STAR TOPOLOGY
        elif topology == "star":
            # Node 0 is a central node reaching all other nodes
            self.nodes[0].place_node((0, 0))
            self.nodes[0].coverage = MAX_COVERAGE = ncsv.SCREEN_HEIGHT / \
                2 - ncsv.SCREEN_MARGIN  # Set the Ring Radius

            # Adjust Cursor starting position
            draw_cursor.setposition(0, int(-MAX_COVERAGE-50))
            node_spacing = 360/NUM_OF_NODES                         # Set Node Spacing
            # Loop over the Nodes and Set Positions
            for i, node in enumerate(self.nodes):
                # skip central node
                if i == 0:
                    continue
                # Move Cursor in circle shape by node spacing angle
                draw_cursor.circle(MAX_COVERAGE, node_spacing)
                # Set heading towards the drawing cursor
                node.setheading(node.towards(draw_cursor.pos()))
                # init before use
                node_position = 0
                # Move random fd distance
                success = False
                while not success:
                    success = True
                    node_position = np.random.randint(
                        MIN_DIST_NODES, MAX_COVERAGE)
                    node.place_node(node_position, only_fd=True)
                    # Check if there is overlapping nodes
                    for index, neighbor in enumerate(self.nodes):
                        # skip central node
                        if index == 0:
                            continue
                        # Check until reaching node index
                        if neighbor == node:
                            break
                        if node.distance(neighbor) < MIN_DIST_NODES:
                            trace.warning(
                                f"node {node.node_id} was overlapping node {neighbor.node_id}")
                            success = False
                # Set node coverage to at least reach central node
                node.coverage = node_position + 10

        else:
            trace.error("Invalid Topology input, using Random")
            self.draw_network("random")

    def discover_network(self):
        kpi.info(f"totn {NUM_OF_NODES},alln,topology {TOPOLOGY_TYPE}")
        # Loop over all nodes
        self.screen.visual_output_msg(f"Nodes are discovering their neighbors")
        for node in self.nodes:
            # LOGGING:
            trace.info(f"node {node.node_id:2} discovering its neighbors")
            self.screen.show_coverage(node)
            self.screen.screen_refresh()
            # Scan all nodes within the coverage area
            for neighbor in self.nodes:
                if node.distance(neighbor) < node.coverage:
                    node.add_neighbor(neighbor)
            time.sleep(0.01)
            # Check if there was no neighbors
            if len(node.neighbors) == 0:
                # LOGGING:
                trace.critical(f"node {node.node_id} has no neighbors")
            else:
                msg = "node {:2},init,{:2} neighbors".format(
                    node.node_id, len(node.neighbors)
                )
                # LOGGING:
                kpi.info(msg)
                trace.info(msg.replace(",init,", " has "))
            self.screen.hide_coverage()
        # Loop over all nodes
        self.screen.visual_output_msg(
            f"Please choose running method from the controller")

    def tx_phase(self, r):
        # All transmit in random order
        for node in np.random.permutation(self.nodes):
            self.screen.visual_send_packet(node, node.get_neighbors())
            self.screen.screen_refresh()
            time.sleep(ncsv.SCREEN_REFRESH_TIME)

            # Choose time and frequency channels
            freq = np.random.randint(node.ch_num)
            timeslot = np.random.randint(node.ts_num)
            # set the random chosen channel
            node.set_sending_channel(freq, timeslot)

            cde.node_broadcast(node, node.get_neighbors(), r, _logger=kpi)

            # update tx counter
            node.update_tx_counter()
            #
            self.screen.clear_send_packets()

    def rx_phase(self, r):
        # All receive in random order
        for node in np.random.permutation(self.nodes):
            node.sense_spectrum(PACKET_LOSS, logger=trace)
            packets = node.get_rx_packets()
            if packets:
                cde.node_receive(node, packets, r, _logger=kpi)

    def run_round(self, r):
        # wait between generations
        while self.ctrl.is_continuous_run() > 1:
            self.screen.root.update()
            self.screen.root.update_idletasks()
            if self.ctrl.is_nxt_clicked():
                self.ctrl.post_click()
                break
        g = self.current_gen
        # TRANSMISSION PHASE
        # logging:
        log_msg = f"Generation {g}/{GENERATIONS} round {r}/{ROUNDS}, Transmitting phase"
        self.screen.visual_output_msg(log_msg)
        trace.info(log_msg)
        # Transmit
        self.tx_phase(r)

        # Receiving PHASE
        # logging:
        log_msg = f"Generation {g}/{GENERATIONS} round {r}/{ROUNDS}, Receiving phase"
        trace.info(log_msg)
        # nothing to show when nodes are digesting the received messages
        self.screen.visual_output_msg(log_msg)
        self.screen.screen_refresh()
        # Receiving
        self.rx_phase(r)

        # Collect data of the round
        self.end_round(r)

    def run_gen(self, xtra=False):
        g = self.current_gen
        # LOGGING:
        self.screen.visual_output_msg(f"New generation {g}")
        # wait between generations
        while not xtra and self.ctrl.is_continuous_run() > 0:
            self.screen.root.update()
            self.screen.root.update_idletasks()
            if self.ctrl.is_nxt_clicked():
                self.ctrl.post_click()
                # enable if was disabled
                self.ctrl.enb_rnd()
                break

        # LOGGING:
        trace.info(f"generation {g} begin")
        print("\nGeneration {} \n".format(g))
        # clean up before new generation
        self.gen_clean_up()

        # Generate new data
        cde.generate_data()

        # round zero is consuming self data
        self.end_round(0)

        # Starting from second round
        for r in range(1, ROUNDS+1):
            self.run_round(r)

        self.end_generation()

        # continue running if check box marked
        if self.ctrl.is_run_to_full() and self.ctrl.is_continuous_run() == 0:
            self.run_to_full()

    def end_round(self, round_num):
        # calculate data for the round
        aods = cde.calculate_aod(round_num, _logger=kpi)
        aods_tuples = list(zip(*aods))
        ranks = [cde.get_ranks(n.node_id) for n in self.nodes]
        stats = [n.print_aod_percentage(
            round_num, aods_tuples[i], ranks[i]) for i, n in enumerate(self.nodes)]
        oh_nodes = list(zip(*[n.get_additive_oh() for n in self.nodes]))
        oh_dict = {
            'Simple': np.sum(oh_nodes[0]),
            'Greedy': np.sum(oh_nodes[1]),
            'Heuristic': np.sum(oh_nodes[2])
        }
        self.ctrl.update_analysis(
            [aods, ranks, stats], oh_dict, round_num, ROUNDS, EXTRA_RNDS)

        # Log data of interest
        if round_num == ROUNDS:
            # Store statistics at specific rounds
            stats_df = pd.DataFrame(stats)
            stats_df['Generation'] = [self.current_gen] * NUM_OF_NODES
            self.statistics_df = self.statistics_df.append(
                stats_df, ignore_index=True)

        # get AoDs
        algs = {0: "Simple", 1: "Greedy", 2: "Heuristic"}
        for i, n in enumerate(self.nodes):
            for alg in algs:
                if not self.logged[i][alg] and aods_tuples[i][alg] == 100:
                    self.logged[i][alg] = True
                    # Store results
                    s_oh, g_oh, h_oh = n.get_additive_oh()
                    self.at_done_df = self.at_done_df.append(
                        {
                            'Generation': self.current_gen,
                            'Round': round_num,
                            'Node': i,
                            'Algorithm': algs[alg],
                            'added_s_overhead': s_oh,
                            'added_g_overhead': g_oh,
                            'added_h_overhead': h_oh
                        }, ignore_index=True)

        print(f"end round {round_num}")

    def end_generation(self):
        # Calculate nodes with 100% AoD
        self.full_AoD = [1 if n.last_aod == (
            100, 100, 100) else 0 for n in self.nodes]
        kpi.info(
            f"totn {NUM_OF_NODES},al{ROUNDS + EXTRA_RNDS},AoD {sum(self.full_AoD):2}/{len(self.full_AoD)} has 100%")

        if self.ctrl.is_continuous_run() > 1:
            self.ctrl.enable_nxt_btn('gen')
            self.ctrl.cont_run.set(1)
            self.ctrl.dis_rnd()

    # Simulation Sequence
    def run_generations(self):
        for _ in range(GENERATIONS):
            self.current_gen += 1
            self.run_gen()

        # LOGGING:
        self.screen.visual_output_msg(
            f"Completed generations {GENERATIONS} x {ROUNDS} rounds")
        trace.info("run completed")
        self.ctrl.dis_btns(dis_all=True)
        self.enable_extra_runs()

        # Exporting files
        self.statistics_df.to_csv(f'{LOG_FILES_NAME}_at_tx.csv', index=False, mode='a',)
        self.at_done_df.to_csv(f'{LOG_FILES_NAME}_at_done.csv', index=False, mode='a')

        print("run completed")

    # for extra runs
    def enable_extra_runs(self):
        btn_xtr_gen, btn_xtr_rnd, btn_to_full = self.ctrl.get_xtr_btns()
        btn_xtr_gen['state'] = 'normal'
        btn_xtr_rnd['state'] = 'normal'
        btn_to_full['state'] = 'normal'

        btn_xtr_gen['command'] = self.extra_gen
        btn_xtr_rnd['command'] = self.extra_rnd
        btn_to_full['command'] = self.run_to_full

    def gen_clean_up(self):
        global EXTRA_RNDS
        EXTRA_RNDS = 0
        self.logged = [[False, False, False] for _ in range(NUM_OF_NODES)]
        self.ctrl.new_generation_cleanup()
        for n in self.nodes:
            n.clear_counters()

    def extra_gen(self):
        global GENERATIONS
        global EXTRA_RNDS
        GENERATIONS += 1
        EXTRA_RNDS = 0
        self.current_gen += 1

        # self.ctrl.new_gen_enable_btns()
        self.run_gen(True)

    def extra_rnd(self):
        global EXTRA_RNDS
        EXTRA_RNDS += 1
        self.run_round(ROUNDS + EXTRA_RNDS)
        self.end_generation()

    def run_to_full(self):
        counter = 0
        breaker = 100
        while np.sum(self.full_AoD) != NUM_OF_NODES:
            self.extra_rnd()
            counter = counter + 1
            if counter == breaker:
                # LOGGING:
                self.screen.visual_output_msg(
                    f"TIMEOUT 100 runs!!!")
                trace.error('TIMEOUT!!')
                print(f"breaker +{breaker} rounds and no full AoD!")
                break

    def end_keep_open(self):
        self.screen.mainloop()


if __name__ == "__main__":
    print("Network Coding Simulator class")
