import os
import zlib
import numpy as np
from PIL import Image

def decompress_czi(input_file, output_dir):
    # Read the compressed file
    with open(input_file, 'rb') as f:
        compressed_data = f.read()
    
    # Split the compressed data into individual image slices
    slices = []
    start = 0
    while start < len(compressed_data):
        try:
            decompressed_slice = zlib.decompress(compressed_data[start:])
            slices.append(decompressed_slice)
            start += len(compressed_data[start:])
        except zlib.error:
            decompressed_slice = zlib.decompress(compressed_data[start:len(compressed_data)])
            slices.append(decompressed_slice)
            break

    # Reconstruct the original image data
    # Here we're not assuming any fixed dimensions. We'll determine them dynamically
    images = []
    for i, slice in enumerate(slices):
        # Convert bytes to numpy array, assuming uint8 data
        slice_data = np.frombuffer(slice, dtype=np.uint8)
        
        # # Estimate dimensions. Here we're assuming square images for simplicity
        side_length = int(np.sqrt(len(slice_data)))
        # if side_length * side_length == len(slice_data):  # Check if it's a perfect square
        #     img = slice_data.reshape((side_length, side_length))
        # else:
        #     # If not square, we can either skip this image or try another method to determine size
        #     print(f"Warning: Slice {i} does not form a square image. Skipping.")
        #     continue
        img = slice_data.reshape((side_length, side_length))
        images.append(img)
        
        # Save each slice as an image for verification
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        img_pil = Image.fromarray(img)
        img_pil.save(os.path.join(output_dir, f"slice_{i}.png"))
# Example usage
input_compressed = '/Users/silvioo/Downloads/compressed_file.czi'
output_dir = '/Users/silvioo/Downloads/decompressed_images.czi'
decompress_czi(input_compressed, output_dir)