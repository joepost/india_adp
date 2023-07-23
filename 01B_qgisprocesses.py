# ==================================================================================================================

# DISSERTATION
# SECTION 01B: QGIS Operations
#   This file lists each of the progressive QGIS operations, as used in Sophie's Sri Lanka script.
#   The script should be copied whole into QGIS Python plug-in and run. 

#   Tip: to inspect the documentation for QGIS processes, run: processing.algorithmHelp("processname")

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
# import geopandas as gpd
# import numpy as np
# import matplotlib.pyplot as plt
# from osgeo import gdal

from globals import *       # Imports the filepaths defined in globals.py

print('Packages imported.\n')

# Start timer
start_time = time.time()

# ==================================================================================================================
# 2. QGIS PROCESSES: GHSL
#   Final output: ghsl_india_clipped (ghsl_india_vector_clipped.shp)

# 2.1 Merge GHSL inputs into single raster covering all of India
time_21s = time.time()
print('Merging GHSL input layers...\n')
processing.run('gdal:merge',
                   {'INPUT': ghsl_to_merge,
                    'PCT': False,
                    'SEPARATE': False,
                    'NODATA_INPUT': None,
                    'NODATA_OUTPUT': None,
                    'OPTIONS': '',
                    'EXTRA': '',
                    'DATA_TYPE': 6,
                    'OUTPUT': ghsl_merged})
print('GHSL input layers merged.')
timestamp(time_21s)


# 2.2 Convert CRS of merged GHSL layer
time_22s = time.time()
print('Changing GHSL merged layers projection...\n')
processing.run('gdal:warpreproject',
                   {'INPUT': ghsl_merged,
                    'SOURCE_CRS': QgsCoordinateReferenceSystem('ESRI:54009'),
                    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                    'RESAMPLING': 0,
                    'NODATA': None,
                    'TARGET_RESOLUTION': None,
                    'OPTIONS': '',
                    'DATA_TYPE': 0,
                    'TARGET_EXTENT': None,
                    'TARGET_EXTENT_CRS': None,
                    'MULTITHREADING': False,
                    'EXTRA': '',
                    'OUTPUT': ghsl_merged_wgs84})
print('GHSL merged layers projection changed.\n')
timestamp(time_22s)


# 2.2b Clip to specified state boundary
time_22bs = time.time()
#   Due to the size of full Indian continent, processes from this point onwards are broken down by the state level
#   This requires the creation of state-specific shapefile, from script 01_preparefiles.py
print('Clipping GHSL raster layer to KARNATAKA district boundaries...\n')
processing.run('gdal:cliprasterbymasklayer',
                   {'INPUT': ghsl_merged_wgs84,     # raster to clip
                    'MASK': districts_29_filepath,  # vector mask of desired boundaries
                    'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                    'KEEP_RESOLUTION': True,
                    'OUTPUT': ghsl_29_clipped})
print('GHSL raster layer clipped.\n')
timestamp(time_22bs)


# 2.3 Vectorise GHSL layer
time_23s = time.time()
print('Vectorising re-projected GHSL merged layer...\n')
processing.run('gdal:polygonize',
                   {'INPUT': ghsl_29_clipped, # **TODO: Switch input tp 'ghsl_merged_wgs84' when moving to whole India analysis
                    'BAND': 1,
                    'FIELD': 'settlement_type',
                    'EIGHT_CONNECTEDNESS': False,
                    'EXTRA': '',
                    'OUTPUT': ghsl_poly})
print('Re-projected GHSL merged layer vectorised.\n')
timestamp(time_23s)


# 2.4 Fix geometries on new polygon
time_24s = time.time()
#   This is a process to ensure the generated vector features are valid, and follow OpenGIS compliance (e.g. polygons don't have rings crossing)
#   For details, see: https://gis.stackexchange.com/questions/378154/what-is-fix-geometries-tool-actually-doing-in-qgis
#   Or see: https://www.qgistutorials.com/en/docs/3/handling_invalid_geometries#handling-invalid-geometries-qgis3 
print('Fixing geometries of GHSL poly layer...\n')
processing.run('native:fixgeometries',
                   {'INPUT': ghsl_poly,
                    'OUTPUT': ghsl_poly_fixed})
print('Geometries of GHSL poly layer fixed.\n')
timestamp(time_24s)


# 2.5 Clip the shape to India state boundaries
time_25s = time.time()
#       Does this need to be repeated after clipping with mask (step 2.2b)?
#       YES - the mask has created a square image to the bounding box of state; need to clip polygon exactly
print('Clipping GHSL poly layer...\n')
processing.run('native:clip',
                   {'INPUT': ghsl_poly_fixed,
                    'OVERLAY': districts_29_filepath,    #boundaries_state,
                    'OUTPUT': ghsl_india_clipped})
print('GHSL poly layer clipped.\n')
timestamp(time_25s)



# ==================================================================================================================
# 3. QGIS PROCESSES: Agricultural Lands (Dynamic World)
#   Final output: cropland_poly_dissolved (cropland_vector_dissolved.shp)


# 3.1 Vectorise DW croplands layer
if not os.path.isfile(cropland_poly):
    time_31s = time.time()
    print('Vectorising DW croplands raster layer...\n')
    processing.run("gdal:polygonize", 
                {'INPUT':cropland,
                    'BAND':1,
                    'FIELD':'cropland',
                    'EIGHT_CONNECTEDNESS':False,
                    'EXTRA': '-mask "C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp/Data/dynamicworld/2020_dw_karnataka_cropland_100m.tif"',
                    'OUTPUT': cropland_poly})
    print('DW croplands layer vectorised.\n')
    timestamp(time_31s)

# 3.2 Fix geometries on new polygon
time_32s = time.time()
print('Fixing geometries of DW croplands poly layer...\n')
processing.run('native:fixgeometries',
                   {'INPUT': cropland_poly,
                    'OUTPUT': cropland_poly_fixed})
print('Geometries of DW croplands poly layer fixed.\n')
timestamp(time_32s)


# 3.3 Clip the shape to India state boundaries
# NOTE: No longer required if masking with cropland values in 3.1
# time_33s = time.time()
# print('Clipping DW croplands poly layer...\n')
# processing.run('native:clip',
#                    {'INPUT': cropland_poly_fixed,
#                     'OVERLAY': districts_29_filepath,    #boundaries_state,
#                     'OUTPUT': cropland_poly_clipped})
# print('GHSL poly layer clipped.\n')
# timestamp(time_33s)


# 3.4 Dissolve the vector into a single feature
# Dissolve also causing runtime issues with 100m inputs. Alternative: transfer to 02_python script?
print('Dissolving DW croplands poly layer into single feature...\n')
time_34s = time.time()
processing.run('native:dissolve',
                   {'INPUT': cropland_poly_fixed,
                    'FIELD': 'cropland_b',
                    'OUTPUT': cropland_poly_dissolved})
print('DW croplands poly layer dissolved.\n')
timestamp(time_34s)


# 3.5 Create spatial index
processing.run('native:createspatialindex',
                   {'INPUT': cropland_poly_dissolved})



# ==================================================================================================================
# 4. QGIS PROCESSES: WorldPop
#   Final output: pop_points (pop_points.shp)


# ALTERNATIVE (added 2023-07-19): 
# 4.0 clip the boundaries of worldpop to state FIRST, and then generate point dataset
time_40s = time.time()
#   Reduces the processing load for following steps 
print('Clipping WorldPop raster layer to KARNATAKA district boundaries...\n')
processing.run('gdal:cliprasterbymasklayer',
                   {'INPUT': pop_tif,     # raster to clip
                    'MASK': districts_29_filepath,  # vector mask of desired boundaries
                    'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                    'KEEP_RESOLUTION': True,
                    'OUTPUT': pop_tif_clipped})
print('Worldpop raster layer clipped to state boundaries.\n')
timestamp(time_40s)

# 4.1 Create the point shape file of population from the Worldpop raster input
time_41s = time.time()
processing.run('native:pixelstopoints',
                   {'INPUT_RASTER': pop_tif_clipped,
                    'RASTER_BAND': 1,
                    'FIELD_NAME': 'pop_count',
                    'OUTPUT': pop_points})
print('Worldpop raster layer converted to points.\n')
timestamp(time_41s)
    


print('\nScript complete.\n')
timestamp(start_time)
