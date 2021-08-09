from ncsim import NCSim


def main() -> None:
    """
    Main function of the simulator

    Returns
    -------
    None.

    """
    # Normal Scenario
    # Create the simulation
    sim = NCSim()

    # Nodes discover its neighbors
    sim.discover_network()

    # Run the configured simulation
    sim.run_generations()
    print("Done Simulation")

    # Keep window open
    sim.end_keep_open()


if __name__ == '__main__':
    main()
