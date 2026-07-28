# Quench Labeling Interface

A Streamlit web app for viewing and labeling cavity quench waveforms stored in HDF5 files.

---

## What You Need Before Starting

- **Python 3.12 or newer** installed on your computer
- **Git** installed (to clone the repository)
- An **HDF5 (`.h5`) data file** containing quench events *(not included in this repo)*

To check if you have Python and Git:

```bash
python --version
git --version
```

---

## Step 1: Clone the Repository

```bash
git clone <repo-url>    # replace with the actual repository URL
```


## Step 2: Create a conda Environment 

```bash
conda create -n quench-labeler python=3.12
```

## Step 3: Activate the conda Environment


```bash
conda activate quench-labeler
```

## Step 4: Install Dependencies

```bash
conda install streamlit plotly h5py numpy pandas
```

## Step 5: Get a Data File

The app needs an HDF5 (`.h5`) quench data file, which is not included in the repository. 

Example path:

```bash
/Users/yourname/data/quench_data_L1.h5
```

## Step 6: Run the App

From the repository root, run:

```bash
streamlit run interface/app.py
```


## Important:
> - Use `streamlit run` not `python interface/app.py`.

The app opens in your browser automatically. If it doesn't, copy that **URL** from the terminal into your browser.

## Step 7: Use the App

1. Enter the full path to your `.h5` file in the text box at the top.
2. Filter events by **cryomodule, cavity, year** and **label**.
3. Select an event to view its waveform and classification suggestion.
4. Label the event using the buttons at the bottom.

---
## Troubleshooting: 
| Problem | Fix |
|---|---|
| `streamlit: command not found` | Activate your conda environment `conda activate quench-labeler` and try running again |
| Nothing happens when you run it | You used `python` instead of `streamlit run` |
| File not found in the app | The HDF5 path you entered is incorrect |
| `ModuleNotFoundError` | Make sure you are in the `root` directory |
| App won't open in browser | Manually paste the URL from the terminal into your browser.

---
## Stopping the App

In the terminal, press:

```
Ctrl + C
```


