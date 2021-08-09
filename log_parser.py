"""
Parsing the csv from NCSim module
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
# import re

LOG_PATH = "logs/"
LOG_FILE = "random_14_Simple_WSN_3"


def preprocess_at_tx():
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
    
    df_at_tx_ranks = df_at_tx_less.drop(df_at_tx.filter(regex='AoD').columns, axis=1)
    df_at_tx_aods = df_at_tx_less.drop(df_at_tx.filter(regex='rank').columns, axis=1)
    df_ranks = df_at_tx_ranks.melt('Generation', 
        var_name='Algorithm', value_name='Ranks')
    df_aods = df_at_tx_aods.melt('Generation', 
    var_name='Algorithm', value_name='Availability of Data percentage')
    
    return df_aods, df_ranks


def plots_at_tx():
    pass

def main():
    pass

def preprocessing(data_frame) -> pd.DataFrame:
    """
    Prepare data for analysis
    """
    # wide to long df_at_tx
    # df_ready = pd.wide_to_long(data_frame)
    df_ready = data_frame
    return df_ready


if __name__ == '__main__':

    # load the file
    df_at_tx = preprocessing(pd.read_csv(LOG_PATH + LOG_FILE + "_at_tx.csv"))
    df_at_done = pd.read_csv(LOG_PATH + LOG_FILE + "_at_done.csv")

    # visualize data
    print(df_at_tx)
    print(df_at_tx.info())
    print(df_at_tx.head())
    print(df_at_tx.sample(3))

    print(df_at_done)
    print(df_at_done.info())
    print(df_at_done.head())
    print(df_at_done.sample(3))
    
    df_aods, df_ranks = preprocess_at_tx()

    main()
