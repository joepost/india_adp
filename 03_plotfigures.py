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


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# NOTE: CAUTION !!!!!!
#   The code below assumes that all buffer_gdf files have the same column stucture. 
#   All files created BEFORE 17-08-2023 14:00 have the OLD file structure. 
#   These files should be recalculated or manually removed from the merge list prior to concatenation. 

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
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

print('Input data files loaded.\n')
timestamp(time_11s)



# =================================================================================================================
# 7. PLOT FIGURES

# ==================================
# Plot figures: POINT PLOTS

# Prepare the dataset
dot_df = masterdf[['d_name','Population', 'Population per sq km'
            , 'ADPa_pctotal', 'ADPc5_pctotal', 'd_pc5'
            # , 'd_pc0'
            ]]

# Make the PairGrid
f, ax = plt.subplots(figsize=(14, 12))
sns.set_theme(style="whitegrid")
g = sns.PairGrid(dot_df.sort_values("ADPa_pctotal", ascending=False), x_vars=dot_df.columns[3:], y_vars=["d_name"],
                 height=10, aspect=.25)

# Draw a dot plot using the stripplot function
g.map(sns.stripplot, size=10, orient="h", jitter=False, palette="flare_r", linewidth=1, edgecolor="w")

# Use the same x axis limits on all columns and add better labels
g.set(xlim=(-25, 105), ylabel="", xlabel="Per cent")

# Use semantically meaningful titles for the columns
titles = ['$ADP_{A}$ as % Total Pop', '$ADP_{C5}$ as % Total Pop', '% difference'
          # , 'base difference'
          ]

for ax, title in zip(g.axes.flat, titles):

    # Set a different title for each axes
    ax.set(title=title)

    ax.axvline(x=0, c="red", dashes=(5, 2))

    # Make the grid horizontal instead of vertical
    ax.xaxis.grid(False)
    ax.yaxis.grid(True)

sns.despine(left=True, bottom=True)

# Add a main title to the PairGrid
plt.subplots_adjust(top=0.88)  # Adjust top margin for the title
g.fig.suptitle("Agricultural Dependent Population estimates by district"
                , x=0.05, y=0.98, ha="left"
                , fontsize=16
                , fontweight='bold'
               )


# Add a subtitle below the main title
subtitle_text = "Karnataka, India"
plt.figtext(0.05, 0.935, subtitle_text, ha="left", fontsize=12)

# Add footnote
footnote = "$ADP_{A}$: aggregated Agricultural Dependent Population\n$ADP_{C5}$: census Agricultural Dependent Population"
plt.figtext(0.05, -0.02, footnote, ha="left", fontsize=10)


# save figure to output folder
plt.savefig(pointplot_adp, dpi=600, facecolor="white", bbox_inches="tight")

# plt.show()

# ==================================================================================================================



# ==================================
# Plot figures: RASTER MAP OF ADP DISTRIBUTION (KARNATAKA)

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


