import h5py
import pandas as pd
import numpy as np

def add_multipacting_flags(file_path, multipacting_file, flag_attr='Multipacting'):
    """
    Add a multipacting flag to each events in the h5 file
    - The function matches the event name in the h5 file with the data in the csv file 
    - Each event in the h5 file gets a boolean attribute so either true or false 
    - Match only after ignoring the time (HHMMSS) in the h5 file since the events are saved with no time records
    """
    dataframe = load_csv(multipacting_file) # Load the csv file into a dataframe 

    # build a set of keys to identify each multipacting event
    multipacting_keys = set()
    for _, row in dataframe.iterrows():
        key =(
            str(row['cm']).strip(),     # cryomodule as a string
            str(row['cav']).strip(),    # cavity as a string 
            f"{int(row['year']):04d}",  # year : 4 digits, e.g. 2025
            f"{int(row['month']):02d}", # month : 2 didgits, e.g. 07
            f"{int(row['day']):02d}",   # day : 2 digits, e.g. 19
        )
        multipacting_keys.add(key)

    matched = 0     # flagged events 
    total = 0       # valid processed events 

    # read the h5 file 
    with h5py.File(file_path, 'a') as f :
        event_paths = []
        f.visit(lambda name: event_paths.append(name))

        # Loop over each path 
        for path in event_paths:
            parts = path.split('/')     # split like this ['CM01', 'CAV1', '20240116_103022']

            # A real event has exactly 3 parts: CM / CAV / timestamp
            # Skip anything else (like top-level CM or CAV groups)
            if len(parts) != 3:
                continue

            cm, cav, timestamp = parts

            if '_' not in timestamp or len(timestamp.split('_')[0]) != 8:
                continue

            date_part = timestamp.split('_')[0]
            year = date_part[0:4]
            month = date_part[4:6]
            day = date_part[6:8]

            event_key = (cm.strip(), cav.strip(), year, month, day)
            total += 1

            is_multipacting = event_key in multipacting_keys
            f[path].attrs[flag_attr] = bool(is_multipacting)

            if is_multipacting:
                matched += 1

def load_csv(path):
    """
    load the csv or txt files into pandas dataframe 

    - csv files are read direclty 
    - txt files are comma-seperated first, if that fails it fall back to whitespace-seperated 
    - Otherwise, it throws an error 
    """
    if path.endswith('.csv'):
        return pd.read_csv(path)
    elif path.endswith('.txt'):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.read_csv(path, delim_whitespace=True)
    else:
        raise ValueError(f"Error with file type: {path}")


if __name__ == '__main__':
    h5_file_path = '/Users/nelian/slacNNN/data/quench_data_L1.h5' # Your h5 file path
    csv_file = '/Users/nelian/slacNNN/config/all_mp_dates.csv' # The mp file 

    add_multipacting_flags(file_path=h5_file_path, multipacting_file=csv_file)

    with h5py.File(h5_file_path, 'r') as f:
        event_paths = []
        f.visit(lambda name: event_paths.append(name))

        for path in event_paths:
            if len(path.split('/')) != 3:
                continue
            obj = f[path]
            print(path, ":", dict(obj.attrs))

