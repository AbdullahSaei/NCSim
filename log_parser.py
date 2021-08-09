# import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
# import re

LOG_PATH = "logs/"
LOG_FILE = "random_14_Simple_WSN_3"

# load the file
df_at_tx = pd.read_csv(LOG_PATH + LOG_FILE + "_at_tx.csv")
df_at_done = pd.read_csv(LOG_PATH + LOG_FILE + "_at_done.csv")

# visualize data
print(df_at_tx)
print(df_at_tx.info())
print(df_at_tx.head())
print(df_at_tx.sample(5))

print(df_at_done)
print(df_at_done.info())
print(df_at_done.head())
print(df_at_done.sample(5))

def main():
    pass


if __name__ == '__main__':
    main()
