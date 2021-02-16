from turtle import Screen, Turtle
from node import Node
from platform import system as os_type
import json
import time
import random

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
SCREEN_MARGIN = int(CFG_SIM.get('screen_margin', 30))
SCREEN_BGCOLOR = CFG_SIM.get('screen_bgcolor', 'black')
SCREEN_REFRESH_TIME = int(CFG_SIM.get("screen_refresh_time", 0.1))
SCREEN_TITLE = CFG_SIM.get('screen_title', 'Network Coding Simulator')

# Fetch Nodes related Configurations, or set default values.
NUM_OF_NODES = int(CFG_PARAM.get("nodes_num", '10'))
NODE_COVERAGE = int(CFG_PARAM.get("nodes_coverage", '100'))
NODE_BUFFER_SIZE = int(CFG_PARAM.get('node_buffer_size', 1))
TOPOLOGY_TYPE = CFG_PARAM.get('topology', 'random')


class NCSim:
    def __init__(self):
        self.screen = Screen()                      # Create Screen Object
        self.nodes = []                             # Create List of Nodes Variable
        self.screen_init()                          # Call Screen Init Method
        self.create_nodes()                         # Call Nodes Init Method

    def screen_init(self):
        # Setup Screen Size
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        # Setup Screen Coloring
        self.screen.bgcolor(SCREEN_BGCOLOR)
        # Setup Screen Title
        self.screen.title(SCREEN_TITLE)
        # Stop Auto-update Screen changes
        self.screen.tracer(0)
        # Add app icon
        LOGO_PATH = "assets/favicon.ico"
        # do not forget "@" symbol and .xbm format for Ubuntu
        LOGO_LINUX_PATH = "@assets/favicon_linux.xbm"
        root = self.screen._root
        if CFG_OS.lower() == "linux":
            root.iconbitmap(LOGO_LINUX_PATH)
        else:
            root.iconbitmap(LOGO_PATH)

    def create_nodes(self):
        # Loop over #no. of nodes to create it's objects
        for _ in range(NUM_OF_NODES):
            # Append the created node to list of nodes
            self.nodes.append(Node(n_coverage=NODE_COVERAGE,
                                   buf_size=NODE_BUFFER_SIZE))
        # Adjust Nodes Co-ordinates according to topology
        self.draw_network(TOPOLOGY_TYPE)
        # Update Screen Changes
        self.screen.update()

    def draw_network(self, topology):
        draw_cursor = Turtle()                  # Create A Drawing Cursor
        draw_cursor.color("white")
        draw_cursor.ht()                        # Hide the Cursor
        draw_cursor.penup()                     # Hide Cursor pen movements
        draw_cursor.setposition(0, (SCREEN_HEIGHT/2)-SCREEN_MARGIN)
        draw_cursor.write(f"{topology.title()} topology - {NUM_OF_NODES} nodes",
                          align="Center", font=("Arial", 14, "normal"))

        # IF RING TOPOLOGY
        if topology == "ring":
            ring_radius = SCREEN_HEIGHT/3                           # Set the Ring Radius
            # Adjust Cursor starting position
            draw_cursor.setposition(0, int(-ring_radius))
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
            draw_cursor.setposition(-(chain_length/2) +
                                    SCREEN_MARGIN, -(chain_length/2)+SCREEN_MARGIN)
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
            FACTOR = 0.75
            # Set the Quarter Size
            quarter_size = int(NODE_COVERAGE*FACTOR)
            # Set the Quarter Areas in list Variable, X and Y Lower and Higher values
            quarters_areas = [{"X_RANGE": [-quarter_size, 0],
                               "Y_RANGE": [0, quarter_size]},       # Q1
                              {"X_RANGE": [0, quarter_size],
                               "Y_RANGE": [0, quarter_size]},       # Q2
                              {"X_RANGE": [-quarter_size, 0],
                                "Y_RANGE": [-quarter_size, 0]},     # Q3
                              {"X_RANGE": [0, quarter_size],
                                "Y_RANGE": [-quarter_size, 0]}]     # Q4
            # Loop over the Nodes and Set Positions
            for index in range(NUM_OF_NODES):
                # Randomly Set the Node X Position, in specific Quarter
                x_position = random.randint(
                    quarters_areas[index % 4]["X_RANGE"][LOW_VALUE],
                    quarters_areas[index % 4]["X_RANGE"][HIGH_VALUE])
                # Randomly Set the Node Y Position, in specific Quarter
                y_position = random.randint(
                    quarters_areas[index % 4]["Y_RANGE"][LOW_VALUE],
                    quarters_areas[index % 4]["Y_RANGE"][HIGH_VALUE])
                # print((index % 4))
                # print(x_position, y_position)
                # Locate Node where Cursor Stops
                self.nodes[index].place_node((x_position, y_position))
        # IF HYBRID TOPOLOGY
        elif topology == "hybrid":
            pass
        # IF BUTTERFLY TOPOLOGY
        elif topology == "butterfly":
            pass
        else:
            raise Warning("Invalid Topology input.")

    def discover_network(self):
        # Loop over all nodes
        for node in self.nodes:
            node.show_coverage()
            self.screen.update()
            # Scan all nodes within the coverage area
            for neighbor in self.nodes:
                if node.distance(neighbor) < node.coverage:
                    node.add_neighbor(neighbor)
            time.sleep(0.05)
            # Check if there was no neighbors
            if len(node.neighbors) == 0:
                print("Warning! node {} has no neighbors".format(node.id))
            node.hide_coverage()

    def run_generations(self):
        generations = int(CFG_PARAM.get("generations_num", '5'))
        T_g = int(CFG_PARAM.get("generation_time_ms", '1000'))
        T_a = int(CFG_PARAM.get("action_time_ms", '40'))
        rounds = int(T_g/T_a)
        for g in range(generations):
            for r in range(rounds):
                for i, node in enumerate(self.nodes, start=1):
                    self.screen.update()
                    time.sleep(SCREEN_REFRESH_TIME)
                    if g == 0 and r == 0:
                        print("node {} has {} neighbors".format(
                            i, len(node.neighbors)))

        print("run completed")

    def mainloop(self):
        self.screen.exitonclick()
