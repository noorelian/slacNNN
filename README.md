# LCLS-SC Quench Analysis Project

This project contains Python scripts for analyzing and visualizing SRF cavity quench data from the LCLS-SC.

### Prerequisites

*   Conda must be installed.
*   You must have your raw .h5 quench data files.

### Installation & Setup

1.  **Set up the Directory Structure:**
    ```
    SLACPYTHON/
    ├── config/
    ├── data/
    ├── images/
    ├── src/
    ```
    *   Place all your .h5 data files into the data folder.
    *   The images folder is where output plots will be automatically saved.
    *   All python files are located in src folder.
    *   All csv files are located in config folder.

2.  **Create and Activate the Conda Environment:**
    *   conda create -n `<your-env-name>` python=3.10
    *   conda activate `<your-env-name>`

3.  **Install Required Python Packages:**
    *   With the `<your-env-name>` environment active, run the following command: 
    ```bash
    pip install numpy pandas h5py matplotlib scipy
    
### Development Tools
This project uses Ruff for auto-formatting and mypy for strict type checking.

### Usage

1.  **Navigate into the script directory:**
    *   cd src

2.  **Run the script:**
    *   python `<python-script-file>`.py
    
3.  **Find the Output:**
    *   The generated plot files will be saved in the images folder.
