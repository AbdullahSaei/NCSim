#! /usr/bin/env python
# encoding: utf-8

# Cooperative data exchange network
import kodo
import json
import numpy as np
import string

"""
Cooperative data exchange network using network coding.

This file creates kodo for all nodes using kodo for CDE.
"""

try:
    # Open the NCSim Config Json file
    with open('config.json') as json_file:
        cfg = json.loads(json_file.read())    # Read Content

except Exception as e:
    cfg = {"unk": "unk"}
    print('failure to read config.json, running default values')
    print(e)

# Fetch Parameters Dictionary
CFG_PARAM = cfg.get('Parameters', {"unk": "unk"})

# Fetch KODO related configurations, or set default values.
# seed value for random generation
SEED_VALUE = int(CFG_PARAM.get('seed', 0))
# symbols or generation size
NUM_OF_NODES = int(CFG_PARAM.get("nodes_num", '10'))
# symbol size or packet size per node
PACKET_SIZE = int(CFG_PARAM.get("packet_size_bytes", 10))
# how many bits identifying each node
FINITE_FIELD = CFG_PARAM.get("fifi", "binary")

# fifi translation
fifi = {
    "binary16": kodo.field.binary16,
    "binary8": kodo.field.binary8,
    "binary4": kodo.field.binary4,
    "binary": kodo.field.binary
}

fifi_num = {
    "binary16": 16,
    "binary8": 8,
    "binary4": 4,
    "binary": 2
}

# Configure kodo parameters
field = fifi.get(FINITE_FIELD, "binary8")
field_max = 2 ** int(fifi_num.get(FINITE_FIELD, 8))
symbols = NUM_OF_NODES
symbol_size = PACKET_SIZE

# Pseudo random seed
np.random.seed(SEED_VALUE)

# Global scope Create list of encoder and decoder triples
nodes = []
data_in = []
simple_data_out = []
greedy_data_out = []
heuristic_data_out = []

# Master encoder
master_data_in = []
master_encoder = kodo.RLNCEncoder(field, symbols, symbol_size)


def kodo_init():
    # Create list of encoder and decoder triples
    global nodes
    global data_in
    global simple_data_out
    global greedy_data_out
    global heuristic_data_out
    global master_data_in

    nodes = []
    data_in = []
    simple_data_out = []
    greedy_data_out = []
    heuristic_data_out = []
    master_data_in = []

    # init one encoder
    master_encoder.set_seed(SEED_VALUE)

    for _ in range(NUM_OF_NODES):
        seed = np.random.randint(SEED_VALUE)

        # init decoders
        simple_decoder = kodo.RLNCDecoder(field, symbols, symbol_size)
        simple_decoder.set_seed(seed)

        greedy_decoder = kodo.RLNCDecoder(field, symbols, symbol_size)
        greedy_decoder.set_seed(seed)

        heuristic_decoder = kodo.RLNCDecoder(field, symbols, symbol_size)
        heuristic_decoder.set_seed(seed)

        # decoder.set_log_callback(callback_function)
        nodes.append([simple_decoder, greedy_decoder, heuristic_decoder])


def generate_data():
    global master_data_in

    # Always clear when new generation
    kodo_init()

    # for random message generation
    _alphabet = string.ascii_uppercase + string.digits
    _alphabet_list = [char for char in _alphabet]

    # Generate random message
    for i, decoders, *_ in enumerate(nodes):
        s_decoder, g_decoder, h_decoder = decoders
        msg = "IAM{:02}X".format(i) + "".join(
            np.random.choice(_alphabet_list, size=PACKET_SIZE - 6))
        data_in.append(bytearray(msg, encoding="utf-8"))
        simple_data_out.append(bytearray(s_decoder.block_size()))
        greedy_data_out.append(bytearray(g_decoder.block_size()))
        heuristic_data_out.append(bytearray(h_decoder.block_size()))

    # setup encoders and decoders
    master_data_in = bytearray(b"".join(data_in))
    master_encoder.set_symbols_storage(master_data_in)

    for i, node in enumerate(nodes):
        s_decoder, g_decoder, h_decoder = node
        s_decoder.set_symbols_storage(simple_data_out[i])
        s_decoder.consume_systematic_symbol(data_in[i], i)

        g_decoder.set_symbols_storage(greedy_data_out[i])
        g_decoder.consume_systematic_symbol(data_in[i], i)

        h_decoder.set_symbols_storage(heuristic_data_out[i])
        h_decoder.consume_systematic_symbol(data_in[i], i)


def node_broadcast(node, neighbours, rnd, _logger):
    # get kodo encoder and decoder
    s_decoder, *_ = nodes[node.node_id]

    # produce packet to broadcast
    pack = s_decoder.produce_payload()

    # log data
    # log message and channel
    _logger.info(
        "node {:2},tx{:2},broadcast to {} nodes".format(
            node.node_id, rnd, len(neighbours)))

    # print("\nDecoder rank: {}/{}".format(decoder.rank(), symbols))
    # print(f"Node {i} sending to ", end='')
    for n in neighbours:
        # get kodo encoder and decoder of the neighbor
        # n_i, n_encoder, n_decoder = nodes[n.node_id]
        # print(f"{n_i:02} ", end='')
        n.access_rx_buffer(node.node_id, pack, node.sending_channel)
    # print("")


def node_receive(node, packets, rnd, _logger):
    s_decoder, g_decoder, h_decoder = nodes[node.node_id]
    # check if data in buffer
    log_msg = "node {:2},rx{:2},".format(node.node_id, rnd)

    if len(packets) > 0:
        for src, p in packets:
            n_decoder, *_ = nodes[src]

            # greedy decoder
            g_coe = bytearray([np.random.randint(1, field_max) if n_decoder.is_symbol_pivot(
                sym) else 0 for sym in range(NUM_OF_NODES)])
            g_pack = master_encoder.produce_symbol(g_coe)
            g_decoder.consume_symbol(g_pack, g_coe)

            # heuristic decoder
            h_coe = bytearray([np.random.randint(1, field_max) if s_decoder.is_symbol_missing(
                sym) and n_decoder.is_symbol_pivot(sym) else 0 for sym in range(NUM_OF_NODES)])
            h_pack = master_encoder.produce_symbol(h_coe)
            h_decoder.consume_symbol(h_pack, h_coe)

            # simple decoder
            s_decoder.consume_payload(p)

        ranks = get_ranks(node.node_id)
        _logger.info(log_msg + "Ranks: Simple {} Greedy {} Heuristic {}".format(*ranks))

    else:
        log_msg += "no buffered packets"
        _logger.warning(log_msg)


def calculate_aod(rnd="i", _logger=None):
    aods = []
    for i, data in enumerate(simple_data_out):
        d_i = [data[x:x+PACKET_SIZE] for x in range(0, len(data), PACKET_SIZE)]
        aod = [1 if din == dout else 0 for din, dout in zip(data_in, d_i)]
        s = "{} " * len(aod)
        if _logger:
            _logger.info(
                ("node {:2},kp{:2},AoD {:2}/{} [" + s + "]").format(
                    i, rnd, sum(aod), len(aod), *aod)
            )
        aods.append(sum(aod)/len(aod) * 100)
    return aods


def get_ranks(index):
    s_decoder, g_decoder, h_decoder = nodes[index]
    s_decoder.update_symbol_status()
    g_decoder.update_symbol_status()
    h_decoder.update_symbol_status()
    ranks = (
        s_decoder.rank(),
        g_decoder.rank(),
        h_decoder.rank()       
    )
    return ranks
