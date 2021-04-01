from turtle import Turtle
from node import Node
from controller import MouseClick, Controller
from platform import system as os_type
import ncsim_visualizer as ncsv
import json
import time
import numpy as np
import logging
import cde

try:
    # Open the NCSim Config Json file
    with open('config.json') as json_file:
        cfg = json.loads(json_file.read())    # Read Content

except Exception as e:
    cfg = {"unk": "unk"}
    print('failure to read config.json, running default values')
    print(e)

CFG_OS = os_type()
CFG_SIM = cfg.get('Simulation', {"unk": "unk"})   # Fetch Simulation Dictionary
# Fetch Parameters Dictionary
CFG_PARAM = cfg.get('Parameters', {"unk": "unk"})

# Fetch Screen related Configurations, or set default values.
SCREEN_WIDTH = int(CFG_SIM.get('screen_width', 600))
SCREEN_HEIGHT = int(CFG_SIM.get('screen_height', 600))
SCREEN_HEADER = CFG_SIM.get('screen_header', "NCSim Visualizer")
HEADER_FONT_SIZE = int(CFG_SIM.get('header_font_size', 30))
TEXT_FONT_SIZE = int(CFG_SIM.get('text_font_size', 12))
SCREEN_MARGIN = int(CFG_SIM.get('screen_margin', 50))
HEAD_MARGIN = int(CFG_SIM.get('head_margin', 150))
MESSAGE_MARGIN = int(CFG_SIM.get('message_margin', 100))
SCREEN_BGCOLOR = CFG_SIM.get('screen_bgcolor', 'black')
SCREEN_REFRESH_TIME = int(CFG_SIM.get("screen_refresh_time", 0.1))
SCREEN_TITLE = CFG_SIM.get('screen_title', 'Network Coding Simulator')

TOTAL_WIDTH = SCREEN_WIDTH + (2 * SCREEN_MARGIN)
TOTAL_HEIGHT = SCREEN_HEIGHT + HEAD_MARGIN + SCREEN_MARGIN

# Fetch Nodes related Configurations, or set default values.
NUM_OF_NODES = int(CFG_PARAM.get("nodes_num", '10'))
MIN_DIST_NODES = int(CFG_PARAM.get('min_dist_between_nodes', 20))
SEED_VALUE = int(CFG_PARAM.get('seed', 0))
NODE_COVERAGE = int(CFG_PARAM.get("nodes_coverage", '100'))
NODE_BUFFER_SIZE = int(CFG_PARAM.get('node_buffer_size', 1))
TOPOLOGY_TYPE = CFG_PARAM.get('topology', 'random')

# Fetch simulation parameters
PACKET_SIZE = int(CFG_PARAM.get("packet_size_bytes", 10))
PACKET_LOSS = int(CFG_PARAM.get("packet_loss_percent", 0))
CHANNEL_NUM = int(CFG_PARAM.get("channels", 2))
TIMESLOT_NUM = int(CFG_PARAM.get("timeslots", 2))
FINITE_FIELD = CFG_PARAM.get("fifi", "binary")

# Kodo configuration
CFG_KODO = {
    "n_coverage": NODE_COVERAGE,
    "buf_size": NODE_BUFFER_SIZE,
    "fifi": FINITE_FIELD,
    "gen_size": NUM_OF_NODES,
    "packet_size": PACKET_SIZE,
    "channels": CHANNEL_NUM,
    "timeslots": TIMESLOT_NUM,
    "seed": SEED_VALUE
}

# Fetch Logger related Configurations, or set default values.
LOG_PATH = CFG_SIM.get('log_path', "")
EXP_NAME = CFG_SIM.get('name', "test")
EXP_ID = int(CFG_SIM.get('id', 0))

# Create two Loggers .log for traces and .csv for KPIs
# create loggers
trace = logging.getLogger('trace')
kpi = logging.getLogger('kpi')

# add a file handler
log_fh = logging.FileHandler(
    f'{LOG_PATH}/{TOPOLOGY_TYPE}_{NUM_OF_NODES}_{EXP_NAME}_{EXP_ID}.log', 'w+')
kpi_fh = logging.FileHandler(
    f'{LOG_PATH}/{TOPOLOGY_TYPE}_{NUM_OF_NODES}_{EXP_NAME}_{EXP_ID}.csv', 'w+')

# create a formatter and set the formatter for the handler.
log_frmt = logging.Formatter('%(asctime)s:%(levelname)-10s: %(funcName)-16s: %(message)s',
                             datefmt="%Y-%m-%d %H.%M.%S")
kpi_frmt = logging.Formatter('%(asctime)s,%(msecs)-3d,%(funcName)-17s,%(message)s',
                             datefmt="%Y-%m-%d %H:%M:%S")
log_fh.setFormatter(log_frmt)
kpi_fh.setFormatter(kpi_frmt)


def fmt_filter(record):
    record.levelname = '[%s]' % record.levelname
    return True


# add the Handler to the logger
trace.addHandler(log_fh)
trace.setLevel(logging.DEBUG)
trace.addFilter(fmt_filter)
kpi.addHandler(kpi_fh)
kpi.setLevel(logging.DEBUG)

# For Generations
GENERATIONS = int(CFG_PARAM.get("generations_num", '5'))
T_g = int(CFG_PARAM.get("generation_time_ms", '1000'))
T_a = int(CFG_PARAM.get("action_time_ms", '40'))
ROUNDS = int(T_g/T_a)
EXTRA_RNDS = 0

# Pesudo random seed
np.random.seed(SEED_VALUE)


class NCSim:
    def __init__(self):
        # Call to NCSimVisualizer create Screen
        self.screen = ncsv.NCSimVisualizer(CFG_OS)
        # Log operating system
        trace.info(f"running on {CFG_OS.lower()}")
        # Create place holder of the data per gen
        self.data_in = ""
        # Create List of Nodes Variable
        self.nodes = []
        # Call Nodes Init Method
        self.create_nodes()

        # create right click listener
        self.mclick = MouseClick(self.screen.root, self.nodes)
        # attach popup to window
        self.screen.set_click_listener(
            fun=self.mclick.left_click, btn=1, add=True)
        # attach left click
        self.screen.set_click_listener(fun=self.mclick.popup, btn=3, add=True)

        # Init controller window
        self.ctrl = Controller(self.screen.root, NUM_OF_NODES)

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
            ring_radius = SCREEN_HEIGHT/4                           # Set the Ring Radius
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
            chain_length = SCREEN_WIDTH
            # Adjust Cursor starting position
            draw_cursor.setposition(-(chain_length/2) + SCREEN_MARGIN,
                                    -(chain_length/2) + SCREEN_MARGIN)
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

            # IF THERE ARE NODES AWAY ADJUST FACTOR DECREASE IT
            FACTOR = 1.25
            # Set the Quarter Size
            quarter_size = int(NODE_COVERAGE*FACTOR)
            # Set the Quarter Areas in list Variable, X and Y Lower and Higher values
            quarters_areas = [{"X_RANGE": [-quarter_size, 0],
                               "Y_RANGE": [0, quarter_size]},      # Q1
                              {"X_RANGE": [0, quarter_size],
                               "Y_RANGE": [0, quarter_size]},      # Q2
                              {"X_RANGE": [-quarter_size, 0],
                               "Y_RANGE": [-quarter_size, 0]},     # Q3
                              {"X_RANGE": [0, quarter_size],
                               "Y_RANGE": [-quarter_size, 0]}]     # Q4
            # Loop over the Nodes and Set Positions
            for index, node in enumerate(self.nodes):
                success = False
                while not success:
                    success = True
                    # Randomly Set the Node X Position, in specific Quarter
                    x_position = np.random.randint(
                        quarters_areas[index % 4]["X_RANGE"][LOW_VALUE],
                        quarters_areas[index % 4]["X_RANGE"][HIGH_VALUE])
                    # Randomly Set the Node Y Position, in specific Quarter
                    y_position = np.random.randint(
                        quarters_areas[index % 4]["Y_RANGE"][LOW_VALUE],
                        quarters_areas[index % 4]["Y_RANGE"][HIGH_VALUE])
                    # Locate Node where Cursor Stops
                    node.place_node((x_position, y_position))
                    # Check if there is overlapping nodes
                    for neighbor in self.nodes:
                        # Check until reaching node index
                        if neighbor == node:
                            break
                        if node.distance(neighbor) < MIN_DIST_NODES:
                            trace.warning(
                                f"node {node.node_id} was overlapping node {neighbor.node_id}")
                            success = False

        # IF HYBRID TOPOLOGY
        elif topology == "hybrid":
            pass
        # IF BUTTERFLY TOPOLOGY
        elif topology == "butterfly":
            pass
        # IF GRID TOPOLOGY
        elif topology == "grid":
            # Get nearest root + 1
            def nearest_square(limit):
                answer = 0
                while (answer+1)**2 < limit:
                    answer += 1
                return answer+1

            # Set the Chain Length
            chain_v_length = SCREEN_HEIGHT - HEAD_MARGIN - MESSAGE_MARGIN
            chain_h_length = SCREEN_WIDTH - SCREEN_MARGIN * 2
            chains = np.array_split(self.nodes, nearest_square(NUM_OF_NODES))
            for index, chain in enumerate(chains):
                v_move = (chain_v_length/len(chains)) * index
                # Adjust Cursor starting position
                draw_cursor.setposition(-(chain_h_length/2 + SCREEN_MARGIN),
                                        (chain_v_length/2) - v_move - MESSAGE_MARGIN)
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
            self.nodes[0].coverage = MAX_COVERAGE = SCREEN_HEIGHT / \
                2 - SCREEN_MARGIN  # Set the Ring Radius

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
                # Set heading towards the drawing curser
                node.setheading(node.towards(draw_cursor.pos()))
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
            self.draw_network("grid")

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
        self.screen.visual_output_msg(f"Please choose running method from the controller")

    def get_nodes_cor(self):
        return [n.pos() for n in self.nodes]

    def tx_phase(self, r):
        # All transmit in random order
        for node in np.random.permutation(self.nodes):
            self.screen.visual_send_packet(node, node.get_neighbors())
            self.screen.screen_refresh()
            time.sleep(SCREEN_REFRESH_TIME)

            # broadcast the message
            cde.node_broadcast(node, node.get_neighbors(), r, logger=kpi)
            self.screen.clear_send_packets()

    def rx_phase(self, r):
        # All receive in random order
        for node in np.random.permutation(self.nodes):
            node.sense_spectrum(PACKET_LOSS, logger=trace)
            packets = node.get_rx_packets()
            if packets:
                cde.node_receive(node, packets, r, logger=kpi)

    def run_round(self, g, r):
        # wait between generations
        while self.ctrl.is_continuous_run() > 1:
            self.screen.root.update()
            self.screen.root.update_idletasks()
            if self.ctrl.is_nxt_clicked():
                self.ctrl.post_click()
                break
        # TRANSMISSION PHASE
        # logging:
        log_msg = f"Generation {g}/{GENERATIONS} round {r}/{ROUNDS}, Transmitting phase"
        self.screen.visual_output_msg(log_msg)
        trace.info(log_msg)
        # Transmit
        self.tx_phase(r)

        # TODO remove this delay
        time.sleep(0.1)

        # Receiving PHASE
        # logging:
        log_msg = f"Generation {g}/{GENERATIONS} round {r}/{ROUNDS}, Receiving phase"
        trace.info(log_msg)
        # nothing to show when nodes are digesting the received messages
        self.screen.visual_output_msg(log_msg)
        self.screen.screen_refresh()
        # Receiving
        self.rx_phase(r)

        # TODO remove this delay
        time.sleep(0.1)

        # Collect data of the round
        self.end_round(r)

    def run_gen(self, g):

        # wait between generations
        while self.ctrl.is_continuous_run() > 0:
            self.screen.root.update()
            self.screen.root.update_idletasks()
            if self.ctrl.is_nxt_clicked():
                self.ctrl.post_click()
                # enable if was disabled
                self.ctrl.enb_rnd()
                break

        # LOGGING:
        trace.info(f"generation {g} begin")
        print("\n Generation {} \n".format(g))
        # clean up before new generation
        cde.clean_up_all()
        # Generate new data
        cde.generate_data()

        # Starting from second round
        for r in range(1, ROUNDS+1):
            self.run_round(g, r)
        self.end_generation()

    def end_round(self, round):
        # calculate data for the round
        aods = cde.calculate_aod(round, logger=kpi)
        # rank_txs = cde.calculate_rank_txs(round, logger=kpi)
        [n.print_aod_percentage(aods[i]) for i, n in enumerate(self.nodes)]
        self.ctrl.update_analysis(aods)
        print("end round")

    def end_generation(self):
        # Calculate nodes with 100% AoD
        self.full_AoD = [1 if n.aod == 100 else 0 for _, n in enumerate(self.nodes)]
        kpi.info("totn {},al{},AoD {:2}/{} has 100%".format(
                NUM_OF_NODES, 
                ROUNDS + EXTRA_RNDS,
                sum(self.full_AoD),len(self.full_AoD)))

        if self.ctrl.is_continuous_run() > 1:
            self.ctrl.enable_nxt_btn('gen')
            self.ctrl.cont_run.set(1)
            self.ctrl.dis_rnd()
        print("end generation")

    # Simulation Sequence
    def run_generations(self):
        for g in range(1, GENERATIONS+1):
            self.run_gen(g)

        # LOGGING:
        self.screen.visual_output_msg(
            f"Completed generations {GENERATIONS} x {ROUNDS} rounds")
        trace.info("run completed")
        self.ctrl.dis_btns(dis_all=True)
        self.enable_extra_runs()
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

    def extra_gen(self):
        global GENERATIONS
        global EXTRA_RNDS
        GENERATIONS = GENERATIONS + 1
        EXTRA_RNDS = 0
        self.run_gen(GENERATIONS)

    def extra_rnd(self):
        global EXTRA_RNDS
        EXTRA_RNDS = EXTRA_RNDS + 1
        self.run_round(GENERATIONS, ROUNDS + EXTRA_RNDS)
        self.end_generation()

    def run_to_full(self):
        counter = 0
        while sum(self.full_AoD) != NUM_OF_NODES:
            self.extra_rnd()
            counter = counter + 1
            if counter == 100:
                trace.error('TIMEOUT!!')
                break
            
    # Analysis Sequence
    def set_analysis(self):
        self.screen.enable_btns()

    def end_keep_open(self):
        self.screen.mainloop()


if __name__ == "__main__":
    print("Network Coding Simulator class")
