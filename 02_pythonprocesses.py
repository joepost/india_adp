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
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
# from osgeo import gdal

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

gdf_pop = gpd.read_file(pop_points)
gdf_crops = gpd.read_file(cropland_poly_dissolved)
gdf_ghsl = gpd.read_file(ghsl_india_clipped)
    
districts_29 = gpd.read_file(districts_29_filepath)

ag_workers = pd.read_csv(agworkers_filepath)


# ==================================================================================================================
# 2. JOIN WORLDPOP POINTS TO LAND COVER POLYGONS

# ===========
# 2.1 Join WorldPop to GHSL rural areas
time_21s = time.time()

# Join points to GHSL
if os.path.isfile(pop_points_rural_path):
    pop_points_rural = gpd.read_file(pop_points_rural_path)
    print('Rural population points loaded from shapefile.\n')
else:
    #   This joins the attributes of the points to the polygons they fall within
    pop_joined_ghsl = gdf_pop.sjoin(gdf_ghsl, how = 'inner')

    # Create a filtered df and just keep the rural points (11, 12, 13, 21)
    pop_points_rural = pop_joined_ghsl.loc[pop_joined_ghsl['settlement'].isin([11, 12, 13, 21])]
    pop_points_rural = pop_points_rural.drop(columns='index_right')

    # Export the filtered rural population as a shp file
    pop_points_rural.to_file(pop_points_rural_path, driver='ESRI Shapefile')
    print('Rural population points exported to shapefile.\n')

timestamp(time_21s)

# ===========
# 2.2 Join WorldPop to DynamicWorld cropland areas
time_22s = time.time()

# Join points to cropland
if os.path.isfile(pop_points_cropland_path):
    pop_points_cropland = gpd.read_file(pop_points_cropland_path)
    print('Cropland population points loaded from shapefile.\n')
else:
    pop_joined_dw = gdf_pop.sjoin(gdf_crops, how='inner')
    pop_points_cropland = pop_joined_dw.loc[pop_joined_dw['cropland_b']==1]
    pop_points_cropland = pop_points_cropland.drop(columns='index_right')
    pop_points_cropland.to_file(pop_points_cropland_path, driver='ESRI Shapefile')
    print('Cropland population points exported to shapefile.\n')

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
# ag_workers_jn[ag_workers_jn['_merge'] != 'both']    # check to see if any rows have not joined

# Split into urban/rural/total
# NOTE: Need to decide whether the urban/rural/total census split is relevant, or just to select one (Unresolved as of 2023-07-12)
# ag_workers_jn_total = ag_workers_jn[ag_workers_jn['Total Rural Urban'] == 'Total']
# ag_workers_jn_rural = ag_workers_jn[ag_workers_jn['Total Rural Urban'] == 'Rural']
# ag_workers_jn_urban = ag_workers_jn[ag_workers_jn['Total Rural Urban'] == 'Urban']

# ****TODO: Create function for this split action ^^^ above? -> Currently occurs TWICE in code

# TODO: Remove shapefile exports for python script intermediaries?
# Export the joined census and boundary data as a shp file
# if not os.path.isfile(agworkers_jn_filepath):
#     ag_workers_jn.to_file(agworkers_jn_filepath, driver='ESRI Shapefile')
#     ag_workers_jn_total.to_file(agworkers_jn_filepath_t, driver='ESRI Shapefile')
#     ag_workers_jn_rural.to_file(agworkers_jn_filepath_r, driver='ESRI Shapefile')
#     ag_workers_jn_urban.to_file(agworkers_jn_filepath_u, driver='ESRI Shapefile')
#     print('Census data by district boundary exported to shapefile.\n')

print('Census ADP counts joined to district boundaries.\n')
timestamp(time_31s)


# ===========
# 3.2 Join WorldPop points to district boundaries
time_32s = time.time()

# This joins the attributes of the points to the polygons they fall within
pop_jn_districts = gdf_pop.sjoin(districts_29, how = 'inner')

# Dissolve points to calculate aggregated population for district
dissolve_df = pop_jn_districts[['pop_count', 'geometry', 'pc11_d_id', 'd_name']]
sum_pop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'pop_count':'sum',
                                                                                    'd_name':'first'})
sum_pop_districts['pop_count'] = sum_pop_districts['pop_count'].round()         # remove unnecessary decimals

# Export the filtered rural population as a shp file
# if not os.path.isfile(pop_jn_district_path):
#     sum_pop_districts.to_file(pop_jn_district_path, driver='ESRI Shapefile')
#     print('Pop points joined to district boundaries and exported to shapefile.\n')

print('Pop points joined to district boundaries.\n')
timestamp(time_32s)

# ===========
# 3.3 Join WorldPop RURAL points to district boundaries
time_33s = time.time()

# This joins the attributes of the points to the polygons they fall within
rupop_jn_districts = pop_points_rural.sjoin(districts_29, how = 'inner')

# Dissolve points to calculate aggregated population for district
dissolve_df = rupop_jn_districts[['pop_count', 'geometry', 'pc11_d_id', 'd_name']]
sum_rupop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'pop_count':'sum',
                                                                                      'd_name':'first'})
sum_rupop_districts['pop_count'] = sum_rupop_districts['pop_count'].round()

# Export the filtered rural population as a shp file
# if not os.path.isfile(rupop_jn_district_path):
#     sum_rupop_districts.to_file(rupop_jn_district_path, driver='ESRI Shapefile')
#     print('Rural pop points joined to district boundaries and exported to shapefile.\n')

print('Rural pop points joined to district boundaries.\n')
timestamp(time_33s)

# ===========
# 3.4 Join WorldPop CROPLAND points to district boundaries
time_34s = time.time()

# This joins the attributes of the points to the polygons they fall within
crpop_jn_districts = pop_points_cropland.sjoin(districts_29, how = 'inner')

# Dissolve points to calculate aggregated population for district
dissolve_df = crpop_jn_districts[['pop_count', 'geometry', 'pc11_d_id', 'd_name']]
sum_crpop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'pop_count':'sum',
                                                                                      'd_name':'first'})
sum_crpop_districts['pop_count'] = sum_crpop_districts['pop_count'].round()

# Export the filtered rural population as a shp file
# if os.path.isfile(crpop_jn_district_path):
#     sum_crpop_districts.to_file(crpop_jn_district_path, driver='ESRI Shapefile')
#     print('Cropland pop points joined to district boundaries and exported to shapefile.\n')

print('Cropland pop points joined to district boundaries.\n')
timestamp(time_34s)

# ===========
# 3.5 Join census total population estimates to district boundaries
time_35s = time.time() 

# TODO: Consider a validation step comparing Total WorldPop Estimate for a district to the Total census population estimate for a district. 
#   This can give an indication of the existing margin of error in the methodology, before bringing further uncertainty through the cropland masking process. 

# Read in census population (total, urban, rural)
# NOTE: MOVED THIS SECTION TO SCRIPT 01
# census_pop = pd.read_csv(census_population)
# census_pop = census_pop[['State  Code', 'District Code', 'Region', 'Name', 'Total Rural Urban',
#        'Population', 'Area sq km', 'Population per sq km']]
# census_pop = census_pop.astype({'Population':'int64'},
#                                {'Population per sq km':'float64'})

census_pop_jn = districts_29.merge(census_pop, how='left', left_on='pc11_d_id', right_on='District Code', sort=True)
census_pop_jn = census_pop_jn[census_pop_jn['Total Rural Urban']=='Total']

# Split into urban/rural/total
# NOTE: Need to decide whether the urban/rural/total census split is relevant, or just to select one (Unresolved as of 2023-07-12)
# census_pop_jn_total = census_pop_jn[census_pop_jn['Total Rural Urban'] == 'Total']
# census_pop_jn_rural = census_pop_jn[census_pop_jn['Total Rural Urban'] == 'Rural']
# census_pop_jn_urban = census_pop_jn[census_pop_jn['Total Rural Urban'] == 'Urban']

# Export the joined census total population and district boundaries as a shp file
# if not os.path.isfile(census_jn_filepath):
#     census_pop_jn.to_file(census_jn_filepath, driver='ESRI Shapefile')
#     census_pop_jn_total.to_file(census_jn_filepath_t, driver='ESRI Shapefile')
#     census_pop_jn_rural.to_file(census_jn_filepath_r, driver='ESRI Shapefile')
#     census_pop_jn_urban.to_file(census_jn_filepath_u, driver='ESRI Shapefile')
#     print('Census data by district boundary exported to shapefile.\n')

print('Census total population counts joined to district boundaries.\n')

timestamp(time_35s)

# ==================================================================================================================
# 4. COLLATE OUTPUT INTO SINGLE GEODATAFRAME
time_40s = time.time()

# Input files:
#   1. Census population counts by district
#   2. Census agricultural workers by district  >>> use combo of first 2 to calculate Ag Workers Density (per km2)
#   3. WorldPop (all points) aggregated count by district
#   4. WorldPop (rural points) aggregated count by district
#   5. WorldPop (cropland points) aggregated count by district

masterdf = census_pop_jn[['pc11_s_id', 'pc11_d_id', 'd_name', 'geometry', 'State  Code',
                                'Population', 'Area sq km', 'Population per sq km']]

join_agworkers = ag_workers_jn[['pc11_d_id','crop_labourers', 'all_primary_sector']]
masterdf = masterdf.merge(join_agworkers, how='left', on=['pc11_d_id'])

join_worldpop_all = sum_pop_districts[['pc11_d_id', 'pop_count']]
join_worldpop_all = join_worldpop_all.rename(columns={'pop_count':'worldpop'})
masterdf = masterdf.merge(join_worldpop_all, how='left', on=['pc11_d_id'])

join_worldpop_rural = sum_rupop_districts[['pc11_d_id', 'pop_count']]
join_worldpop_rural = join_worldpop_rural.rename(columns={'pop_count':'worldpop_rural'})
masterdf = masterdf.merge(join_worldpop_rural, how='left', on=['pc11_d_id'])

join_worldpop_crop = sum_crpop_districts[['pc11_d_id', 'pop_count']]
join_worldpop_crop = join_worldpop_crop.rename(columns={'pop_count':'worldpop_crop'})
masterdf = masterdf.merge(join_worldpop_crop, how='left', on=['pc11_d_id'])

# Calculate difference between Census ADP and Worldpop cropland calculation
masterdf['adp_difference'] = masterdf['crop_labourers'] - masterdf['worldpop_crop']
masterdf['adp_diff_pc'] = round(masterdf['adp_difference']/masterdf['crop_labourers']*100,2)

masterdf.drop(columns='geometry', inplace=True)

masterdf.columns
masterdf.head()

# Export masterdf to csv
masterdf.to_csv(masterdf_path, index=False)

timestamp(time_40s)



print('\nScript complete.\n')
timestamp(start_time)