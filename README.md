# LCLS-SC Quench Analysis Project

This project contains Python scripts for analyzing and visualizing SRF cavity quench data from the LCLS-SC.

### Prerequisites

- You must have your .h5 quench data files.
- Conda install is recommended.

---

### Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/slaclab/slacq.git
    cd slacq
    ```

2.  **Set up the Directory Structure:**
    ```
    slacq/
    ├── classification/     
    ├── config/
    ├── data/
    ├── images/
    ├── interface/   
    ├── plotter/           
    └── utils/
    ```
- Create a data directory and place your .h5 files in it.
- All csv files containing multipacting dates are located in config directory.
- The images directory is where output plots will be automatically saved.

3.  **Create and Activate the Conda Environment:**
    ```bash
    conda create -n YOUR_ENV_NAME python=3.10
    ```
    ```bash
    conda activate YOUR_ENV_NAME
    ```

4.  **Install Required Python Packages:**
    ```bash
    pip install numpy pandas h5py matplotlib scipy streamlit plotly
    ```
    
### Development Tools
This project uses Ruff for auto-formatting and mypy for strict type checking.

---

## Usage
    
1.  **Run the script:**
    ```bash
    python generate_plots.py
    ```
    
2.  **Find the Output:**
    The generated plot files will be saved in the images folder.
