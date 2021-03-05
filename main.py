from ncsim import NCSim


def main():
    # Normal Scenario
    # Create the simulation
    sim = NCSim()

    # Nodes discover its neighbors
    sim.discover_network()

    # Run the configured simulation
    sim.run_generations()
    print("Done Simulation")

    # Analysis phase
    sim.set_analysis()

    # Keep window open
    sim.end_keep_open()


if __name__ == '__main__':
    main()
