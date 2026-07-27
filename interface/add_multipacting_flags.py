import h5py
import pandas as pd
import numpy as np

def add_multipacting_flags(file_path, multipacting_file, flag_attr='Multipacting'):
    dataframe = load_csv(multipacting_file)

    multipacting_keys = set()
    for _, row in dataframe.iterrows():
        key =(
            str(row['cm']).strip(),
            str(row['cav']).strip(),
            f"{int(row['year']):04d}",
            f"{int(row['month']):02d}",
            f"{int(row['day']):02d}",
        )
        multipacting_keys.add(key)

    matched = 0
    total = 0

    with h5py.File(file_path, 'a') as f :
        event_paths = []
        f.visit(lambda name: event_paths.append(name))

        for path in event_paths:
            parts = path.split('/')

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
    h5_file_path = '/Users/nelian/slacNNN/data/quench_data_L0.h5' # Your h5 file path
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

