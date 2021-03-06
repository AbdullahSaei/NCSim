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
PACKET_SIZE = int(CFG_PARAM.get("packet_size_bytes", 10)) + 6
# how many bits identifying each node
FINITE_FIELD = CFG_PARAM.get("fifi", "binary")

# fifi translation
fifi = {
    "binary16": kodo.field.binary16,
    "binary8": kodo.field.binary8,
    "binary4": kodo.field.binary4,
    "binary": kodo.field.binary,
}

# Configure kodo parameters
field = fifi.get(FINITE_FIELD, "binary")
symbols = NUM_OF_NODES
symbol_size = PACKET_SIZE

# We want to follow the decoding process step-by-step


def callback_function(zone, message):
    if zone in ["decoder_state", "symbol_coefficients_before_consume_symbol"]:
        print("{}:".format(zone))
        print(message)


# Create list of encoder and decoder triples
nodes = []
data_in = []
data_out = []
for i in range(NUM_OF_NODES):
    # init encoder
    encoder = kodo.RLNCEncoder(field, symbols, symbol_size)
    encoder.set_seed(SEED_VALUE)

    # init decoder
    decoder = kodo.RLNCDecoder(field, symbols, symbol_size)
    decoder.set_seed(SEED_VALUE)
    decoder.set_log_callback(callback_function)
    nodes.append([i, encoder, decoder])


def generate_data():
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
        pack = encoder.produce_systematic_symbol(i)
        decoder.consume_systematic_symbol(pack, i)


def node_broadcast(node, neighbours, logger):
    # choose channel
    freq = np.random.choice([*range(node.ch_num)])
    time = np.random.choice([*range(node.ts_num)])
    node.sending_channel = (freq, time)

    # get kodo encoder and decoder
    i, encoder, decoder = nodes[node.node_id]

    # produce packet to broadcast
    pack = decoder.produce_payload()

    # log data
    # log message and channel
    logger.info(
        "Node {:2},tx,msg {},broadcast_to {}".format(
            i, pack, len(neighbours)))
            
    for n in neighbours:
        # get kodo encoder and decoder of the neighbor
        n_i, n_encoder, n_decoder = nodes[n.node_id]
        print(f"Node {i} sending to {n_i}")
        n_decoder.consume_payload(pack)
        n.access_rx_buffer(i, pack, node.sending_channel)
        print("Decoder rank: {}/{}\n".format(decoder.rank(), symbols))

def nodes_receive(node, neighbours, logger):
    i, encoder, decoder = nodes[node.node_id]
    # check if data in buffer
    log_msg = "Node {:2},rx,".format(i)
    if len(neighbours) > 0:
        for n in neighbours:
            n_i, n_encoder, n_decoder = nodes[n.node_id]
        log_msg += "decoded/Missing/total {}/{}/{}".format(
        decoder.symbols_decoded(),
        decoder.symbols_missing(),
        decoder.symbols())
        logger.info(log_msg)
    else:
        log_msg += "no buffered packets"
        logger.warning(log_msg)
