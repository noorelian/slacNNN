import os

HERE = os.path.dirname(os.path.abspath(__file__))

H5_GLOB = os.path.join(HERE, "..", "data", "quench_data_L*.h5")
IMG_DIR = os.path.join(HERE, "..", "images")

os.makedirs(IMG_DIR, exist_ok=True)
