from turtle import Screen
from node import Node
import json
import time
import random

try:
    with open('config.json') as json_file:
        cfg = json.loads(json_file.read())
        CFG_SIM = cfg.get('Simulation')
        CFG_PARAM = cfg.get('Parameters')
        SCREEN_WIDTH = int(CFG_SIM.get('screen_width', 600))
        SCREEN_HEIGHT = int(CFG_SIM.get('screen_height', 600))
        SCREEN_MARGIN = int(CFG_SIM.get('screen_margin', 30))
        SCREEN_BGCOLOR = CFG_SIM.get('screen_bgcolor', 'black')
        SCREEN_TITLE = CFG_SIM.get('screen_title', 'Network Coding Simulator')
except ValueError as e:
    print('failure to read config.json, running default values')
    print(e)


class NCSim():
    screen = Screen()
    s_r_t = int(CFG_SIM.get("screen_refresh_time", '0.1'))

    def __init__(self):
        self.nodes = []
        self.screen_init()
        self.create_nodes("random")

    def screen_init(self):
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.screen.bgcolor(SCREEN_BGCOLOR)
        self.screen.title(SCREEN_TITLE)
        self.screen.tracer(0)

    def create_nodes(self, topology):
        num_nodes = int(CFG_PARAM.get("nodes_num", '10'))
        ranges = int(CFG_PARAM.get("nodes_coverage", '20'))
        for _ in range(num_nodes):
            x_position = random.randint(
                -1*SCREEN_WIDTH/2 + SCREEN_MARGIN,
                SCREEN_WIDTH/2 - SCREEN_MARGIN)
            y_position = random.randint(
                -1*SCREEN_HEIGHT/2 + SCREEN_MARGIN,
                SCREEN_HEIGHT/2 - SCREEN_MARGIN)
            n = Node(ranges, (x_position, y_position))
            self.nodes.append(n)
        self.screen.update()

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
                    time.sleep(self.s_r_t)
                    print("node {} broadcast in range {}".format(i, node.coverage))

    def mainloop(self):
        self.screen.exitonclick()
