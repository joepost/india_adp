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
    
districts_29 = gpd.read_file(districts_29_filepath)

ag_workers = pd.read_csv(agworkers_filepath) 

print('Input data files loaded.\n')
timestamp(time_11s)


# ==================================================================================================================
# 2. JOIN WORLDPOP POINTS TO LAND COVER POLYGONS

# ===========
# 2.1 Join WorldPop to GHSL rural areas
time_21s = time.time()

# Join points to GHSL
pop_points_rural = gdf_pop.sjoin(gdf_ghsl, how = 'inner', predicate='within')

# Export the filtered rural population
pop_points_rural.to_feather(pop_points_rural_path)    
print(f'Rural population points exported to {sfmt}.\n')

timestamp(time_21s)

# ===========
# 2.2 Join WorldPop to DynamicWorld cropland areas
time_22s = time.time()

# Join points to cropland
pop_joined_dw = gdf_pop.sjoin(gdf_crops, how='inner', predicate='within')
# pop_points_cropland = pop_joined_dw.loc[pop_joined_dw['cropland']==1]     # remove here because now filtered in script 01C
pop_points_cropland = pop_joined_dw.drop(columns='index_right')
pop_points_cropland.to_feather(pop_points_cropland_path)
print(f'Cropland population points exported to {sfmt}.\n')

timestamp(time_22s)


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

ag_workers_jn = districts_29.merge(ag_workers, how='left', left_on='pc11_d_id', right_on='District code', sort=True
                                #    , indicator=True, validate='one_to_many'       # Creates a '_merge' column, for quality checking
                                   )
ag_workers_jn.head()

print('Census ADP counts joined to district boundaries.\n')
timestamp(time_31s)


# ===========
# 3.2 Join WorldPop points to district boundaries
time_32s = time.time()

# This joins the attributes of the points to the polygons they fall within
pop_jn_districts = gdf_pop.sjoin(districts_29, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = pop_jn_districts[['pop_count', 'geometry', 'pc11_d_id', 'd_name']]
sum_pop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'pop_count':'sum',
                                                                                    'd_name':'first'})
sum_pop_districts['pop_count'] = sum_pop_districts['pop_count'].round()         # remove unnecessary decimals

print('Pop points joined to district boundaries.\n')
timestamp(time_32s)

# ===========
# 3.3 Join WorldPop RURAL points to district boundaries
time_33s = time.time()

# This joins the attributes of the points to the polygons they fall within
rupop_jn_districts = pop_points_rural.sjoin(districts_29, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = rupop_jn_districts[['pop_count', 'geometry', 'pc11_d_id', 'd_name']]
sum_rupop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'pop_count':'sum',
                                                                                      'd_name':'first'})
sum_rupop_districts['pop_count'] = sum_rupop_districts['pop_count'].round()

print('Rural pop points joined to district boundaries.\n')
timestamp(time_33s)

# ===========
# 3.4 Join WorldPop CROPLAND points to district boundaries
time_34s = time.time()

# This joins the attributes of the points to the polygons they fall within
crpop_jn_districts = pop_points_cropland.sjoin(districts_29, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = crpop_jn_districts[['pop_count', 'geometry', 'pc11_d_id', 'd_name']]
sum_crpop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'pop_count':'sum',
                                                                                      'd_name':'first'})
sum_crpop_districts['pop_count'] = sum_crpop_districts['pop_count'].round()

print('Cropland pop points joined to district boundaries.\n')
timestamp(time_34s)

# ===========
# 3.5 Join census total population estimates to district boundaries
# time_35s = time.time() 
 
# # TODO: Consider a validation step comparing Total WorldPop Estimate for a district to the Total census population estimate for a district. 
# #   This can give an indication of the existing margin of error in the methodology, before bringing further uncertainty through the cropland masking process. 

# census_pop_jn = districts_29.merge(ag_workers, how='left', left_on='pc11_d_id', right_on='District code', sort=True)

# print('Census total population counts joined to district boundaries.\n')
# timestamp(time_35s)

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

# join_agworkers = ag_workers_jn[['pc11_d_id', 'ADP1', 'ADP2', 'ADP3', 'ADP4', 'Total workers', 'ADP5']]
# masterdf = masterdf.merge(join_agworkers, how='left', on=['pc11_d_id'])

join_worldpop_all = sum_pop_districts[['pc11_d_id', 'pop_count']]
join_worldpop_all = join_worldpop_all.rename(columns={'pop_count':'worldpop'})
masterdf = masterdf.merge(join_worldpop_all, how='left', on=['pc11_d_id'])

join_worldpop_rural = sum_rupop_districts[['pc11_d_id', 'pop_count']]
join_worldpop_rural = join_worldpop_rural.rename(columns={'pop_count':'worldpop_rural'})
masterdf = masterdf.merge(join_worldpop_rural, how='left', on=['pc11_d_id'])

join_worldpop_crop = sum_crpop_districts[['pc11_d_id', 'pop_count']]
join_worldpop_crop = join_worldpop_crop.rename(columns={'pop_count':'worldpop_crop'})
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

# Calculate difference between Worldpop total population and Census total population
masterdf['d0_poptotals'] = masterdf['worldpop'] - masterdf['Population']
masterdf['d0_pc'] = round(100 - masterdf['Population']/masterdf['worldpop']*100,2)

# Calculate difference between Worldpop cropland population and ADP1
masterdf['d1_adp1'] = masterdf['worldpop_crop'] - masterdf['ADP1']
masterdf['d1_pc'] = round(100 - masterdf['ADP1']/masterdf['worldpop_crop']*100,2)

# Calculate difference between Worldpop cropland population and ADP2
masterdf['d2_adp2'] = masterdf['worldpop_crop'] - masterdf['ADP2']
masterdf['d2_pc'] = round(100 - masterdf['ADP2']/masterdf['worldpop_crop']*100,2)

# Calculate difference between Worldpop cropland population and ADP3
masterdf['d3_adp3'] = masterdf['worldpop_crop'] - masterdf['ADP3']
masterdf['d3_pc'] = round(100 - masterdf['ADP3']/masterdf['worldpop_crop']*100,2)

# Calculate difference between Worldpop cropland population and ADP4
masterdf['d4_adp4'] = masterdf['worldpop_crop'] - masterdf['ADP4']
masterdf['d4_pc'] = round(100 - masterdf['ADP4']/masterdf['worldpop_crop']*100,2)

# Calculate difference between Worldpop cropland population and ADP5
masterdf['d5_adp5'] = masterdf['worldpop_crop'] - masterdf['ADP5']
masterdf['d5_pc'] = round(100 - masterdf['ADP5']/masterdf['worldpop_crop']*100,2)

dlist = ['d0_poptotals', 'd1_adp1', 'd2_adp2', 'd3_adp3','d4_adp4', 'd5_adp5']

masterdf.drop(columns='geometry', inplace=True)

masterdf.columns
masterdf.head()

# Export masterdf to csv
masterdf.to_csv(masterdf_path, index=False)

print('Master results file exported to csv.\n')


print('\nScript complete.\n')
timestamp(start_time)