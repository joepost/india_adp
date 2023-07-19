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
import pandas as pd
# import geopandas as gpd
# import numpy as np
# import matplotlib.pyplot as plt
# from osgeo import gdal

from globals import *       # Imports the filepaths defined in globals.py

print('Packages imported.\n')


# ==================================================================================================================
# 2. QGIS PROCESSES: GHSL
#   Final output: ghsl_india_clipped (ghsl_india_vector_clipped.shp)

# 2.1 Merge GHSL inputs into single raster covering all of India
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


# 2.2 Convert CRS of merged GHSL layer
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


# 2.2b Clip to specified state boundary
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


# 2.3 Vectorise GHSL layer
print('Vectorising re-projected GHSL merged layer...\n')
processing.run('gdal:polygonize',
                   {'INPUT': ghsl_29_clipped, # **TODO: Switch input tp 'ghsl_merged_wgs84' when moving to whole India analysis
                    'BAND': 1,
                    'FIELD': 'settlement_type',
                    'EIGHT_CONNECTEDNESS': False,
                    'EXTRA': '',
                    'OUTPUT': ghsl_poly})
print('Re-projected GHSL merged layer vectorised.\n')


# 2.4 Fix geometries on new polygon
#   This is a process to ensure the generated vector features are valid, and follow OpenGIS compliance (e.g. polygons don't have rings crossing)
#   For details, see: https://gis.stackexchange.com/questions/378154/what-is-fix-geometries-tool-actually-doing-in-qgis
#   Or see: https://www.qgistutorials.com/en/docs/3/handling_invalid_geometries#handling-invalid-geometries-qgis3 
print('Fixing geometries of GHSL poly layer...\n')
processing.run('native:fixgeometries',
                   {'INPUT': ghsl_poly,
                    'OUTPUT': ghsl_poly_fixed})
print('Geometries of GHSL poly layer fixed.\n')


# 2.5 Clip the shape to India state boundaries
#       Does this need to be repeated after clipping with mask (step 2.2b)?
#       YES - the mask has created a square image to the bounding box of state; need to clip polygon exactly
print('Clipping GHSL poly layer...\n')
processing.run('native:clip',
                   {'INPUT': ghsl_poly_fixed,
                    'OVERLAY': districts_29_filepath,    #boundaries_state,
                    'OUTPUT': ghsl_india_clipped})
print('GHSL poly layer clipped.\n')



# ==================================================================================================================
# 3. QGIS PROCESSES: Agricultural Lands (Dynamic World)
#   Final output: cropland_poly_dissolved (cropland_vector_dissolved.shp)


# 3.1 Vectorise DW croplands layer
print('Vectorising DW croplands raster layer...\n')
processing.run('gdal:polygonize',
                   {'INPUT': cropland, 
                    'BAND': 1,
                    'FIELD': 'cropland_bool',
                    'EIGHT_CONNECTEDNESS': False,
                    'EXTRA': '',
                    'OUTPUT': cropland_poly})
print('DW croplands layer vectorised.\n')


# 3.2 Fix geometries on new polygon
print('Fixing geometries of DW croplands poly layer...\n')
processing.run('native:fixgeometries',
                   {'INPUT': cropland_poly,
                    'OUTPUT': cropland_poly_fixed})
print('Geometries of DW croplands poly layer fixed.\n')


# 3.3 Clip the shape to India state boundaries
print('Clipping DW croplands poly layer...\n')
processing.run('native:clip',
                   {'INPUT': cropland_poly_fixed,
                    'OVERLAY': districts_29_filepath,    #boundaries_state,
                    'OUTPUT': cropland_poly_clipped})
print('GHSL poly layer clipped.\n')


# 3.4 Dissolve the vector into a single feature
print('Dissolving DW croplands poly layer into single feature...\n')
processing.run('native:dissolve',
                   {'INPUT': cropland_poly_clipped,
                    'FIELD': 'cropland_b',
                    'OUTPUT': cropland_poly_dissolved})
print('DW croplands poly layer dissolved.\n')


# 3.5 Create spatial index
#       Confirm with FL the purpose of this; speed up processing? 
processing.run('native:createspatialindex',
                   {'INPUT': cropland_poly_dissolved})



# ==================================================================================================================
# 4. QGIS PROCESSES: WorldPop
#   Final output: pop_points (pop_points.shp)


# ALTERNATIVE (added 2023-07-19): 
# 4.0 clip the boundaries of worldpop to state FIRST, and then generate point dataset
#   Reduces the processing load for following steps 
print('Clipping WorldPop raster layer to KARNATAKA district boundaries...\n')
processing.run('gdal:cliprasterbymasklayer',
                   {'INPUT': pop_tif,     # raster to clip
                    'MASK': districts_29_filepath,  # vector mask of desired boundaries
                    'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                    'KEEP_RESOLUTION': True,
                    'OUTPUT': pop_tif_clipped})
print('GHSL raster layer clipped.\n')

# 4.1 Create the point shape file of population from the Worldpop raster input
processing.run('native:pixelstopoints',
                   {'INPUT_RASTER': pop_tif_clipped,
                    'RASTER_BAND': 1,
                    'FIELD_NAME': 'pop_count',
                    'OUTPUT': pop_points})
    

# 4.2 Clip the shape to India state boundaries
#  NOTE: Continues to ERROR OUT; not sure reason. Can successfully be replaced by geopandas functions?
#       Valid as of 2023-07-19
# print('Clipping WorldPop points layer...\n')
# processing.run('native:clip',
#                    {'INPUT': pop_points,
#                     'OVERLAY': districts_29_filepath,    #boundaries_state,
#                     'OUTPUT': pop_points_clipped})
# print('WorldPop points layer clipped.\n')
# ^^^^^^^^ REMOVE; can be done in Script 02


# ==================================================================================================================
# 5. PYTHON PROCESSES:

# **********************
# NOTE: As of 2023-07-11, have switched to Script 02_pythonprocesses.py from this point onward
# **********************


