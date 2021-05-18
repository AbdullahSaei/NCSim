#! /usr/bin/env python
# encoding: utf-8
"""
    Cooperative data exchange example

    One of Network Coding applications is All-to-All network.

    This example shows how three nodes can dissimenate data between each other to
    simulate a simple network as shown below (for simplicity
    we have error free links, i.e. no data packets are lost when being
    sent):

            +---------+     +---------+     +---------+
            |  node 1 |+---.| node 0  |+---.|  node 2 |
            +---------+     +---------+     +---------+
                              
    In a practical application, network coding substitutes routing protocols. 
    With the help on recoding, all messages were able to probagate through nodes 
    without dedicated link between nodes.
"""

# Minimal example of cooperative data exchange network
import kodo
import numpy as np
import string

SEED_VALUE = 12
NUM_OF_NODES = 3
PACKET_SIZE = 100

# Choose the finite field, the number of symbols (i.e. generation size)
# and the symbol size in bytes
field = kodo.field.binary16
symbols = NUM_OF_NODES
symbol_size = PACKET_SIZE

# Global scope: Create lists of needed variables
# each node is a triples of (id, encoder, decoder)
nodes = [() for _ in range(NUM_OF_NODES)]
data_in = [[] for _ in range(NUM_OF_NODES)]
data_out = [[] for _ in range(NUM_OF_NODES)]
ranks = [[] for _ in range(NUM_OF_NODES)]

# Store previous value to compare if decreasing
prev_ranks = [0, 0, 0]

# to store received messages before consuming it by the decoder
# to have separate tx phase and rx phase
rx_buffers = [[] for _ in range(NUM_OF_NODES)]

# manual list of neighbours
list_of_neighbours = [
    [1, 2],
    [0],
    [0]
]


# Define a custom trace function for the decoder which filters the
# trace message based on their zones
def callback_function(zone, message) -> None:
    # disabled. to enable it remove the 'False and'
    if False and zone in ["decoder_state", "symbol_coefficients_before_consume_symbol"]:
        print("{}:".format(zone))
        print(message)

# Reset all kodo values for clean generation startup
def kodo_init() -> None:
    global nodes
    global data_in
    global data_out
    global prev_ranks
    global ranks

    nodes = []
    data_in = []
    data_out = []
    prev_ranks = [0, 0, 0]
    ranks = []

    # Create fresh nodes now
    for i in range(NUM_OF_NODES):
        # init encoder
        encoder = kodo.RLNCEncoder(field, symbols, symbol_size)
        seed = np.random.randint(SEED_VALUE)
        encoder.set_seed(seed)

        # init decoder
        decoder = kodo.RLNCDecoder(field, symbols, symbol_size)
        decoder.set_seed(seed)
        decoder.set_log_callback(callback_function)
        nodes.append([i, encoder, decoder])
        ranks.append((0, 0, 0, 0, 0))

# generates random ascii messages for each node and 
# feed this data to the decoder systematically
def generate_data() -> None:
    # clean start up
    kodo_init()

    # for random message generation
    _alphabet = string.ascii_uppercase + string.digits
    _alphabet_list = [char for char in _alphabet]

    # Generate random message
    for i, encoder, decoder in nodes:
        msg = "IAM{:02}X".format(i) + "".join(
            np.random.choice(_alphabet_list, size=PACKET_SIZE - 6))
        data = bytearray(msg, encoding="utf-8")
        data_rx = bytearray(decoder.block_size())
        data_in.append(data)
        data_out.append(data_rx)

    # setup encoders and decoders
    for i, encoder, decoder in nodes:
        decoder.set_symbols_storage(data_out[i])
        encoder.set_symbol_storage(data_in[i], i)

        # round zero each node consumes its own packet
        pack = encoder.produce_systematic_symbol(i)
        decoder.consume_systematic_symbol(pack, i)

        # Update and check ranks
        decoder.update_symbol_status()
        ranks[i] = (
            decoder.rank(),
            decoder.symbols_partially_decoded(),
            decoder.symbols_decoded(),
            decoder.symbols_missing(),
            decoder.symbols()
        )


# Send decoded message to all neighbours
def node_broadcast(node_id: int, neighbours_id: list) -> None:

    # get kodo encoder and decoder
    i, encoder, decoder = nodes[node_id]

    # produce packet to broadcast
    pack = decoder.produce_payload()

    # send pack to all neighbors
    for id in neighbours_id:
        rx_buffers[id].append(pack)

# Check the rx_buffer and consume the received data
def node_receive(node_id: int) -> None:
    global rx_buffers
    i, encoder, decoder = nodes[node_id]
    # check if data in buffer
    if not len(rx_buffers[node_id]):
        print(f"no data in buffer {node_id}")
        return

    log_msg = f"node {i:2} "

    # consume buffered data
    for packet in rx_buffers[node_id]:
        decoder.consume_payload(packet)

    # Empty buffer
    rx_buffers[node_id] = []

    # Update and check ranks
    decoder.update_symbol_status()
    ranks[i] = (
        decoder.rank(),
        decoder.symbols_partially_decoded(),
        decoder.symbols_decoded(),
        decoder.symbols_missing(),
        decoder.symbols()
    )
    log_msg += "rank/part/decoded/missing/total {}/{}/{}/{}/{}".format(
        *ranks[i])
    #print(log_msg)


def main():
    """Simple all-to-all network consist of 3 nodes
        showing how to dissimenate data in the network"""
    global prev_ranks

    # how many iterations to test it with
    num_generations = 10000
    print(f"Testing {num_generations} generations")
    for gen in range(num_generations):
        #### DEBUGING PRINTS
        #print(f"Generation {gen}")

        # new generation
        generate_data()
        
        # each generation consist of rounds to disseminate data in it
        num_rounds = 10
        for rnd in range(num_rounds):
            # Prepare statistics
            avg_prev = sum(prev_ranks)/len(prev_ranks)
            all_ranks = [rank for rank, *_ in ranks]
            avg_ranks = sum(all_ranks)/len(all_ranks)

            # Round zero the systematic coding for self-info
            # Should result rank = 1 for all nodes, avg rank of all nodes = 1
            
            #### DEBUGING PRINTS
            #print(f"round {rnd} avg prev {avg_prev:.2f} new {avg_ranks:.2f}")

            # clean leftovers for new round
            prev_ranks = [rank for rank, *_ in ranks]
            
            # Tx phase
            for node in np.random.permutation(nodes):
                node_id = node[0]
                node_broadcast(node_id, list_of_neighbours[node_id])

            # Rx phase
            for node in np.random.permutation(nodes):
                node_id = node[0]
                node_receive(node_id)

            # Calculate rank changes
            for id, _, _ in nodes:
                if prev_ranks[id] > ranks[id][0]:
                    print("ERROOOOOOOOOOOOOOORRRRRRRRRRR!!!!!!!!")
                    print(f"gen {gen} round {rnd} node {id} prev {prev_ranks[id]} new {ranks[id][0]}")
        
        # Check if data disseminated successfully 
        # during the specified num of rounds
        if avg_ranks < NUM_OF_NODES:
            msg = f"gen {gen:>4} avg {avg_ranks:.2f}/{NUM_OF_NODES} incomplete!"
            #### DEBUGING PRINTS
            print(msg)
                

if __name__ == "__main__":
    print("Start test...")
    main()
    print("Done!")
