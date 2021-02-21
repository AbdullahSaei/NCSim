from turtle import Screen, Turtle
import json

try:
    # Open the NCSim Config Json file
    with open('config.json') as json_file:
        cfg = json.loads(json_file.read())    # Read Content

except Exception as e:
    cfg = {"unk": "unk"}
    print('failure to read config.json, running default values')
    print(e)

# Fetch Simulation Dictionary
CFG_SIM = cfg.get('Simulation', {"unk": "unk"})
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
TOPOLOGY_TYPE = CFG_PARAM.get('topology', 'random')


class NCSimVisualizer:
    def __init__(self):
        # Create Screen Object
        self.screen = Screen()

        # Create Screen Layout Cursor
        self.layout_cursor = Turtle()
        self.layout_cursor.ht()
        self.layout_cursor.penup()
        self.layout_cursor.pensize(3)
        self.layout_cursor.color("slate grey")

        #Create Screen Message Cursor
        self.msg_cursor = Turtle()
        self.msg_cursor.ht()
        self.msg_cursor.penup()
        self.msg_cursor.color("midnight blue")

        # Create Screen Send Packet Cursor
        self.snd_pckt = Turtle()
        self.snd_pckt.ht()
        self.snd_pckt.penup()
        self.snd_pckt.pensize(2)
        self.snd_pckt.color("saddle brown")

        # Call Screen Init Method
        self.screen_init()

    def screen_init(self):
        # Set Screen Dimensions and Coloring
        self.screen.setup(TOTAL_WIDTH, TOTAL_HEIGHT)
        self.screen.bgcolor(SCREEN_BGCOLOR)

        self.layout_cursor.color("slate grey")
        self.layout_cursor.setposition(-((TOTAL_WIDTH / 2) - SCREEN_MARGIN), -((TOTAL_HEIGHT / 2) - SCREEN_MARGIN))

        self.layout_cursor.speed(8)
        self.layout_cursor.pendown()
        self.layout_cursor.fd(SCREEN_WIDTH)
        self.layout_cursor.rt(-90)
        self.layout_cursor.fd(SCREEN_HEIGHT)
        self.layout_cursor.rt(-90)
        self.layout_cursor.fd(SCREEN_WIDTH)
        self.layout_cursor.rt(-90)
        self.layout_cursor.fd(SCREEN_HEIGHT)
        self.layout_cursor.setheading(90)
        self.layout_cursor.fd(MESSAGE_MARGIN)
        self.layout_cursor.setheading(0)
        self.layout_cursor.fd(SCREEN_WIDTH)

        self.layout_cursor.penup()
        self.layout_cursor.speed("fastest")
        self.layout_cursor.color("midnight blue")

        x_cor = 0
        y_cor = int((TOTAL_HEIGHT / 2) - (3 / 4 * HEAD_MARGIN))
        self.layout_cursor.setposition(x_cor, y_cor)
        self.layout_cursor.write(f"{SCREEN_HEADER}", align="Center", font=("Calibri", HEADER_FONT_SIZE, "bold"))

        x_cor = 20 - (int(SCREEN_WIDTH / 2))
        y_cor = (int(TOTAL_HEIGHT / 2)) - (HEAD_MARGIN + 40)
        self.layout_cursor.setposition(x_cor, y_cor)
        self.layout_cursor.write(f"Topology: {TOPOLOGY_TYPE.title()}",
                                 align="Left", font=("Calibri", TEXT_FONT_SIZE, "bold"))

        x_cor = (int(SCREEN_WIDTH / 2)) - 20
        y_cor = (int(TOTAL_HEIGHT / 2)) - (HEAD_MARGIN + 40)
        self.layout_cursor.setposition(x_cor, y_cor)
        self.layout_cursor.write(f"Nodes: {NUM_OF_NODES}",
                                 align="Right", font=("Calibri", TEXT_FONT_SIZE, "bold"))

        self.visual_output_msg("This where the text message appears")

        # Stop Auto-update Screen changes
        self.screen.tracer(0)

    def visual_output_msg(self, message):
        x_cor = 20 - (int(SCREEN_WIDTH / 2))
        y_cor = (SCREEN_MARGIN + 15) - (int(TOTAL_HEIGHT / 2))
        self.msg_cursor.setposition(x_cor, y_cor)
        self.msg_cursor.clear()
        self.msg_cursor.write(f"{message}", align="Left", font=("Calibri", TEXT_FONT_SIZE, "bold"))

    def visual_send_packet(self, tx_cor, rx_cor):
        self.snd_pckt.setposition(tx_cor)
        self.snd_pckt.pendown()
        self.snd_pckt.setposition(rx_cor)
        self.snd_pckt.penup()

    def screen_refresh(self):
        self.screen.update()


    def mainloop(self):
        self.screen.exitonclick()