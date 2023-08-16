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

masterdf = pd.read_csv(masterdf_path
                         , dtype = {'pc11_s_id':str, 'pc11_d_id':str}
                         )

buffer_df = pd.read_csv(bufferdf_path
                         , dtype = {'pc11_s_id':str, 'pc11_d_id':str}
                         )
buffer_gdf = gpd.read_feather(buffergdf_path)


# Merged buffer files 
# Use glob to create list of all completed buffers
bufferdf_to_merge = glob.glob(os.path.join(outputfolder, 'final', 'tables', f'bufferdf_*_{tru_cat}_{ADPcn}.csv')) 

# Use loop to read the files into an empty list
buffer_allstates_list = []
for file in bufferdf_to_merge:
    statefile = pd.read_csv(file, dtype = {'pc11_s_id':str, 'pc11_d_id':str})
    buffer_allstates_list.append(statefile)

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
               , orient="h").set(title=f"Performance of aggregated ADP estimate against census results, \nby district, {state_name}"
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
