from ncsim import NCSim
from node import Node

## Ahmed Montasser Changes

sim = NCSim()

def main():
    sim.network_discover()
    sim.run()
    print("Done!")
    
    sim.mainloop()


if __name__ == '__main__':
    main()

