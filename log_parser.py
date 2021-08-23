# %%
"""
Parsing the csv from NCSim module
"""

# TODO:
# - add grid
# - normalise rank

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use('seaborn-deep')

LOG_PATH = "logs/"
LOG_FILES = ["random_5_Simple_WSN_17", "random_10_Simple_WSN_13", "random_20_Simple_WSN_3",
             "random_30_Simple_WSN_13", "random_40_Simple_WSN_17", "random_50_Simple_WSN_17"]
LOG_FILE = "random_5_Simple_WSN_17"


def prepare_at_tx():
    """
    Prepares df_at_tx dataframe

    RETURN
    ------
    df_aods, df_ranks
    """
    rnd_num = np.max(df_at_tx['Round'])
    nodes_num = np.max(df_at_tx['Node'])
    gen_num = np.max(df_at_tx['Generation'])

    df_at_tx_less = df_at_tx.drop(['Round', 'Node'], axis=1)

    df_at_tx_ranks = df_at_tx_less.drop(
        df_at_tx.filter(regex='AoD').columns, axis=1)
    df_at_tx_aods = df_at_tx_less.drop(
        df_at_tx.filter(regex='rank').columns, axis=1)
    df_ranks = df_at_tx_ranks.melt('Generation',
                                   var_name='Algorithm', value_name='Ranks')
    df_aods = df_at_tx_aods.melt('Generation',
                                 var_name='Algorithm', value_name='Availability of Data percentage')

    return df_aods, df_ranks, list(map(int, [rnd_num, nodes_num, gen_num]))


def prepare_at_done(df_at_done):
    """
    Prepares df_at_done dataframe

    RETURN
    ------
    df_aods, df_ranks
    """

    gens = {g for g in df_at_done['Generation']}
    algs = {alg for alg in df_at_done['Algorithm']}
    at_done_means = []
    at_done_maxes = []
    for g in gens:
        for alg in algs:
            at_done_means.append(df_at_done.query(
                f"Generation == {g} and Algorithm == '{alg}'").mean())
            at_done_maxes.append(df_at_done.query(
                f"Generation == {g} and Algorithm == '{alg}'").max())

    df_at_done_maxes = pd.concat(at_done_maxes, axis=1).T
    df_at_done_means = pd.concat(at_done_means, axis=1).T
    df_at_done_means['Algorithm'] = df_at_done_maxes['Algorithm']

    return df_at_done_means, df_at_done_maxes


def plots_at_tx(rnd_num, nodes_num):
    plt.figure()
    sns.boxplot(data=df_aods, x="Availability of Data percentage",
                y="Algorithm", notch=True).set_title(f"AoD at tx = {rnd_num} of {nodes_num} nodes")
    plt.grid()
    plt.figure()
    sns.boxplot(data=df_ranks, x="Ranks",
                y="Algorithm", notch=True).set_title(f"Ranks at tx = {rnd_num} of {nodes_num} nodes")
    plt.grid()


def plots_at_done(rnd_num, nodes_num):
    plt.figure()
    sns.boxplot(data=df_done_maxes, x="Round", y="Algorithm", order=['Simple', 'Greedy', 'Heuristic'], notch=True).set_title(
        f"Max num of rounds when done {nodes_num} nodes")
    add_v_line(rnd_num)
    plt.grid()
    plt.figure()
    sns.boxplot(data=df_done_means, x="Round", y="Algorithm", order=['Simple', 'Greedy', 'Heuristic'], notch=True).set_title(
        f"Mean num of rounds when done {nodes_num} nodes")
    add_v_line(rnd_num)
    plt.grid()


def add_v_line(pos):
    plt.axvline(pos, ls='--', color="red",)
    plt.text(pos + 0.1, 0.1, f"tx = {pos}", color='tab:red',
             rotation=270)


def add_h_line(pos):
    plt.axhline(pos, ls='--', color="red",)
    plt.text(0, pos+1, f"tx = {pos}", color='tab:red')


def main(rnd_num=0, nodes_num=0, _=0):
    plots_at_tx(rnd_num, nodes_num)
    plots_at_done(rnd_num, nodes_num)
    plot_trends()


def plot_trends():
    plt.figure()
    sns.boxplot(data=df_master_maxes, x="Nodes", y="Rounds", hue="Algorithm", hue_order=['Simple', 'Greedy', 'Heuristic'], notch=True, showfliers=False).set_title(
        f"Max num of rounds vs num of nodes")
    add_h_line(25)
    plt.grid()
    plt.figure()
    sns.boxplot(data=df_master_means, x="Nodes", y="Rounds", hue="Algorithm",hue_order=['Simple', 'Greedy', 'Heuristic'], notch=True, showfliers=False).set_title(
        f"Mean num of rounds vs num of nodes")
    add_h_line(25)
    plt.grid()


def prepare_trend():
    maxes_list_dicts = []
    means_list_dicts = []
    for log_file in LOG_FILES:
        df = pd.read_csv(LOG_PATH + log_file + "_at_done.csv")
        num_nodes = int(log_file.split("_")[1])
        df_maxes, df_means = prepare_at_done(df)
        list_dicts_maxes = [{
            "Nodes": num_nodes,
            "Rounds": rnd,
            "Algorithm": alg
        } for rnd, alg in zip(df_maxes['Round'], df_maxes['Algorithm'])]

        list_dicts_means = [{
            "Nodes": num_nodes,
            "Rounds": rnd,
            "Algorithm": alg
        } for rnd, alg in zip(df_means['Round'], df_means['Algorithm'])]

        maxes_list_dicts.append(list_dicts_maxes)
        means_list_dicts.append(list_dicts_means)

    df_master_maxes = pd.DataFrame()
    for l in maxes_list_dicts:
        df_master_maxes = df_master_maxes.append(
            pd.DataFrame(l), ignore_index=True)

    df_master_means = pd.DataFrame()
    for l in means_list_dicts:
        df_master_means = df_master_means.append(
            pd.DataFrame(l), ignore_index=True)

    return df_master_maxes, df_master_means


if __name__ == '__main__':

    # load the file
    df_at_tx = pd.read_csv(LOG_PATH + LOG_FILE + "_at_tx.csv")
    df_at_done = pd.read_csv(LOG_PATH + LOG_FILE + "_at_done.csv")

    # visualize data
    print(df_at_tx.info())
    print(df_at_tx.head())
    # print(df_at_tx.sample(3))

    print(df_at_done.info())
    print(df_at_done.head())
    # print(df_at_done.sample(3))

    df_aods, df_ranks, configs = prepare_at_tx()
    df_done_means, df_done_maxes = prepare_at_done(df_at_done)

    df_master_means, df_master_maxes = prepare_trend()

    main(*configs)

# %%
