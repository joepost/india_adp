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
districts = districts.astype({'pc11_s_id':'int64',
                              'pc11_d_id':'int64'})

# ******************************
# TODO: The code in this bracket is specified to Karnataka, as part of the test run. This will need to updated for the whole India approach. 

# Create shapefile specific to Karnataka
state_29 = states[states["NAME_1"]=="Karnataka"]
# districts_29 = districts[districts["NAME_1"]=="Karnataka"]
districts_29 = districts[districts['pc11_s_id']==29]          # 2023-07-12 Have changed input file to SHRUG source. Includes census coding, unlike GADM. 

# Export Karnataka shapefiles
state_29.to_file(state_29_filepath, mode="w")
districts_29.to_file(districts_29_filepath, mode="w")

# ******************************

# Read in the census data
census_data = pd.read_csv(agworkers)
census_data.columns

# Calculate ADP
census_data["crop_labourers"] = census_data["Cultivators P"] + census_data["Agricultural labourers P"]
census_data["all_primary_sector"] = census_data["Cultivators P"] + census_data["Agricultural labourers P"] + census_data["Primary sector other P"]
census_data_cln = census_data[census_data['Age group'] == 'Total']
ag_workers = census_data_cln[['State code', 'District code', 'Area name', 'Total Rural Urban',
                             'crop_labourers', 'all_primary_sector']]

ag_workers

# Export cleaned census data
ag_workers.to_csv(agworkers_filepath, mode="w", index=False)