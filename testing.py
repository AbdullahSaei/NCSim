from turtle import Screen, Turtle
from node import Node
from platform import system as os_type
import json
import time

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
HEADER_FONT = int(CFG_SIM.get('header_font_size', 30))
TEXT_FONT = int(CFG_SIM.get('text_font_size', 12))
SCREEN_MARGIN = int(CFG_SIM.get('screen_margin', 50))
HEAD_MARGIN = int(CFG_SIM.get('head_margin', 150))
MESSAGE_MARGIN = int(CFG_SIM.get('message_margin', 100))
SCREEN_BGCOLOR = CFG_SIM.get('screen_bgcolor', 'black')
SCREEN_REFRESH_TIME = int(CFG_SIM.get("screen_refresh_time", 0.1))
SCREEN_TITLE = CFG_SIM.get('screen_title', 'Network Coding Simulator')



screen = Screen()

# Set Screen Dimensions and Coloring
TOTAL_WIDTH = SCREEN_WIDTH+(2*SCREEN_MARGIN)
TOTAL_HEIGHT = SCREEN_HEIGHT+HEAD_MARGIN+SCREEN_MARGIN
screen.setup(TOTAL_WIDTH, TOTAL_HEIGHT)
screen.bgcolor(SCREEN_BGCOLOR)

layout_cursor = Turtle()
layout_cursor.ht()
layout_cursor.penup()
layout_cursor.speed("fastest")
layout_cursor.pensize(3)
#HIDE TURTLE AND PATH
layout_cursor.color("slate grey")
layout_cursor.setposition(-((TOTAL_WIDTH/2)-SCREEN_MARGIN), -((TOTAL_HEIGHT/2)-SCREEN_MARGIN))

layout_cursor.pendown()
layout_cursor.fd(SCREEN_WIDTH)
layout_cursor.rt(-90)
layout_cursor.fd(SCREEN_HEIGHT)
layout_cursor.rt(-90)
layout_cursor.fd(SCREEN_WIDTH)
layout_cursor.rt(-90)
layout_cursor.fd(SCREEN_HEIGHT)
layout_cursor.setheading(90)
layout_cursor.fd(MESSAGE_MARGIN)
layout_cursor.setheading(0)
layout_cursor.fd(SCREEN_WIDTH)
layout_cursor.speed("fastest")


layout_cursor.color("midnight blue")
layout_cursor.ht()
layout_cursor.penup()

x_cor = 0
y_cor = int((TOTAL_HEIGHT/2)-(3/4*HEAD_MARGIN))
layout_cursor.setposition(x_cor, y_cor)
layout_cursor.write(f"{SCREEN_HEADER}", align="Center", font=("Calibri", HEADER_FONT, "bold"))

x_cor = 20 - (int(SCREEN_WIDTH/2))
y_cor = (int(TOTAL_HEIGHT/2)) - (HEAD_MARGIN+40)
layout_cursor.setposition(x_cor, y_cor)
layout_cursor.write(f"Topology: Random", align="Left", font=("Calibri", TEXT_FONT, "bold"))

x_cor = (int(SCREEN_WIDTH/2)) - 20
y_cor = (int(TOTAL_HEIGHT/2))-(HEAD_MARGIN+40)
layout_cursor.setposition(x_cor, y_cor)
layout_cursor.write(f"Number of nodes: 15", align="Right", font=("Calibri", TEXT_FONT, "bold"))



x_cor = 20 - (int(SCREEN_WIDTH/2))
y_cor = (SCREEN_MARGIN+15)-(int(TOTAL_HEIGHT/2))
layout_cursor.setposition(x_cor, y_cor)
layout_cursor.write(f"Number of nodes: 15", align="Left", font=("Calibri", TEXT_FONT, "bold"))





screen.exitonclick()