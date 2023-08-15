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

masterdf = pd.read_csv(masterdf_path)

buffer_df = pd.read_csv(bufferdf_path)
buffer_gdf = gpd.read_feather(buffergdf_path)

print('Input data files loaded.\n')
timestamp(time_11s)



# =================================================================================================================
# 7. PLOT FIGURES

# NOTE: SNS plot syntax does not require long data; therefore can remove this section (2023-08-02)
# # pivot master df into a long format, for stats and plotting by ADP group
# statsdf = masterdf[['pc11_d_id', 'd_name'
#                     , 'd_adp1', 'd_adp2', 'd_adp3', 'd_adp4', 'd_adp5'
#                     # , 'd_pc1', 'd_pc2', 'd_pc3', 'd_pc4', 'd_pc5'
#                     ]]
# statsdf = pd.wide_to_long(statsdf, stubnames='d_adp', i=['pc11_d_id', 'd_name'], j='ADP')

# statsdf_pc = masterdf[['pc11_d_id', 'd_name'
#                     # , 'd_adp1', 'd_adp2', 'd_adp3', 'd_adp4', 'd_adp5'
#                     , 'd_pc1', 'd_pc2', 'd_pc3', 'd_pc4', 'd_pc5'
#                     ]]
# statsdf_pc = pd.wide_to_long(statsdf_pc, stubnames='d_pc', i=['pc11_d_id', 'd_name'], j='ADP')

# # Append into a single dataframe
# statsdf['d_pc'] = statsdf_pc['d_pc']

# # masterdf_bplot = masterdf[['d_poptotals', 'd_adp1', 'd_adp2', 'd_adp3', 'd_adp4', 'd_adp5']]
# masterdf_bplot_pc = masterdf[['d_pc1', 'd_pc2', 'd_pc3', 'd_pc4', 'd_pc5']]

# # ==================================
# # Plot figures: BOXPLOT
# # Apply the default theme
# fig, axes = plt.subplots(2, 1, figsize=(12, 8))
# # create chart in each subplot
# sns.boxplot(data=masterdf_bplot_pc
#             , orient = 'h'
#             , ax=axes[0]
#             , palette = 'Blues'
#             ).set(title="Difference in census and disaggregated ADP estimate, by ADP definition", xlabel = "", ylabel="")
# sns.boxplot(data=masterdf_bplot_pc
#             , orient = 'h'
#             , ax=axes[1]
#             , palette = 'Blues'
#             ).set(title="Percentage difference in census and disaggregated ADP estimate, by ADP definition", xlabel = "", ylabel="")
# # save figure to output folder
# plt.savefig(bplot_adp, dpi=600, facecolor="white", bbox_inches="tight")
# # display figure
# plt.show()


# ==================================
# Plot figures: DISTRIBUTION PLOT

box_df = masterdf[['d_pc1','d_pc2','d_pc3','d_pc4','d_pc5']]

# Violin Plot
sns.violinplot(data=box_df
               , palette="viridis"
              #  , color="skyblue"
               , inner="point"
               , orient="h").set(title="Performance of aggregated ADP estimate against census results, \nby district, Karnataka"
               , xlabel = "Percentage difference"
               , ylabel="")

# sns.stripplot(data=box_df
#               , orient = 'h'
#               , size=4, color=".3", linewidth=0)

# Change labels of Y ticks
plt.yticks(ticks=[0,1,2,3,4]
           ,labels=['$ADP_{C1}$', '$ADP_{C2}$', '$ADP_{C3}$', '$ADP_{C4}$', '$ADP_{C5}$'])

# Add footnote
footnote = "ADP: Agricultural Dependent Population"
plt.annotate(footnote, (0.5, -0.20), xycoords="axes fraction", ha="right", fontsize=8
            #  , fontstyle="italic"
             )

plt.show()



# ==================================
# Plot figures: POINT PLOTS

# Prepare the dataset
dot_df = masterdf[['d_name','Population', 'Population per sq km'
            , 'ADPa_pctotal', 'ADPc5_pctotal', 'd_pc5']]

# Make the PairGrid
sns.set_theme(style="whitegrid")
g = sns.PairGrid(dot_df.sort_values("d_pc5", ascending=False)
                 , x_vars=dot_df.columns[3:], y_vars=["d_name"],
                 height=10, aspect=.25)

# Draw a dot plot using the stripplot function
g.map(sns.stripplot, size=10, orient="h", jitter=False,
      palette="flare_r", linewidth=1, edgecolor="w")

# Use the same x axis limits on all columns and add better labels
g.set(xlim=(-95, 95), ylabel="", xlabel="Per cent")

# Use semantically meaningful titles for the columns
titles = ['$ADP_{A}$ as % Total Pop', '$ADP_{C5}$ as % Total Pop', '% difference']

for ax, title in zip(g.axes.flat, titles):

    # Set a different title for each axes
    ax.set(title=title)

    # Make the grid horizontal instead of vertical
    ax.xaxis.grid(False)
    ax.yaxis.grid(True)

sns.despine(left=True, bottom=True)

# Add a main title to the PairGrid
plt.subplots_adjust(top=0.9)  # Adjust top margin for the title
g.fig.suptitle("Population characteristics by District, Karnataka", fontsize=16)

plt.show()

# ==================================================================================================================
