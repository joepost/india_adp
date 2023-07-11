# ==================================================================================================================

# DISSERTATION
# SECTION 02: Python processing
#   This file picks up at the end of 01B, and uses the output from the first set of QGIS process.
#   This script is intended to be run in full as a single python file. 

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
# from osgeo import gdal

from globals import *       # Imports the filepaths defined in globals.py

print('Packages imported.\n')


# ==================================================================================================================
# 1. LOAD DATA

# Read in the output files from script 01B: 
#   1. WorldPop points
#   2. Landcover (cropland)
#   3. GHSL rural poylgons

# Then clip the population points just to rural areas (using GHSL) 

gdf_crops = gpd.read_file(cropland_poly_dissolved)
gdf_ghsl = gpd.read_file(ghsl_india_clipped)
gdf_pop = gpd.read_file(pop_points)

# Filter ghsl into rural and urban (do this here or after the clipping?)

# Clip points to GHSL
pop_clipped = gpd.clip(gdf_pop, gdf_ghsl)
