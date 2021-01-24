# Network Coding Simulator

It is a simple network simulator coded in Python to simulate broadcast networks. This simulator consists of 4 main classes:

- NCSim.py is the simulator class. It reads the simulation's configuration from `config.json` and it is responsible for:

  - Simulation time.
  - Screen size.
  - Number of nodes.
  - Transmission time of nodes.
  - Message validation period per round.

- node.py is the node class inherited from python drawing turtle. It contains the following:

  - node coordinates (x, y)
  - node symbol
  - node coverage range
