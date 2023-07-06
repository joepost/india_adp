# ==================================================================================================================

# DISSERTATION
# SECTION 01B: QGIS Operations
#   This file lists each of the progressive QGIS operations, as used in Sophie's Sri Lanka script.
#   The script should be copied whole into QGIS Python plug-in and run. 
# Date: 2023-07-06
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
# 2. QGIS PROCESSES

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
print('GHSL merged layers projection changed.')




