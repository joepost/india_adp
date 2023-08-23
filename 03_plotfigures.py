# ==================================================================================================================

# DISSERTATION
# SECTION 03: Plot figures
#   This script generates plots using the output from scripts 01-02. 

# Author: J Post

# ==================================================================================================================
# 0. IMPORT PACKAGES

import os
import glob
import subprocess
import sys
import json 
import time
import pandas as pd

os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# from osgeo import gdal
# from pygeos import Geometry

import rasterio
from rasterio.mask import mask
from rasterio.features import geometry_mask
from rasterio.plot import show
from shapely.geometry import mapping, shape

import fiona

from globals import *       # Imports the filepaths defined in globals.py

print('Packages imported.\n')



# ==================================================================================================================
# 1. LOAD DATA

# Read in the output files from script 01B: 
#   1. WorldPop points
#   2. Landcover (cropland)
#   3. GHSL rural polygons

time_11s = time.time()

# if sfmt == '.shp':
#         gdf_pop = gpd.read_file(pop_points)
#         gdf_crops = gpd.read_file(cropland_poly_dissolved)
#         gdf_ghsl = gpd.read_file(ghsl_poly_dissolved)
# elif sfmt == '.feather':
#         gdf_pop = gpd.read_feather(pop_points)
#         gdf_crops = gpd.read_feather(cropland_poly_dissolved)
#         gdf_ghsl = gpd.read_feather(ghsl_poly_dissolved)
    
districts_shp = gpd.read_file(districts_filepath)

ag_workers = pd.read_csv(agworkers_filepath
                         , dtype = {'State code':str, 'District code':str}
                         ) 

masterdf = pd.read_csv(masterdf_path
                         , dtype = {'pc11_s_id':str, 'pc11_d_id':str}
                         )

buffer_df = pd.read_csv(bufferdf_path
                         , dtype = {'pc11_s_id':str, 'pc11_d_id':str}
                         )
buffer_gdf = gpd.read_feather(buffergdf_path)


print('Input data files loaded.\n')
timestamp(time_11s)




# ==================================
# Plot figures: RASTER MAP OF ADP DISTRIBUTION

# NOTE: The WorldPop raster will need to be masked twice:
#   1st: on the buffer multipolygon
#   2nd: on the rural area polygon
#   This is to ensure the final map only shows rural areas within the buffer zone (which are the only areas where population is counted).

# Import the buffer area polygon 
#   NOTE: need to use fiona to work with rasterio (GeoPandas causes attribute error)
with fiona.open(buffermap_path, "r") as shapefile:
    shapes = [feature["geometry"] for feature in shapefile]

# Mask the WorldPop raster using polygon
with rasterio.open(pop_tif) as src:
    out_image, out_transform = rasterio.mask.mask(src, shapes, crop=False)
    out_meta = src.meta

# Output to new file
with rasterio.open(pop_tif_buffer_mask, "w", **out_meta) as dest:
    dest.write(out_image)

# Import the rural area polygon (first as feather)
feather_rural = gpd.read_feather(ghsl_poly_dissolved)
# Export as shapefile
feather_rural.to_file(ghsl_poly_shp)

with fiona.open(ghsl_poly_shp, "r") as shapefile:
    rural = [feature["geometry"] for feature in shapefile]

# Mask the WorldPop raster using polygon
with rasterio.open(pop_tif_buffer_mask) as src:
    out_image, out_transform = rasterio.mask.mask(src, rural, crop=False)
    out_meta = src.meta

# Output to new file
with rasterio.open(pop_tif_final, "w", **out_meta) as dest:
    dest.write(out_image)




# =================================================================================================================
# 2. MERGE RESULTS FILES FOR ALL STATES



# ==================
# 2.1 Buffer files

# Merged buffer files 
# Use glob to create list of all completed buffers
bufferdf_to_merge = glob.glob(os.path.join(outputfolder, 'final', 'tables', f'bufferdf_*_{tru_cat}_{ADPcn}.csv')) 

# Use loop to read the files into an empty list
buffer_allstates_list = []
for file in bufferdf_to_merge:
    statefile = pd.read_csv(file, dtype = {'pc11_s_id':str, 'pc11_d_id':str})
    buffer_allstates_list.append(statefile)

# Concatenate all GeoDataFrames in the list
buffer_combined = pd.concat(buffer_allstates_list)

# Export combined buffer df to csv
buffer_combined.to_csv(buffercombined_path, index=False)



# ==================
# 2.2 Buffer map

# Merged buffer files 
# Use glob to create list of all completed buffers
buffermap_to_merge = glob.glob(os.path.join(outputfolder, 'final', 'spatial_files', f'bufferdf_*_{tru_cat}_{ADPcn}.shp')) 

# Use loop to read the files into an empty list
buffer_allmaps_list = []
for file in buffermap_to_merge:
    statefile = gpd.read_file(file)
    buffer_allmaps_list.append(statefile)

# Concatenate all GeoDataFrames in the list
buffer_combined = pd.concat(buffer_allmaps_list)

# 

# Export combined buffer map to .shp
buffer_combined.to_file(buffercombined_map)




# ==================
# 2.3 List of ineligible states

# Use glob to create list of all completed inel. files
ineligibledf_to_merge = glob.glob(os.path.join(outputfolder, 'final', 'tables', f'ineligibledf_*_{tru_cat}_{ADPcn}.csv')) 

# Use loop to read the files into an empty list
inel_allstates_list = []
for file in ineligibledf_to_merge:
    statefile = pd.read_csv(file, dtype = {'pc11_s_id':str, 'pc11_d_id':str})
    inel_allstates_list.append(statefile)

# Concatenate all GeoDataFrames in the list
inel_combined = pd.concat(inel_allstates_list)

# Export combined buffer df to csv
inel_combined.to_csv(ineligiblecombined_path, index=False)


