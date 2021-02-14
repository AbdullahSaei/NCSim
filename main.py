from ncsim import NCSim
from node import Node
import kodo
import os

# Choose the finite field, the number of symbols (i.e. generation size)
# and the symbol size in bytes
field = kodo.field.binary8
symbols = 5
symbol_size = 160

# Create an encoder and a decoder
encoder = kodo.RLNCEncoder(field, symbols, symbol_size)
decoder = kodo.RLNCDecoder(field, symbols, symbol_size)

# Generate some random data to encode. We create a bytearray of the same
# size as the encoder's block size and assign it to the encoder.
# This bytearray must not go out of scope while the encoder exists!
data_in = bytearray(os.urandom(encoder.block_size()))
encoder.set_symbols_storage(data_in)

# Define the data_out bytearray where the symbols should be decoded
# This bytearray must not go out of scope while the encoder exists!
data_out = bytearray(decoder.block_size())
decoder.set_symbols_storage(data_out)

sim = NCSim()


def main():
    sim.discover_network()
    sim.run()
    print("Done!")
    
    sim.mainloop()


if __name__ == '__main__':
    main()

