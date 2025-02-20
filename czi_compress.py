#!/usr/bin/env python
import argparse
import json
import struct
import zlib
import numpy as np
from czifile import CziFile
import sys 

HEADER_LEN_SIZE = 4  # number of bytes to store header length
def compress_file(input_file, output_file):
    # Validate that the input file is a valid CZI file.
    try:
        with CziFile(input_file) as czi:
            # You can optionally print some info from the CZI file here.
            print("Valid CZI file detected.")
    except Exception as e:
        print(f"Error: {input_file} is not a valid CZI file. {e}")
        return

    # Read the entire file as binary.
    with open(input_file, "rb") as f:
        file_data = f.read()
    
    # Compress the full file content.
    compressed_data = zlib.compress(file_data)
    
    with open(output_file, "wb") as f:
        f.write(compressed_data)
    
    print(f"Compressed '{input_file}' to '{output_file}'.")


def decompress_file(input_file, output_file):
    # Read the compressed data.
    with open(input_file, "rb") as f:
        compressed_data = f.read()
    
    # Decompress the data.
    try:
        file_data = zlib.decompress(compressed_data)
    except zlib.error as e:
        print(f"Decompression error: {e}")
        return

    # Write the decompressed bytes to output.
    with open(output_file, "wb") as f:
        f.write(file_data)
    
    print(f"Decompressed '{input_file}' to '{output_file}'.")

    
def main(input_file, output_file, action):
    if action == "compress":
        compress_file(input_file, output_file)
    elif action == "decompress":
        decompress_file(input_file, output_file)
    else:
        print("Invalid action. Use 'compress' or 'decompress'.")
        sys.exit(1)

# Example usage
input = '/Users/silvioo/Downloads/810325307087_compressed_v3.czi'
output= '/Users/silvioo/Downloads/810325307087_decompressed_v3.czi'
action = "decompress"


if __name__ == "__main__":
    main(input, output, action)
