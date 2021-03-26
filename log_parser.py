import numpy as np
import pandas as pd
import re

LOG_PATH = "logs/"
LOG_FILE = "star_17_Simple_WSN_3.csv"


# load the file
df = pd.read_csv(LOG_PATH + LOG_FILE,
                names=[
                    "timestamp",
                    "time_ns",
                    "function",
                    "node",
                    "mode",
                    "data"]
                )

# convert Time to datetime for easier work
print(df)
print(df.info())
print(df.head())
print(df.sample(5))

def main():
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(df.info())

if __name__ == '__main__':
    main()