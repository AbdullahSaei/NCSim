#! /usr/bin/env python
# encoding: utf-8

# Cooperative data exchange network
import json
import numpy as np
import string
import typing
import kodo

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
simple_sparse = [0.5, 0.5]

# Pseudo random seed
np.random.seed(SEED_VALUE)

# Global scope Create list of encoder and decoder triples
nodes: typing.List[typing.List[kodo.RLNCDecoder]] = []
data_in: typing.List[bytearray] = []
simple_data_out: typing.List[bytearray] = []
greedy_data_out: typing.List[bytearray] = []
heuristic_data_out: typing.List[bytearray] = []

# Master encoder
master_data_in: bytearray
master_encoder = kodo.RLNCEncoder(field, symbols, symbol_size)


def kodo_init():
    # Create list of encoder and decoder triples
    global nodes
    global data_in
    global simple_data_out
    global greedy_data_out
    global heuristic_data_out

    nodes = []
    data_in = []
    simple_data_out = []
    greedy_data_out = []
    heuristic_data_out = []

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
    _alphabet_list = list(string.ascii_uppercase + string.digits)

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
    s_decoder, g_decoder, h_decoder = nodes[node.node_id]

    # Generate random coefficients
    random_code_vector = np.random.randint(1, field_max, size=NUM_OF_NODES)

    # produce simple packet to broadcast
    s_pack_coe = [np.random.choice([random_code_vector[sym], 0], p=simple_sparse) if s_decoder.is_symbol_pivot(
        sym) else 0 for sym in range(NUM_OF_NODES)]
    s_coe = bytearray(s_pack_coe)
    s_pack_msg = master_encoder.produce_symbol(s_coe)
    s_pack = {
        'msg': s_pack_msg,
        'coe': s_coe
    }
    s_overhead = np.count_nonzero(s_pack_coe) * 8

    # produce greedy packet to broadcast
    g_pack_coe = [random_code_vector[sym] if g_decoder.is_symbol_pivot(
        sym) else 0 for sym in range(NUM_OF_NODES)]
    g_coe = bytearray(g_pack_coe)
    g_pack_msg = master_encoder.produce_symbol(g_coe)
    g_pack = {
        'msg': g_pack_msg,
        'coe': g_coe
    }
    g_overhead = np.count_nonzero(g_pack_coe) * 8

    all_nei_done = True
    for ngbr in neighbours:
        _, _, ngbr_h_decoder = nodes[ngbr.node_id]
        all_nei_done = all_nei_done and ngbr_h_decoder.is_complete()

    # if all neighbors done, shut down
    if all_nei_done:
        node.node_sleep()
        h_pack = None
        h_overhead = 0
    else:
        h_pack_coe = [random_code_vector[sym] if h_decoder.is_symbol_pivot(
            sym) else 0 for sym in range(NUM_OF_NODES)]
        h_coe = bytearray(h_pack_coe)
        h_pack_msg = master_encoder.produce_symbol(h_coe)
        h_pack = {
            'msg': h_pack_msg,
            'coe': h_coe
        }
        # nonzeros of Coding vector + src ID + done 1 bit
        h_overhead = np.count_nonzero(h_pack_coe) * 8 + 8 + 1

        # 10 Nodes * 8 bits coe = 80

    # combine all packs
    pack = (s_pack, g_pack, h_pack)

    # update overhead counters
    node.add_to_overhead([s_overhead, g_overhead, h_overhead])

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

    # consume received messages
    if len(packets) > 0:
        for _, pkt in packets:
            s_pkt, g_pkt, h_pkt = pkt

            # heuristic decoder
            if h_pkt:
                h_pack, h_coe = h_pkt.values()
                h_decoder.consume_symbol(h_pack, h_coe)

            # greedy decoder
            if g_pkt:
                g_pack, g_coe = g_pkt.values()
                g_decoder.consume_symbol(g_pack, g_coe)

            # simple decoder
            if s_pkt:
                s_pack, s_coe = s_pkt.values()
                s_decoder.consume_symbol(s_pack, s_coe)

        ranks = get_ranks(node.node_id)
        _logger.info(
            log_msg + "Ranks: Simple {} Greedy {} Heuristic {}".format(*ranks))

    # warn if no messages at all
    else:
        log_msg += "no buffered packets"
        _logger.warning(log_msg)


def calculate_aod(rnd="i", _logger=None):
    s_aods = []
    g_aods = []
    h_aods = []

    for i, s_data, g_data, h_data in zip(range(NUM_OF_NODES),
                                         simple_data_out, greedy_data_out, heuristic_data_out):
        s_d_i = [s_data[x:x+PACKET_SIZE]
                 for x in range(0, len(s_data), PACKET_SIZE)]
        s_aod = [1 if din == dout else 0 for din, dout in zip(data_in, s_d_i)]

        g_d_i = [g_data[x:x+PACKET_SIZE]
                 for x in range(0, len(g_data), PACKET_SIZE)]
        g_aod = [1 if din == dout else 0 for din, dout in zip(data_in, g_d_i)]

        h_d_i = [h_data[x:x+PACKET_SIZE]
                 for x in range(0, len(h_data), PACKET_SIZE)]
        h_aod = [1 if din == dout else 0 for din, dout in zip(data_in, h_d_i)]

        s = "{} " * len(s_aod)
        if _logger:
            _logger.info(
                ("node {:2},kp{:2},S_AoD {:2}/{} [" + s + "]").format(
                    i, rnd, sum(s_aod), len(s_aod), *s_aod)
            )
            _logger.info(
                ("node {:2},kp{:2},G_AoD {:2}/{} [" + s + "]").format(
                    i, rnd, sum(g_aod), len(g_aod), *g_aod)
            )
            _logger.info(
                ("node {:2},kp{:2},H_AoD {:2}/{} [" + s + "]").format(
                    i, rnd, sum(h_aod), len(h_aod), *h_aod)
            )
        s_aods.append(sum(s_aod)/len(s_aod) * 100)
        g_aods.append(sum(g_aod)/len(g_aod) * 100)
        h_aods.append(sum(h_aod)/len(h_aod) * 100)

    return s_aods, g_aods, h_aods


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
