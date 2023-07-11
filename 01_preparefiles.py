# ==================================================================================================================

# DISSERTATION
# SECTION 01: Prepare Files
# Date: 2023-06-19
# Author: J Post

# ==================================================================================================================
# 0. IMPORT PACKAGES

import os
import glob
import subprocess
import sys
import json
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal


from globals import *       # Imports the filepaths defined in globals.py

print('Packages imported.\n')


# ==================================================================================================================
# 1. CREATE REQUIRED SUBFOLDERS

for path in data_subfolders:
    subfolderpath = os.path.join(datafolder, path)
    if not os.path.exists(subfolderpath):
        print(f"Creating folder {subfolderpath}")
        os.makedirs(subfolderpath)

for path in output_subfolders:
    subfolderpath = os.path.join(outputfolder, 'intermediates', path)
    if not os.path.exists(subfolderpath):
        print(f"Creating folder {subfolderpath}")
        os.makedirs(subfolderpath)



# ==================================================================================================================
# 2. LOAD AND CLEAN DATA

loc_codes = pd.read_csv(locationcodes)
loc_codes.head()

# Create a df of state codes and names
state_codes = loc_codes[(loc_codes["District Code"]==0) &
                        (loc_codes["Sub District Code"]==0) & 
                        (loc_codes["Town-Village Code"]==0)].filter(items=["State Code", "Town-Village Name"])
state_codes

# Create a df of district codes and names
# Initially, this is just for the test state Karnataka
district_codes = loc_codes[(loc_codes["State Code"]==29) &
                           (loc_codes["Sub District Code"]==0) &
                           (loc_codes["Town-Village Code"]==0)].filter(items=["State Code", "District Code", "Town-Village Name"])
district_codes.head(10)


# Read in shapefile
states = gpd.read_file(boundaries_state)
districts = gpd.read_file(boundaries_district)


# ******************************
# TODO: The code in this bracket is specified to Karnataka, as part of the test run. This will need to updated for the whole India approach. 

# Create shapefile specific to Karnataka
state_29 = states[states["NAME_1"]=="Karnataka"]
districts_29 = districts[districts["NAME_1"]=="Karnataka"]

# Export Karnataka shapefiles
state_29.to_file(state_29_filepath, mode="w")
districts_29.to_file(districts_29_filepath, mode="w")

# ******************************

# plot the map
fig, ax = plt.subplots() 
state_29.plot(ax = ax, color='green').set_axis_off()
# plt.show()      # use 'show' to bring up a viz window

# fig, ax = plt.subplots()              ## NOT VISUALISING CORRETLY; WHY?
# districts_29.plot(ax = ax, color='bue').set_axis_off()
# plt.show()     
