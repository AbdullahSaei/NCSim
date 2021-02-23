from turtle import Screen, Turtle
from node import Node
from platform import system as os_type
import ncsim_visualizer as ncsv
import json
import time
import numpy as np
import string
import logging

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

# Fetch Logger related Configurations, or set default values.
LOG_PATH = CFG_SIM.get('log_path', "")
EXP_NAME = CFG_SIM.get('name', "test")
EXP_ID = int(CFG_SIM.get('id', 0))

# Create two Loggers .log for traces and .csv for KPIs
# create loggers
trace = logging.getLogger('trace')
kpi = logging.getLogger('kpi')

# add a file handler
log_fh = logging.FileHandler(f'{LOG_PATH}/{EXP_NAME}_{EXP_ID}.log', 'w+')
kpi_fh = logging.FileHandler(f'{LOG_PATH}/{EXP_NAME}_{EXP_ID}.csv', 'w+')

# create a formatter and set the formatter for the handler.
log_frmt = logging.Formatter('%(asctime)s: %(levelname)-8s: %(funcName)-16s: %(message)s',
                             datefmt="%Y-%m-%d %H.%M.%S")
kpi_frmt = logging.Formatter('%(asctime)s,%(levelname)-8s,%(funcName)-17s,%(message)s',
                             datefmt="%Y-%m-%d %H:%M:%S")
log_fh.setFormatter(log_frmt)
kpi_fh.setFormatter(kpi_frmt)

# add the Handler to the logger
trace.addHandler(log_fh)
trace.setLevel(logging.DEBUG)
kpi.addHandler(kpi_fh)
kpi.setLevel(logging.DEBUG)


class NCSim:
    def __init__(self):
        # Call to NCSimVisualizer create Screen
        self.screen = ncsv.NCSimVisualizer(CFG_OS)
        # Log operating system
        trace.info(f"running on {CFG_OS.lower()}")
        # Create List of Nodes Variable
        self.nodes = []
        # Call Nodes Init Method
        self.create_nodes()

    def create_nodes(self):
        # LOGGING:
        self.screen.visual_output_msg(
            f"Set {NUM_OF_NODES} nodes to {TOPOLOGY_TYPE} topology")
        trace.info(f"creating {NUM_OF_NODES} node(s)")
        # Loop over #no. of nodes to create its objects
        for index in range(NUM_OF_NODES):
            # Append the created node to list of nodes
            self.nodes.append(Node(index, n_coverage=NODE_COVERAGE,
                                   buf_size=NODE_BUFFER_SIZE))
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
            # Pesudo random seed
            np.random.seed(SEED_VALUE)
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
                                        (chain_v_length/2) - v_move - MESSAGE_MARGIN )
                # Loop over the Nodes and Set Positions
                for node in chain:
                    # Move Cursor forward by node spacing value
                    draw_cursor.fd(chain_h_length/len(chain))
                    node_position = draw_cursor.position()     # fetch Cursor Position
                    # Locate Node where Cursor Stops
                    node.place_node(node_position)

        # IF STAR TOPOLOGY
        elif topology == "star":
            # Pesudo random seed
            np.random.seed(SEED_VALUE)
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
            trace.warning("Invalid Topology input, using Random")
            self.draw_network("grid")

    def discover_network(self):
        # Loop over all nodes
        self.screen.visual_output_msg(f"Nodes are discovering their neighbors")
        for node in self.nodes:
            # LOGGING:
            trace.info(f"node {node.node_id} discovering its neighbors")
            self.screen.show_coverage(node)
            self.screen.screen_refresh()
            # Scan all nodes within the coverage area
            for neighbor in self.nodes:
                if node.distance(neighbor) < node.coverage:
                    node.add_neighbor(neighbor)
            time.sleep(0.1)
            # Check if there was no neighbors
            if len(node.neighbors) == 0:
                # LOGGING:
                trace.warning(f"node {node.node_id} has no neighbors")
            else:
                # LOGGING:
                trace.info(
                    f"node {node.node_id} has {len(node.neighbors)} neighbors")
            self.screen.hide_coverage()

    # Analysis Sequence
    def set_analysis(self):
        self.screen.enable_btns()

    # Simulation Sequence
    def run_generations(self):
        generations = int(CFG_PARAM.get("generations_num", '5'))
        packet_size = int(CFG_PARAM.get("packet_size_bytes", 10))
        packet_loss = int(CFG_PARAM.get("packet_loss_percent", 0))
        T_g = int(CFG_PARAM.get("generation_time_ms", '1000'))
        T_a = int(CFG_PARAM.get("action_time_ms", '40'))
        rounds = int(T_g/T_a)
        # for random message generation
        _alphabet = string.ascii_uppercase + string.digits
        _alphabet_list = [char for char in _alphabet]
        for g in range(1, generations+1):
            # LOGGING:
            trace.info(f"generation {g} begin")
            print("\n Generation {} \n".format(g))
            for r in range(1, rounds+1):
                # LOGGING:
                log_msg = f"Generation {g}/{generations} round {r}/{rounds}, Transmitting phase"
                self.screen.visual_output_msg(log_msg)
                trace.info(log_msg)
                # All transmit in random order
                for node in np.random.permutation(self.nodes):
                    self.screen.visual_send_packet(node, node.get_neighbors())
                    self.screen.screen_refresh()
                    time.sleep(SCREEN_REFRESH_TIME+0.5)
                    msg = "".join(np.random.choice(
                        _alphabet_list, size=packet_size))
                    node.broadcast_message(msg, logger=kpi)
                    self.screen.clear_send_packets()

                # TODO remove this delay
                time.sleep(0.1)

                # LOGGING:
                log_msg = f"Generation {g}/{generations} round {r}/{rounds}, Receiving phase"
                trace.info(log_msg)
                # nothing to show when nodes are digesting the received messages
                self.screen.visual_output_msg(log_msg)
                self.screen.screen_refresh()

                # All receive in random order
                for node in np.random.permutation(self.nodes):
                    node.sense_spectrum(packet_loss, logger=kpi)
                    node.rx_packet(kpi)

                # TODO remove this delay
                time.sleep(0.1)

        # LOGGING:
        self.screen.visual_output_msg("Generations run completed!")
        trace.info("run completed")
        print("run completed")

    def end_keep_open(self):
        self.screen.mainloop()