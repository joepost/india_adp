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

# Start timer
start_time = time.time()

# ==================================================================================================================
# 1. LOAD DATA

# Read in the output files from script 01B: 
#   1. WorldPop points
#   2. Landcover (cropland)
#   3. GHSL rural polygons

time_11s = time.time()

if sfmt == '.shp':
        gdf_pop = gpd.read_file(pop_points)
        gdf_crops = gpd.read_file(cropland_poly_dissolved)
        gdf_ghsl = gpd.read_file(ghsl_poly_dissolved)
elif sfmt == '.feather':
        gdf_pop = gpd.read_feather(pop_points)
        gdf_crops = gpd.read_feather(cropland_poly_dissolved)
        gdf_ghsl = gpd.read_feather(ghsl_poly_dissolved)
    
districts_shp = gpd.read_file(districts_filepath)

ag_workers = pd.read_csv(agworkers_filepath
                         , dtype = {'State code':str, 'District code':str}
                         ) 

print('Input data files loaded.\n')
timestamp(time_11s)


# ==================================================================================================================
# 2. JOIN WORLDPOP POINTS TO LAND COVER POLYGONS

# ===========
# 2.1 Join WorldPop to GHSL rural areas
time_21s = time.time()

# Join points to GHSL
pop_points_rural = gdf_pop.sjoin(gdf_ghsl, how = 'inner', predicate='within')
pop_points_rural = pop_points_rural.drop(columns='index_right')

# Export the filtered rural population
# pop_points_rural.to_feather(pop_points_rural_path)    
print(f'Rural population points gdf created.\n')

timestamp(time_21s)

# pop_points_rural.plot(column='raster_value')
# plt.show()

# ===========
# 2.2 Join WorldPop to DynamicWorld cropland areas
time_22s = time.time()

# Join points to cropland
pop_joined_dw = gdf_pop.sjoin(gdf_crops, how='inner', predicate='within')
# pop_points_cropland = pop_joined_dw.loc[pop_joined_dw['cropland']==1]     # remove here because now filtered in script 01C
pop_points_cropland = pop_joined_dw.drop(columns='index_right')
pop_points_cropland.to_feather(pop_points_cropland_path)
print(f'Cropland population points gdf created and exported to {sfmt}.\n')

timestamp(time_22s)

# pop_points_cropland.plot(column='raster_value')
# plt.show()


# ==================================================================================================================
# 3. CALCULATE DISTRICT LEVEL POPULATION

# Next steps:
# 1.    Break down state counts (Karnataka) into districts -> Need to decide if this is necessary? What is the most accurate?
# 2.    Sum point population estimates by district, to get a total district population estimate from WorldPop
# 3.    Sum rural point population estimates by district, to get a rural district population estimate from WorldPop
# 4.    Sum cropland point population estimates by district, to get a cropland population district estimate from WorldPop
# 5.    Sum rural-crop point population estimates by district, to get final ADP estimate -> Will this be any different than value in Step (4)?


# ===========
# 3.1 Join census agworkers to district boundaries
time_31s = time.time()

ag_workers_jn = districts_shp.merge(ag_workers, how='left', left_on='pc11_d_id', right_on='District code', sort=True
                                #    , indicator=True, validate='one_to_many'       # Creates a '_merge' column, for quality checking
                                   )
ag_workers_jn.head()

print('Census ADP counts joined to district boundaries.\n')
timestamp(time_31s)


# ===========
# 3.2 Join WorldPop points to district boundaries
time_32s = time.time()

# This joins the attributes of the points to the polygons they fall within
pop_jn_districts = gdf_pop.sjoin(districts_shp, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = pop_jn_districts[['raster_value', 'geometry', 'pc11_d_id', 'd_name']]
sum_pop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'raster_value':'sum',
                                                                                    'd_name':'first'})
sum_pop_districts['raster_value'] = sum_pop_districts['raster_value'].round()         # remove unnecessary decimals

# Export the worldpop points by district
sum_pop_districts.to_feather(sum_pop_districts_path)  

print(f'Pop points joined to district boundaries and exported to {sfmt}.\n')
timestamp(time_32s)


# ===========
# 3.3 Join WorldPop RURAL points to district boundaries
time_33s = time.time()

# This joins the attributes of the points to the polygons they fall within
rupop_jn_districts = pop_points_rural.sjoin(districts_shp, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = rupop_jn_districts[['raster_value', 'geometry', 'pc11_d_id', 'd_name']]
sum_rupop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'raster_value':'sum',
                                                                                      'd_name':'first'})
sum_rupop_districts['raster_value'] = sum_rupop_districts['raster_value'].round()

# Export the rural points by district
sum_rupop_districts.to_feather(sum_rupop_districts_path)  

print(f'Rural pop points joined to district boundaries and export to {sfmt}.\n')
timestamp(time_33s)

# ===========
# 3.4 Join WorldPop CROPLAND points to district boundaries
time_34s = time.time()

# This joins the attributes of the points to the polygons they fall within
crpop_jn_districts = pop_points_cropland.sjoin(districts_shp, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = crpop_jn_districts[['raster_value', 'geometry', 'pc11_d_id', 'd_name']]
sum_crpop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'raster_value':'sum',
                                                                                      'd_name':'first'})
sum_crpop_districts['raster_value'] = sum_crpop_districts['raster_value'].round()

# Export the cropland points by district
sum_crpop_districts.to_feather(sum_crpop_districts_path)  

print(f'Cropland pop points joined to district boundaries and exported to {sfmt}.\n')
timestamp(time_34s)


# ==================================================================================================================
# 4. COLLATE OUTPUT INTO SINGLE GEODATAFRAME

# Input files:
#   1. Census population counts by district
#   2. Census agricultural workers by district  >>> use combo of first 2 to calculate Ag Workers Density (per km2)
#   3. WorldPop (all points) aggregated count by district
#   4. WorldPop (rural points) aggregated count by district
#   5. WorldPop (cropland points) aggregated count by district

masterdf = ag_workers_jn[['pc11_s_id', 'pc11_d_id', 'd_name', 'geometry', 'District code',
                                'Population', 'Area sq km', 'Population per sq km', 
                                'ADP1', 'ADP2', 'ADP3', 'ADP4', 'Total workers', 'ADP5']]

join_worldpop_all = sum_pop_districts[['pc11_d_id', 'raster_value']]
join_worldpop_all = join_worldpop_all.rename(columns={'raster_value':'worldpop'})
masterdf = masterdf.merge(join_worldpop_all, how='left', on=['pc11_d_id'])

join_worldpop_rural = sum_rupop_districts[['pc11_d_id', 'raster_value']]
join_worldpop_rural = join_worldpop_rural.rename(columns={'raster_value':'worldpop_rural'})
masterdf = masterdf.merge(join_worldpop_rural, how='left', on=['pc11_d_id'])

join_worldpop_crop = sum_crpop_districts[['pc11_d_id', 'raster_value']]
join_worldpop_crop = join_worldpop_crop.rename(columns={'raster_value':'worldpop_crop'})
masterdf = masterdf.merge(join_worldpop_crop, how='left', on=['pc11_d_id'])


# ==================================================================================================================
# 5. CALCULATE DIFFERENCE IN POPULATION ESTIMATES

# Columns to compute:
#   0. Difference between Worldpop total population and Census total population 
#   1. Difference between Worldpop cropland population and ADP1
#   2. Difference between Worldpop cropland population and ADP2
#   3. Difference between Worldpop cropland population and ADP3
#   4. Difference between Worldpop cropland population and ADP4
#   5. Difference between Worldpop cropland population and ADP5

# TODO: recalculate percentage changes to follow Sri Lanka method
#       1. Calculate the ADPc as a proportion of total population
#       2. Calculate the ADPa as a proportion of total population
#       3. Calculate the difference between [1] and [2]

# Calculate difference between Worldpop total population and Census total population
masterdf['d_poptotals'] = masterdf['worldpop'] - masterdf['Population']
masterdf['d_pc0'] = round(100 - masterdf['Population']/masterdf['worldpop']*100,2)

# NEW: 2023-08-07
masterdf['ADPa_pctotal'] = masterdf['worldpop_crop']/masterdf['Population']*100

# Calculate difference between Worldpop cropland population and ADP1
masterdf['ADPc1_pctotal'] = masterdf['ADP1']/masterdf['Population']*100
# masterdf['d_adp1'] = masterdf['worldpop_crop'] - masterdf['ADP1']
# masterdf['d_pc1'] = round(100 - masterdf['ADP1']/masterdf['worldpop_crop']*100,2)
masterdf['d_pc1'] = masterdf['ADPc1_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between Worldpop cropland population and ADP2
masterdf['ADPc2_pctotal'] = masterdf['ADP2']/masterdf['Population']*100
# masterdf['d_adp2'] = masterdf['worldpop_crop'] - masterdf['ADP2']
# masterdf['d_pc2'] = round(100 - masterdf['ADP2']/masterdf['worldpop_crop']*100,2)
masterdf['d_pc2'] = masterdf['ADPc2_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between Worldpop cropland population and ADP3
masterdf['ADPc3_pctotal'] = masterdf['ADP3']/masterdf['Population']*100
# masterdf['d_adp3'] = masterdf['worldpop_crop'] - masterdf['ADP3']
# masterdf['d_pc3'] = round(100 - masterdf['ADP3']/masterdf['worldpop_crop']*100,2)
masterdf['d_pc3'] = masterdf['ADPc3_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between Worldpop cropland population and ADP4
masterdf['ADPc4_pctotal'] = masterdf['ADP4']/masterdf['Population']*100
# masterdf['d_adp4'] = masterdf['worldpop_crop'] - masterdf['ADP4']
# masterdf['d_pc4'] = round(100 - masterdf['ADP4']/masterdf['worldpop_crop']*100,2)
masterdf['d_pc4'] = masterdf['ADPc4_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between Worldpop cropland population and ADP5
masterdf['ADPc5_pctotal'] = masterdf['ADP5']/masterdf['Population']*100
# masterdf['d_adp5'] = masterdf['worldpop_crop'] - masterdf['ADP5']
# masterdf['d_pc5'] = round(100 - masterdf['ADP5']/masterdf['worldpop_crop']*100,2)
masterdf['d_pc5'] = masterdf['ADPc5_pctotal'] - masterdf['ADPa_pctotal']

dlist = ['d_poptotals', 'd_pc1', 'd_pc2', 'd_pc3','d_pc4', 'd_pc5']

masterdf.drop(columns='geometry', inplace=True)

# masterdf.columns
masterdf.head()

# Add column to flag districts that need a buffer
# Use defined function with conditional rules: categorise_buffer

# Next apply conditional rows to each row of masterdf
masterdf['need_buffer'] = masterdf.apply(lambda row: categorise_buffer(row, 'd_pc3'), axis=1)

# Export masterdf to csv
masterdf.to_csv(masterdf_path, index=False)

print('Master results file exported to csv.\n')



# ==================================================================================================================
# 6. BUFFER ITERATION

# =====================
# 6.1 Define a function to create a buffer and recalculate the ADP estimate

# Where:
# 1. district_shp = districts_shp   
# 2. crops_shp = gdf_crops
# 3. rural_points = pop_points_rural
# 4. district_code = string format of district code
# 5. buffer_radius = set accordingly; default 50m
# 6. buffer_type = 'enlarge' or 'reduce'
def generate_buffer(districts_shp, crops_shp, rural_points, district_code, buffer_radius, buffer_type):
        time_buff = time.time()
        print('Creating ' + str(buffer_radius) + 'm buffers on crop lands for district: ' + district_code)

        # Define district boundaries
        district_boundary = districts_shp.loc[districts_shp['pc11_d_id'] == district_code]
        crop_by_district_boundary = gpd.overlay(crops_shp, district_boundary, how='intersection')

        # Convert to a Geoseries
        district_series = crop_by_district_boundary['geometry']

        # Convert buffer metre input into degrees (WGS84)
        if buffer_type == 'enlarge':
                degrees = buffer_radius * (0.00001/1.11)
        elif buffer_type == 'subtract':
                buffer_radius = buffer_radius * -1              # negative buffer radius = reduction in size
                degrees = buffer_radius * (0.00001/1.11)       
        elif buffer_type == 'unchanged':
                degrees = 0                                     # No buffer required (type == 'unchanged')
        else: 
                degrees = 0     

        # Calculate buffer
        d_buffer = district_series.buffer(degrees)
        d_buffer.name = 'geometry'
        d_buffer_gdf = gpd.GeoDataFrame(d_buffer, crs="EPSG:4326", geometry='geometry')

        # Join rural points to buffer zone
        ru_points_buffer = rural_points.sjoin(d_buffer_gdf, how='inner', predicate='within')
        ru_points_buffer = ru_points_buffer.drop(columns='index_right')

        # Dissolve points to calculate aggregated population for district
        sum_buffer_points = ru_points_buffer.dissolve(as_index=False, aggfunc={'raster_value':'sum'})
        sum_buffer_points['raster_value'] = sum_buffer_points['raster_value'].round()

        # Add district code and buffer radius to geodataframe
        sum_buffer_points['pc11_d_id'] = district_code
        sum_buffer_points['buffer_r'] = buffer_radius

        print(f'Rural pop points joined to buffer area and new ADP calculated.')

        # Merge census data from masterdf
        check_buffer = sum_buffer_points.merge(masterdf[['pc11_d_id', 'Population', 'ADPc3_pctotal', 'need_buffer']], how='left', on='pc11_d_id')

        check_buffer['buffered_pctotal'] = check_buffer['raster_value']/check_buffer['Population']*100
        check_buffer['d_bufferedpc'] = check_buffer['ADPc3_pctotal'] - check_buffer['buffered_pctotal']

        # Next apply conditional rows to each row of masterdf
        check_buffer['revised_buffer'] = check_buffer.apply(lambda row: buffer_logic(row, 'need_buffer', 'd_bufferedpc'), axis=1)

        timestamp(time_buff)
        return check_buffer

# TEST RUN
sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, '583', 50, 'subtract')

# TEST ZERO BUFFER
sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, '582', 0, 'enlarge')


# =====================
# 6.2 Run function over set of districts and combine outputs into a single GeoDataframe

# First, create an empty GDF to store the output as a row for each district
df = pd.DataFrame(columns=['raster_value', 'pc11_d_id', 'buffer_r', 'geometry'])
buffer_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

# Create a dictionary of the districts
buffer_dict = dict(zip(masterdf['pc11_d_id'], masterdf['need_buffer']))

# TEST LOOP THROUGH DICTIONARY
buffer_dict = {'581': 'enlarge', '582': 'unchanged', '583': 'subtract', '584': 'enlarge'}

# NOTE: Loop below works to run a single iteration of the buffer function for each district
# time_buffer = time.time()
# for key, value in buffer_dict.items():
#         sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, key, 50, value)
#         sum_buffer_gdf.to_crs(crs=buffer_gdf.crs, inplace=True)
#         # Concatenate output for each district into a single dataframe
#         buffer_gdf = pd.concat([sum_buffer_gdf, buffer_gdf])

# buffer_gdf
# timestamp(time_buffer)


# Create for loop to iterate through buffer process
# NOTE: CURRENT ERROR IN WHILE LOOPS. NOT SUCCEEDING IN HAVING THE CONDITION UPDATE AND CEASE ACCORDINGLY. 
time_buffer = time.time()
df = pd.DataFrame(columns=['raster_value', 'pc11_d_id', 'buffer_r', 'geometry'])
df['buffer_r'] = df['buffer_r'].astype(int)
buffer_gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
for key, value in buffer_dict.items():
        buffer_radius = 100
        while sum_buffer_gdf['need_buffer'].item() != 'unchanged':
                if value == 'enlarge':
                        sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, key, buffer_radius, 'enlarge')
                        print('buffer radius: ' + buffer_radius + ' ' + sum_buffer_gdf['need_buffer'].item())
                        buffer_radius = buffer_radius * 2       # increase the size of buffer for next iteration
                        buffer_dict[key]='enlarge'              # update the value in dictionary for next iteration
                elif value == 'subtract': 
                        sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, key, buffer_radius, 'subtract')
                        print('buffer radius: ' + buffer_radius + ' ' + sum_buffer_gdf['need_buffer'].item())
                        buffer_radius = buffer_radius / 4       # reduce the size of buffer for next iteration
                        buffer_dict[key]='subtract'             # update the value in dictionary for next iteration
                else:
                        break
        # Make sure dataframes have the same crs
        sum_buffer_gdf.to_crs(crs=buffer_gdf.crs, inplace=True)
        # Concatenate output for each district into a single dataframe
        buffer_gdf = pd.concat([sum_buffer_gdf, buffer_gdf])
timestamp(time_buffer)



# Export buffer_gdf to .feather
buffer_gdf.to_feather(buffergdf_path)

# Export buffer_df to csv
buffer_df = pd.DataFrame(buffer_gdf.drop(columns = 'geometry'))
buffer_df.to_csv(bufferdf_path, index=False)

# ********
# TODO: 
# Before running for next set of buffers, need to finish output of buffer process;
# i.e. export new masterdf results to csv
# Also need to add iteration step; how are the buffer results checked, and the outputs fed back into the function? 



# ==================================================================================================================
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

# masterdf_bplot = masterdf[['d_poptotals', 'd_adp1', 'd_adp2', 'd_adp3', 'd_adp4', 'd_adp5']]
masterdf_bplot_pc = masterdf[['d_pc1', 'd_pc2', 'd_pc3', 'd_pc4', 'd_pc5']]

# ==================================
# Plot figures: BOXPLOT
# Apply the default theme
fig, axes = plt.subplots(2, 1, figsize=(12, 8))
# create chart in each subplot
sns.boxplot(data=masterdf_bplot_pc
            , orient = 'h'
            , ax=axes[0]
            , palette = 'Blues'
            ).set(title="Difference in census and disaggregated ADP estimate, by ADP definition", xlabel = "", ylabel="")
sns.boxplot(data=masterdf_bplot_pc
            , orient = 'h'
            , ax=axes[1]
            , palette = 'Blues'
            ).set(title="Percentage difference in census and disaggregated ADP estimate, by ADP definition", xlabel = "", ylabel="")
# save figure to output folder
plt.savefig(bplot_adp, dpi=600, facecolor="white", bbox_inches="tight")
# display figure
plt.show()


# ==================================
# Plot figures: DISTRIBUTION PLOT
# Trial Kernel density estimates of ADP results? 

# Plot standalone figures
# fig, ax = plt.subplots(figsize=(12, 8))
# ax = sns.catplot(data=masterdf_bplot_pc, kind="swarm")
# plt.show()

# sns.set_theme(style="white", palette="Greens", font="arial")

# ax = sns.catplot(data=masterdf_bplot_pc
#             , orient = 'h'
#             , kind="box")
#         #     , ax=axes[1]
#         #     ).set(title="Percentage difference in census and disaggregated ADP estimate, by ADP definition", xlabel = "", ylabel="")
# # sns.despine()
# plt.show()



# ==================================================================================================================


print('\nScript complete.\n')
timestamp(start_time)