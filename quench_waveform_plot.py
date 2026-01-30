import matplotlib.pyplot as plt
import numpy as np
import re # importing regular expression module

filename = 'ACCL_L3B_3180_20220630_164905_QUENCH.txt'   # imput data file
timestamp = '2022-06-30_16:49:05.440831'                # waveform timestamp 

# PV or fault string to search for and precise timestamp of the waveform
cavity_faultname = 'ACCL:L3B:3180:CAV:FLTAWF'    # cavity details 
forward_pow = 'ACCL:L3B:3180:FWD:FLTAWF'         # forward power details
reverse_pow = 'ACCL:L3B:3180:REV:FLTAWF'         # reverse power details
decay_ref = 'ACCL:L3B:3180:DECAYREFWF'           # decay reference details

# read the entire file into memory
with open(filename,'r') as file:
    lines = file.readlines()

def extract_data(lines, faultname, timestamp):
    # initilization: find the section of interest based on keywords 
    search_string = f"{faultname} {timestamp}"
    data_lines = []

    # flag to indicate that we are in the right section
    in_section = False

    # loop through lines to find the section matching the fault and timestamp
    for i, line in enumerate(lines):
        if search_string in line:
            in_section = True
            print(f"Found section start at line {i}")
        elif in_section and faultname not in line:
            print(f"Found section end at line {i}")
            break
        if in_section:
            data_part = line.split(timestamp, 1)[-1].strip()    # removes the timestamp and label
            data_lines.append(data_part)                        # extracting data lines

    # extracting numeric data from each line using regular expressions
    data = []
    for line in data_lines:
        # using regex to find all numbers in the line 
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line) # matches integers or floats
        if numbers:
            # convering the first number found to float and add it to data list
            # data.append([float(num) for num in numbers])  # add all numbers in the line to data
            data.extend([float(num) for num in numbers])    # flattening the data list (extend vs append)
        else:
            print(f"Skipping line with no numeric data: {line}")

    # diagnostic check for data content and confirming proper structure
    print("\n== Data Diagnostics ===")
    print(f"Type of 'data': {type(data)}")
    if len(data) > 0:
        print(f"Type of first element: {type(data[0])}")
        print(f"Number of data points: {len(data)}")
        print(f"First 10 values: {data[:10]}")
    else:
        print("No valid numberic data extracted")
    print("=======================\n")

    print(f"Extracted {len(data)} points from {faultname}\n")
    return data

# extract each waveform
cavity_data = extract_data(lines, cavity_faultname, timestamp)
forward_data = extract_data(lines, forward_pow, timestamp)
reverse_data = extract_data(lines, reverse_pow, timestamp)
decay_data = extract_data(lines, decay_ref, timestamp)

# finding the lengths of all waveforms
lengths = {
    'cavity': len(cavity_data),
    'forward': len(forward_data),
    'reverse': len(reverse_data),
    'decay': len(decay_data)
}

for name, length in lengths.items():
    print(f"{name} data points: {length}")

# finding the minimum length 
min_length = min(lengths.values())
print(f"\nMinimum number of data points across all waveforms: {min_length}")

# trimming decay_data to cavity length because they must be the same length in order to plot
cavity_data = cavity_data[:min_length]
forward_data = forward_data[:min_length]
reverse_data = reverse_data[:min_length]
decay_data = decay_data[:min_length]

# plotting them all on the same axes
time_range = list(range(min_length))

# plot setup
plt.figure(figsize=(14,6))
plt.plot(time_range, cavity_data, label = "Cavity", color = 'blue')
plt.plot(time_range, forward_data, label = "Forward Power", color = 'green')
plt.plot(time_range, reverse_data, label = "Reverse Power", color = 'red')
plt.scatter(time_range, decay_data, label = "Normal Cavity Decay Reference", color = 'cyan', s=1, marker='o')

# plot formatting
plt.xlabel('Number of Data Points')
plt.ylabel('MV')
plt.title(f'Quench Waveforms - {cavity_faultname} {timestamp}')
plt.legend()
plt.grid(True)
plt.tight_layout()

# save the plot to file
plot_filename = f"combined_{filename.replace('.txt',"")}.png"
plt.savefig(plot_filename)
print(f"Plot saved as: {plot_filename}")

# show plot 
plt.show()