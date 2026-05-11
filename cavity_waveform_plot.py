import matplotlib.pyplot as plt
import numpy as np
import re # importing regular expression module

# changes with each file
filename = 'ACCL_L3B_3180_20220630_164905_QUENCH.txt'   # imput data file

# cavity details
faultname = 'ACCL:L3B:3180:CAV:FLTAWF'      # PV or fault string to search for 
timestamp = '2022-06-30_16:49:05.440831'    # precise timestamp of the waveform

# read the entire file into memory
with open(filename,'r') as file:
    lines = file.readlines()

# initilization: find the section of interest based on keywords 
start_line = None 
end_line = None
data_lines = []

# flag to indicate that we are in the right section
in_section = False

# building the string to identify the start of waveform section
search_string = f"{faultname} {timestamp}"

# loop through lines to find the section matching the fault and timestamp
for i, line in enumerate(lines):
    if search_string in line:
        start_line = i
        in_section = True
        print(f"Found section start at line {i}")
    elif in_section and search_string not in line:
        end_line = i
        print(f"Found section end at line {i}")
        break
    if in_section:
        # extracting just the part of the line that comes after the timestamp
        data_part = line.split(timestamp, 1)[-1]    # removes the timestamp and label
        data_lines.append(data_part.strip())        # extracting data lines

# extracting numeric data from each line using regular expressions
data = []
for line in data_lines:
    # using regex to find all numbers in the line
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line) #matches integers or floats
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

# plotting the data if it is valid
if data: 
    # time axis assuming uniform spacing
    time = list(range(len(data)))
    # time = np.linspace(-0.04, 0.08, len(data))

    # validate the lengths match
    print(f"Length of time axis: {len(time)}")
    print(f"Length of data: {len(data)}")
    if len(time) != len(data):
        print("Time and data lengths do not match. Skipping plot.")
    else:
        # confirm the min and max values of the data
        data_min = np.min(data)
        data_max = np.max(data)
        print(f"Data range: min = {data_min}, max = {data_max}")

        # plotting the data
        plt.figure(figsize=(14,6))
        plt.plot(time, data, label="Cavity", color='blue')
        plt.xlabel('Number of Data Points')
        plt.ylabel('MV')
        plt.title(f'Quench Waveform {faultname} {timestamp}')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        # saving the figure
        safe_faultname = search_string.replace(":", "_")    # search_string = f"{faultname} {timestamp}"
        plot_filename = f"cavity_{filename.replace('.txt','')}.png"
        plt.savefig(plot_filename)
        print(f"Plot saved as: {plot_filename}")

        plt.show()
else:
    print("No data was extracted, no plot will be displayed.")