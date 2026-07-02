# LCLS-SC Quench Analysis Project

This project contains Python scripts for analyzing and visualizing SRF cavity quench data from the LCLS-SC.

### Prerequisites

*   Conda must be installed.
*   You must have your raw .h5 quench data files.

---

### Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone URL_TO_THIS_GITHUB_REPO
    cd SLACPYTHON
    ```

2.  **Set up the Directory Structure:**
    ```
    SLACPYTHON/
    ├── config/
    ├── data/
    ├── images/
    └── src/
    ```
    
    *   Place all your .h5 data files into the data folder.
    *   The images folder is where output plots will be automatically saved.
    *   All python files are located in src folder.
    *   All csv files are located in config folder.

3.  **Create and Activate the Conda Environment:**
    ```bash
    conda create -n YOUR_ENV_NAME python=3.10
    ```
    ```bash
    conda activate YOUR_ENV_NAME
    ```

4.  **Install Required Python Packages:**
    ```bash
    pip install numpy pandas h5py matplotlib scipy
    ```
    
### Development Tools
This project uses Ruff for auto-formatting and mypy for strict type checking.

---

## Usage

1.  **Navigate into the script directory:**
    ```bash
    cd src
    ```
    
2.  **Run the script:**
    ```bash
    python YOUR_PYTHON_SCRIPT.py
    ```
    
3.  **Find the Output:**
    The generated plot files will be saved in the images folder.
