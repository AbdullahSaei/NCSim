from turtle import Screen, Turtle
from node import Node
import json
import time
import random


try:
    ## Open the NCSim Config Json file
    with open('config.json') as json_file:
        cfg = json.loads(json_file.read())                                  # Read Content
        CFG_SIM = cfg.get('Simulation')                                     # Fetch Simulation Dictionary
        CFG_PARAM = cfg.get('Parameters')                                   # Fetch Parameters Dictionary

        ## Fetch Screen related Configurations, or set default values.
        SCREEN_WIDTH = int(CFG_SIM.get('screen_width', 600))
        SCREEN_HEIGHT = int(CFG_SIM.get('screen_height', 600))
        SCREEN_MARGIN = int(CFG_SIM.get('screen_margin', 30))
        SCREEN_BGCOLOR = CFG_SIM.get('screen_bgcolor', 'black')
        SCREEN_REFRESH_TIME = int(CFG_SIM.get("screen_refresh_time", '0.1'))
        SCREEN_TITLE = CFG_SIM.get('screen_title', 'Network Coding Simulator')

        ## Fetch Nodes related Configurations, or set default values.
        NUM_OF_NODES = int(CFG_PARAM.get("nodes_num", '10'))
        NODE_COVERAGE = int(CFG_PARAM.get("nodes_coverage", '20'))
        TOPOLOGY_TYPE = CFG_PARAM.get('topology', 'random')

except ValueError as e:
    print('failure to read config.json, running default values')
    print(e)


class NCSim:
    def __init__(self):
        self.screen = Screen()                      # Create Screen Object
        self.nodes = []                             # Create List of Nodes Variable
        self.screen_init()                          # Call Screen Init Method
        self.create_nodes()                         # Call Nodes Init Method

    def screen_init(self):
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)     # Setup Screen Size
        self.screen.bgcolor(SCREEN_BGCOLOR)                             # Setup Screen Coloring
        self.screen.title(SCREEN_TITLE)                                 # Setup Screen Title
        self.screen.tracer(0)                                           # Stop Auto-update Screen changes

    def create_nodes(self):
        ## Loop over #no. of nodes to create it's objects
        for _ in range(NUM_OF_NODES):
            self.nodes.append(Node(NODE_COVERAGE))                  # Append the created node to list of nodes
        self.draw_network(TOPOLOGY_TYPE)                            # Adjust Nodes Co-ordinates according to topology
        self.screen.update()                                        # Update Screen Changes

    def draw_network(self, topology):
        draw_cursor = Turtle()                  # Create A Drawing Cursor
        draw_cursor.color("white")
        draw_cursor.ht()                        # Hide the Cursor
        draw_cursor.penup()                     # Hide Cursor pen movements
        draw_cursor.setposition(0, (SCREEN_HEIGHT/2)-SCREEN_MARGIN)
        draw_cursor.write(f"{topology.title()} Topology", align="Center", font=("Arial", 18, "normal"))

        ## IF RING TOPOLOGY
        if topology == "ring":
            ring_radius = SCREEN_HEIGHT/3                           # Set the Ring Radius
            draw_cursor.setposition(0, int(-ring_radius))           # Adjust Cursor starting position
            node_spacing = 360/NUM_OF_NODES                         # Set Node Spacing
            ## Loop over the Nodes and Set Positions
            for index in range(NUM_OF_NODES):
                draw_cursor.circle(ring_radius, node_spacing)       # Move Cursor in circle shape by node spacing angle
                node_position = draw_cursor.position()              # fetch Cursor Position
                self.nodes[index].place_node(node_position)         # Locate Node where Cursor Stops
        ## IF CHAIN TOPOLOGY
        elif topology == "chain":
            chain_length = SCREEN_WIDTH*0.75                        # Set the Chain Length
            draw_cursor.setposition(-(chain_length/2), 0)           # Adjust Cursor starting position
            ## Loop over the Nodes and Set Positions
            for index in range(NUM_OF_NODES):
                node_position = draw_cursor.position()              # fetch Cursor Position
                self.nodes[index].place_node(node_position)         # Locate Node where Cursor Stops
                draw_cursor.fd(chain_length/NUM_OF_NODES)           # Move Cursor forward by node spacing value
        ## IF RANDOM TOPOLOGY
        elif topology == "random":
            ## Constants
            LOW_VALUE = 0
            HIGH_VALUE = 1
            FACTOR = 0.75
            quarter_size = int(NODE_COVERAGE*FACTOR)                 # Set the Quarter Size
            ## Set the Quarter Areas in list Variable, X and Y Lower and Higher values
            quarters_areas = [{"X_RANGE": [-quarter_size, 0], "Y_RANGE": [0, quarter_size]},      # Q1
                              {"X_RANGE": [0, quarter_size], "Y_RANGE": [0, quarter_size]},       # Q2
                              {"X_RANGE": [-quarter_size, 0], "Y_RANGE": [-quarter_size, 0]},     # Q3
                              {"X_RANGE": [0, quarter_size], "Y_RANGE": [-quarter_size, 0]}]      # Q4
            ## Loop over the Nodes and Set Positions
            for index in range(NUM_OF_NODES):
                ## Randomly Set the Node X Position, in specific Quarter
                x_position = random.randint(
                    quarters_areas[index % 4]["X_RANGE"][LOW_VALUE],
                    quarters_areas[index % 4]["X_RANGE"][HIGH_VALUE])
                ## Randomly Set the Node Y Position, in specific Quarter
                y_position = random.randint(
                    quarters_areas[index % 4]["Y_RANGE"][LOW_VALUE],
                    quarters_areas[index % 4]["Y_RANGE"][HIGH_VALUE])
                # print((index % 4))
                # print(x_position, y_position)
                self.nodes[index].place_node((x_position, y_position))      # Locate Node where Cursor Stops
        ## IF HYBRID TOPOLOGY
        elif topology == "hybrid":
            pass
        else:
            print("Error! Invalid Topology input.")

    def network_discover(self):
        for n in self.nodes:
            n.show_coverage()
            self.screen.update()
            time.sleep(1)
            n.hide_coverage()

    def run(self):
        rounds = int(CFG_PARAM.get("rounds_num", '5'))
        round_time_ms = int(CFG_PARAM.get("round_time_ms", '1000'))
        nodes_tx_time_ms = int(CFG_PARAM.get("nodes_tx_time_ms", '40'))
        tx_times = int(round_time_ms/nodes_tx_time_ms)
        for _ in range(rounds):
            for _ in range(tx_times):
                for i, node in enumerate(self.nodes, start=1):
                    self.screen.update()
                    time.sleep(SCREEN_REFRESH_TIME)
                    print("node {} broadcast in range {}".format(i, node.coverage))

    def mainloop(self):
        self.screen.exitonclick()
