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

sys.path.append("C:\\Users\\joepo\\anaconda3\\envs\\dissertation\\Scripts")
# import gdal_merge as gm  

print('Packages imported.\n')


# ==================================================================================================================
# 1. DEFINE FILE PATHS

# Working directories
repository = 'C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp/'
datafolder = repository + 'Data/'
outputfolder = repository + 'Output/'

# Input files
boundaries_national =   datafolder + 'boundaries/gadm41_IND_0.shp'                        # GADM India boundaries shapefile
boundaries_state =      datafolder + 'boundaries/gadm41_IND_1.shp'                        # GADM India boundaries shapefile
boundaries_district =   datafolder + 'boundaries/gadm41_IND_2.shp'                        # GADM India boundaries shapefile
boundaries_subdist =    datafolder + 'boundaries/gadm41_IND_3.shp'                        # GADM India boundaries shapefile
locationcodes =         datafolder + 'census/CensusIndia2011_LocationDirectory.csv'       # State and district names and codes from Census
pop_tif =               datafolder + 'worldpop/ind_ppp_2011_1km_Aggregated_UNadj.tif'     # WorldPop UN adjusted 1km 2011 (adjust as necessary)
agland =                datafolder + 'dynamicworld/2020_dw_karnataka_cropland.tif'        # DynamicWorld extracted from GEE

# GHSL component files
# Selected files cover India 
ghsl_raw_1 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R6_C25.tif'
ghsl_raw_2 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R6_C26.tif'
ghsl_raw_3 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R6_C27.tif'
ghsl_raw_4 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R7_C25.tif'
ghsl_raw_5 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R7_C26.tif'
ghsl_raw_6 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R7_C27.tif'
ghsl_raw_7 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R7_C28.tif'
ghsl_raw_8 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R8_C26.tif'
ghsl_raw_9 =  datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R8_C27.tif'
ghsl_raw_10 = datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R8_C28.tif'
ghsl_raw_11 = datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R9_C26.tif'
ghsl_raw_12 = datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R9_C27.tif'
ghsl_raw_13 = datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R10_C26.tif'

ghsl_to_merge = glob.glob(datafolder + 'ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_*.tif')  # creates a list containing all the files above
ghsl_to_merge_str = " ".join(ghsl_to_merge)



# Census statistics 
# Currently, this file loads just the data for the test state Karnataka (State Code 29).
# The file has been cleaned from the website download into a readable csv table.
agworkers_29 =          datafolder + 'census/CensusIndia2011_IndustrialCategory_Karnataka_DDW-B04-2900_cln.csv'

# Generated files
# These file paths store intermediate files generated during the analysis
ghsl_merged = outputfolder + 'intermediates/ghsl/ghsl_india.tif'

# Output files
# These file paths store the final output files used in the Results section


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
state_29 = states[states["NAME_1"]=="Karnataka"]
districts_29 = districts[districts["NAME_1"]=="Karnataka"]

# plot the map
fig, ax = plt.subplots() 
state_29.plot(ax = ax, color='green').set_axis_off()
# plt.show()      # use 'show' to bring up a viz window

# fig, ax = plt.subplots()              ## NOT VISUALISING CORRETLY; WHY?
# districts_29.plot(ax = ax, color='bue').set_axis_off()
# plt.show()     



# ==================================================================================================================
# 3. CREATION OF GHSL LAYER

# Create the GHSL layer ready to be joined by location (attributes) with 100m population points
# Merge together the components of the GHSL layer
print('Creating GHSL layer to filter out urban population...')
print()

# *** READ FIRST ****
# The functions below must be run through QGIS.
# However, it should be possible to replace any QGIS functions with internal python packages (e.g. merge from GDAL)

# if not os.path.isfile(ghsl_merged):
#     print('Merging GHSL input layers...')
#     print()
#     processing.run('gdal:merge',
#                    {'INPUT': [ghsl_raw_1, ghsl_raw_2, ghsl_raw_3, ghsl_raw_4],
#                     'PCT': False,
#                     'SEPARATE': False,
#                     'NODATA_INPUT': None,
#                     'NODATA_OUTPUT': None,
#                     'OPTIONS': '',
#                     'EXTRA': '',
#                     'DATA_TYPE': 6,
#                     'OUTPUT': ghsl_merged})
#     print('GHSL input layers merged.')
#     print()


# *** ATTEMPT THROUGH GDAL ****
# command = "gdal_merge.py -o C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp/Data/ghsl/GHSL_Mosaic.tif -of gtiff " + ghsl_to_merge_str
# process = os.popen(command)
# preprocessed = process.read()
# process.close()
# print(os.popen(command).read())     # 'popen' = 'open pipe': opens a pipe to or from command

# *** ATTEMPT #2 ****
gm.main(['', '-o', 'merged.tif', ghsl_raw_1, ghsl_raw_2])


# ISSUES: 2023-06-29
#   Command above is run, but no output is produced. Why?
#   Note that I also had to copy 'gdal_merge.py' from the environment Scripts folder to the working directory
#   The current working directory is 'india_adp' (os.getcwd())   

# print(os.popen('ls C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp/Data/ghsl/').read())


# *** BELOW SCRIPT ***
# Script below has been copied directly from SL python script, which uses QGIS processing

# # Convert crs of merged sri lanka file
# if not os.path.isfile(ghsl_sl_wgs84):
#     print('Changing GHSL merged layers projection...')
#     print()
#     processing.run('gdal:warpreproject',
#                    {'INPUT': ghsl_merged,
#                     'SOURCE_CRS': QgsCoordinateReferenceSystem('ESRI:54009'),
#                     'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
#                     'RESAMPLING': 0,
#                     'NODATA': None,
#                     'TARGET_RESOLUTION': None,
#                     'OPTIONS': '',
#                     'DATA_TYPE': 0,
#                     'TARGET_EXTENT': None,
#                     'TARGET_EXTENT_CRS': None,
#                     'MULTITHREADING': False,
#                     'EXTRA': '',
#                     'OUTPUT': ghsl_sl_wgs84})
#     print('GHSL merged layers projection changed.')
#     print()

# # Vectorise then fix geometries, then clip to sri lanka outline

# # Vectorise
# if not os.path.isfile(ghsl_poly):
#     print('Vectorising re-projected GHSL merged layer...')
#     print()
#     processing.run('gdal:polygonize',
#                    {'INPUT': ghsl_sl_wgs84,
#                     'BAND': 1,
#                     'FIELD': 'settlement_type',
#                     'EIGHT_CONNECTEDNESS': False,
#                     'EXTRA': '',
#                     'OUTPUT': ghsl_poly})
#     print('Re-projected GHSL merged layer vectorised.')
#     print()

# # Fix geometries on new polygon
# if not os.path.isfile(ghsl_sl_wgs84_geom):
#     print('Fixing geometries of GHSL poly layer...')
#     print()
#     processing.run('native:fixgeometries',
#                    {'INPUT': ghsl_poly,
#                     'OUTPUT': ghsl_sl_wgs84_geom})
#     print('Geometries of GHSL poly layer fixed.')
#     print()

# # Now clip the shape to sri lanka boundaries
# if not os.path.isfile(ghsl_merged_clipped):
#     print('Clipping GHSL poly layer...')
#     print()
#     processing.run('native:clip',
#                    {'INPUT': ghsl_sl_wgs84_geom,
#                     'OVERLAY': districts,
#                     'OUTPUT': ghsl_merged_clipped})
#     print('GHSL poly layer clipped.')
#     print()

# print('GHSL layer created.')
# print()
