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

gdf_crops = gpd.read_file(cropland_poly_dissolved)
gdf_ghsl = gpd.read_file(ghsl_india_clipped)
gdf_pop = gpd.read_file(pop_points)


# ==================================================================================================================
# 2. JOIN WORLDPOP POINTS TO GHSL RURAL AREAS


# Clip points to GHSL
#   This keeps the objects separate, but clips off any points that fall outside the mask boundaries
#   NOTE: Unnecessary; JOIN below used instead. 
# *CAN DELETE THESE LINES >>>>>>>>>>*
# pop_clipped = gpd.clip(gdf_pop, gdf_ghsl)
# # Export to shapefile
# pop_clipped.to_file(pop_points_clipped, mode="w")
# print('Clipped (to state boundary) population points exported to shapefile.\n')
# *<<<<<<<<< CAN DELETE THESE LINES*


# Join points to GHSL
#   This joins the attributes of the points to the polygons they fall within
pop_joined_ghsl = gdf_pop.sjoin(gdf_ghsl, how = 'inner')

# Create a filtered df and just keep the rural points (11, 12, 13, 21)
pop_points_rural = pop_joined_ghsl.loc[pop_joined_ghsl['settlement'].isin([11, 12, 13, 21])]

# Export the filtered rural population as a shp file
pop_points_rural.to_file(pop_points_rural_path, driver='ESRI Shapefile')
print('Rural population points exported to shapefile.\n')


# ==================================================================================================================
# 3. JOIN WORLDPOP POINTS TO GHSL RURAL AREAS

